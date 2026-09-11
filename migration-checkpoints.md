# Migration Checkpoints

This file is the durable resume point for the sequential Substack-to-MDX
migration. A post is recorded as complete only after its MDX and any original
full-resolution images have been validated, uploaded to their exact Shayan
Arman S3 keys, checksum-verified, reflected in the writings ledgers, and removed
from temporary storage.

## Post 414: Never Enough Intelligence

Source: https://shayanarman.substack.com/p/never-enough-intelligence

Shayan requested this one post as a local draft, subsequently authorized its
image and MDX uploads, then rejected an assistant-written excerpt. The excerpt
was corrected in both the local draft and the exact S3 article object to:

> Once you realize what you can do. It’s never enough. We will ALWAYS be limited by Compute and Inference.

Shayan reviewed the exact local migration and explicitly approved upload with
"okay upload now". The approved draft is now uploaded to the existing article
key and checksum-verified. The original image was reverified and left unchanged.
No further revision or S3 write is pending. Reconcile the exact existing keys
before any future authorized update and use a conditional write.

- Local review file: `../shayan-arman-blog/site/draft-post/2026-09-05-never-enough-intelligence.mdx`
- Preview: `/drafts/never-enough-intelligence`
- Exact publication timestamp: `2026-09-05T06:02:02.808Z`
- Subtitle: `Oh how I’ve changed in just a few short months!`
- MDX key: `sites/shayan-arman-blog/posts/writings/2026-09-05-never-enough-intelligence.mdx`
- Last verified S3 MDX: 2,420 bytes, MD5 `d25e450bab5cea406ee935ac0c96602d`.
- The approved local draft and S3 article both use the exact source phrases
  `tokens` and `Compute and Inference` in place of the generated keyword phrases.
- Image key: `sites/shayan-arman-blog/public/images/posts/writings/never-enough-intelligence/never-enough-intelligence.webp`
- Original image: `https://substack-post-media.s3.amazonaws.com/public/images/fc9b1a16-28af-4de1-ba6b-1eb7afd099aa_2160x2160.png`
- Verified image: original WebP bytes, 2160 × 2160, 162,058 bytes,
  `image/webp`, MD5 `e21ccd08bb20b5876a0308eb5da62e46`. Only the misleading
  filename extension was corrected. One body image, also used as the thumbnail;
  no source caption, and none added.

The body was compared word for word with the canonical API source; the excerpt
was separately checked as verbatim source text. MDX compilation and site
validation passed. No other posts or S3 objects were changed. The requested
local draft is retained. Shayan subsequently clarified that this post directly
follows post 413, “The Value of Things,” so it is recorded as post 414 in the
archive, range ledger, dashboard, and numbered checkpoint below.

## Post 415: The Shayan Arman Singularity

Source: https://shayanarman.substack.com/p/the-shayan-arman-singularity

Shayan confirmed this post is already on the live site. A complete comparison
of the 415 downloaded live writing files against every numbered range-ledger
entry found this as the only live writing absent from the numbered archive.
It directly follows post 414 and is now recorded as post 415.

- Local live file: `../shayan-arman-blog/site/live-posts/shayan-arman-blog/writings/2026-09-07-the-shayan-arman-singularity.mdx`
- Exact publication timestamp: `2026-09-07T00:16:05.526Z`
- Subtitle: `A Billion is Fast Approaching`
- MDX key: `sites/shayan-arman-blog/posts/writings/2026-09-07-the-shayan-arman-singularity.mdx`
- Downloaded live MDX: 2,498 bytes, MD5 `7f751dd8d44ec15256728682f366c0da`.
- Image key: `sites/shayan-arman-blog/public/images/posts/writings/the-shayan-arman-singularity/the-shayan-arman-singularity.webp`
- Original image: `https://substack-post-media.s3.amazonaws.com/public/images/9b0e563c-c7ae-40b7-95b6-2743da338587_2160x2160.png`
- Verified original image: WebP bytes, 2160 × 2160, 81,878 bytes,
  `image/webp`, MD5 `f995b48392d0ade16c14afcc5daa1cf0`.

Operational rules, including the prohibition on invented excerpts, live in
`agent-instructions.md`. The reusable starter request is `Prompt.md`.

## Explanation of what to do for each post migration

This section describes explicitly authorized direct-publication batches.
For a local draft request, follow the review and sign-off workflow in
`agent-instructions.md`; current user authorization takes precedence.

Migrate exactly one numbered post at a time. Never begin the next post until
the current post's source copy, metadata, images, MDX, S3 objects, writings
ledgers, temporary-file cleanup, and checkpoint update are all complete. Do not
perform parallel post work.

