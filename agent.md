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

It ignores images and image captions, and it does not download media.

## Image References

This archive usually references images instead of downloading or embedding them.

When the user asks for an image reference, use this placeholder format on its own line:

```text
<image-name: caption `Caption text here.`>
```

Example:

```text
<nature-lover: caption `In the late 1990s, Julia Hill climbed a 200-foot, approximately 1000-year-old Californian redwood, staying up there for 100s of days, eventually saving it! How many toys does a child need? 1? 2? 18?`>
```

Put the placeholder where the image appears in the Substack post. The placeholder represents the image and its caption; do not add or download image files unless the user explicitly asks.

Important: older imports may have Substack image captions as plain text body lines. When adding a placeholder for an image caption, remove the duplicate plain caption text if it only came from the image caption. Keep repeated text only when the live Substack post also has it as separate body text.

Post 51 (`substack/41-60/51/On Work.md`) is the pattern to follow: image placeholders stand in for the image/caption, while any remaining repeated lines are body text that also exists in the original.

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
