# Agent Instructions: Shayan Arman Writings Migration

Read [`migration-checkpoints.md`](migration-checkpoints.md) first. It contains
the current resume point, completed ranges, active batch, detailed per-post
procedure, and interruption-recovery instructions. Also read `agent.md` for the
broader archive and ledger conventions.

This file contains operational rules only. Do not add post-by-post history or
completed-stage narratives here; record those in `migration-checkpoints.md`.

## Objective

Convert the numbered Substack archive into publishable Shayan Arman MDX while
preserving original metadata, wording, links, hashtags, image order, captions,
and full-quality media. Follow the active authorization and `Next post` value
in `migration-checkpoints.md`.

## Canonical Paths

Archive and range ledgers:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/writings/substack/
/Users/shayanarman/projects/seogangster/sites/shayan-arman/writings/substack/<range>/posts-list.json
/Users/shayanarman/projects/seogangster/sites/shayan-arman/writings/substack/dashboard.json
```

Checkpoint:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/writings/migration-checkpoints.md
```

Site application:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/
```

For the active direct-publication batch, create temporary files only under:

```text
/private/tmp/shayan-post-<number>/
```

Do not add active-batch MDX to `site/live-posts/` or `site/draft-post/`. Do not
place Shayan Arman files in the Zero Inbox site.

## Sequential Checkpoint Rule

- Process exactly one numbered post at a time. Do not parallelize post work.
- Complete validation, S3 upload, exact-key verification, ledger updates, and
  temporary-file cleanup before starting another post.
- Update `migration-checkpoints.md` only after the entire post is complete.
- Once a checkpoint is complete, continue automatically when the active batch
  authorizes later posts. Do not request approval between posts in that batch.
- If interrupted, resume from the checkpoint file and follow its recovery
  instructions. Do not assume partially staged or uploaded work is complete.
- Future work outside the active checkpoint batch requires explicit approval.

## Strict S3 Boundary

Only access this prefix or a narrower key:

```text
s3://seo-gangster/sites/shayan-arman-blog/
```

Never perform bucket-wide operations or inspect another site prefix.

Images:

```text
s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/<filename>
```

Published writings:

```text
s3://seo-gangster/sites/shayan-arman-blog/posts/writings/YYYY-MM-DD-<slug>.mdx
```

## Source Metadata

Start with the archived Markdown and matching range-ledger entry. Retrieve
canonical metadata when needed from:

```text
https://shayanarman.substack.com/api/v1/posts/<substack-slug>
```

Use the API's:

- `title` as the authoritative title;
- `subtitle` as the subtitle, omitting it from frontmatter when absent;
- exact `post_date` in the ledger;
- `YYYY-MM-DD` portion of `post_date` in the MDX filename and frontmatter;
- canonical URL as the quoted frontmatter `source-url`;
- body HTML for original image order, direct source objects, and source links.

Never reconstruct the post URL from the MDX slug when a ledger URL exists.
`source-url` belongs in frontmatter only; the shared layout renders the source
attribution.

## Slugs, Filenames, And Frontmatter

- Use a simple lowercase kebab-case slug based on the real title.
- Preserve historical spellings unless Shayan asks for corrections.
- Name MDX files `YYYY-MM-DD-<slug>.mdx`.
- Normalize image basenames to descriptive lowercase kebab-case.
- Make the image extension match the actual file bytes.

### Mandatory Global Uniqueness Check

Before creating the temporary MDX, and again immediately before the first S3
upload for that post, prove that the proposed `<slug>` is globally unique
across the whole Shayan Arman writings collection. An exact-key `head-object`
check is not sufficient because different dated filenames can still derive the
same route slug.

Run all three checks:

1. Search every `substack/*/posts-list.json` entry for the proposed
   `draft_slug`. A match belonging to any other post is a collision.
2. List only the authorized
   `sites/shayan-arman-blog/posts/writings/` S3 prefix, derive each route slug
   by removing the leading `YYYY-MM-DD-` and trailing `.mdx` from the basename,
   and reject any match with the proposed slug. Never broaden this listing to
   the bucket or another site prefix.
3. List the exact candidate image folder
   `sites/shayan-arman-blog/public/images/posts/<slug>/`. It must be empty for a
   new post. Even one existing object is a collision unless the post is being
   resumed and every existing exact key has already passed the documented
   byte-size, MIME-type, and checksum reconciliation. Never reuse another
   post's image folder, even when the images or titles happen to match.

Use the fail-closed preflight for all checks and the post-specific image-prefix
check; do not replace it with an informal `rg` or exact-key-only check:

```text
python3 substack/scripts/verify_publication_slug_unique.py <slug> --post-number <number>
```

Run it once before creating the MDX and again immediately before the first
upload. A nonzero result blocks publication. The recovery-only allow flags may
be used only after the interruption procedure has verified every exact current-
post S3 object separately.

If either check finds a collision, stop using that slug. Prefer the canonical
Substack URL slug when it is unique; otherwise append a concise descriptive
subtitle or other stable suffix. Then rerun both checks. Use the final unique
slug consistently in the MDX filename, route, post image prefix, thumbnail and
body image S3 URIs, and all ledger fields. Do not upload, overwrite, copy, or
delete an existing colliding object merely to make the check pass without
Shayan's explicit direction.

Use this frontmatter shape as applicable:

```mdx
---
title: "Post title"
subtitle: "Original subtitle"
date: "YYYY-MM-DD"
category: "Writings"
collection: "Writings"
author: "Shayan Arman"
source-url: "https://shayanarman.substack.com/p/example-slug"
keywords:
  - "descriptive keyword"
hashtags:
  - "#literal-source-hashtag"
excerpt: "A concise summary of the article."
changefreq: "monthly"
priority: "0.8"
thumbnail: "s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/<filename>"
imageAlt: "Meaningful image description"
imageFallbackText: "Post title"
---
```

Omit `subtitle` when absent. Omit thumbnail and image fields on text-only
posts. Use the first suitable source image or Substack-selected cover as the
thumbnail without duplicating it in the body.

## Body, Links, And Hashtags

- Remove the source title and subtitle from the body.
- Preserve all remaining wording, capitalization, punctuation, typos,
  paragraph order, line structure, and intentional roughness.
- Preserve source links. Convert visible raw `http://` or `https://` URLs into
  explicit Markdown links without changing their displayed text.
- Extract only literal source hashtags into a quoted, lowercase, deduplicated
  frontmatter list. Keep the original hashtag lines in the body.
- Do not invent hashtags, links, captions, or body copy.

## Footer Contract

Import the standard components and end every article in this exact order:

```mdx
<ShareArticleClipboard />

<ArticleDivider />

<ProductLinks />
```

There must be only one of each component and no separate body source link.

## Image Quality And Media Rules

- "make sure to download the full image versions, the highest quality not the slimmed down versions provided by some cdns"
- Download the direct original
  `substack-post-media.s3.amazonaws.com` object, never a resized or recompressed
  `substackcdn.com/image/fetch` rendition.
- Inspect actual format, byte size, native dimensions, MD5, and visual content.
- Do not trust a URL extension or API display width when the downloaded bytes
  show another format or larger native dimensions.
- Preserve original bytes when browser-compatible, including JPEG, PNG, WebP,
  GIF, and AVIF.
- For browser-incompatible originals such as HEIC, make a full-resolution,
  high-quality browser-compatible conversion without downscaling and record
  the processing in the ledger.
- Preserve image order and body position. Use meaningful alt text.
- Constrain small artwork to native width with `figureStyle`.

Use `GangsterImage` for body media:

```mdx
import GangsterImage from "@shared/components/GangsterImage";

<GangsterImage
  src="s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/<filename>"
  width={1200}
  height={800}
  alt="Meaningful description"
  sizes="(max-width: 768px) 100vw, 760px"
  caption="Exact source caption"
/>
```

Archive placeholders such as ``<todo-image-shayan: add image `...`>`` contain
authoritative captions. Put the exact caption in the matching `caption` prop,
remove the placeholder, and add exactly one standalone `<br />` immediately
after every captioned image. Do not add that spacer to uncaptioned images.
Keep linked or marked-up captions as React-node content rather than flattening
them.

## Ledger And Dashboard Rules

For every completed post, update its exact range-ledger entry with:

- canonical subtitle or `null`;
- exact `published_at` timestamp;
- `draft_slug` and `draft_file`;
- literal normalized hashtags when present;
- `image_s3_prefix`, ordered image mappings, native dimensions, exact source
  URLs, final S3 URIs, and processing notes when applicable;
- `images_uploaded_to_s3: true` only after every image verifies; use a null
  prefix, empty image array, and null upload flag for text-only posts;
- current `last_verified` date.

Update `substack/dashboard.json` counts, remaining work, publication state, and
date after each post. Record completion and the next post in
`migration-checkpoints.md` only after final cleanup.

## Required Validation

Before upload:

- compare visible MDX body copy against the archived source exactly;
- confirm title, subtitle, date, source URL, hashtags, links, image order,
  native dimensions, captions, thumbnail, and footer;
- confirm no placeholders or raw Markdown images remain;
- compile the temporary file with `@mdx-js/mdx`;
- run `yarn validate-site` from the site application;
- confirm no post-specific file exists in `site/live-posts/`.

For S3:

- run exact-key `head-object` checks before upload and do not overwrite an
  unexpected object;
- upload images sequentially with their real MIME types, then upload MDX;
- verify every uploaded object's `ContentLength` and single-part MD5 `ETag`;
- verify each image's `ContentType`;
- never use broad list, copy, sync, or delete operations.

After ledger updates:

- validate edited JSON with `jq empty`;
- run `git diff --check` in the writings repository;
- delete temporary text files with `apply_patch`;
- delete only explicit temporary image and preview paths;
- remove the empty post directory with `rmdir`;
- confirm the temporary directory and post-specific live-post path are absent;
- advance the checkpoint only after all prior checks pass.

Do not run `yarn build` or `yarn dev`.

## Worktree Safety And Handoff

Preserve unrelated user changes in both repositories. Do not stage, revert,
overwrite, or clean them. Never delete archive source files.

Keep progress updates concise. Report the latest durable checkpoint rather
than a history dump; detailed status belongs in `migration-checkpoints.md`.