The publishable MDX must be created only in
`../shayan-arman-blog/.tmp-shayan-post-<number>/`.
Do not add it to the Shayan Arman site's `site/live-posts/` directory. Upload
the finished MDX directly to:

```text
s3://seo-gangster/sites/shayan-arman-blog/posts/writings/
```

Upload images only below the post-specific prefix:

```text
s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/writings/<slug>/
```

The `writings` collection segment is mandatory for every upload and every
recorded image key. A direct-under-`posts/` reference is stale and incorrect.

Never write outside `sites/shayan-arman-blog/` in S3. Never run `yarn build`
or `yarn dev`.

## Migration Complete Through Post 417

The numbered migration is complete through post 417. Shayan uploaded the
approved local drafts for post 416, “Celebrations,” and post 417, “Singing.”
Both exact S3 MDX objects are byte-identical to their retained local drafts,
and both original images passed exact S3 size, MIME-type, and checksum
verification under the `public/images/posts/writings/<slug>/` hierarchy.

Before beginning work, the next agent must read `agent.md`,
`agent-instructions.md`, and this file completely, then confirm this exact
durable state:

- post 304, “The Startup Algorithm,” is fully published, checksum-verified,
  reflected in its range ledger and dashboard, cleaned from temporary storage,
  and recorded in the completed-checkpoint table below;
- `Last completed post` is 417 and the next numbered post is not yet identified
  or authorized;
- posts 416 and 417 are fully published, checksum-verified, and recorded in the
  401–420 ledger and dashboard;
- no post-specific reconciliation directory remains for either post;
- do not begin post 418 without current user authorization and its canonical
  Substack URL.

Do not use a batch importer, do not parallelize posts, and do not create local
copies in `site/draft-post/` or `site/live-posts/`. Temporary post files belong
only in `../shayan-arman-blog/.tmp-shayan-post-<number>/` and must be deleted
afterward. Run `yarn validate-site` for each post; never run `yarn build` or
`yarn dev` for this migration.

The global route-slug and image-folder uniqueness preflight is mandatory twice
for every post: once before creating its MDX and again immediately before its
first upload. A nonzero result blocks the post:

```text
python3 substack/scripts/verify_publication_slug_unique.py <slug> --post-number <number>
```

This preflight must check every local range ledger, all route slugs derived
from dated MDX filenames under the authorized S3 writings prefix, and the exact
candidate `public/images/posts/writings/<slug>/` folder. A new post's image
folder must contain no image objects. Its exact zero-byte folder marker is
allowed. Never reuse another post's route slug or image folder.

Post 57 already owns the `on-language` slug. A later collision from post 112
caused every non-prerendered writing route to return HTTP 500. Post 112 was
repaired and is now recorded as:

```text
sites/shayan-arman-blog/posts/writings/2025-06-18-on-language-parts-and-position.mdx
```

Never change post 112 back to `on-language`. Apply the uniqueness preflight to
all later posts so no dated MDX pair or image-folder pair can collide again.

### Current Uniqueness Audit

On 2026-08-11, immediately before the post-120 handoff:

- every populated `draft_slug` across all local
  `substack/*/posts-list.json` ledgers was grouped and checked, with zero
  duplicates;
- all 119 dated MDX objects under the authorized
  `sites/shayan-arman-blog/posts/writings/` S3 prefix were checked by deriving
  the route slug from each filename, with zero duplicates;
- the S3 prefix directory marker was the only non-MDX listing entry and does
  not create a route.

This audit describes the handoff state only. It does not replace either of the
two mandatory per-post uniqueness preflights for posts 120–408.

### How To Check Every New Post Slug

For every new post, use this exact procedure:

1. Propose a simple lowercase kebab-case slug based on the real title.
2. From the `shayan-arman/writings/` repository root, run:

   ```text
   python3 substack/scripts/verify_publication_slug_unique.py <slug> --post-number <number>
   ```

3. Treat the slug as unique only when the command exits zero and explicitly
   confirms all three conditions:
   - no other post in any local `substack/*/posts-list.json` ledger uses the
     proposed `draft_slug`;
   - no dated MDX filename under the authorized
     `sites/shayan-arman-blog/posts/writings/` S3 prefix derives the same route
     slug after its leading date and trailing `.mdx` are removed;
   - the exact candidate
     `sites/shayan-arman-blog/public/images/posts/writings/<slug>/` S3 folder
     has no objects below its optional exact zero-byte folder marker for a new
     post.
4. A nonzero result blocks MDX creation and every upload. Do not bypass it with
   an exact-key `head-object`, because two different dated MDX keys can still
   create the same route slug.
