#!/usr/bin/env python3
"""Read-only fidelity audit for Shayan Arman's Substack-to-MDX migrations."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from audit_substack_images import TreeParser, clean_inline_text, node_caption, text_content
from import_substack_post import USER_AGENT, html_to_markdown


SCRIPT_PATH = Path(__file__).resolve()
WRITINGS_ROOT = SCRIPT_PATH.parents[2]
SUBSTACK_ROOT = WRITINGS_ROOT / "substack"
SHAYAN_ROOT = WRITINGS_ROOT.parent
SITE_ROOT = SHAYAN_ROOT / "shayan-arman-blog"
LIVE_ROOT = SITE_ROOT / "site/live-posts/shayan-arman-blog/writings"
NODE_EXTRACTOR = SCRIPT_PATH.with_name("extract_audit_events.mjs")
RESULTS_PATH = SUBSTACK_ROOT / "audit-results.json"
PLAYWRIGHT_WRAPPER = (
    Path.home() / ".codex/skills/playwright/scripts/playwright_cli.sh"
)
PLAYWRIGHT_SESSION = "shayan-audit"

BUCKET = "seo-gangster"
WRITINGS_PREFIX = "sites/shayan-arman-blog/posts/writings/"
IMAGE_PREFIX = "sites/shayan-arman-blog/public/images/posts/"
LIVE_BASE = "https://www.shayanarman.com/writings"

TODO_IMAGE_RE = re.compile(
    r"^\s*<todo-image-shayan:\s*add image(?:\s+`(?P<caption>[^`]*)`)?\s*>\s*$"
)
MARKDOWN_IMAGE_RE = re.compile(
    r"^\s*!\[(?P<alt>[^\]]*)\]\((?P<url>[^)]+)\)\s*$"
)
ITALIC_LINE_RE = re.compile(r"^\s*\*(?P<caption>.+)\*\s*$")
HASHTAG_RE = re.compile(r"(?<![\w#])#[A-Za-z0-9_]+")
PLAIN_URL_RE = re.compile(r"https?://[^\s<>]+")
VOID_HTML_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
SOURCE_CHROME_COMPONENTS = {"ButtonCreateButton", "SubscribeWidgetToDOM"}


class AuditError(RuntimeError):
    """A deterministic audit failure that should be recorded."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def range_folder(post_number: int) -> str:
    start = ((post_number - 1) // 20) * 20 + 1
    return f"{start}-{start + 19}"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary.write(payload)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 90,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown command failure"
        raise AuditError(f"Command failed ({' '.join(command[:3])}): {detail}")
    return result


def extract_with_node(kind: str, path: Path) -> dict[str, Any]:
    result = run_command(
        ["node", str(NODE_EXTRACTOR), kind, str(path)],
        cwd=WRITINGS_ROOT,
        timeout=120,
        check=False,
    )
    output = result.stdout.strip()
    if not output:
        raise AuditError(result.stderr.strip() or f"Node extractor returned no output for {path}")
    try:
        payload = json.loads(output.splitlines()[-1])
    except json.JSONDecodeError as error:
        raise AuditError(f"Node extractor returned invalid JSON for {path}") from error
    if payload.get("parse", {}).get("status") != "PASS":
        raise AuditError(
            f"Node extractor could not parse {path}: {payload.get('parse', {}).get('error')}"
        )
    return payload


def fetch_bytes(url: str, *, timeout: int = 45, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/html,image/avif,image/webp,image/*,*/*",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(attempt)
    raise AuditError(f"Could not fetch {url}: {last_error}")


def fetch_json(url: str) -> tuple[dict[str, Any], bytes]:
    raw = fetch_bytes(url)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise AuditError(f"Invalid JSON from {url}") from error
    if not isinstance(payload, dict):
        raise AuditError(f"Expected a JSON object from {url}")
    return payload, raw


def ledger_for_post(post_number: int) -> tuple[Path, dict[str, Any]]:
    ledger_path = SUBSTACK_ROOT / range_folder(post_number) / "posts-list.json"
    entries = load_json(ledger_path)
    entry = entries.get(str(post_number))
    if not isinstance(entry, dict):
        raise AuditError(f"Post {post_number} is missing from {ledger_path}")
    return ledger_path, entry


def archive_for_post(post_number: int) -> Path:
    folder = SUBSTACK_ROOT / range_folder(post_number) / str(post_number)
    candidates = sorted(folder.glob("*.md"))
    if len(candidates) != 1:
        raise AuditError(f"Expected one archive Markdown file in {folder}, found {len(candidates)}")
    return candidates[0]


def substack_api_url(entry: dict[str, Any]) -> str:
    source_url = str(entry.get("substack_url") or "")
    parsed = urlparse(source_url)
    matched = re.fullmatch(r"/p/([^/]+)", parsed.path.rstrip("/"))
    if not matched:
        raise AuditError(f"Cannot derive Substack API slug from {source_url!r}")
    return f"https://shayanarman.substack.com/api/v1/posts/{matched.group(1)}"


def strip_archive_header_and_media(
    raw: str,
    *,
    title: str,
    subtitle: str | None,
) -> tuple[str, list[dict[str, Any]]]:
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    if index < len(lines) and lines[index].strip() == title.strip():
        lines[index] = ""
        index += 1
    if subtitle and index < len(lines) and lines[index].strip() == subtitle.strip():
        lines[index] = ""

    media: list[dict[str, Any]] = []
    skip_lines: set[int] = set()
    for line_index, line in enumerate(lines):
        todo = TODO_IMAGE_RE.fullmatch(line)
        if todo:
            todo_caption = normalize_text(todo.group("caption")) or None
            if todo_caption == "caption the image":
                todo_caption = None
            media.append(
                {
                    "kind": "todo",
                    "src": None,
                    "alt": None,
                    "caption": todo_caption,
                    "line": line_index + 1,
                }
            )
            skip_lines.add(line_index)
            continue

        image_match = MARKDOWN_IMAGE_RE.fullmatch(line)
        if not image_match:
            continue

        item = {
            "kind": "markdown",
            "src": image_match.group("url"),
            "alt": normalize_text(image_match.group("alt")) or None,
            "caption": None,
            "line": line_index + 1,
        }
        skip_lines.add(line_index)
        next_index = line_index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index < len(lines):
            caption_match = ITALIC_LINE_RE.fullmatch(lines[next_index])
            if caption_match:
                item["caption"] = normalize_text(caption_match.group("caption")) or None
                skip_lines.add(next_index)
        media.append(item)

    for line_index in skip_lines:
        lines[line_index] = ""

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip() + "\n"
    return cleaned, media


def has_descendant(node: Any, tag: str) -> bool:
    if getattr(node, "tag", None) == tag:
        return True
    return any(has_descendant(child, tag) for child in getattr(node, "children", []))


def direct_source_url(attrs: dict[str, str]) -> str | None:
    encoded = attrs.get("data-attrs") or ""
    if encoded:
        try:
            payload = json.loads(encoded)
            candidate = payload.get("src")
            if isinstance(candidate, str) and candidate:
                return candidate
        except json.JSONDecodeError:
            pass
    source = attrs.get("src") or ""
    if source.startswith("https://substack-post-media.s3.amazonaws.com/"):
        return source
    decoded = html.unescape(source)
    matched = re.search(
        r"https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com%2F[^?&\"']+",
        decoded,
        flags=re.I,
    )
    if matched:
        from urllib.parse import unquote

        return unquote(matched.group(0))
    return source or None


def strip_source_platform_chrome(body_html: str) -> str:
    """Remove Substack UI components that are not authored post content."""
    parser = TreeParser()
    parser.feed(body_html)
    parser.close()

    def serialize(node: Any) -> str:
        if getattr(node, "tag", None) is None:
            return html.escape(str(getattr(node, "text", "")), quote=False)
        if node.tag == "root":
            return "".join(serialize(child) for child in node.children)
        if node.attrs.get("data-component-name") in SOURCE_CHROME_COMPONENTS:
            return ""
        attributes = "".join(
            f' {key}="{html.escape(str(value), quote=True)}"'
            for key, value in node.attrs.items()
        )
        opening = f"<{node.tag}{attributes}>"
        if node.tag in VOID_HTML_TAGS:
            return opening
        return opening + "".join(serialize(child) for child in node.children) + f"</{node.tag}>"

    return serialize(parser.root)


def source_semantic_events(body_html: str) -> list[dict[str, str]]:
    """Extract authored HTML blocks without flattening their semantic kinds."""
    parser = TreeParser()
    parser.feed(body_html)
    parser.close()

    def visible_text(node: Any) -> str:
        tag = getattr(node, "tag", None)
        if tag is None:
            return str(getattr(node, "text", ""))
        if tag in {"script", "style", "iframe", "figure", "figcaption"}:
            return ""
        if tag == "br":
            return "\n"
        return "".join(visible_text(child) for child in getattr(node, "children", []))

    events: list[dict[str, str]] = []

    def append(kind: str, node: Any) -> None:
        raw_text = visible_text(node)
        chunks = re.split(r"\n\s*\n", raw_text) if kind == "paragraph" else [raw_text]
        for chunk in chunks:
            text = normalize_text(chunk)
            if text:
                events.append({"kind": kind, "text": text})

    def walk(node: Any) -> None:
        tag = getattr(node, "tag", None)
        if tag in {"script", "style", "iframe", "figure", "figcaption"}:
            return
        if tag == "blockquote":
            append("blockquote", node)
            return
        if tag in {"ul", "ol"}:
            for child in getattr(node, "children", []):
                if getattr(child, "tag", None) == "li":
                    append("list-item", child)
            return
        if tag == "li":
            append("list-item", node)
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            append(f"heading{tag[1:]}", node)
            return
        if tag == "pre":
            append("code", node)
            return
        if tag == "hr":
            events.append({"kind": "thematic-break", "text": "---"})
            return
        if tag == "p":
            append("paragraph", node)
            return
        for child in getattr(node, "children", []):
            walk(child)

    walk(parser.root)
    return events


def source_media_and_links(body_html: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    parser = TreeParser()
    parser.feed(body_html)
    parser.close()
    media: list[dict[str, Any]] = []
    links: list[dict[str, str]] = []

    def walk(node: Any, inherited_caption: str = "") -> None:
        tag = getattr(node, "tag", None)
        if tag is None:
            for matched in PLAIN_URL_RE.findall(str(getattr(node, "text", ""))):
                url = html.unescape(matched).rstrip(".,;:!?")
                links.append({"text": normalize_text(url), "url": url})
            return
        if tag in {"script", "style", "iframe", "figcaption"}:
            return

        caption = inherited_caption
        attrs = getattr(node, "attrs", {})
        if tag == "figure" or "captioned" in attrs.get("class", ""):
            caption = node_caption(node)

        if tag == "img":
            data_attrs: dict[str, Any] = {}
            if attrs.get("data-attrs"):
                try:
                    parsed_attrs = json.loads(attrs["data-attrs"])
                    if isinstance(parsed_attrs, dict):
                        data_attrs = parsed_attrs
                except json.JSONDecodeError:
                    pass
            media.append(
                {
                    "source_url": direct_source_url(attrs),
                    "caption": clean_inline_text(caption) or None,
                    "alt": clean_inline_text(attrs.get("alt", "")) or None,
                    "width": data_attrs.get("width") or attrs.get("width") or None,
                    "height": data_attrs.get("height") or attrs.get("height") or None,
                }
            )
            return

        if tag == "a":
            if not has_descendant(node, "img"):
                visible = clean_inline_text(text_content(node))
                href = attrs.get("href", "")
                if visible and href:
                    links.append({"text": normalize_text(visible), "url": html.unescape(href)})
                return
            for child in getattr(node, "children", []):
                walk(child, caption)
            return

        for child in getattr(node, "children", []):
            walk(child, caption)

    walk(parser.root)
    return media, links


def normalize_event_texts(extraction: dict[str, Any]) -> list[str]:
    return [normalize_text(event.get("text")) for event in extraction.get("events", [])]


def normalize_event_shapes(extraction: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"kind": str(event.get("kind")), "text": normalize_text(event.get("text"))}
        for event in extraction.get("events", [])
    ]


def compact_diff(left: Iterable[str], right: Iterable[str], left_label: str, right_label: str) -> str:
    left_lines = [f"[{index + 1}] {value}" for index, value in enumerate(left)]
    right_lines = [f"[{index + 1}] {value}" for index, value in enumerate(right)]
    lines = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=left_label,
            tofile=right_label,
            lineterm="",
            n=2,
        )
    )
    return "\n".join(lines[:80])


