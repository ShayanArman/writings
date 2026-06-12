#!/usr/bin/env python3
"""Verify the common parts of a Substack Markdown import."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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


def sanitize_filename(title: str) -> str:
    filename = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    filename = re.sub(r"\s+", " ", filename)
    return filename or "post"


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


def resolve_target(target: Path) -> tuple[Path, Path]:
    if target.is_file():
        return target.parent, target

    if not target.exists():
        raise FileNotFoundError(f"Destination does not exist: {target}")
    if not target.is_dir():
        raise ValueError(f"Destination is not a directory or file: {target}")

    markdown_files = sorted(target.glob("*.md"))
    if not markdown_files:
        raise FileNotFoundError(f"No Markdown file found in: {target}")
    if len(markdown_files) > 1:
        names = ", ".join(path.name for path in markdown_files)
        raise ValueError(f"Multiple Markdown files found; pass one file explicitly: {names}")

    return target, markdown_files[0]


def git_status(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return [f"git status failed: {result.stderr.strip() or result.stdout.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def relative_to(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def verify(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser()
    repo_root = Path(args.repo_root).expanduser().resolve()

    errors: list[str] = []
    warnings: list[str] = []

    # Step 1: Resolve the destination to the one Markdown file we expect.
    print("Step 1: Resolve destination")
    try:
        destination, markdown_path = resolve_target(target)
    except (FileNotFoundError, ValueError) as error:
        print(f"FAIL {error}")
        return 1

    print(f"OK destination: {relative_to(destination.resolve(), repo_root)}")
    print(f"OK markdown: {relative_to(markdown_path.resolve(), repo_root)}")

    # Step 2: Confirm the import produced a readable Markdown-shaped file.
    print("\nStep 2: Check Markdown file shape")
    text = markdown_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    nonempty_lines = [line.strip() for line in lines if line.strip()]

    if not text.strip():
        errors.append("Markdown file is empty.")
    if not text.endswith("\n"):
        warnings.append("Markdown file does not end with a newline.")
    if len(nonempty_lines) < 2:
        errors.append("Markdown has fewer than two non-empty lines.")

    title = nonempty_lines[0] if nonempty_lines else ""
    expected_name = f"{sanitize_filename(title)}.md" if title else ""
    if title:
        print(f"OK title line: {title}")
    if expected_name and markdown_path.name != expected_name:
        warnings.append(
            f"Filename is {markdown_path.name!r}; title would sanitize to {expected_name!r}."
        )

    print(f"OK line count: {len(lines)}")
    print(f"OK byte count: {markdown_path.stat().st_size}")

    # Step 3: Catch common extraction failures before reading the whole file.
    print("\nStep 3: Scan for extraction artifacts")
    lowered_text = text.lower()
    found_markers = [marker for marker in RAW_MARKERS if marker.lower() in lowered_text]
    if found_markers:
        errors.append(f"Found raw import markers: {', '.join(found_markers)}")
    else:
        print("OK no raw HTML/JSON/script/network-error markers found")

    htmlish_lines = [
        (index, line.strip())
        for index, line in enumerate(lines, start=1)
        if re.search(r"</?(div|span|p|figure|img|iframe|script|style)\b", line, re.I)
    ]
    if htmlish_lines:
        preview = "; ".join(f"{index}: {line[:80]}" for index, line in htmlish_lines[:3])
        errors.append(f"Found likely raw HTML lines: {preview}")
    else:
        print("OK no likely raw HTML lines found")

    # Step 4: Use the original Substack URL when available for source checks.
    print("\nStep 4: Check optional Substack source metadata")
    if args.url:
        try:
            preloads = extract_preloads(fetch_text(args.url))
            post = preloads.get("post") or {}
            source_title = (post.get("title") or "").strip()
            source_subtitle = (post.get("subtitle") or "").strip()
            body_html = post.get("body_html") or ""
            image_count = body_html.count("<img")
            figure_count = body_html.count("<figure")
            caption_count = body_html.count("<figcaption")

            if source_title and title and source_title != title:
                errors.append(
                    f"Title mismatch: Markdown has {title!r}, source has {source_title!r}."
                )
            elif source_title:
                print("OK title matches source")

            if source_subtitle:
                second_line = nonempty_lines[1] if len(nonempty_lines) > 1 else ""
                if second_line != source_subtitle:
                    warnings.append(
                        "Source subtitle differs from the second non-empty Markdown line."
                    )
                else:
                    print("OK subtitle matches source")

            print(
                "INFO source media tags: "
                f"images={image_count}, figures={figure_count}, captions={caption_count}"
            )
            if image_count or figure_count or caption_count:
                warnings.append(
                    "Source body contains media; manually verify placeholder placement and captions."
                )
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            warnings.append(f"Source metadata check skipped: {error}")
    else:
        print("SKIP no --url provided")

    # Step 5: Surface unrelated local changes instead of accidentally hiding them.
    print("\nStep 5: Check Git status")
    status_lines = git_status(repo_root)
    if status_lines:
        for line in status_lines:
            print(f"INFO git: {line}")
    else:
        print("OK git status is clean")

    # Step 6: Keep the final result machine-readable and easy to skim.
    print("\nStep 6: Report")
    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"FAIL {error}")

    if errors:
        print("RESULT failed")
        return 1

    print("RESULT passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the common checks after importing a Substack post."
    )
    parser.add_argument(
        "target",
        help="Destination folder or Markdown file, e.g. 61-80/61",
    )
    parser.add_argument(
        "--url",
        help="Optional Substack URL for title/subtitle/media-count checks.",
    )
    parser.add_argument(
        "--repo-root",
        default="..",
        help="Repo root for git status when running from substack/. Default: ..",
    )
    return parser.parse_args()


def main() -> int:
    return verify(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
