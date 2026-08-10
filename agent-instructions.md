# Agent Instructions: Shayan Arman Writings Migration

Use this file as the handoff for converting Shayan Arman's numbered Substack archive into reviewable MDX drafts for the Shayan Arman blog.

Also read `agent.md` in this directory. It contains the broader archive-import workflow and range-ledger conventions. When instructions overlap, this file controls the MDX migration and publishing workflow.

## Objective

Convert the archived Markdown articles under `substack/` into local MDX drafts for review, preserve their original Substack metadata and media placement, upload approved/requested images to the Shayan Arman site's S3 image area, and do not upload MDX posts until Shayan explicitly approves the drafts.

## Canonical Local Paths

Archive root:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/writings/substack/
```

Detailed ledger for posts 1–20:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/writings/substack/1-20/posts-list.json
```

Correct local application:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/
```

Correct local MDX draft directory:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/site/draft-post/
```

Do not put Shayan Arman drafts in:

```text
/Users/shayanarman/projects/seogangster/sites/zero-inbox-blog/site/draft-post/
```

That path was used temporarily by mistake. The 20 Shayan Arman MDX files were moved out of it and into the correct Shayan Arman application.

## Strict S3 Boundary

Only access this site prefix:

```text
s3://seo-gangster/sites/shayan-arman-blog/
```

Do not list, read, write, copy, sync, inspect permissions for, or delete any other prefix in the `seo-gangster` bucket.

Every AWS command must target `sites/shayan-arman-blog/` or a narrower key. Do not perform a bucket-wide operation.

Canonical post-image location:

```text
s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<post-slug>/<image-filename>
```

Future approved writings-post location:

```text
s3://seo-gangster/sites/shayan-arman-blog/posts/writings/YYYY-MM-DD-<slug>.mdx
```

Do not upload MDX posts until Shayan explicitly approves the local drafts. Permission to create drafts or upload images is not permission to publish posts.

## Current Completed State: Posts 1–20

All 20 posts from `substack/1-20/` have been converted into validated local MDX drafts in the correct Shayan Arman draft directory.

Draft files:

```text
2024-10-04-coming-soon.mdx
2024-10-04-the-economics-of-tourism.mdx
2024-10-12-freedom-from.mdx
2024-10-15-starting-a-billion-dollar-company.mdx
2024-10-16-thaly-ai-will-help-sales-people-sell-more.mdx
2024-10-16-the-way-of-things.mdx
2024-10-17-on-canada-and-democracy.mdx
2024-10-19-camino-santiago.mdx
2024-10-21-the-art-of-selling.mdx
2024-10-23-brands-are.mdx
2024-10-24-on-fear-and-opportunity.mdx
2024-10-26-are-solo-entrepreneurs-atheletes.mdx
2024-10-27-on-definitions.mdx
2024-10-29-on-running.mdx
2024-10-31-who-did-it.mdx
2024-11-08-the-two-layers-of-the-universe.mdx
2024-11-09-inter-conceptual-travel.mdx
2024-11-13-on-meditation.mdx
2024-11-18-the-unsettled-mind.mdx
2024-11-18-odysseus.mdx
```

There are 21 article images across 12 image-bearing posts. All 21 were uploaded and individually verified under the canonical Shayan Arman S3 image prefix. No MDX post was uploaded.

The `substack/1-20/posts-list.json` ledger was enriched and marks all 12 image-bearing posts with `images_uploaded_to_s3: true`.

Do not redo posts 1–20 unless Shayan asks for revisions. For the next migration prompt, start with the exact range Shayan names—most likely `substack/21-40/`—and apply the same ledger, date, hashtag, image-quality, draft-location, S3-boundary, and approval rules.

## Source Metadata Rules

The range ledger already provides the title and canonical Substack URL. Use it first.

When a publication date or subtitle is missing, retrieve the original Substack metadata from:

```text
https://shayanarman.substack.com/api/v1/posts/<substack-slug>
```

Use:

- `title` as the authoritative title.
- `subtitle` as the authoritative subtitle, or `null` when absent.
- `post_date` as the authoritative publication timestamp.
- The `YYYY-MM-DD` portion of `post_date` in both the MDX filename and frontmatter `date`.

Whenever metadata is recovered, update that exact entry in the matching `posts-list.json`. Do not leave recovered metadata only in the MDX.

## Ledger Fields For MDX Migration

Each migrated ledger entry can include:

- `subtitle`: original Substack subtitle or `null`.
- `published_at`: exact original Substack timestamp.
- `draft_slug`: chosen lowercase kebab-case slug.
- `draft_file`: dated MDX filename.
- `image_s3_prefix`: slug-specific S3 image folder or `null`.
- `images`: ordered image mapping array.
- `images_uploaded_to_s3`: `true` only after every mapped image was verified in S3; use `null` for posts with no images.
- `last_verified`: current verification date.

Each object in `images` records:

- `archive_filename`: original local archive filename, or `null` if the source image had been missing locally.
- `filename`: normalized final filename.
- `width` and `height`.
- `s3_uri`.
- `source_url`: original full-quality source object.
- `processing` when a browser-compatibility conversion was required.

## Slug And Filename Rules

- Create a simple lowercase kebab-case slug from the actual Substack title.
- Keep the historical spelling in the title and slug unless Shayan asks for a correction. For example, post 12 currently uses `are-solo-entrepreneurs-atheletes`.
- MDX filenames must be `YYYY-MM-DD-<slug>.mdx`.
- Frontmatter `date` must match the filename date.
- Normalize image basenames to lowercase kebab-case with dashes.
- Replace underscores with dashes, such as `zero_inbox.jpg` to `zero-inbox.png` when the source content is actually PNG.
- Use a correct browser-compatible extension for the real file format.