def unique_hashtags(text: str) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for hashtag in HASHTAG_RE.findall(text):
        normalized = hashtag.lower()
        if normalized not in seen:
            seen.add(normalized)
            output.append(normalized)
    return output


def s3_key_from_uri(uri: str) -> str:
    prefix = f"s3://{BUCKET}/"
    if not uri.startswith(prefix):
        raise AuditError(f"S3 URI escapes the authorized bucket: {uri}")
    key = uri[len(prefix) :]
    if not key.startswith("sites/shayan-arman-blog/"):
        raise AuditError(f"S3 URI escapes the authorized site prefix: {uri}")
    return key


def s3_head(key: str) -> dict[str, Any]:
    if not key.startswith("sites/shayan-arman-blog/"):
        raise AuditError(f"Refusing S3 head outside authorized prefix: {key}")
    result = run_command(
        [
            "aws",
            "s3api",
            "head-object",
            "--bucket",
            BUCKET,
            "--key",
            key,
            "--output",
            "json",
        ],
        timeout=60,
    )
    return json.loads(result.stdout)


def file_metadata(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    metadata: dict[str, Any] = {
        "bytes": len(raw),
        "md5": md5_bytes(raw),
        "sha256": sha256_bytes(raw),
        "mime": mimetypes.guess_type(path.name)[0],
        "format": None,
        "width": None,
        "height": None,
        "encoded_width": None,
        "encoded_height": None,
        "exif_orientation": None,
    }
    try:
        from PIL import Image

        with Image.open(path) as image:
            metadata["format"] = image.format
            encoded_width, encoded_height = image.size
            exif_orientation = image.getexif().get(274)
            display_width, display_height = (
                (encoded_height, encoded_width)
                if exif_orientation in {5, 6, 7, 8}
                else (encoded_width, encoded_height)
            )
            metadata["width"] = display_width
            metadata["height"] = display_height
            metadata["encoded_width"] = encoded_width
            metadata["encoded_height"] = encoded_height
            metadata["exif_orientation"] = exif_orientation
            metadata["mime"] = Image.MIME.get(image.format, metadata["mime"])
    except Exception:
        file_result = run_command(["file", "-b", "--mime-type", str(path)], check=False)
        if file_result.returncode == 0:
            metadata["mime"] = file_result.stdout.strip() or metadata["mime"]
        sips_result = run_command(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            check=False,
        )
        if sips_result.returncode == 0:
            width = re.search(r"pixelWidth:\s*(\d+)", sips_result.stdout)
            height = re.search(r"pixelHeight:\s*(\d+)", sips_result.stdout)
            if width and height:
                metadata["width"] = int(width.group(1))
                metadata["height"] = int(height.group(1))
                metadata["encoded_width"] = metadata["width"]
                metadata["encoded_height"] = metadata["height"]
    return metadata


def perceptual_difference(left: Path, right: Path) -> float:
    """Return normalized mean pixel difference after EXIF-aware thumbnailing."""
    from PIL import Image, ImageChops, ImageOps, ImageStat

    with Image.open(left) as left_image, Image.open(right) as right_image:
        left_sample = ImageOps.exif_transpose(left_image).convert("RGB").resize((64, 64))
        right_sample = ImageOps.exif_transpose(right_image).convert("RGB").resize((64, 64))
        difference = ImageChops.difference(left_sample, right_sample)
        return sum(ImageStat.Stat(difference).mean) / (3 * 255)


def playwright_result_json(output: str) -> dict[str, Any]:
    matched = re.search(r"### Result\n(?P<json>\{.*?\}|\[.*?\])\n### ", output, flags=re.DOTALL)
    if not matched:
        raise AuditError(f"Could not parse Playwright result: {output[-800:]}")
    try:
        payload = json.loads(matched.group("json"))
    except json.JSONDecodeError as error:
        raise AuditError("Playwright returned invalid result JSON") from error
    if not isinstance(payload, dict):
        raise AuditError("Playwright result was not an object")
    return payload


def browser_audit(url: str) -> dict[str, Any]:
    if not PLAYWRIGHT_WRAPPER.exists():
        raise AuditError(f"Playwright wrapper not found: {PLAYWRIGHT_WRAPPER}")
    encoded_url = json.dumps(url)
    code = f"""async (page) => {{
  const consoleErrors = [];
  const pageErrors = [];
  const requestFailures = [];
  const onConsole = (message) => {{ if (message.type() === 'error') consoleErrors.push(message.text()); }};
  const onPageError = (error) => pageErrors.push(String(error));
  const onRequestFailed = (request) => requestFailures.push({{url: request.url(), error: request.failure()?.errorText || 'failed'}});
  page.on('console', onConsole);
  page.on('pageerror', onPageError);
  page.on('requestfailed', onRequestFailed);
  await page.setViewportSize({{width: 1440, height: 900}});
  let response = null;
  let navigationError = null;
  try {{
    response = await page.goto({encoded_url}, {{waitUntil: 'domcontentloaded', timeout: 45000}});
    await page.waitForSelector('main article', {{timeout: 30000}});
    await page.waitForLoadState('networkidle', {{timeout: 15000}}).catch(() => null);
    for (const image of await page.$$('main article img')) {{
      await image.scrollIntoViewIfNeeded().catch(() => null);
      await page.waitForTimeout(100);
    }}
    await page.waitForFunction(
      () => Array.from(document.querySelectorAll('main article img')).every((image) => image.complete && image.naturalWidth > 0),
      null,
      {{timeout: 20000}},
    ).catch(() => null);
    await page.evaluate(() => window.scrollTo(0, 0));
  }} catch (error) {{ navigationError = String(error); }}
  const desktop = await page.evaluate(() => {{
    const normalize = (value) => String(value || '').replace(/\\r\\n?/g, '\\n').normalize('NFC').replace(/[\\t ]+/g, ' ').replace(/ *\\n */g, '\\n').trim();
    const article = document.querySelector('main article');
    const body = article?.lastElementChild || null;
    const children = [];
    if (body) {{
      for (const element of Array.from(body.children)) {{
        if (element.tagName === 'SECTION' || element.getAttribute('role') === 'separator' || element.querySelector('nav[aria-label]')) break;
        children.push(element);
      }}
    }}
    const events = [];
    const links = [];
    const media = [];
    for (const element of children) {{
      const tag = element.tagName;
      if (tag === 'FIGURE') {{
        const image = element.querySelector('img');
        if (!image) continue;
        const caption = element.querySelector('figcaption');
        media.push({{
          alt: image?.getAttribute('alt') || null,
          src: image?.currentSrc || image?.getAttribute('src') || null,
          width: image?.getAttribute('width') ? Number(image.getAttribute('width')) : null,
          height: image?.getAttribute('height') ? Number(image.getAttribute('height')) : null,
          naturalWidth: image?.naturalWidth || 0,
          naturalHeight: image?.naturalHeight || 0,
          complete: Boolean(image?.complete),
          caption: normalize(caption?.textContent) || null,
          caption_links: Array.from(caption?.querySelectorAll('a') || []).map((link) => ({{text: normalize(link.textContent), url: link.getAttribute('href') || ''}})),
          event_index: events.length,
        }});
        continue;
      }}
      if (tag === 'BR') continue;
      if (tag === 'UL' || tag === 'OL') {{
        for (const item of Array.from(element.children)) {{
          const text = normalize(item.textContent);
          if (text) events.push({{kind: 'list-item', text}});
        }}
      }} else if (tag === 'BLOCKQUOTE') {{
        events.push({{kind: 'blockquote', text: normalize(element.textContent)}});
      }} else if (/^H[1-6]$/.test(tag)) {{
        events.push({{kind: 'heading' + tag.slice(1), text: normalize(element.textContent)}});
      }} else if (tag === 'PRE') {{
        events.push({{kind: 'code', text: normalize(element.textContent)}});
      }} else if (tag === 'HR') {{
        events.push({{kind: 'thematic-break', text: '---'}});
      }} else {{
        const text = normalize(element.textContent);
        if (text) events.push({{kind: tag === 'P' ? 'paragraph' : tag.toLowerCase(), text}});
      }}
      for (const link of Array.from(element.querySelectorAll('a'))) {{
        links.push({{text: normalize(link.textContent), url: link.getAttribute('href') || ''}});
      }}
    }}
    const articleChildren = Array.from(article?.children || []);
    const headingIndex = articleChildren.findIndex((element) => element.tagName === 'H1');
    const bodyIndex = articleChildren.indexOf(body);
    const headerTexts = articleChildren.slice(headingIndex + 1, bodyIndex).map((element) => normalize(element.textContent)).filter(Boolean);
    return {{
      url: location.href,
      documentTitle: document.title,
      canonical: document.querySelector('link[rel="canonical"]')?.getAttribute('href') || null,
      h1: normalize(article?.querySelector('h1')?.textContent) || null,
      headerTexts,
      sourceHref: Array.from(article?.querySelectorAll('a') || []).find((link) => normalize(link.textContent) === 'Source article')?.getAttribute('href') || null,
      events,
      links,
      media,
      h1Count: document.querySelectorAll('main article h1').length,
      desktopOverflow: document.documentElement.scrollWidth > window.innerWidth,
    }};
  }});
  const mobilePage = await page.context().newPage();
  await mobilePage.setViewportSize({{width: 390, height: 844}});
  await mobilePage.goto({encoded_url}, {{waitUntil: 'domcontentloaded', timeout: 45000}}).catch(() => null);
  await mobilePage.waitForSelector('main article', {{timeout: 30000}}).catch(() => null);
  await mobilePage.waitForTimeout(500);
  const mobile = await mobilePage.evaluate(() => ({{overflow: document.documentElement.scrollWidth > window.innerWidth, width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth}}));
  await mobilePage.close();
  page.off('console', onConsole);
  page.off('pageerror', onPageError);
  page.off('requestfailed', onRequestFailed);
  return {{status: response?.status() || null, navigationError, desktop, mobile, consoleErrors, pageErrors, requestFailures}};
}}"""
    result = run_command(
        [
            str(PLAYWRIGHT_WRAPPER),
            "--session",
            PLAYWRIGHT_SESSION,
            "run-code",
            code,
        ],
        cwd=WRITINGS_ROOT,
        timeout=90,
        check=False,
    )
    if result.returncode:
        raise AuditError(result.stderr.strip() or result.stdout.strip() or "Playwright failed")
    return playwright_result_json(result.stdout)


def lane(status: str, summary: str, **evidence: Any) -> dict[str, Any]:
    return {"status": status, "summary": summary, "evidence": evidence}


def compare_links(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    *,
    decode_percent: bool = False,
) -> bool:
    def normalized_url(value: Any) -> str:
        url = html.unescape(str(value or ""))
        return unquote(url) if decode_percent else url

    normalized_left = [
        {"text": normalize_text(item.get("text")), "url": normalized_url(item.get("url"))}
        for item in left
    ]
    normalized_right = [
        {"text": normalize_text(item.get("text")), "url": normalized_url(item.get("url"))}
        for item in right
    ]
    return normalized_left == normalized_right


def result_store(path: Path) -> dict[str, Any]:
    if path.exists():
        value = load_json(path)
        if not isinstance(value, dict):
            raise AuditError(f"Audit results root must be an object: {path}")
        value.setdefault("schema_version", 1)
        value.setdefault("posts", {})
        return value
    return {
        "schema_version": 1,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "inventory": {},
        "posts": {},
    }


def record_post_result(path: Path, result: dict[str, Any]) -> None:
    store = result_store(path)
    store["posts"][str(result["post_number"])] = result
    store["updated_at"] = utc_now()
    write_json_atomic(path, store)


def finding_rows(post_number: int, lanes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    severity = {
        "inventory": "P0",
        "s3_identity": "P1",
        "metadata": "P1",
        "text": "P1",
        "structure": "P2",
        "links": "P1",
        "hashtags": "P1",
        "media": "P1",
        "mdx_compile": "P0",
        "live_render": "P0",
    }
    rows = []
    for name, value in lanes.items():
        if value["status"] == "PASS":
            continue
        lane_severity = severity.get(name, "P2")
        if name == "live_render":
            summary = str(value.get("summary") or "").lower()
            if "overflow" in summary or "image" in summary or "caption" in summary:
                lane_severity = "P2"
            elif "body events" in summary or "body links" in summary:
                lane_severity = "P1"
        rows.append(
            {
                "id": f"AP-{post_number:04d}-{name.upper().replace('_', '-')}",
                "severity": lane_severity,
                "lane": name,
                "summary": value["summary"],
                "status": "AMBIGUOUS" if value["status"] == "REVIEW" else "OPEN",
            }
        )
    return rows


def reclassify_results(path: Path) -> dict[str, int]:
    store = result_store(path)
    updated = 0
    for key, result in store.get("posts", {}).items():
        post_number = int(key)
        result["findings"] = finding_rows(post_number, result.get("lanes", {}))
        updated += 1
    store["updated_at"] = utc_now()
    write_json_atomic(path, store)
    return {"posts": updated}


def overall_status(lanes: dict[str, dict[str, Any]]) -> str:
    statuses = {value["status"] for value in lanes.values()}
    if "BLOCKED" in statuses:
        return "BLOCKED"
    if "FAIL" in statuses:
        return "FAIL"
    if "REVIEW" in statuses:
        return "REVIEW"
    return "PASS"


def audit_post(
    post_number: int,
    *,
    results_path: Path,
    use_browser: bool,
    verify_source_images: bool,
    mdx_override: Path | None = None,
    record: bool = True,
) -> dict[str, Any]:
    started_at = utc_now()
    ledger_path, entry = ledger_for_post(post_number)
    archive_path = archive_for_post(post_number)
    draft_file = str(entry.get("draft_file") or "")
    local_mdx_path = mdx_override or (LIVE_ROOT / draft_file)
    expected_mdx_path = LIVE_ROOT / draft_file
    s3_key = f"{WRITINGS_PREFIX}{draft_file}"
    slug = str(entry.get("draft_slug") or "")
    public_url = f"{LIVE_BASE}/{slug}"
    temp_dir = Path(f"/private/tmp/shayan-post-audit-{post_number}")
    if temp_dir.exists():
        raise AuditError(f"Temporary directory already exists: {temp_dir}")
    temp_dir.mkdir()
    created_paths: list[Path] = []

    result: dict[str, Any] = {
        "post_number": post_number,
        "title": entry.get("title"),
        "started_at": started_at,
        "completed_at": None,
        "paths": {
            "ledger": str(ledger_path.relative_to(WRITINGS_ROOT)),
            "archive": str(archive_path.relative_to(WRITINGS_ROOT)),
            "local_mdx": str(expected_mdx_path),
            "s3_key": s3_key,
            "public_url": public_url,
        },
        "hashes": {},
        "lanes": {},
        "findings": [],
        "overall": "BLOCKED",
    }

    try:
        archive_raw = archive_path.read_bytes()
        local_mdx_raw = local_mdx_path.read_bytes()
        result["hashes"]["archive_sha256"] = sha256_bytes(archive_raw)
        result["hashes"]["local_mdx_sha256"] = sha256_bytes(local_mdx_raw)
        result["hashes"]["local_mdx_md5"] = md5_bytes(local_mdx_raw)

        inventory_errors = []
        if int(entry.get("file_number") or -1) != post_number:
            inventory_errors.append("ledger file_number does not match key")
        if local_mdx_path != expected_mdx_path and mdx_override is None:
            inventory_errors.append("resolved local MDX path is unexpected")
        if not expected_mdx_path.exists():
            inventory_errors.append("expected local live MDX is missing")
        expected_name = f"{str(entry.get('published_at') or '')[:10]}-{slug}.mdx"
        if draft_file != expected_name:
            inventory_errors.append(f"draft_file {draft_file!r} != {expected_name!r}")
        result["lanes"]["inventory"] = lane(
            "FAIL" if inventory_errors else "PASS",
            "; ".join(inventory_errors) if inventory_errors else "Ledger, archive, and local MDX identity resolve exactly.",
            errors=inventory_errors,
        )

        s3_metadata = s3_head(s3_key)
        s3_etag = str(s3_metadata.get("ETag") or "").strip('"')
        s3_size = int(s3_metadata.get("ContentLength") or -1)
        s3_errors = []
        if s3_size != len(local_mdx_raw):
            s3_errors.append(f"local bytes={len(local_mdx_raw)} S3 bytes={s3_size}")
        if "-" not in s3_etag and s3_etag != md5_bytes(local_mdx_raw):
            s3_errors.append("local MD5 does not match S3 ETag")
        if s3_errors:
            s3_download = temp_dir / "s3-published.mdx"
            run_command(
                [
                    "aws",
                    "s3api",
                    "get-object",
                    "--bucket",
                    BUCKET,
                    "--key",
                    s3_key,
                    str(s3_download),
                ],
                timeout=90,
            )
            created_paths.append(s3_download)
            s3_raw = s3_download.read_bytes()
            result["hashes"]["downloaded_s3_mdx_sha256"] = sha256_bytes(s3_raw)
            if s3_raw != local_mdx_raw:
                s3_errors.append("downloaded S3 MDX bytes differ from local live MDX")
            else:
                s3_errors = []
        result["s3"] = {
            "etag": s3_etag,
            "content_length": s3_size,
            "content_type": s3_metadata.get("ContentType"),
            "last_modified": s3_metadata.get("LastModified"),
        }
        result["lanes"]["s3_identity"] = lane(
            "FAIL" if s3_errors else "PASS",
            "; ".join(s3_errors) if s3_errors else "Local live MDX is byte-identical to the exact S3 object.",
            errors=s3_errors,
            etag=s3_etag,
            bytes=s3_size,
        )

        source, source_raw = fetch_json(substack_api_url(entry))
        source_path = temp_dir / "source.json"
        source_path.write_bytes(source_raw)
        created_paths.append(source_path)
        result["hashes"]["source_json_sha256"] = sha256_bytes(source_raw)

        source_body_html = strip_source_platform_chrome(str(source.get("body_html") or ""))
        source_body_text = html_to_markdown(source_body_html)
        source_body_path = temp_dir / "source-body.md"
        source_body_path.write_text(source_body_text + "\n", encoding="utf-8")
        created_paths.append(source_body_path)

        archive_cleaned, archive_media = strip_archive_header_and_media(
            archive_raw.decode("utf-8"),
            title=str(entry.get("title") or ""),
            subtitle=entry.get("subtitle"),
        )
        archive_body_path = temp_dir / "archive-body.md"
        archive_body_path.write_text(archive_cleaned, encoding="utf-8")
        created_paths.append(archive_body_path)

        source_extract = {"events": source_semantic_events(source_body_html)}
        archive_extract = extract_with_node("archive", archive_body_path)
        mdx_extract = extract_with_node("mdx", local_mdx_path)
        result["hashes"].update(
            {
                "source_event_sha256": stable_hash(source_extract.get("events", [])),
                "archive_event_sha256": archive_extract.get("eventHash"),
                "mdx_event_sha256": mdx_extract.get("eventHash"),
            }
        )

        metadata = mdx_extract.get("metadata", {})
        metadata_errors = []
        source_title = str(source.get("title") or "").strip()
        source_subtitle = str(source.get("subtitle") or "").strip() or None
        expected_metadata = {
            "title": source_title,
            "subtitle": source_subtitle,
            "date": str(source.get("post_date") or "")[:10],
            "category": "Writings",
            "collection": "Writings",
            "author": "Shayan Arman",
            "source-url": source.get("canonical_url") or entry.get("substack_url"),
        }
        for key, expected in expected_metadata.items():
            actual = metadata.get(key)
            actual = actual if actual not in ("", None) else None
            expected = expected if expected not in ("", None) else None
            if key in {"title", "subtitle", "source-url"}:
                actual = str(actual).strip() if actual is not None else None
                expected = str(expected).strip() if expected is not None else None
            if actual != expected:
                metadata_errors.append(f"{key}: MDX={actual!r} source={expected!r}")
        if str(entry.get("title") or "").strip() != source_title:
            metadata_errors.append("ledger title differs from Substack")
        if (str(entry.get("subtitle") or "").strip() or None) != source_subtitle:
            metadata_errors.append("ledger subtitle differs from Substack")
        if entry.get("published_at") != source.get("post_date"):
            metadata_errors.append("ledger published_at differs from Substack")
        if entry.get("substack_url") != source.get("canonical_url"):
            metadata_errors.append("ledger URL differs from Substack canonical_url")
        result["lanes"]["metadata"] = lane(
            "FAIL" if metadata_errors else "PASS",
            "; ".join(metadata_errors) if metadata_errors else "Canonical identity metadata matches Substack, ledger, filename, and MDX.",
            errors=metadata_errors,
            expected=expected_metadata,
        )

        source_texts = normalize_event_texts(source_extract)
        archive_texts = normalize_event_texts(archive_extract)
        mdx_texts = normalize_event_texts(mdx_extract)
        source_archive_equal = source_texts == archive_texts
        archive_mdx_equal = archive_texts == mdx_texts
        source_mdx_equal = source_texts == mdx_texts
        if source_archive_equal and archive_mdx_equal:
            text_status = "PASS"
            text_summary = "Substack, archive, and MDX visible text match exactly."
            text_diff = ""
        elif source_archive_equal and not archive_mdx_equal:
            text_status = "FAIL"
            text_summary = "Confirmed migration text defect: Substack and archive agree but MDX differs."
            text_diff = compact_diff(archive_texts, mdx_texts, "archive", "mdx")
        else:
            text_status = "REVIEW"
            text_summary = "Substack, archive, and MDX text do not establish one unambiguous direction of truth."
            if not source_archive_equal:
                text_diff = compact_diff(source_texts, archive_texts, "substack", "archive")
            else:
                text_diff = compact_diff(source_texts, mdx_texts, "substack", "mdx")
        result["lanes"]["text"] = lane(
            text_status,
            text_summary,
            source_archive_equal=source_archive_equal,
            archive_mdx_equal=archive_mdx_equal,
            source_mdx_equal=source_mdx_equal,
            diff=text_diff,
        )

        source_shapes = normalize_event_shapes(source_extract)
        archive_shapes = normalize_event_shapes(archive_extract)
        mdx_shapes = normalize_event_shapes(mdx_extract)
        source_archive_structure_equal = source_shapes == archive_shapes
        archive_mdx_structure_equal = archive_shapes == mdx_shapes
        source_mdx_structure_equal = source_shapes == mdx_shapes
        if source_archive_structure_equal and archive_mdx_structure_equal:
            structure_status = "PASS"
            structure_summary = "Substack, archive, and MDX block structure match exactly."
            structure_diff = ""
        elif source_archive_structure_equal and not archive_mdx_structure_equal:
            structure_status = "FAIL"
            structure_summary = "Confirmed migration structure defect: Substack and archive agree but MDX differs."
            structure_diff = compact_diff(
                [json.dumps(item, ensure_ascii=False) for item in archive_shapes],
                [json.dumps(item, ensure_ascii=False) for item in mdx_shapes],
                "archive-structure",
                "mdx-structure",
            )
        else:
            structure_status = "REVIEW"
            structure_summary = "Substack, archive, and MDX structure do not establish one unambiguous direction of truth."
            structure_diff = compact_diff(
                [json.dumps(item, ensure_ascii=False) for item in source_shapes],
                [json.dumps(item, ensure_ascii=False) for item in archive_shapes],
                "substack-structure",
                "archive-structure",
            )
        result["lanes"]["structure"] = lane(
            structure_status,
            structure_summary,
            source_archive_equal=source_archive_structure_equal,
            archive_mdx_equal=archive_mdx_structure_equal,
            source_mdx_equal=source_mdx_structure_equal,
            diff=structure_diff,
        )

        source_media, source_links = source_media_and_links(source_body_html)
        archive_links = archive_extract.get("links", [])
        mdx_links = mdx_extract.get("links", [])
        source_archive_links_equal = compare_links(source_links, archive_links)
        archive_mdx_links_equal = compare_links(archive_links, mdx_links)
        source_mdx_links_equal = compare_links(source_links, mdx_links)
        if source_archive_links_equal and archive_mdx_links_equal:
            links_status = "PASS"
            links_summary = "Substack, archive, and MDX link pairs match exactly."
        elif source_archive_links_equal and not archive_mdx_links_equal:
            links_status = "FAIL"
            links_summary = "Confirmed migration link defect: Substack and archive agree but MDX differs."
        else:
            links_status = "REVIEW"
            links_summary = "Substack, archive, and MDX links do not establish one unambiguous direction of truth."
        result["lanes"]["links"] = lane(
            links_status,
            links_summary,
            source=source_links,
            archive=archive_links,
            mdx=mdx_links,
            source_archive_equal=source_archive_links_equal,
            archive_mdx_equal=archive_mdx_links_equal,
            source_mdx_equal=source_mdx_links_equal,
        )

        source_hashtags = unique_hashtags(source_body_text)
        archive_hashtags = unique_hashtags(archive_cleaned)
        metadata_hashtags = [str(value).lower() for value in metadata.get("hashtags", []) or []]
        source_archive_hashtags_equal = source_hashtags == archive_hashtags
        archive_mdx_hashtags_equal = archive_hashtags == metadata_hashtags
        source_mdx_hashtags_equal = source_hashtags == metadata_hashtags
        if source_archive_hashtags_equal and archive_mdx_hashtags_equal:
            hashtags_status = "PASS"
            hashtags_summary = "Literal source, archive, and frontmatter hashtags match."
        elif source_archive_hashtags_equal and not archive_mdx_hashtags_equal:
            hashtags_status = "FAIL"
            hashtags_summary = "Confirmed migration hashtag defect: Substack and archive agree but MDX differs."
        else:
            hashtags_status = "REVIEW"
            hashtags_summary = "Substack, archive, and frontmatter hashtags do not establish one unambiguous direction of truth."
        result["lanes"]["hashtags"] = lane(
            hashtags_status,
            hashtags_summary,
            source=source_hashtags,
            archive=archive_hashtags,
            mdx=metadata_hashtags,
            source_archive_equal=source_archive_hashtags_equal,
            archive_mdx_equal=archive_mdx_hashtags_equal,
            source_mdx_equal=source_mdx_hashtags_equal,
        )

        ledger_images = entry.get("images") or []
        body_ledger_images = [
            image for image in ledger_images if image.get("usage") != "thumbnail"
        ]
        mdx_media = mdx_extract.get("media", [])
        media_errors = []
        media_reviews = []
        if len(source_media) != len(archive_media):
            media_reviews.append(
                f"source images={len(source_media)} archive image tokens={len(archive_media)}"
            )
        if len(archive_media) != len(body_ledger_images):
            media_errors.append(
                f"archive image tokens={len(archive_media)} body ledger images={len(body_ledger_images)}"
            )
        if len(body_ledger_images) != len(mdx_media):
            media_errors.append(
                f"body ledger images={len(body_ledger_images)} MDX images={len(mdx_media)}"
            )

        image_evidence = []
        body_image_index = 0
        for image_index, ledger_image in enumerate(ledger_images):
            is_thumbnail_only = ledger_image.get("usage") == "thumbnail"
            if is_thumbnail_only:
                source_item = {}
                archive_item = {}
                mdx_item = {}
            else:
                source_item = (
                    source_media[body_image_index]
                    if body_image_index < len(source_media)
                    else {}
                )
                archive_item = (
                    archive_media[body_image_index]
                    if body_image_index < len(archive_media)
                    else {}
                )
                mdx_item = (
                    mdx_media[body_image_index]
                    if body_image_index < len(mdx_media)
                    else {}
                )
                body_image_index += 1
            expected_source_url = ledger_image.get("source_url")
            expected_s3_uri = ledger_image.get("s3_uri")
            if not is_thumbnail_only and source_item.get("source_url") != expected_source_url:
                media_reviews.append(f"image {image_index + 1} source URL differs from ledger")
            if not is_thumbnail_only and mdx_item.get("src") != expected_s3_uri:
                media_errors.append(f"image {image_index + 1} MDX S3 URI differs from ledger")
            if not is_thumbnail_only and int(mdx_item.get("width") or -1) != int(ledger_image.get("width") or -1):
                media_errors.append(f"image {image_index + 1} MDX width differs from ledger")
            if not is_thumbnail_only and int(mdx_item.get("height") or -1) != int(ledger_image.get("height") or -1):
                media_errors.append(f"image {image_index + 1} MDX height differs from ledger")
            source_caption = normalize_text(source_item.get("caption")) or None
            archive_caption = normalize_text(archive_item.get("caption")) or None
            mdx_caption = normalize_text(mdx_item.get("caption")) or None
            if not is_thumbnail_only and archive_caption != mdx_caption:
                media_errors.append(
                    f"image {image_index + 1} archive caption differs from MDX: "
                    f"archive={archive_caption!r} MDX={mdx_caption!r}"
                )
            if not is_thumbnail_only and source_caption != archive_caption:
                media_reviews.append(
                    f"image {image_index + 1} source caption differs from archive: "
                    f"source={source_caption!r} archive={archive_caption!r}"
                )
            if not is_thumbnail_only and bool(mdx_caption) != bool(mdx_item.get("has_caption_spacer")):
                media_errors.append(f"image {image_index + 1} caption spacer contract differs")
            if not is_thumbnail_only and not normalize_text(mdx_item.get("alt")):
                media_errors.append(f"image {image_index + 1} has empty alt text")

            evidence: dict[str, Any] = {
                "index": image_index + 1,
                "usage": "thumbnail" if is_thumbnail_only else "body",
                "source_url": expected_source_url,
                "s3_uri": expected_s3_uri,
            }
            if verify_source_images and expected_source_url and expected_s3_uri:
                suffix = Path(urlparse(expected_source_url).path).suffix or Path(
                    str(ledger_image.get("filename") or "image.bin")
                ).suffix
                source_image_path = temp_dir / f"source-image-{image_index + 1}{suffix}"
                source_image_path.write_bytes(fetch_bytes(expected_source_url, timeout=60))
                created_paths.append(source_image_path)
                source_file = file_metadata(source_image_path)
                image_head = s3_head(s3_key_from_uri(expected_s3_uri))
                image_etag = str(image_head.get("ETag") or "").strip('"')
                evidence.update({"source_file": source_file, "s3": image_head})
                processing = normalize_text(ledger_image.get("processing"))
                if processing:
                    expected_key = s3_key_from_uri(expected_s3_uri)
                    s3_suffix = Path(str(ledger_image.get("filename") or "image.bin")).suffix
                    s3_image_path = temp_dir / f"s3-image-{image_index + 1}{s3_suffix}"
                    run_command(
                        [
                            "aws", "s3api", "get-object", "--bucket", BUCKET,
                            "--key", expected_key, str(s3_image_path),
                        ],
                        timeout=90,
                    )
                    created_paths.append(s3_image_path)
                    s3_file = file_metadata(s3_image_path)
                    evidence.update({"processing": processing, "s3_file": s3_file})
                    ledger_dimensions = {
                        int(ledger_image.get("width") or -1),
                        int(ledger_image.get("height") or -1),
                    }
                    source_dimensions = {
                        int(source_file.get("width") or -2),
                        int(source_file.get("height") or -2),
                    }
                    if source_dimensions != ledger_dimensions:
                        media_errors.append(
                            f"image {image_index + 1} converted source resolution differs from ledger"
                        )
                    if (
                        int(s3_file.get("width") or -1) != int(ledger_image.get("width") or -1)
                        or int(s3_file.get("height") or -1) != int(ledger_image.get("height") or -1)
                    ):
                        media_errors.append(
                            f"image {image_index + 1} converted S3 dimensions differ from ledger"
                        )
                    if "-" not in image_etag and s3_file.get("md5") != image_etag:
                        media_errors.append(
                            f"image {image_index + 1} converted S3 MD5 differs from ETag"
                        )
                    converted_source_path = temp_dir / f"source-image-{image_index + 1}-converted.jpg"
                    conversion = run_command(
                        [
                            "sips", "-s", "format", "jpeg", str(source_image_path),
                            "--out", str(converted_source_path),
                        ],
                        timeout=120,
                        check=False,
                    )
                    if conversion.returncode:
                        media_errors.append(
                            f"image {image_index + 1} documented conversion could not be visually checked"
                        )
                    else:
                        created_paths.append(converted_source_path)
                        visual_difference = perceptual_difference(
                            converted_source_path, s3_image_path
                        )
                        evidence["perceptual_difference"] = visual_difference
                        if visual_difference > 0.03:
                            media_errors.append(
                                f"image {image_index + 1} converted visual content differs"
                            )
                else:
                    if "-" not in image_etag and image_etag != source_file["md5"]:
                        media_errors.append(f"image {image_index + 1} source MD5 differs from S3 ETag")
                    if int(image_head.get("ContentLength") or -1) != source_file["bytes"]:
                        media_errors.append(f"image {image_index + 1} source bytes differ from S3")
                    if source_file.get("width") != int(ledger_image.get("width") or -1):
                        media_errors.append(f"image {image_index + 1} native width differs from ledger")
                    if source_file.get("height") != int(ledger_image.get("height") or -1):
                        media_errors.append(f"image {image_index + 1} native height differs from ledger")
            image_evidence.append(evidence)

        thumbnail = metadata.get("thumbnail")
        ledger_uris = [image.get("s3_uri") for image in ledger_images]
        if thumbnail and thumbnail not in ledger_uris:
            media_errors.append("thumbnail is not one of the current post's ledger images")
        if not ledger_images and thumbnail:
            media_errors.append("text-only post has a thumbnail")
        if not body_ledger_images and mdx_media:
            media_errors.append("text-only post has body media")
        media_status = "FAIL" if media_errors else "REVIEW" if media_reviews else "PASS"
        media_summary = "; ".join(media_errors or media_reviews)
        result["lanes"]["media"] = lane(
            media_status,
            media_summary if media_summary else "Source, archive, ledger, MDX, and S3 media identity match.",
            errors=media_errors,
            reviews=media_reviews,
            images=image_evidence,
        )

        compile_errors = []
        if mdx_extract.get("compile", {}).get("status") != "PASS":
            compile_errors.append(str(mdx_extract.get("compile", {}).get("error")))
        if mdx_extract.get("footerSequence") != [
            "ShareArticleClipboard",
            "ArticleDivider",
            "ProductLinks",
        ]:
            compile_errors.append("footer sequence is missing, duplicated, or reordered")
        if mdx_extract.get("rawMarkers"):
            compile_errors.append(f"raw markers remain: {mdx_extract['rawMarkers']}")
        if mdx_extract.get("rawMarkdownImages"):
            compile_errors.append("raw Markdown image remains in MDX")
        result["lanes"]["mdx_compile"] = lane(
            "FAIL" if compile_errors else "PASS",
            "; ".join(compile_errors) if compile_errors else "MDX parses, compiles, and satisfies the footer/artifact contract.",
            errors=compile_errors,
        )

        if use_browser:
            browser = browser_audit(public_url)
            result["browser"] = browser
            desktop = browser.get("desktop") or {}
            live_errors = []
            if browser.get("status") != 200:
                live_errors.append(f"HTTP status is {browser.get('status')}")
            if browser.get("navigationError"):
                live_errors.append(f"navigation failed: {browser['navigationError']}")
            if desktop.get("url") != public_url:
                live_errors.append(f"final URL is {desktop.get('url')!r}")
            if desktop.get("canonical") != public_url:
                live_errors.append(f"canonical is {desktop.get('canonical')!r}")
            if normalize_text(desktop.get("h1")) != normalize_text(entry.get("title")):
                live_errors.append("rendered H1 differs from ledger title")
            if desktop.get("sourceHref") != entry.get("substack_url"):
                live_errors.append("rendered source href differs from ledger URL")
            if desktop.get("h1Count") != 1:
                live_errors.append(f"rendered H1 count is {desktop.get('h1Count')}")
            expected_header_first = entry.get("subtitle") or metadata.get("excerpt")
            if expected_header_first and (desktop.get("headerTexts") or [None])[0] != expected_header_first:
                live_errors.append("rendered subtitle/excerpt header differs")
            live_events = [
                {"kind": item.get("kind"), "text": normalize_text(item.get("text"))}
                for item in desktop.get("events", [])
            ]
            if live_events != mdx_shapes:
                live_errors.append("rendered body events differ from local/S3 MDX")
            if not compare_links(desktop.get("links", []), mdx_links, decode_percent=True):
                live_errors.append("rendered body links differ from MDX")
            public_media = desktop.get("media", [])
            if len(public_media) != len(mdx_media):
                live_errors.append("rendered figure count differs from MDX")
            for index, public_image in enumerate(public_media):
                if not public_image.get("complete") or not public_image.get("naturalWidth"):
                    live_errors.append(f"rendered image {index + 1} did not load")
                if index < len(mdx_media):
                    if normalize_text(public_image.get("caption")) != normalize_text(
                        mdx_media[index].get("caption")
                    ):
                        live_errors.append(f"rendered image {index + 1} caption differs from MDX")
                    if public_image.get("alt") != mdx_media[index].get("alt"):
                        live_errors.append(f"rendered image {index + 1} alt differs from MDX")
            if desktop.get("desktopOverflow") or (browser.get("mobile") or {}).get("overflow"):
                live_errors.append("page overflows the viewport")
            if browser.get("pageErrors"):
                live_errors.append(f"browser page errors: {browser['pageErrors'][:3]}")
            first_party_failures = [
                failure
                for failure in browser.get("requestFailures", [])
                if str(failure.get("url") or "").startswith("https://www.shayanarman.com/")
            ]
            if first_party_failures:
                live_errors.append(f"failed first-party requests: {first_party_failures[:3]}")
            result["lanes"]["live_render"] = lane(
                "FAIL" if live_errors else "PASS",
                "; ".join(live_errors) if live_errors else "Public route renders the exact MDX body, links, and media without browser errors.",
                errors=live_errors,
                console_errors=browser.get("consoleErrors", []),
            )
        else:
            result["lanes"]["live_render"] = lane(
                "BLOCKED", "Real-browser validation was skipped by command option."
            )

        result["overall"] = overall_status(result["lanes"])
        result["findings"] = finding_rows(post_number, result["lanes"])
        result["completed_at"] = utc_now()
        if record:
            record_post_result(results_path, result)
        return result
    except Exception as error:
        result["lanes"].setdefault(
            "runtime",
            lane("BLOCKED", f"Audit could not obtain required evidence: {error}"),
        )
        result["overall"] = "BLOCKED"
        result["completed_at"] = utc_now()
        result["findings"] = [
            {
                "id": f"AP-{post_number:04d}-RUNTIME",
                "severity": "P0",
                "lane": "runtime",
                "summary": str(error),
                "status": "OPEN",
            }
        ]
        if record:
            record_post_result(results_path, result)
        return result
    finally:
        for path in reversed(created_paths):
            if path.exists() and path.parent == temp_dir:
                path.unlink()
        if temp_dir.exists() and not any(temp_dir.iterdir()):
            temp_dir.rmdir()


def inventory_preflight(results_path: Path) -> dict[str, Any]:
    entries: dict[int, dict[str, Any]] = {}
    ledger_paths = sorted(SUBSTACK_ROOT.glob("*/posts-list.json"))
    for ledger_path in ledger_paths:
        for key, value in load_json(ledger_path).items():
            entries[int(key)] = value

    errors = []
    expected_numbers = set(range(1, 409))
    if set(entries) != expected_numbers:
        errors.append("ledger numbers do not cover 1-408 exactly")

    archive_paths = []
    for post_number in range(1, 409):
        folder = SUBSTACK_ROOT / range_folder(post_number) / str(post_number)
        candidates = sorted(folder.glob("*.md"))
        if len(candidates) != 1:
            errors.append(f"post {post_number} has {len(candidates)} archive Markdown files")
        archive_paths.extend(candidates)

    expected_files = {str(value.get("draft_file") or "") for value in entries.values()}
    local_files = {path.name for path in LIVE_ROOT.glob("*.mdx")}
    if expected_files != local_files:
        errors.append(
            f"local filename set mismatch: missing={sorted(expected_files-local_files)} extra={sorted(local_files-expected_files)}"
        )

    for post_number, entry in entries.items():
        if entry.get("file_number") != post_number:
            errors.append(f"post {post_number} file_number mismatch")
        required = ["title", "substack_url", "published_at", "draft_slug", "draft_file"]
        if any(not entry.get(field) for field in required):
            errors.append(f"post {post_number} missing required ledger identity")
        expected_name = f"{str(entry.get('published_at') or '')[:10]}-{entry.get('draft_slug')}.mdx"
        if entry.get("draft_file") != expected_name:
            errors.append(f"post {post_number} draft filename/date/slug mismatch")

    for field in ["substack_url", "draft_slug", "draft_file"]:
        values = [entry.get(field) for entry in entries.values()]
        if len(set(values)) != 408:
            errors.append(f"ledger field {field} is not globally unique")

    s3_result = run_command(
        [
            "aws",
            "s3api",
            "list-objects-v2",
            "--bucket",
            BUCKET,
            "--prefix",
            WRITINGS_PREFIX,
            "--output",
            "json",
        ],
        timeout=90,
    )
    s3_payload = json.loads(s3_result.stdout)
    s3_files = {
        str(item.get("Key") or "")[len(WRITINGS_PREFIX) :]
        for item in s3_payload.get("Contents", [])
        if str(item.get("Key") or "").endswith(".mdx")
    }
    if s3_files != expected_files:
        errors.append(
            f"S3 filename set mismatch: missing={sorted(expected_files-s3_files)} extra={sorted(s3_files-expected_files)}"
        )

    dashboard = load_json(SUBSTACK_ROOT / "dashboard.json")
    dashboard_mdx = sum(int(value.get("published_mdx_count") or 0) for value in dashboard.values())
    dashboard_imported = sum(int(value.get("imported_count") or 0) for value in dashboard.values())
    if dashboard_mdx != 408 or dashboard_imported != 408:
        errors.append(
            f"dashboard totals disagree: mdx={dashboard_mdx} imported={dashboard_imported}"
        )

    report = {
        "checked_at": utc_now(),
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "counts": {
            "ledger_entries": len(entries),
            "archive_markdown": len(archive_paths),
            "local_mdx": len(local_files),
            "s3_mdx": len(s3_files),
            "dashboard_mdx": dashboard_mdx,
            "dashboard_imported": dashboard_imported,
        },
        "hashes": {
            "expected_filenames": stable_hash(sorted(expected_files)),
            "local_filenames": stable_hash(sorted(local_files)),
            "s3_filenames": stable_hash(sorted(s3_files)),
        },
    }
    store = result_store(results_path)
    store["inventory"] = report
    store["updated_at"] = utc_now()
    write_json_atomic(results_path, store)
    return report


def self_test() -> int:
    fixtures = {
        1: "2024-10-04-coming-soon.mdx",
        3: "2024-10-12-freedom-from.mdx",
        51: "2025-01-27-on-work.mdx",
        112: "2025-06-18-on-language-parts-and-position.mdx",
        408: "2026-08-11-a-new-mind.mdx",
    }
    failures = []
    for post_number, filename in fixtures.items():
        path = LIVE_ROOT / filename
        extracted = extract_with_node("mdx", path)
        if extracted.get("compile", {}).get("status") != "PASS":
            failures.append(f"fixture {post_number} does not compile")
    if (extract_with_node("mdx", LIVE_ROOT / fixtures[1]).get("metadata", {}).get("subtitle")):
        failures.append("post 1 should not have a subtitle")
    if extract_with_node("mdx", LIVE_ROOT / fixtures[408]).get("metadata", {}).get("subtitle") != "Lessons from the Dawn of the Quantum Age":
        failures.append("post 408 subtitle fixture mismatch")
    if extract_with_node("mdx", LIVE_ROOT / fixtures[112]).get("metadata", {}).get("source-url") != "https://shayanarman.substack.com/p/on-language-eae":
        failures.append("post 112 source fixture mismatch")

    with tempfile.TemporaryDirectory(prefix="shayan-audit-self-test-", dir="/private/tmp") as folder:
        temp_root = Path(folder)
        original_path = LIVE_ROOT / fixtures[3]
        original_raw = original_path.read_text(encoding="utf-8")
        original = extract_with_node("mdx", original_path)

        mutations = {
            "word": original_raw.replace("He got an entire MIT", "He got an MIT", 1),
            "punctuation": original_raw.replace("Scott Young!", "Scott Young?", 1),
            "link": original_raw.replace(
                "[https://thaly.ai](https://thaly.ai)",
                "[https://thaly.ai](https://example.com)",
                1,
            ),
        }
        for name, raw in mutations.items():
            path = temp_root / f"{name}.mdx"
            path.write_text(raw, encoding="utf-8")
            mutated = extract_with_node("mdx", path)
            text_changed = normalize_event_texts(original) != normalize_event_texts(mutated)
            links_changed = original.get("links") != mutated.get("links")
            if name in {"word", "punctuation"} and (not text_changed or links_changed):
                failures.append(f"{name} negative control did not isolate the text lane")
            if name == "link" and (text_changed or not links_changed):
                failures.append("link negative control did not isolate the link lane")

        caption_original_path = LIVE_ROOT / fixtures[51]
        caption_raw = caption_original_path.read_text(encoding="utf-8")
        caption_mutated = caption_raw.replace(
            'caption="The Death of Achilles, Rubens"',
            'caption="The Death of Achilles, Rubens?"',
            1,
        )
        caption_path = temp_root / "caption.mdx"
        caption_path.write_text(caption_mutated, encoding="utf-8")
        caption_original = extract_with_node("mdx", caption_original_path)
        caption_result = extract_with_node("mdx", caption_path)
        if normalize_event_texts(caption_original) != normalize_event_texts(caption_result):
            failures.append("caption negative control changed the text lane")
        if caption_original.get("media") == caption_result.get("media"):
            failures.append("caption negative control did not change the media lane")

        move_raw = original_raw
        component_match = re.search(r"\n<GangsterImage\n[\s\S]*?\n/>\n", move_raw)
        target = "\nA bunch of guys came after"
        if component_match and target in move_raw:
            component = component_match.group(0)
            without = move_raw[: component_match.start()] + "\n" + move_raw[component_match.end() :]
            moved = without.replace(target, component + target, 1)
            move_path = temp_root / "move-image.mdx"
            move_path.write_text(moved, encoding="utf-8")
            move_result = extract_with_node("mdx", move_path)
            if normalize_event_texts(original) != normalize_event_texts(move_result):
                failures.append("image-move negative control changed the text lane")
            if original.get("media") == move_result.get("media"):
                failures.append("image-move negative control did not change media position")
        else:
            failures.append("could not construct image-move negative control")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"RESULT self-test failed ({len(failures)} issue(s))")
        return 1
    print("RESULT self-test passed: fixtures and five negative controls behaved correctly")
    return 0


def print_post_summary(result: dict[str, Any]) -> None:
    lanes = " ".join(
        f"{name}={value.get('status')}" for name, value in result.get("lanes", {}).items()
    )
    print(
        f"POST {result['post_number']:03d} {result.get('overall')} "
        f"{result.get('title')!r} {lanes}",
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post", type=int, nargs="?", help="One post number to audit")
    parser.add_argument("--start", type=int, help="First post in a sequential range")
    parser.add_argument("--end", type=int, help="Last post in a sequential range")
    parser.add_argument("--inventory", action="store_true", help="Run collection inventory preflight")
    parser.add_argument("--self-test", action="store_true", help="Run fixture and negative-control tests")
    parser.add_argument("--reclassify", action="store_true", help="Refresh finding severities from saved lanes")
    parser.add_argument("--skip-browser", action="store_true", help="Skip real-browser validation (records BLOCKED)")
    parser.add_argument("--skip-source-images", action="store_true", help="Skip source-image byte checks")
    parser.add_argument("--no-record", action="store_true", help="Do not update audit-results.json")
    parser.add_argument("--mdx-override", type=Path, help="Temporary MDX override for a one-post diagnostic")
    parser.add_argument("--results", type=Path, default=RESULTS_PATH)
    args = parser.parse_args()
    if args.self_test or args.inventory or args.reclassify:
        return args
    if args.post is not None and (args.start is not None or args.end is not None):
        parser.error("use either one post or --start/--end")
    if args.post is None and (args.start is None or args.end is None):
        parser.error("provide a post number or both --start and --end")
    start = args.post if args.post is not None else args.start
    end = args.post if args.post is not None else args.end
    if start is None or end is None or start < 1 or end > 408 or end < start:
        parser.error("post range must be within 1-408")
    if args.mdx_override and start != end:
        parser.error("--mdx-override is valid only for one post")
    return args


def main() -> int:
    args = parse_args()
    results_path = args.results.expanduser().resolve()
    if args.self_test:
        return self_test()
    if args.inventory:
        report = inventory_preflight(results_path)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    if args.reclassify:
        print(json.dumps(reclassify_results(results_path), indent=2))
        return 0

    start = args.post if args.post is not None else args.start
    end = args.post if args.post is not None else args.end
    assert start is not None and end is not None
    exit_code = 0
    for post_number in range(start, end + 1):
        result = audit_post(
            post_number,
            results_path=results_path,
            use_browser=not args.skip_browser,
            verify_source_images=not args.skip_source_images,
            mdx_override=args.mdx_override,
            record=not args.no_record,
        )
        print_post_summary(result)
        if result["overall"] != "PASS":
            exit_code = 1
        if result["overall"] == "BLOCKED":
            break
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
