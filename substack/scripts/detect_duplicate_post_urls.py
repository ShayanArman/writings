#!/usr/bin/env python3
"""Find duplicate Substack post URLs in the archive post lists."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def iter_post_lists(substack_root: Path) -> list[Path]:
    return sorted(
        path
        for path in substack_root.glob("*/posts-list.json")
        if path.is_file()
    )


def load_posts(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")

    return data


def find_duplicate_urls(substack_root: Path) -> tuple[int, int, dict[str, list[dict[str, Any]]]]:
    url_entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total_entries = 0

    for posts_list in iter_post_lists(substack_root):
        for post_key, post in load_posts(posts_list).items():
            if not isinstance(post, dict):
                continue

            total_entries += 1
            url = (post.get("substack_url") or "").strip()
            if not url:
                continue

            url_entries[url].append(
                {
                    "post_key": post_key,
                    "file_number": post.get("file_number"),
                    "title": post.get("title"),
                    "posts_list": posts_list,
                }
            )

    duplicates = {
        url: entries
        for url, entries in url_entries.items()
        if len(entries) > 1
    }
    return total_entries, len(url_entries), duplicates


def sort_entry(entry: dict[str, Any]) -> tuple[int, str]:
    file_number = entry.get("file_number")
    if isinstance(file_number, int):
        return file_number, str(entry.get("post_key") or "")
    return 10**9, str(entry.get("post_key") or "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report duplicate substack_url values from substack/*/posts-list.json."
    )
    parser.add_argument(
        "substack_root",
        nargs="?",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Path to the substack archive root. Defaults to this script's parent archive.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    substack_root = args.substack_root.expanduser().resolve()

    total_entries, unique_urls, duplicates = find_duplicate_urls(substack_root)
    duplicate_slots = sum(len(entries) - 1 for entries in duplicates.values())

    print(f"Scanned entries: {total_entries}")
    print(f"Unique non-empty URLs: {unique_urls}")
    print(f"Duplicate URL groups: {len(duplicates)}")
    print(f"Extra duplicate slots: {duplicate_slots}")

    if not duplicates:
        print("\nNo duplicate post URLs found.")
        return 0

    print("\nDuplicates:")
    for url in sorted(duplicates):
        entries = sorted(duplicates[url], key=sort_entry)
        print(f"- {url} ({len(entries)} entries)")
        for entry in entries:
            posts_list = entry["posts_list"].relative_to(substack_root)
            print(
                "  "
                f"{entry.get('file_number')}: {entry.get('title')!r} "
                f"in {posts_list}"
            )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