## MDX Frontmatter Shape

Use the existing Shayan drafts as the pattern. Common fields are:

```mdx
---
title: "Post title"
subtitle: "Original subtitle"
date: "YYYY-MM-DD"
category: "Writings"
collection: "Writings"
author: "Shayan Arman"
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

Omit image fields when the article has no images. Omit `subtitle` when the original post has none.

Use the first suitable source image as the metadata thumbnail. Preserve that image's original body position; do not add a second hero image that duplicates it solely for presentation.

## Hashtag Rules

Extract only literal source hashtags from the archived Markdown. Add them to frontmatter as a quoted `hashtags:` list with the leading `#`, normalized to lowercase and deduplicated.

Do not invent hashtags for source posts that do not contain them.

Six posts in range 1–20 contain literal hashtags and already have metadata:

- `the-economics-of-tourism`: `#zeroinbox`, `#inboxzero`, `#sellanything`, `#thaly`, `#sales`
- `freedom-from`: `#learning`, `#art`, `#financial`, `#freedom`, `#passive`, `#income`, `#sellanything`, `#sales`, `#ai`, `#thaly`, `#zeroinbox`, `#inboxzero`
- `starting-a-billion-dollar-company`: `#sellanything`
- `camino-santiago`: `#sellanything`, `#sales`, `#salesai`
- `brands-are`: `#sales`, `#ai`, `#thaly`
- `on-fear-and-opportunity`: `#sellanything`

The source hashtag lines remain in the article bodies. Do not remove them unless Shayan asks.

## Body Conversion Rules

- Remove the source title and subtitle from the body because the article layout renders them from frontmatter.
- Preserve Shayan's wording, capitalization, punctuation, paragraph order, and intentional roughness.
- Preserve source links.
- Convert angle-bracket URLs that MDX interprets as JSX into normal Markdown links.
- Replace invalid extraction placeholders with real media components.
- Preserve every source image's original position and order.
- Use `GangsterImage` for body images:

```mdx
import GangsterImage from "@shared/components/GangsterImage";

<GangsterImage
  src="s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/<filename>"
  width={1200}
  height={800}
  alt="Meaningful description"
  sizes="(max-width: 768px) 100vw, 760px"
/>
```

- Constrain small logos or artwork with `figureStyle` so they are not stretched beyond their native dimensions.
- Use real source captions when present. Do not invent a caption merely to fill a prop.
- Always provide meaningful alt text.

## Full-Quality Image Rules

- Use the original full-resolution `substack-post-media.s3.amazonaws.com` object.
- Never use a resized, cropped, or recompressed `substackcdn.com/image/fetch` rendition when the original browser-compatible object is available.
- Confirm the original dimensions and media type.
- If the original is browser-incompatible, such as HEIC, create a full-resolution browser-compatible conversion without downscaling.
- Post 14's running image was an original 3024×4032 HEIC and was uploaded as a full-resolution JPEG conversion.
- Post 6 had a source image placeholder but no local file. The original 233×590 Thaly logo-variations JPEG was recovered from the Substack source and uploaded.

## Draft Review And Approval Gate

Drafts are local-only until approval.

Preview route:

```text
/drafts/<slug>
```

Examples:

```text
/drafts/coming-soon
/drafts/the-economics-of-tourism
/drafts/freedom-from
```

The local development server must be running for these routes to work. Do not start `yarn dev` or `yarn build`; Shayan starts and builds the application himself.

After Shayan approves a draft:

1. Confirm title, date, slug, copy, images, and hashtags.
2. Confirm every final MDX image reference uses the approved S3 URI.
3. Upload the approved MDX to `sites/shayan-arman-blog/posts/writings/` only when explicitly asked.
4. Rebuild and verify using the site's established workflow when explicitly requested.
5. Do not delete local drafts or source archive files before the published route is confirmed.

## Required Validation

Before reporting a converted range as complete:

- Parse every MDX frontmatter block.
- Confirm filename date equals frontmatter `date`.
- Compile every MDX file with `@mdx-js/mdx`.
- Confirm no `<todo-image-shayan: ...>` placeholders remain.
- Confirm no unconverted Markdown image references remain when the draft uses `GangsterImage`.
- Confirm all S3 references begin with:
  `s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/`
- Compare the unique image references in the MDX set against the image mappings in `posts-list.json`.
- For uploaded images, verify each exact S3 key rather than doing a bucket-wide check.
- Set `images_uploaded_to_s3: true` only after exact-key verification succeeds.
- Do not run `yarn build` or `yarn dev`.

## Existing Worktree And Cleanup Notes

The Shayan Arman nested site repository already contains unrelated user changes. Preserve them and do not stage, revert, overwrite, or clean them.

During the range 1–20 image upload, temporary local image copies were staged under:

```text
/Users/shayanarman/projects/seogangster/sites/zero-inbox-blog/public/drafts/
```

Those files are not the canonical Shayan Arman drafts and are not referenced by the final MDX. Do not treat that Zero Inbox location as a source of truth. The original archive images and verified S3 objects remain canonical.

## Final Response Style

Keep handoffs concise. State:

- which numbered range was converted;
- the correct local draft directory;
- how many drafts and images were validated;
- whether images were uploaded;
- that no MDX posts were uploaded unless publication was explicitly approved;
- any real blocker that still needs Shayan's decision.
