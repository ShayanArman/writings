#!/usr/bin/env python3
"""Import a public Substack post into this archive's Markdown folder style."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)

class BodyMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "iframe"}:
            self.ignored_tag_depth += 1
            return

        if self.ignored_tag_depth:
            return

        if tag in {"p", "div", "section", "figure", "blockquote", "h1", "h2", "h3", "li"}:
            self._block_break()
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe"} and self.ignored_tag_depth:
            self.ignored_tag_depth -= 1
            return

        if self.ignored_tag_depth:
            return

        if tag in {"p", "div", "section", "figure", "blockquote", "h1", "h2", "h3", "li"}:
            self._block_break()

    def handle_data(self, data: str) -> None:
        if not self.ignored_tag_depth:
            self.parts.append(data)

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.strip() for line in text.strip().splitlines()]
        return "\n".join(lines).strip()

    def _block_break(self) -> None:
        current = "".join(self.parts)
        if current and not current.endswith("\n\n"):
            if current.endswith("\n"):
                self.parts.append("\n")
            else:
                self.parts.append("\n\n")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_preloads(html: str) -> dict:
    match = re.search(
        r"window\._preloads\s*=\s*JSON\.parse\((?P<encoded>\".*?\")\)</script>",
        html,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Substack's embedded post data.")

    encoded_json = json.loads(match.group("encoded"))
    return json.loads(encoded_json)


def html_to_markdown(body_html: str) -> str:
    parser = BodyMarkdownParser()
    parser.feed(body_html)
    parser.close()
    return parser.markdown()


def sanitize_filename(title: str) -> str:
    filename = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    filename = re.sub(r"\s+", " ", filename)
    return filename or "post"


def compose_markdown(title: str, subtitle: str, body: str) -> str:
    chunks = [title.strip()]
    if subtitle.strip():
        chunks.append(subtitle.strip())
    chunks.append(body.strip())
    return "\n".join(chunks[: 1 + bool(subtitle.strip())]) + "\n\n" + chunks[-1] + "\n"


def import_post(url: str, destination: Path, overwrite: bool) -> Path:
    html = fetch_text(url)
    preloads = extract_preloads(html)
    post = preloads.get("post") or {}

    title = (post.get("title") or "").strip()
    body_html = post.get("body_html") or ""
    subtitle = (post.get("subtitle") or "").strip()

    if not title:
        raise ValueError("Could not find a post title.")
    if not body_html:
        raise ValueError("Could not find post body_html.")

    destination.mkdir(parents=True, exist_ok=True)
    body = html_to_markdown(body_html)
    markdown_path = destination / f"{sanitize_filename(title)}.md"

    if markdown_path.exists() and not overwrite:
        raise FileExistsError(f"Markdown file already exists: {markdown_path}")

    markdown_path.write_text(compose_markdown(title, subtitle, body), encoding="utf-8")
    return markdown_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a public Substack post and save it as Markdown."
    )
    parser.add_argument("url", help="Substack post URL")
    parser.add_argument("destination", help="Folder to write into, e.g. 41-60/46")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing Markdown file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    destination = Path(args.destination).expanduser()

    try:
        markdown_path = import_post(args.url, destination, args.overwrite)
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"Network error while fetching Substack post: {error}", file=sys.stderr)
        return 1
    except (FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
