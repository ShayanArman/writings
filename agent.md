# Agent Handoff: Substack Imports

This repo stores Shayan's Substack posts as plain Markdown files under numbered folders in `substack/`.

## What To Ask The User For

For each post import, ask for:

- The Substack post URL.
- The destination folder number or path.

Example user input:

```text
next 51 https://shayanarman.substack.com/p/example-post
```

That means: import the URL into `substack/41-60/51`.

## Folder Pattern

Posts are grouped by ranges:

- `substack/1-20/<number>/`
- `substack/21-40/<number>/`
- `substack/41-60/<number>/`

For the current batch, use:

```text
substack/41-60/<number>/
```

The importer creates the destination folder if it does not exist.

## Script To Use

The script is:

```text
substack/scripts/import_substack_post.py
```

It imports raw text only:

- Title
- Optional subtitle
- Article body

It ignores images and does not download media.

## How To Run It

Preferred: run from the `substack` directory.

```bash
cd /Users/shayanarman/projects/other/writings/substack
scripts/import_substack_post.py "https://shayanarman.substack.com/p/example-post" "41-60/51"
```

You can also run from the repo root:

```bash
cd /Users/shayanarman/projects/other/writings
substack/scripts/import_substack_post.py "https://shayanarman.substack.com/p/example-post" "substack/41-60/51"
```

The command should print something like:

```text
Wrote 41-60/51/Post Title.md
```

If the script says the Markdown file already exists, do not overwrite it unless the user clearly asks. Use `--overwrite` only when replacing the existing file is intentional.

## Network Access

The script fetches Substack over the network. If the sandbox blocks DNS/network access, rerun the exact command with escalated network permission.

The approved command prefix may already exist:

```text
scripts/import_substack_post.py
```

## How To Check The Work

After every import, verify the result before replying.

From `/Users/shayanarman/projects/other/writings/substack`, run:

```bash
ls -la "41-60/51"
```

Then read the imported file:

```bash
sed -n '1,160p' "41-60/51/Post Title.md"
```

If the post is longer, read more:

```bash
sed -n '161,320p' "41-60/51/Post Title.md"
tail -40 "41-60/51/Post Title.md"
```

Check these things:

- The destination folder number is correct.
- The Markdown file name matches the Substack post title.
- The file is not empty.
- The first line is the title.
- The subtitle, if present, is on the second text line.
- The body text is readable plain text.
- There is no raw Substack HTML, no JSON, no script content, and no network error text in the file.
- No images were downloaded unless the user separately asked for images.

Also check Git status:

```bash
git status --short
```

Confirm the new/modified files match the user's request. Do not stage or commit unless the user asks.

Note: `.DS_Store` files may appear in Git status if they were already tracked before `.gitignore` ignored them. Do not touch them unless the user asks.

## Final Reply Pattern

Keep the final response short. Include the created file path as a clickable absolute link.

Example:

```text
Done. Imported post 51 into:

[Post Title.md](/Users/shayanarman/projects/other/writings/substack/41-60/51/Post%20Title.md)
```
