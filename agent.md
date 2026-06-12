# Agent Handoff: Substack Imports

This repo stores Shayan's Substack posts as plain Markdown files under numbered folders in `substack/`.

## What To Ask The User For

For each post import, ask for:

- The Substack post URL.
- The destination folder number or path.

Example user input:

```text
next 61 https://shayanarman.substack.com/p/example-post
```

That means: import the URL into `substack/61-80/61`.

## Folder Pattern

Posts are grouped by ranges:

- `substack/1-20/<number>/`
- `substack/21-40/<number>/`
- `substack/41-60/<number>/`
- `substack/61-80/<number>/`

For the current batch, use:

```text
substack/61-80/<number>/
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

When the image does not have a caption, use the bare image name on its own line:

```text
<image-name>
```

Example:

```text
<sam-altman>
```

Put the placeholder where the image appears in the Substack post. The placeholder represents the image and its caption; do not add or download image files unless the user explicitly asks.

When the user explicitly provides a local image file for a post, use the local file instead of the placeholder. Put the image where it appears in the Substack post, then add the source caption below it in italics:

```text
![Caption text](image-filename.jpg)

*Caption text*
```

If the source image has no caption, use an empty-alt local image reference:

```text
![](image-filename.jpg)
```

Only use this local image format when the user has provided the image file or clearly asked to embed/download an image. Otherwise, keep using placeholders and do not download media.

When the user provides a local image file, preserve the file extension they provided. Do not change `.jpg` to `.webp`, `.png`, or any other extension based on file contents or MIME detection. If the user asks for a more appropriate image name, rename only the basename and keep the original extension unless the user explicitly asks to convert the file format or change the extension.

Important: older imports may have Substack image captions as plain text body lines. When adding a placeholder for an image caption, remove the duplicate plain caption text if it only came from the image caption. Keep repeated text only when the live Substack post also has it as separate body text.

Post 51 (`substack/41-60/51/On Work.md`) is the pattern to follow: image placeholders stand in for the image/caption, while any remaining repeated lines are body text that also exists in the original.

Post 48 (`substack/41-60/48/Intrepid, to the Stars.md`) is the pattern to follow for images without captions: use a bare placeholder like `<sam-altman>`.

Post 64 (`substack/61-80/64/People don't appreciate this enough.md`) is the pattern to follow when the user provides a local image file: use a Markdown image reference like `![Queenstown New Zealand](mountain.jpg)` followed by `*Queenstown New Zealand*`.

## How To Run It

Preferred: run from the `substack` directory.

```bash
cd /Users/shayanarman/projects/other/writings/substack
scripts/import_substack_post.py "https://shayanarman.substack.com/p/example-post" "61-80/61"
```

You can also run from the repo root:

```bash
cd /Users/shayanarman/projects/other/writings
substack/scripts/import_substack_post.py "https://shayanarman.substack.com/p/example-post" "substack/61-80/61"
```

The command should print something like:

```text
Wrote 61-80/61/Post Title.md
```

If the script says the Markdown file already exists, do not overwrite it unless the user clearly asks. Use `--overwrite` only when replacing the existing file is intentional.

## Network Access

The import script fetches Substack over the network. If the sandbox blocks DNS/network access, rerun the exact command with escalated network permission.

The approved command prefixes may already exist:

```text
scripts/import_substack_post.py
scripts/verify_substack_import.py
```

## How To Check The Work

After every import, verify the result before replying. Use the verification script first, then do any manual follow-up it asks for.

From `/Users/shayanarman/projects/other/writings/substack`, run:

```bash
scripts/verify_substack_import.py "61-80/61" --url "https://shayanarman.substack.com/p/example-post"
```

You can also run it from the repo root:

```bash
substack/scripts/verify_substack_import.py "substack/61-80/61" --repo-root "." --url "https://shayanarman.substack.com/p/example-post"
```

The verifier performs the common repeatable checks:

- Step 1: resolve the destination folder or Markdown file.
- Step 2: confirm the Markdown file exists, is non-empty, has a title line, and reports line/byte counts.
- Step 3: scan for raw Substack HTML, JSON, script content, network errors, and traceback text.
- Step 4: when `--url` is provided, compare source title/subtitle and report image/figure/caption counts.
- Step 5: print `git status --short`.
- Step 6: return a pass/fail result with warnings.

If the verifier warns that the source body contains media, manually inspect the live/source post and add the correct placeholders:

```text
<image-name: caption `Caption text here.`>
```

or:

```text
<image-name>
```

If the verifier fails, fix the import before replying. If it passes with warnings, mention only warnings that matter to the user. Confirm the new/modified files match the user's request. Do not stage or commit unless the user asks.

Note: `.DS_Store` files may appear in Git status if they were already tracked before `.gitignore` ignored them. Do not touch them unless the user asks.

## Final Reply Pattern

Keep the final response short. Include the created file path as a clickable absolute link.

Example:

```text
Done. Imported post 51 into:

[Post Title.md](/Users/shayanarman/projects/other/writings/substack/41-60/51/Post%20Title.md)
```
