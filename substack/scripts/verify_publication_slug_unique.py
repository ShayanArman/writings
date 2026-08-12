#!/usr/bin/env python3
"""Fail closed when a proposed Shayan Arman publication slug is not unique."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


BUCKET = "seo-gangster"
WRITINGS_PREFIX = "sites/shayan-arman-blog/posts/writings/"
IMAGE_POSTS_PREFIX = "sites/shayan-arman-blog/public/images/posts/"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATED_MDX_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.mdx$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a proposed post slug against every local writings ledger, "
            "the authorized S3 writings prefix, and its exact S3 image prefix."
        )
    )
    parser.add_argument("slug", help="Proposed lowercase kebab-case route slug")
    parser.add_argument(
        "--post-number",
        type=int,
        help="Current archive post number; its own existing ledger entry is ignored",
    )
    parser.add_argument(
        "--allow-writing-key",
        action="append",
        default=[],
        help=(
            "Exact current-post S3 writing key to allow during interruption recovery; "
            "repeat only for exact verified keys"
        ),
    )
    parser.add_argument(
        "--allow-existing-image-prefix",
        action="store_true",
        help=(
            "Allow objects below the candidate image prefix only during interruption "
            "recovery after every existing object has been reconciled separately"
        ),
    )
    parser.add_argument(
        "--writings-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Writings repository root (defaults to the script's repository)",
    )
    return parser.parse_args()


def list_s3_keys(prefix: str, *, max_items: int | None = None) -> list[str]:
    command = [
        "aws",
        "s3api",
        "list-objects-v2",
        "--bucket",
        BUCKET,
        "--prefix",
        prefix,
        "--output",
        "json",
    ]
    if max_items is not None:
        command.extend(["--max-items", str(max_items)])

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown AWS CLI error"
        raise RuntimeError(f"S3 uniqueness check failed closed for `{prefix}`: {detail}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"S3 uniqueness check returned invalid JSON for `{prefix}`") from error

    return [
        entry["Key"]
        for entry in payload.get("Contents", [])
        if isinstance(entry, dict) and isinstance(entry.get("Key"), str)
    ]


def find_ledger_collisions(
    writings_root: Path,
    slug: str,
    current_post_number: int | None,
) -> list[str]:
    collisions: list[str] = []
    ledger_paths = sorted((writings_root / "substack").glob("*/posts-list.json"))
    if not ledger_paths:
        raise RuntimeError(f"No range ledgers found below `{writings_root / 'substack'}`")

    for ledger_path in ledger_paths:
        try:
            entries = json.loads(ledger_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Cannot read ledger `{ledger_path}`: {error}") from error

        if not isinstance(entries, dict):
            raise RuntimeError(f"Ledger `{ledger_path}` is not a JSON object")

        for entry_number, entry in entries.items():
            if not isinstance(entry, dict) or entry.get("draft_slug") != slug:
                continue

            try:
                numeric_entry_number = int(entry_number)
            except ValueError:
                numeric_entry_number = None

            if current_post_number is not None and numeric_entry_number == current_post_number:
                continue

            collisions.append(
                f"ledger post {entry_number} in {ledger_path.relative_to(writings_root)} "
                f"uses draft_slug `{slug}` ({entry.get('draft_file') or 'no draft_file'})"
            )

    return collisions


def derive_writing_slug(key: str) -> str | None:
    basename = key.rsplit("/", 1)[-1]
    matched = DATED_MDX_PATTERN.fullmatch(basename)
    return matched.group("slug") if matched else None


def main() -> int:
    args = parse_args()
    slug = args.slug.strip()
    writings_root = args.writings_root.expanduser().resolve()

    if not SLUG_PATTERN.fullmatch(slug):
        print(
            f"FAIL proposed slug `{slug}` is not simple lowercase kebab-case",
            file=sys.stderr,
        )
        return 2

    allowed_writing_keys = set(args.allow_writing_key)
    invalid_allowed_keys = [
        key for key in allowed_writing_keys if not key.startswith(WRITINGS_PREFIX)
    ]
    if invalid_allowed_keys:
        for key in invalid_allowed_keys:
            print(
                f"FAIL allowed writing key escapes the authorized prefix: `{key}`",
                file=sys.stderr,
            )
        return 2

    try:
        collisions = find_ledger_collisions(writings_root, slug, args.post_number)

        for key in list_s3_keys(WRITINGS_PREFIX):
            if derive_writing_slug(key) == slug and key not in allowed_writing_keys:
                collisions.append(f"S3 writing object derives slug `{slug}`: {key}")

        image_prefix = f"{IMAGE_POSTS_PREFIX}{slug}/"
        image_keys = list_s3_keys(image_prefix, max_items=1)
        if image_keys and not args.allow_existing_image_prefix:
            collisions.append(
                f"S3 image prefix is already populated: {image_prefix} "
                f"(example object: {image_keys[0]})"
            )
    except RuntimeError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 2

    if collisions:
        print(f"FAIL proposed slug `{slug}` is not globally unique:", file=sys.stderr)
        for collision in collisions:
            print(f"- {collision}", file=sys.stderr)
        return 1

    print(f"OK proposed slug `{slug}` is globally unique for post {args.post_number or 'unknown'}")
    print(f"OK checked all local range ledgers below {writings_root / 'substack'}")
    print(f"OK checked s3://{BUCKET}/{WRITINGS_PREFIX}")
    print(f"OK image prefix is clear: s3://{BUCKET}/{IMAGE_POSTS_PREFIX}{slug}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