5. On collision, prefer the canonical Substack URL slug if that alternative is
   unique. Otherwise append a concise, descriptive, stable suffix. Rerun the
   command until it exits zero, then use that one final slug consistently in
   the MDX filename, route, ledger fields, image folder, thumbnail, and body
   image URIs.
6. Run the same command a second time immediately before the post's first S3
   upload. Both the pre-MDX and pre-upload checks must pass.

## Step by Step so next ai agent can continue where we left off.

# Step 1 — Resolve the next post and inspect its source

1. Read `agent.md`, `agent-instructions.md`, this file, the current range's
   `posts-list.json`, and `substack/dashboard.json`.
   For the active posts 78–408 direct-publication batch, this file and
   `agent-instructions.md` override any conflicting older archive-import or
   review-draft guidance in `agent.md`. Do not ask for per-post approval, do
   not use a batch importer, do not create a local `draft-post` or
   `live-posts` copy, do not defer source images, and do not wait between
   completed checkpoints.
2. Use the `Next post` value in this file. Confirm that the preceding row is
   complete and that the ledger agrees with it.
3. Locate the archived source under
   `substack/<range>/<number>/<article>.md` and read the entire file.
4. Read the post's current ledger entry. Record the title, canonical Substack
   URL, placeholder image positions, literal hashtags, visible URLs, and any
   source subtitle.
5. Create exactly one temporary directory inside the site repository:
   `../shayan-arman-blog/.tmp-shayan-post-<number>`.
6. Fetch canonical metadata from
   `https://shayanarman.substack.com/api/v1/posts/<substack-slug>` into
   `source.json` inside that temporary directory.
7. Apply this source-of-truth split exactly:
   - the Substack API controls the title, subtitle, exact `post_date`,
     canonical URL, source-link targets, image order, direct original-image
     URLs, and original-image metadata;
   - the archived Markdown controls all body wording, capitalization, typos,
     punctuation, paragraph order, visible link text, literal hashtags,
     placeholder positions, and placeholder captions.
   Remove only incidental leading or trailing whitespace from metadata fields;
   do not rewrite their actual content. The `YYYY-MM-DD` portion of
   `post_date` controls the MDX date and filename.
8. Propose the post slug, then prove it is globally unique before creating the
   MDX. Search every `substack/*/posts-list.json` for the same `draft_slug` and
   list only the authorized
   `sites/shayan-arman-blog/posts/writings/` S3 prefix. Derive S3 route slugs by
   stripping the `YYYY-MM-DD-` prefix and `.mdx` suffix from each basename.
   Also list the exact candidate image folder
   `sites/shayan-arman-blog/public/images/posts/writings/<slug>/`; it must
   contain no objects below its optional exact zero-byte folder marker for a
   new post. Never share or reuse another post's image folder.
   An exact-key check alone is insufficient: two different dated filenames can
   still create the same route. On collision, prefer the canonical Substack URL
   slug when unique, otherwise add a concise stable suffix; rerun both checks
   and use the resulting slug consistently for the MDX and image prefix.
   Run the mandatory fail-closed preflight; a nonzero result blocks the post:

   ```text
   python3 substack/scripts/verify_publication_slug_unique.py <slug> --post-number <number>
   ```

# Step 2 — Recover and inspect every original image sequentially

1. Extract each image's direct `data-attrs.src` URL from the API body in body
   order. It must use `substack-post-media.s3.amazonaws.com`; never download a
   `substackcdn.com/image/fetch` rendition.
2. Download one image, finish all checks on it, and only then download the next
   image. Use the full original object even when the API's rendered width is
   smaller than the source object's native width.
3. For each download, record and verify:
   - actual file format with `file`;
   - byte size with `stat`;
   - native pixel dimensions with `sips`, or `sharp(...).metadata()` when the
     format is unsupported by `sips`;
   - local MD5 with `md5 -q`;
   - visual contents with the local image viewer.
4. Normalize the final basename to descriptive lowercase kebab-case. The final
   extension must match the actual bytes, even when the source URL or archive
   filename is misleading.
5. Preserve original bytes. If an AVIF or another format cannot be previewed,
   create a separate temporary JPEG preview only for inspection; upload the
   untouched original and delete the preview during cleanup.
6. Use meaningful alt text based on the inspected image. Keep every image in
   its original body position and order. Constrain genuinely small images to
   native width with `figureStyle`.
7. Treat captions encoded in archive placeholders as authoritative. Put the
   exact caption in the matching `GangsterImage` `caption` prop and add exactly
   one standalone `<br />` immediately after every captioned image. Do not add
   the spacer to uncaptioned images.

# Step 3 — Build and validate the temporary MDX

