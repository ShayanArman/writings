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

Posts are grouped by ranges of 20:

- `substack/1-20/<number>/`
- `substack/21-40/<number>/`
- `substack/41-60/<number>/`
- `substack/61-80/<number>/`
- `substack/81-100/<number>/`
- Continue the same pattern through `substack/401-420/<number>/`.

Use the range that contains the post number. Examples:

```text
substack/61-80/74/
substack/81-100/100/
substack/181-200/181/
```

The importer creates the destination folder if it does not exist.

## Post Lists / Task Ledger

The root task dashboard is:

```text
substack/dashboard.json
```

It is keyed by range folder (`1-20`, `21-40`, etc.) and gives the high-level remaining work for each range. Use it as the first place to look when deciding what still needs to be imported, image-reviewed, or verified.

Each range folder also has a detailed `posts-list.json` file:

```text
substack/1-20/posts-list.json
substack/21-40/posts-list.json
...
substack/381-400/posts-list.json
```

Treat these JSON files as the archive task list. They show which numbered posts have been imported, what source URL they came from, whether images still need attention, and when the entry was last verified.

The root `substack/dashboard.json` should stay broad and task-oriented:

```json
{
  "61-80": {
    "posts_list": "61-80/posts-list.json",
    "status": "in_progress",
    "imported_count": 13,
    "remaining": [
      "Import posts 74-80 when ready."
    ],
    "last_updated": "2026-06-12"
  }
}
```

Update the root task dashboard when a whole range changes state, such as when a range becomes complete, a range starts, or image-review tasks are finished.

Each populated file is a JSON object keyed by the post number as a string. Empty future ranges should be valid empty JSON objects:

```json
{}
```

Entry shape:

```json
{
  "71": {
    "file_number": 71,
    "title": "The Nuclear Umbrella",
    "substack_url": "https://shayanarman.substack.com/p/the-nuclear-umbrella",
    "images_added_locally": null,
    "images_linked_in_post": null,
    "last_verified": "2026-06-12"
  }
}
```

Field meanings:

- `file_number`: the numbered archive folder/file.
- `title`: the Substack post title from the imported Markdown.
- `substack_url`: the canonical Substack URL when known; use `null` if it still needs a later URL pass.
- `images_added_locally`: `true` when local image files were added, `false` when the source has images but they are not local, and `null` when the source has no images or has not been image-checked yet.
- `images_linked_in_post`: `true` when the Markdown references local images or image placeholders, `false` when the source has images but the Markdown does not reference them, and `null` when the source has no images or has not been image-checked yet.
- `last_verified`: the date this entry was last checked, in `YYYY-MM-DD`.

When importing or fixing a post, update only that post number inside the matching `posts-list.json`. This keeps the JSON file usable as a precise todo list for remaining archive work, especially image follow-up and unverified URLs.

## Finding The Next Post

When the user asks what is next, check `substack/dashboard.json` first, then the
matching range's `posts-list.json`.

The next post is usually the lowest-numbered entry whose Markdown folder/file is
missing or whose `last_verified` is `null`. If the dashboard says a range is
`in_progress`, start there before moving to later `urls_recorded` ranges.

As of the 2026-06-12 handoff, post 73 is imported and the next planned import is
post 74, "Pain, Pleasure, and Redemption", followed by 75-100.

## Script To Use

For a single post, the script is:

```text
substack/scripts/import_substack_post.py
```

It imports raw text only:

- Title
- Optional subtitle
- Article body

It ignores images and image captions, and it does not download media.

For repeated work, do not manually run the same import/verify/update sequence one
post at a time. Create or use a reusable script under `substack/scripts/` that
can run a numeric range, stop on failures, and safely resume. The batch script
should follow this sequence for each post:

1. Read the post URL from the matching `posts-list.json`.
2. Resolve the destination folder from the post number.
3. Download/import the Markdown.
4. Preserve source image positions as placeholders when images are being left
   for Shayan to add later.
5. Run `scripts/verify_substack_import.py` for that post.
6. Update only that post's `posts-list.json` entry after verification passes.
7. Update `substack/dashboard.json` only when a whole range changes state.

Batch scripts should be idempotent where practical: skip already verified posts
unless the user explicitly asks to overwrite or reimport them.

## Image References

This archive usually references images instead of downloading or embedding them.

When importing a batch and the user asks to leave images out for later manual
download, put this deferred placeholder exactly where the source image appears:

```text
<todo-image-shayan: add image `caption the image`>
```

This means Shayan will later download the image manually and place it in the
right numbered post folder. Do not download image files for these placeholders.
Use one placeholder per source image. Always copy the actual Substack image
caption into the placeholder when the post has one:

```text
<todo-image-shayan: add image `Actual source caption here.`>
```

This keeps the later manual image pass from needing to reopen the source post
just to recover captions. If there is no source caption, keep the placeholder
text as-is so it remains easy to find during image review.

Post 73 (`substack/61-80/73/What is love.md`) is the pattern to follow for this
deferred placeholder style.

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

If the verifier warns that the source body contains media, manually inspect the live/source post and add the correct placeholders. For large batches, make the batch import script inspect the source `body_html` so placeholders land where the images appeared and captions are copied automatically:

```text
<image-name: caption `Caption text here.`>
```

or:

```text
<image-name>
```

If the verifier fails, fix the import before replying. If it passes with warnings, mention only warnings that matter to the user. Confirm the new/modified files match the user's request. Do not stage or commit unless the user asks.

After the Markdown import and verification are correct, update the matching range's `posts-list.json` entry for that exact post number. Include the source URL, image status fields, and the current verification date. If the URL or image status is not known yet, leave that field as `null` rather than guessing.

When using deferred image placeholders, set `images_added_locally` to `false`
and `images_linked_in_post` to `true`, because the image has not been downloaded
locally but the Markdown includes a placeholder at the source location.

Note: `.DS_Store` files may appear in Git status if they were already tracked before `.gitignore` ignored them. Do not touch them unless the user asks.

## Final Reply Pattern

Keep the final response short. Include the created file path as a clickable absolute link.

Example:

```text
Done. Imported post 51 into:

[Post Title.md](/Users/shayanarman/projects/other/writings/substack/41-60/51/Post%20Title.md)
```
