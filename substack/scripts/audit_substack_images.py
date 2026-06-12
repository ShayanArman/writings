#!/usr/bin/env python3
"""Audit Substack source images against local Markdown image references."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)
TODO_PREFIX = "<todo-image-shayan: add image `"
TODO_RE = re.compile(r"<todo-image-shayan: add image `([^`]*)`>")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


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
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(Node(text=data))


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


def source_post(url: str) -> dict:
    preloads = extract_preloads(fetch_text(url))
    post = preloads.get("post") or {}
    if not (post.get("title") or "").strip():
        raise ValueError("Could not find a post title.")
    return post


def clean_inline_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def text_content(node: Node) -> str:
    if node.tag in {"script", "style", "iframe"}:
        return ""
    if node.tag is None:
        return node.text
    return "".join(text_content(child) for child in node.children)


def node_caption(node: Node) -> str:
    captions: list[str] = []
    for child in node.children:
        classes = child.attrs.get("class", "")
        if child.tag == "figcaption" or "caption" in classes:
            caption = clean_inline_text(text_content(child))
            if caption:
                captions.append(caption)
    return " ".join(captions).strip()


def source_image_captions(body_html: str) -> list[str]:
    parser = TreeParser()
    parser.feed(body_html)
    parser.close()
    captions: list[str] = []

    def walk(node: Node, inherited_caption: str = "") -> None:
        if node.tag in {"script", "style", "iframe", "figcaption"}:
            return
        caption = inherited_caption
        if node.tag == "figure" or "captioned" in node.attrs.get("class", ""):
            caption = node_caption(node)
        if node.tag == "img":
            captions.append(clean_inline_text(caption))
            return
        for child in node.children:
            walk(child, caption)

    walk(parser.root)
    return captions


def todo_caption(source_caption: str) -> str:
    caption = clean_inline_text(source_caption)
    if not caption:
        caption = "caption the image"
    return caption.replace("`", "'")


def range_folder(post_number: int) -> str:
    start = ((post_number - 1) // 20) * 20 + 1
    return f"{start}-{start + 19}"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_file(substack_root: Path, post_number: int) -> Path:
    folder = substack_root / range_folder(post_number) / str(post_number)
    files = sorted(folder.glob("*.md"))
    if len(files) != 1:
        raise ValueError(f"Expected one Markdown file in {folder}, found {len(files)}.")
    return files[0]


def markdown_image_tokens(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    combined = re.compile(r"!\[[^\]]*\]\([^)]+\)|<todo-image-shayan: add image `[^`]*`>")
    for match in combined.finditer(text):
        token = match.group(0)
        todo = TODO_RE.fullmatch(token)
        if todo:
            tokens.append(("todo", todo.group(1)))
        else:
            tokens.append(("local", token))
    return tokens


def update_entry(entry: dict, source_count: int, local_count: int, todo_count: int) -> None:
    if source_count == 0:
        entry["images_added_locally"] = None
        entry["images_linked_in_post"] = None
    elif todo_count:
        entry["images_added_locally"] = False
        entry["images_linked_in_post"] = True
    elif local_count >= source_count:
        entry["images_added_locally"] = True
        entry["images_linked_in_post"] = True
    else:
        entry["images_added_locally"] = False
        entry["images_linked_in_post"] = False


def audit_post(substack_root: Path, post_number: int, entry: dict, fix: bool) -> list[str]:
    url = entry.get("substack_url")
    if not url:
        return [f"post {post_number}: missing substack_url"]

    post = source_post(url)
    captions = source_image_captions(post.get("body_html") or "")
    expected_todos = [todo_caption(caption) for caption in captions]
    md_path = markdown_file(substack_root, post_number)
    text = md_path.read_text(encoding="utf-8")
    tokens = markdown_image_tokens(text)
    local_count = sum(1 for kind, _ in tokens if kind == "local")
    todo_count = sum(1 for kind, _ in tokens if kind == "todo")
    issues: list[str] = []

    if len(tokens) != len(captions):
        issues.append(
            f"post {post_number}: source images={len(captions)} local/todo refs={len(tokens)}"
        )

    replacements: list[str] = []
    for index, (kind, value) in enumerate(tokens):
        if kind != "todo":
            continue
        if index >= len(expected_todos):
            issues.append(f"post {post_number}: extra todo placeholder {value!r}")
            continue
        expected = expected_todos[index]
        replacements.append(expected)
        if value != expected:
            issues.append(
                f"post {post_number}: todo caption {value!r} should be {expected!r}"
            )

    changed_text = False
    if fix and replacements:
        replacement_iter = iter(replacements)

        def replace(match: re.Match[str]) -> str:
            nonlocal changed_text
            expected = next(replacement_iter)
            current = match.group(1)
            if current != expected:
                changed_text = True
            return f"{TODO_PREFIX}{expected}`>"

        new_text = TODO_RE.sub(replace, text)
        if changed_text:
            md_path.write_text(new_text, encoding="utf-8")

    before = (
        entry.get("images_added_locally"),
        entry.get("images_linked_in_post"),
    )
    if fix:
        update_entry(entry, len(captions), local_count, todo_count)
    after = (
        entry.get("images_added_locally"),
        entry.get("images_linked_in_post"),
    )
    if before != after:
        if fix:
            issues.append(f"post {post_number}: updated image flags {before} -> {after}")
        else:
            issues.append(f"post {post_number}: image flags {before} should be {after}")

    return issues


def compact_numbers(numbers: list[int]) -> str:
    numbers = sorted(set(numbers))
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


def refresh_dashboard(repo_root: Path, affected_ranges: set[str]) -> None:
    dashboard_path = repo_root / "substack" / "dashboard.json"
    if not dashboard_path.exists():
        return
    dashboard = load_json(dashboard_path)
    substack_root = repo_root / "substack"
    for folder_name in affected_ranges:
        posts_list_path = substack_root / folder_name / "posts-list.json"
        entries = load_json(posts_list_path)
        imported_count = 0
        deferred: list[int] = []
        unverified: list[int] = []
        for key, entry in entries.items():
            post_number = int(key)
            has_markdown = any((substack_root / folder_name / key).glob("*.md"))
            if entry.get("last_verified") and has_markdown:
                imported_count += 1
            if entry.get("substack_url") and not entry.get("last_verified"):
                unverified.append(post_number)
            if entry.get("images_added_locally") is False:
                deferred.append(post_number)
        remaining: list[str] = []
        if unverified:
            status = "in_progress"
            remaining.append(f"Import posts {compact_numbers(unverified)} when ready.")
        elif deferred:
            status = "needs_image_review"
            remaining.append(f"Add deferred/manual images for posts {compact_numbers(deferred)}.")
        else:
            status = "complete"
        dashboard[folder_name] = {
            "posts_list": f"{folder_name}/posts-list.json",
            "status": status,
            "imported_count": imported_count,
            "remaining": remaining,
            "last_updated": "2026-06-12",
        }
    write_json(dashboard_path, dashboard)


def run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    substack_root = repo_root / "substack"
    all_issues: list[str] = []
    affected_ranges: set[str] = set()
    posts_by_list: dict[Path, dict] = {}

    for post_number in range(args.start, args.end + 1):
        folder_name = range_folder(post_number)
        posts_list_path = substack_root / folder_name / "posts-list.json"
        entries = posts_by_list.setdefault(posts_list_path, load_json(posts_list_path))
        entry = entries.get(str(post_number))
        if entry is None:
            all_issues.append(f"post {post_number}: missing posts-list entry")
            continue
        try:
            issues = audit_post(substack_root, post_number, entry, args.fix)
            all_issues.extend(issues)
            if args.fix:
                affected_ranges.add(folder_name)
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            all_issues.append(f"post {post_number}: {error}")

    if args.fix:
        for path, entries in posts_by_list.items():
            write_json(path, entries)
        refresh_dashboard(repo_root, affected_ranges)

    for issue in all_issues:
        print(issue)
    print(f"RESULT issues={len(all_issues)} fix={args.fix}")
    return 1 if all_issues and not args.fix else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Substack source image captions against local Markdown references."
    )
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    parser.add_argument("--fix", action="store_true", help="Fix todo captions and image flags.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to this script's repo.",
    )
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start:
        parser.error("range must be positive and end must be greater than or equal to start")
    return args


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