1. Create `YYYY-MM-DD-<slug>.mdx` inside the temporary directory with
   `apply_patch`.
2. Use the finalized frontmatter pattern: title, optional original subtitle,
   date, `Writings` category and collection, author, source URL, descriptive
   source keyword phrases, only literal normalized source hashtags, a verbatim
   contiguous source excerpt when needed, changefreq, and
   priority. Add thumbnail, imageAlt, and imageFallbackText only when images
   exist. Use the first suitable source image or Substack's selected cover.
3. Remove only the source metadata title and subtitle headings from the body.
   If the API body contains the same subtitle again as a real body paragraph,
   preserve that repeated body line. Preserve every other word,
   capitalization choice, typo, punctuation mark, paragraph, and ordering from
   the archived Markdown.
4. Preserve source links and convert visible raw URLs into explicit Markdown
   links without changing their displayed text. Keep literal hashtag lines in
   the body as well as normalized hashtag metadata in frontmatter.
5. Import the standard article components and `GangsterImage` when needed.
   End every post with this exact footer order:

   ```mdx
   <ShareArticleClipboard />

   <ArticleDivider />

   <ProductLinks />
   ```

6. Run an exact-copy validation that strips frontmatter, imports, media
   components, caption spacers, footer components, and Markdown link targets,
   then compares the remaining visible body lines with the archived source.
7. Validate metadata, literal hashtags, source links, image count and order,
   source captions, image dimensions, thumbnail selection, absence of
   placeholders, and footer order. Check the excerpt separately against the
   source; it must be an exact contiguous passage. Never generate a summary
   for frontmatter. Check keyword phrases against the source as well.
8. Compile the file with `@mdx-js/mdx`, then run `yarn validate-site` from the
   Shayan Arman site. Confirm that no post-specific file exists in
   `site/live-posts/`.

# Step 4 — Upload and verify exact S3 keys sequentially

1. Immediately before uploading, repeat all global slug and image-folder
   uniqueness checks from Step 1. Stop if any other ledger post or S3 writing
   object derives the same slug, or if the exact candidate image folder is
   unexpectedly populated. This collection-wide S3 read must stay scoped to
   `sites/shayan-arman-blog/posts/writings/`; never list the bucket or another
   site prefix. Run the same mandatory
   `verify_publication_slug_unique.py` command again; a nonzero result blocks
   all uploads.
2. Before uploading, run `aws s3api head-object` on every proposed image key
   and the MDX key. A 404 confirms the key is clear. Do not overwrite an
   unexpected existing object; inspect and reconcile it first.
3. Upload one original image at a time with its actual MIME type. Upload the
   validated MDX only after all images have uploaded successfully.
4. For every uploaded object, run an exact `head-object` check and compare:
   - `ContentLength` with the local byte size;
   - image `ContentType` with the actual format;
   - single-part S3 `ETag` with the local MD5.
5. The post is not complete if any uniqueness, exact-key, byte-size, MIME-type,
   or checksum comparison fails.

# Step 5 — Update the writings records

1. Enrich the post's entry in the current range `posts-list.json` with the
   canonical subtitle or `null`, exact publication timestamp, draft slug,
   draft filename, literal hashtags when present, image prefix, ordered image
   mappings, native dimensions, exact source URLs, final S3 URIs, current
   verification date, and `images_uploaded_to_s3: true` only after verification.
   Text-only posts use a null prefix, an empty images array, and a null upload
   flag.
2. Update `substack/dashboard.json`: published MDX count, published image
   count, remaining image-review posts, next conversion range, and date.
3. Do not update any checkpoint state yet. Keep completion history in this
   file, and change `agent-instructions.md` only when an operational rule
   changes.
4. Validate both JSON files with `jq empty` and run `git diff --check` in the
   writings repository.

# Final Step Cleanup tmp files and advance the checkpoint

1. Delete temporary text files (`source.json` and the temporary MDX) with
   `apply_patch`.
2. Delete only the explicit image and preview paths inside that post's exact
   `../shayan-arman-blog/.tmp-shayan-post-<number>/` directory. Do not use a
   broad recursive delete, glob, `$HOME`, `~`, or an unresolved variable.
3. Remove the now-empty temporary directory with `rmdir`.
4. Confirm both the temporary directory and the post-specific `live-posts`
   path do not exist.
5. Re-check the completed ledger entry and dashboard state. Only now update
   this file's `Last completed post`, `Next post`, `Last updated`, completed
   checkpoint table row, and range completion summary together in one patch.
6. After the checkpoint update succeeds, begin the next post automatically.

