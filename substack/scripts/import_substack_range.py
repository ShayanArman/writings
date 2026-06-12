#!/usr/bin/env python3
"""Import a numbered range of Substack posts from the archive ledgers."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)

RAW_MARKERS = [
    "<script",
    "</script",
    "<style",
    "</style",
    "window._preloads",
    "body_html",
    "Network error while fetching Substack post",
    "Import failed:",
    "Traceback (most recent call last)",
]

BLOCK_TAGS = {
    "article",
    "aside",
    "blockquote",
    "div",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "ol",
    "p",
    "section",
    "ul",
}
IGNORED_TAGS = {"iframe", "script", "style"}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass
class Node:
    tag: str | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    text: str = ""
    children: list["Node"] = field(default_factory=list)


class TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node(tag="root")
        self.stack: list[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        node = Node(tag=tag, attrs={key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(Node(text=data))


class BodyRenderer:
    def __init__(self) -> None:
        self.image_count = 0

    def render(self, body_html: str) -> str:
        parser = TreeParser()
        parser.feed(body_html)
        parser.close()
        return self._clean_markdown(self._render_children(parser.root.children, None))

    def _render_children(self, children: list[Node], figure_caption: str | None) -> str:
        return "".join(self._render_node(child, figure_caption) for child in children)

    def _render_node(self, node: Node, figure_caption: str | None) -> str:
        if node.tag is None:
            return node.text

        if node.tag in IGNORED_TAGS or node.tag == "figcaption":
            return ""

        if node.tag == "br":
            return "\n"

        if node.tag == "img":
            self.image_count += 1
            return f"\n\n{self._image_placeholder(figure_caption)}\n\n"

        if node.tag == "figure":
            caption = self._figure_caption(node)
            rendered = self._render_children(node.children, caption)
            return self._as_block(rendered)

        rendered = self._render_children(node.children, figure_caption)
        if node.tag in BLOCK_TAGS:
            return self._as_block(rendered)
        return rendered

    def _figure_caption(self, node: Node) -> str:
        captions = [
            self._clean_inline_text(self._text_content(child))
            for child in node.children
            if child.tag == "figcaption"
        ]
        return " ".join(caption for caption in captions if caption).strip()

    def _text_content(self, node: Node) -> str:
        if node.tag in IGNORED_TAGS:
            return ""
        if node.tag is None:
            return node.text
        return "".join(self._text_content(child) for child in node.children)

    def _image_placeholder(self, caption: str | None) -> str:
        clean_caption = self._clean_inline_text(caption or "")
        if not clean_caption:
            clean_caption = "caption the image"
        clean_caption = clean_caption.replace("`", "'")
        return f"<todo-image-shayan: add image `{clean_caption}`>"

    def _clean_inline_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _as_block(self, text: str) -> str:
        if not text.strip():
            return ""
        return f"\n\n{text.strip()}\n\n"

    def _clean_markdown(self, text: str) -> str:
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.strip() for line in text.strip().splitlines()]
        return "\n".join(lines).strip()


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


def range_folder(post_number: int) -> str:
    start = ((post_number - 1) // 20) * 20 + 1
    return f"{start}-{start + 19}"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def markdown_files(destination: Path) -> list[Path]:
    if not destination.exists():
        return []
    return sorted(destination.glob("*.md"))


def verify_import(script_dir: Path, repo_root: Path, destination: Path, url: str) -> tuple[bool, str]:
    result = subprocess.run(
        [
            str(script_dir / "verify_substack_import.py"),
            str(destination),
            "--repo-root",
            str(repo_root),
            "--url",
            url,
        ],
        cwd=repo_root / "substack",
        check=False,
        text=True,
        capture_output=True,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def source_post(url: str) -> dict:
    html = fetch_text(url)
    preloads = extract_preloads(html)
    post = preloads.get("post") or {}
    if not (post.get("title") or "").strip():
        raise ValueError("Could not find a post title.")
    if not (post.get("body_html") or "").strip():
        raise ValueError("Could not find post body_html.")
    return post


def assert_clean_markdown(text: str, markdown_path: Path) -> None:
    lowered = text.lower()
    found_markers = [marker for marker in RAW_MARKERS if marker.lower() in lowered]
    if found_markers:
        raise ValueError(
            f"{markdown_path} contains raw import markers: {', '.join(found_markers)}"
        )


def import_one(
    *,
    post_number: int,
    entry: dict,
    repo_root: Path,
    today: str,
    overwrite: bool,
) -> tuple[str, Path | None, int]:
    substack_root = repo_root / "substack"
    script_dir = substack_root / "scripts"
    folder_name = range_folder(post_number)
    destination = substack_root / folder_name / str(post_number)
    url = entry.get("substack_url")

    if not url:
        raise ValueError(f"Post {post_number} has no substack_url.")

    existing_markdown = markdown_files(destination)
    if entry.get("last_verified") and existing_markdown and not overwrite:
        return "skipped", existing_markdown[0], 0
    if existing_markdown and not overwrite:
        names = ", ".join(path.name for path in existing_markdown)
        raise FileExistsError(
            f"Post {post_number} already has Markdown; use --overwrite intentionally: {names}"
        )

    post = source_post(url)
    title = (post.get("title") or "").strip()
    subtitle = (post.get("subtitle") or "").strip()
    body_html = post.get("body_html") or ""

    renderer = BodyRenderer()
    body = renderer.render(body_html)
    markdown_text = compose_markdown(title, subtitle, body)
    placeholder_count = markdown_text.count("<todo-image-shayan: add image `")

    if renderer.image_count != placeholder_count:
        raise ValueError(
            f"Post {post_number} image mismatch: source images={renderer.image_count}, "
            f"placeholders={placeholder_count}"
        )

    destination.mkdir(parents=True, exist_ok=True)
    markdown_path = destination / f"{sanitize_filename(title)}.md"
    if markdown_path.exists() and not overwrite:
        raise FileExistsError(f"Markdown file already exists: {markdown_path}")

    markdown_path.write_text(markdown_text, encoding="utf-8")
    assert_clean_markdown(markdown_text, markdown_path)

    verified, verify_output = verify_import(script_dir, repo_root, destination, url)
    if not verified:
        raise RuntimeError(f"Verification failed for post {post_number}:\n{verify_output}")

    entry["file_number"] = post_number
    entry["title"] = title
    entry["substack_url"] = url
    if renderer.image_count:
        entry["images_added_locally"] = False
        entry["images_linked_in_post"] = True
    else:
        entry["images_added_locally"] = None
        entry["images_linked_in_post"] = None
    entry["last_verified"] = today

    return "imported", markdown_path, renderer.image_count


def imported_count_for_range(substack_root: Path, entries: dict) -> int:
    count = 0
    for key, entry in entries.items():
        destination = substack_root / range_folder(int(key)) / key
        if entry.get("last_verified") and markdown_files(destination):
            count += 1
    return count


def compact_numbers(numbers: list[int]) -> str:
    if not numbers:
        return ""

    ranges: list[str] = []
    start = previous = numbers[0]
    for number in numbers[1:]:
        if number == previous + 1:
            previous = number
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = number
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def refresh_dashboard(repo_root: Path, affected_ranges: set[str], today: str) -> None:
    dashboard_path = repo_root / "substack" / "dashboard.json"
    if not dashboard_path.exists():
        return

    dashboard = load_json(dashboard_path)
    substack_root = repo_root / "substack"

    for folder_name in sorted(affected_ranges, key=lambda name: int(name.split("-", 1)[0])):
        posts_list_path = substack_root / folder_name / "posts-list.json"
        if not posts_list_path.exists():
            continue

        entries = load_json(posts_list_path)
        imported_count = imported_count_for_range(substack_root, entries)
        unverified = [
            int(key)
            for key, entry in entries.items()
            if entry.get("substack_url") and not entry.get("last_verified")
        ]
        deferred_images = [
            int(key)
            for key, entry in entries.items()
            if entry.get("images_added_locally") is False
        ]

        remaining: list[str] = []
        if unverified:
            remaining.append(f"Import posts {compact_numbers(unverified)} when ready.")
            status = "in_progress"
        elif deferred_images:
            remaining.append(
                f"Add deferred/manual images for posts {compact_numbers(deferred_images)}."
            )
            status = "needs_image_review"
        else:
            status = "complete"

        dashboard[folder_name] = {
            "posts_list": f"{folder_name}/posts-list.json",
            "status": status,
            "imported_count": imported_count,
            "remaining": remaining,
            "last_updated": today,
        }

    write_json(dashboard_path, dashboard)


def import_range(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    today = args.date or date.today().isoformat()

    imported = 0
    skipped = 0
    image_posts: list[int] = []
    affected_ranges: set[str] = set()
    current_posts_list_path: Path | None = None
    current_entries: dict | None = None

    for post_number in range(args.start, args.end + 1):
        folder_name = range_folder(post_number)
        affected_ranges.add(folder_name)
        posts_list_path = repo_root / "substack" / folder_name / "posts-list.json"
        key = str(post_number)

        if posts_list_path != current_posts_list_path:
            if current_posts_list_path and current_entries is not None:
                write_json(current_posts_list_path, current_entries)
                refresh_dashboard(repo_root, affected_ranges, today)
            current_posts_list_path = posts_list_path
            current_entries = load_json(posts_list_path)

        if current_entries is None or key not in current_entries:
            print(f"FAIL post {post_number}: missing entry in {posts_list_path}", file=sys.stderr)
            return 1

        entry = current_entries[key]
        print(f"POST {post_number}: {entry.get('title') or '(untitled)'}")
        try:
            action, markdown_path, image_count = import_one(
                post_number=post_number,
                entry=entry,
                repo_root=repo_root,
                today=today,
                overwrite=args.overwrite,
            )
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"FAIL post {post_number}: network error: {error}", file=sys.stderr)
            return 1
        except (
            FileExistsError,
            RuntimeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            print(f"FAIL post {post_number}: {error}", file=sys.stderr)
            return 1

        if action == "skipped":
            skipped += 1
            print(f"  skipped verified: {markdown_path}")
        else:
            imported += 1
            if image_count:
                image_posts.append(post_number)
            print(f"  imported: {markdown_path} (images={image_count})")
            write_json(posts_list_path, current_entries)
            refresh_dashboard(repo_root, affected_ranges, today)

    if current_posts_list_path and current_entries is not None:
        write_json(current_posts_list_path, current_entries)
    refresh_dashboard(repo_root, affected_ranges, today)

    print(
        "RESULT passed "
        f"imported={imported} skipped={skipped} "
        f"image_posts={compact_numbers(image_posts) or 'none'}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a numeric range of Substack posts using posts-list.json URLs."
    )
    parser.add_argument("start", type=int, help="First post number to import.")
    parser.add_argument("end", type=int, help="Last post number to import.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to this script's repo.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing Markdown files intentionally.",
    )
    parser.add_argument(
        "--date",
        help="Verification date to write into posts-list.json. Defaults to today.",
    )
    args = parser.parse_args()

    if args.start < 1 or args.end < args.start:
        parser.error("range must be positive and end must be greater than or equal to start")
    return args


def main() -> int:
    return import_range(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
