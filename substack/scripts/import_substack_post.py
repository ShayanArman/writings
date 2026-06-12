#!/usr/bin/env python3
"""Import a public Substack post into this archive's Markdown folder style."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)

ORDINAL_NAMES = [
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
]


class BodyMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, int]] = []
        self.images: list[tuple[str, str]] = []
        self.ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_by_name = {name: value or "" for name, value in attrs}

        if tag in {"script", "style", "iframe"}:
            self.ignored_tag_depth += 1
            return

        if self.ignored_tag_depth:
            return

        if tag in {"p", "div", "section", "figure", "blockquote", "h1", "h2", "h3", "li"}:
            self._block_break()
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "a":
            self.links.append((attrs_by_name.get("href", ""), len(self.parts)))
        elif tag == "img":
            source = (
                attrs_by_name.get("src")
                or attrs_by_name.get("data-src")
                or attrs_by_name.get("data-original-src")
            )
            if source:
                placeholder = ordinal_name(len(self.images))
                self.images.append((placeholder, source))
                self._block_break()
                self.parts.append(f"<{placeholder}>")
                self._block_break()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe"} and self.ignored_tag_depth:
            self.ignored_tag_depth -= 1
            return

        if self.ignored_tag_depth:
            return

        if tag == "a" and self.links:
            href, start_index = self.links.pop()
            link_text = "".join(self.parts[start_index:]).strip()
            if href and not link_text:
                self.parts.append(href)
        elif tag in {"p", "div", "section", "figure", "blockquote", "h1", "h2", "h3", "li"}:
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


def ordinal_name(index: int) -> str:
    if index < len(ORDINAL_NAMES):
        return ORDINAL_NAMES[index]
    return f"image-{index + 1}"


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_binary(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get_content_type()


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


def html_to_markdown(body_html: str) -> tuple[str, list[tuple[str, str]]]:
    parser = BodyMarkdownParser()
    parser.feed(body_html)
    parser.close()
    return parser.markdown(), parser.images


def sanitize_filename(title: str) -> str:
    filename = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    filename = re.sub(r"\s+", " ", filename)
    return filename or "post"


def image_extension(url: str, content_type: str) -> str:
    guessed = mimetypes.guess_extension(content_type)
    if guessed == ".jpe":
        return ".jpg"
    if guessed:
        return guessed

    parsed_path = unquote(urlparse(url).path)
    suffix = Path(parsed_path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


def compose_markdown(title: str, subtitle: str, body: str) -> str:
    chunks = [title.strip()]
    if subtitle.strip():
        chunks.append(subtitle.strip())
    chunks.append(body.strip())
    return "\n".join(chunks[: 1 + bool(subtitle.strip())]) + "\n\n" + chunks[-1] + "\n"


def write_images(images: Iterable[tuple[str, str]], destination: Path, overwrite: bool) -> list[Path]:
    written: list[Path] = []
    for placeholder, url in images:
        data, content_type = fetch_binary(url)
        path = destination / f"{placeholder}{image_extension(url, content_type)}"
        if path.exists() and not overwrite:
            raise FileExistsError(f"Image already exists: {path}")
        path.write_bytes(data)
        written.append(path)
    return written


def import_post(url: str, destination: Path, overwrite: bool) -> tuple[Path, list[Path]]:
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
    body, images = html_to_markdown(body_html)
    markdown_path = destination / f"{sanitize_filename(title)}.md"

    if markdown_path.exists() and not overwrite:
        raise FileExistsError(f"Markdown file already exists: {markdown_path}")

    markdown_path.write_text(compose_markdown(title, subtitle, body), encoding="utf-8")
    image_paths = write_images(images, destination, overwrite)
    return markdown_path, image_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a public Substack post and save it as Markdown."
    )
    parser.add_argument("url", help="Substack post URL")
    parser.add_argument("destination", help="Folder to write into, e.g. 41-60/46")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing Markdown file or downloaded images.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    destination = Path(args.destination).expanduser()

    try:
        markdown_path, image_paths = import_post(args.url, destination, args.overwrite)
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"Network error while fetching Substack post: {error}", file=sys.stderr)
        return 1
    except (FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {markdown_path}")
    for image_path in image_paths:
        print(f"Wrote {image_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