If internet access or the session stops before the final checkpoint update,
the `Next post` value intentionally remains unchanged. On resume, inspect that
post's temporary directory and run exact S3 `head-object` checks for every
expected key. Reuse and verify valid completed objects; do not blindly upload
duplicates. Finish the missing validation, ledger, cleanup, and checkpoint
steps before advancing.

## Active Batch

- Target: none; posts 416–417 are complete
- Processing mode: strictly one post at a time; no parallel post work
- Last completed post: 417
- Next post: 418 (not yet identified or authorized)
- Following post: none recorded
- Last updated: 2026-09-11

## Completed Checkpoints (only keep the last 20 % 0. meaning 400-now, or 420- now if we are at 421 for example)

| Post | Title | MDX S3 key | Images | Completed |
| ---: | --- | --- | ---: | --- |
| 400 | Homeless Man | `sites/shayan-arman-blog/posts/writings/2026-06-11-homeless-man.mdx` | 0 | 2026-08-12 |
| 401 | Pages | `sites/shayan-arman-blog/posts/writings/2026-06-12-pages.mdx` | 0 | 2026-08-12 |
| 402 | Capitalism on Neptune | `sites/shayan-arman-blog/posts/writings/2026-06-14-capitalism-on-neptune.mdx` | 1 | 2026-08-13 |
| 403 | Half Eaten | `sites/shayan-arman-blog/posts/writings/2026-07-09-half-eaten.mdx` | 1 | 2026-08-13 |
| 404 | On Depression | `sites/shayan-arman-blog/posts/writings/2026-07-17-on-depression.mdx` | 0 | 2026-08-13 |
| 405 | War | `sites/shayan-arman-blog/posts/writings/2026-07-18-war.mdx` | 0 | 2026-08-13 |
| 406 | Sharnification | `sites/shayan-arman-blog/posts/writings/2026-08-07-sharnification.mdx` | 0 | 2026-08-13 |
| 407 | Arnold on the Value of Hard Work | `sites/shayan-arman-blog/posts/writings/2026-08-10-arnold-on-the-value-of-hard-work.mdx` | 0 | 2026-08-13 |
| 408 | A New Mind | `sites/shayan-arman-blog/posts/writings/2026-08-11-a-new-mind.mdx` | 0 | 2026-08-13 |
| 409 | The Dawn of AGI | `sites/shayan-arman-blog/posts/writings/2026-08-23-the-dawn-of-agi.mdx` | 0 | 2026-08-22 |
| 410 | Eventual Understanding | `sites/shayan-arman-blog/posts/writings/2026-08-24-eventual-understanding.mdx` | 1 | 2026-08-25 |
| 411 | Token Maxxing | `sites/shayan-arman-blog/posts/writings/2026-08-25-token-maxxing.mdx` | 1 | 2026-08-25 |
| 412 | On Mental Health | `sites/shayan-arman-blog/posts/writings/2026-08-25-mental-health-ontology.mdx` | 1 | 2026-08-25 |
| 413 | The Value of Things | `sites/shayan-arman-blog/posts/writings/2026-09-05-the-value-of-things.mdx` | 1 | 2026-09-04 |
| 414 | Never Enough Intelligence | `sites/shayan-arman-blog/posts/writings/2026-09-05-never-enough-intelligence.mdx` | 1 | 2026-09-10 |
| 415 | The Shayan Arman Singularity | `sites/shayan-arman-blog/posts/writings/2026-09-07-the-shayan-arman-singularity.mdx` | 1 | 2026-09-10 |
| 416 | Celebrations | `sites/shayan-arman-blog/posts/writings/2026-09-08-celebrations.mdx` | 1 | 2026-09-11 |
| 417 | Singing | `sites/shayan-arman-blog/posts/writings/2026-09-11-singing.mdx` | 1 | 2026-09-11 |

## Resume Rule

Resume from the `Next post` value above. Re-check that the preceding post's
ledger entry and exact S3 objects are complete before starting it. Update this
file only after the current post has reached the full checkpoint described at
the top of this file.

## Range Completion Summary

- Posts 1–20: done
- Posts 21–40: done
- Posts 41–60: done
- Posts 61–80: done
- Posts 81–100: done
- Posts 101–120: done
- Posts 121–140: done
- Posts 141–160: done
- Posts 161–180: done
- Posts 181–200: done
- Posts 201–220: done
- Posts 221–240: done
- Posts 241–260: done
- Posts 261–280: done
- Posts 281–300: done
- Posts 301–320: done
- Posts 321–340: done
- Posts 341–360: done
- Posts 361–380: done
- Posts 381–400: done
- Posts 401–417: done
- Posts 418–420: not yet identified or authorized
