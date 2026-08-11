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

There are 21 article images across 12 image-bearing posts. All 21 were uploaded and individually verified under the canonical Shayan Arman S3 image prefix. As of 2026-08-10, all 20 MDX posts are also present under the canonical writings-post prefix.

The `substack/1-20/posts-list.json` ledger was enriched and marks all 12 image-bearing posts with `images_uploaded_to_s3: true`.

Do not redo posts 1–20 unless Shayan asks for revisions. For later ranges, apply the same ledger, date, hashtag, image-quality, draft-location, S3-boundary, and approval rules.

## Current Completed State: Posts 21–40

All 20 posts from `substack/21-40/` have been converted into validated local MDX files in the Shayan Arman draft directory and uploaded to:

```text
s3://seo-gangster/sites/shayan-arman-blog/posts/writings/
```

Post 39 is the only image-bearing post in this range. Its three original full-resolution HEIC images were converted to quality-100 browser-compatible JPEGs without downscaling, uploaded to the post-specific image prefix, and verified at 3024×4032, 3024×4032, and 4284×5712.

All 20 MDX files and all three images were verified against their exact S3 keys and local byte sizes on 2026-08-10. The `substack/21-40/posts-list.json` ledger contains the authoritative metadata, draft filenames, source URLs, image mappings, processing notes, and verification state.

Do not redo posts 21–40 unless Shayan asks for revisions.

## Current Completed State: Posts 41–60

All 20 posts from `substack/41-60/` have been converted into validated,
publishable MDX and uploaded to:

```text
s3://seo-gangster/sites/shayan-arman-blog/posts/writings/
```

Post 41, “One Yellow Card,” began as the one-post pilot and was subsequently
approved, completed, and uploaded. Posts 42–60 were then published directly
without creating intermediate `draft-post` copies.

Posts 43, 48, 51, and 60 are the four image-bearing posts in this range. Their
six original full-quality source images were uploaded under the corresponding
post-specific Shayan Arman image prefixes. The two post-43 files were original
PNG images stored under misleading archive/source extensions, so their final
S3 filenames use the correct `.png` extension. The remaining four images were
preserved as WebP files.

All 20 MDX posts in the range are present in S3. For posts 42–60, all 19 MDX
objects and all six image objects were individually verified against their
exact S3 keys, local byte sizes, and MD5 ETags on 2026-08-10. The published MDX
also passed frontmatter parsing, MDX compilation, ledger/source matching,
visible-link, hashtag, footer, image-order, and caption-placement validation.

The `substack/41-60/posts-list.json` ledger is authoritative for titles,
publication timestamps, source URLs, final filenames, image mappings, and
verification state. Do not redo posts 41–60 unless Shayan asks for revisions.
The next unconverted range starts at post 78.

## Current Completed State: Posts 61–77

Posts 61–66 have been converted into validated, publishable MDX in the local
Shayan Arman `site/live-posts/shayan-arman-blog/writings/` directory and
uploaded to the canonical writings-post S3 prefix. At Shayan's request, posts
67–77 were generated and validated one at a time in temporary storage,
uploaded directly to S3, and were not added to `site/live-posts/`.

Posts 62, 64, 66, 67, 69, 73, 74, 75, and 77 are the nine image-bearing posts
in this batch. Their fourteen original full-quality
`substack-post-media.s3.amazonaws.com` objects were verified at their native
dimensions and checksums before upload. Where archive files existed, the
original source objects were also verified byte-for-byte against them. Post 62's
`factory.jpg` archive file contains WebP data, so its final S3 filename and
MDX reference correctly use `factory.webp`. Post 66's misleading
`shibuya-station.jpg` archive filename was replaced with the descriptive final
filename `death-note-light-and-l.jpg`. Post 69's `judgemental-god.jpg` archive
file also contains WebP data, so its final filename is `judgemental-god.webp`.
Post 73's missing local image was recovered directly from the original
full-quality Substack PNG object. Post 74's three missing local diagrams were
recovered directly from the original full-quality Substack objects; the second
source URL ends in `.jpeg` but serves PNG data, so its final filename and
content type correctly use PNG. Post 75's missing local illustration was
recovered directly from the original full-quality 1024×1024 Substack PNG
object. Post 76 is text-only. Post 77's two missing local Zero Inbox images were
recovered directly from the original full-quality 1292×727 JPEG and 1179×2556
PNG objects. All fourteen image objects and all seventeen MDX objects were
verified against their exact S3 keys, local byte sizes, and MD5 ETags on
2026-08-11.

The `substack/61-80/posts-list.json` ledger is authoritative for the seventeen
titles, publication timestamps, source URLs, filenames, image mappings, and
verification state. Do not redo posts 61–77 unless Shayan asks for revisions.

## Completed Live-Post Pattern Upgrade: Posts 1–40

On 2026-08-10, Shayan asked for every existing local live writing post to be
updated to the finalized article pattern before continuing with later ranges.
All 40 MDX files under:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/site/live-posts/shayan-arman-blog/writings/
```

now comply with the following contract:

- exactly one ledger-matched quoted `source-url` in frontmatter, rendered by
  the shared article layout as the subtle “Source article” metadata link;
- every visible body URL is a clickable Markdown or JSX link rather than raw
  text;
- exactly one import and rendered instance of `ShareArticleClipboard`,
  `ArticleDivider`, and `ProductLinks`;
- the exact footer sequence `<ShareArticleClipboard />`,
  `<ArticleDivider />`, then `<ProductLinks />`;
- exactly one standalone `<br />` immediately after each captioned
  `GangsterImage`, with no spacer added to uncaptioned images.

The upgrade converted 13 raw body-URL occurrences into links and validated all
40 MDX files, all 40 ledger mappings, 24 `GangsterImage` instances, and all six
captioned images. MDX compilation, TypeScript, ESLint, the site contract, and
whitespace checks passed. No updated MDX files were uploaded to S3 as part of
this local live-post upgrade.

## Next Migration State: Posts 78–100

Posts 1–77 are complete and uploaded. The next unconverted posts are 78–80
within `substack/61-80/`, followed by `substack/81-100/`.

This records the intended sequence only. Do not convert or upload either range
until Shayan sends a new approval message naming the work to perform. If he
again requests direct publication without intermediate `draft-post` copies,
use the approved-batch workflow and preserve the same validation and exact-key
verification requirements used for posts 42–60.

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

## Live-Post Source URL Rule

Every migrated MDX file with a known ledger `substack_url`—including a local
review draft—must include the exact quoted `source-url` in frontmatter. The
shared article layout reads this field and renders a subtle “Source article”
text link in the metadata row after the category and date. Do not add a second
source link inside the MDX body.

Every MDX post placed under:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/site/live-posts/shayan-arman-blog/writings/
```

must include a quoted `source-url` field in its frontmatter. Match the live MDX file to its ledger entry using `draft_file`, then copy the exact `substack_url` value from the matching range's `posts-list.json`:

```mdx
source-url: "https://shayanarman.substack.com/p/example-slug"
```

Do not reconstruct the URL from the MDX slug, and do not confuse the post-level `substack_url` with an image mapping's `source_url`. Whenever drafts are moved into `site/live-posts/`, verify that every live post in the migrated range has exactly one `source-url` and that its value exactly matches the ledger.

## Article Footer Contract

Every converted article must end in this order:

1. `<ShareArticleClipboard />`.
2. `<ArticleDivider />`.
3. `<ProductLinks />`.

Import all required site components in the MDX:

```mdx
import ArticleDivider from "@site/components/ArticleDivider";
import ProductLinks from "@site/components/ProductLinks";
import ShareArticleClipboard from "@site/components/ShareArticleClipboard";
```

The source URL belongs only in frontmatter. The footer remains platform-neutral:

```mdx
<ShareArticleClipboard />

<ArticleDivider />

<ProductLinks />
```

Always keep `ArticleDivider`, the share component, and the product component.
This order supersedes the earlier placement of the divider above the share
section. There must be only one article-footer divider: between the share
section and ProductLinks.
Convert visible raw body URLs into explicit Markdown links so readers can click
them.

### Rendered Source Attribution Contract

The source attribution is owned centrally by:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/shared/components/Article/BlogArticle.tsx
```

`parseMdxDocument` maps the frontmatter `source-url` field to article metadata.
When present, `BlogArticle` renders the text “Source article” after the date,
separated by the same subtle metadata dot. The link opens in a new tab with
`noopener noreferrer` and uses quiet metadata styling with understated hover
and keyboard-focus feedback. Do not use a source card, source icon, envelope
icon, `SourceArticleLink` component, or duplicate body link.

### `ArticleDivider` Contract

The reusable component lives at:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/site/components/ArticleDivider/
```

`ArticleDivider` owns the only separator line in the article footer. Use it as
a standalone `<ArticleDivider />` immediately after
`<ShareArticleClipboard />` and immediately before `<ProductLinks />`. It must
render an accessible horizontal separator with a `3.5rem` top margin, a
`1px solid rgba(23, 23, 23, 0.14)` line, and a `2rem` bottom margin. Do not put
footer separator styles inside `ShareArticleClipboard` or `ProductLinks`, and
do not add another line above the share section.

### `ShareArticleClipboard` Contract

The reusable component lives at:

```text
/Users/shayanarman/projects/seogangster/sites/shayan-arman/shayan-arman-blog/site/components/ShareArticleClipboard/
```

Use `<ShareArticleClipboard />` without requiring article-specific props. It
must provide:

- an accessible X share link using
  `https://x.com/intent/post?text=<encoded-title>&url=<encoded-canonical-url>`;
- an accessible LinkedIn share link using
  `https://www.linkedin.com/sharing/share-offsite/?url=<encoded-canonical-url>&title=<encoded-title>`;
- a Copy link button that copies the canonical public article URL and gives
  visible success feedback;
- clear keyboard focus styles and accessible labels;
- the article's exact rendered title when a reader clicks a share control;
- the canonical `/writings/<slug>` URL rather than a local `/drafts/<slug>` URL
  when the component is rendered in draft preview.

Open social-share destinations in a new tab with `noopener noreferrer`. Keep
the presentation restrained and editorial: a “Share this article” heading,
square X and LinkedIn controls, and a wider Copy link control.
`ShareArticleClipboard` must not render a divider or external top
margin/padding. `ArticleDivider` owns the separator after the share section.
Avoid article-typography margins leaking into the share heading. `ProductLinks`
must have no built-in divider and no top padding; retain its `15px`
(`0.9375rem`) top margin after `ArticleDivider`.

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
- Convert every visible raw `http://` or `https://` body URL into an explicit
  Markdown link such as `[https://example.com](https://example.com)`. A URL
  appearing as plain text is not considered a finished link.
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
  caption="Exact source caption"
/>
```

- Constrain small logos or artwork with `figureStyle` so they are not stretched beyond their native dimensions.
- Use real source captions when present. Do not invent a caption merely to fill a prop.
- Always provide meaningful alt text.
- Put `<br />` on its own line immediately after every `GangsterImage` that has
  a `caption` prop. Do not add this caption spacer to images without captions.

### `GangsterImage` Caption Contract

Every real body-image caption belongs to the corresponding `GangsterImage` through its `caption` prop. Never leave a caption as a normal Markdown paragraph above or below the component.

For a plain-text caption, preserve the source wording exactly:

```mdx
<GangsterImage
  src="s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/<filename>"
  width={1200}
  height={800}
  alt="Meaningful description"
  sizes="(max-width: 768px) 100vw, 760px"
  caption="A photo I took in Paros Greece, my love for travel continued…"
/>

<br />
```

When the caption contains links or other inline markup, preserve them by passing a React node rather than flattening the caption into an unlinked string:

```mdx
<GangsterImage
  src="s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/<filename>"
  width={1200}
  height={800}
  alt="Meaningful description"
  sizes="(max-width: 768px) 100vw, 760px"
  caption={<>See <a href="https://example.com">the original source</a>.</>}
/>

<br />
```

Caption identification rules:

- Treat captions already encoded in archive placeholders such as ``<image-name: caption `...`>`` or ``<todo-image-shayan: add image `...`>`` as authoritative captions.
- Treat an italic line paired with a local Markdown image as its caption when the archive workflow identifies it that way.
- Older imports may contain image-specific descriptions, locations, credits, or promotional copy as plain body lines. Move those lines into the matching `caption` prop when the source context shows they belong to the image.
- Do not assume that the first paragraph after every image is a caption. If it continues the argument, story, dialogue, or introduces a separate link, preserve it as article body copy.
- When classification is ambiguous, compare the archived Markdown, the live Substack post, the image itself, and the surrounding paragraphs. If it is still ambiguous, preserve the line as body copy and flag it for Shayan instead of silently absorbing prose into the image.
- Keep caption text, punctuation, capitalization, and links intact. Do not replace the caption with the image alt text, and do not reuse the caption as alt text unless both genuinely serve the same purpose.
- After moving a caption into `GangsterImage`, remove the old standalone caption line so the caption appears exactly once.

## Full-Quality Image Rules

- "make sure to download the full image versions, the highest quality not the slimmed down versions provided by some cdns"
- Use the original full-resolution `substack-post-media.s3.amazonaws.com` object.
- Never use a resized, cropped, or recompressed `substackcdn.com/image/fetch` rendition when the original browser-compatible object is available.
- Confirm the original dimensions and media type.
- If the original is browser-incompatible, such as HEIC, create a full-resolution browser-compatible conversion without downscaling.
- Post 14's running image was an original 3024×4032 HEIC and was uploaded as a full-resolution JPEG conversion.
- Post 6 had a source image placeholder but no local file. The original 233×590 Thaly logo-variations JPEG was recovered from the Substack source and uploaded.

## Draft Review And Approval Gate

Drafts are local-only until approval.

### One-Post Pilot Before A Batch

When Shayan asks to see one post before deciding whether to run a larger batch:

1. Convert only the named pilot post into `site/draft-post/`.
2. Add its exact frontmatter `source-url`; rely on the shared article layout for
   the subtle rendered source link. End the footer with
   `<ShareArticleClipboard />`, `<ArticleDivider />`, and `<ProductLinks />` in
   that exact order.
3. Validate the pilot and provide its `/drafts/<slug>` preview route.
4. Do not convert, prepare, upload, or otherwise touch later posts in the
   proposed batch.
5. Do not upload the pilot MDX or any batch MDX/images to S3.
6. Wait for a new, explicit approval message from Shayan.

A description of what should happen *after* approval—even when it contains
phrasing such as “okay make them all”—is not present approval when Shayan also
says he wants to inspect the pilot first. Treat the approval checkpoint as the
controlling instruction.

After Shayan explicitly approves the pilot and explicitly authorizes the named
batch, perform only those named ranges. If he also says there is no need to
create `draft-post` copies for the approved batch, generate publishable MDX in
a safe local working area, run the complete validation suite, upload images and
MDX to the exact approved Shayan Arman S3 prefixes, verify each exact key, and
update the corresponding ledgers. Do not interpret pilot approval alone as
authorization for unmentioned ranges.

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
- Confirm every MDX with a ledger `substack_url` has exactly one frontmatter
  `source-url` whose value matches the ledger exactly.
- For every live MDX post, confirm `source-url` exactly matches the `substack_url` in the ledger entry identified by `draft_file`.
- Confirm every visible raw body URL has been converted to a clickable Markdown
  link, excluding URLs intentionally used as link destinations, component
  props, or frontmatter values.
- When `substack_url` exists, confirm the shared article header renders exactly
  one subtle “Source article” text link whose `href` matches `source-url`.
- Confirm there is no `SourceArticleLink` import, source card, source icon, or
  duplicate source link in the MDX body.
- Confirm the footer order is exactly one `<ShareArticleClipboard />`, exactly
  one `<ArticleDivider />`, then exactly one `<ProductLinks />`.
- Confirm the only article-footer line is the standalone `<ArticleDivider />`
  between the share section and ProductLinks; confirm neither
  `ShareArticleClipboard` nor `ProductLinks` contains a divider, and confirm
  ProductLinks retains its `15px` (`0.9375rem`) top margin after the divider.
- Confirm the X and LinkedIn share destinations encode the article title and
  canonical public URL, and confirm Copy link uses that same canonical URL.
- Confirm filename date equals frontmatter `date`.
- Compile every MDX file with `@mdx-js/mdx`.
- Confirm no `<todo-image-shayan: ...>` placeholders remain.
- Confirm no unconverted Markdown image references remain when the draft uses `GangsterImage`.
- Inspect every image-bearing post and confirm every known source caption is present exactly once in the corresponding `GangsterImage` `caption` prop.
- Confirm no known caption remains as a standalone Markdown paragraph above or below its `GangsterImage`.
- Confirm ordinary prose adjacent to images was not mistakenly moved into a caption.
- Confirm caption links and other inline markup remain functional React-node content rather than being flattened or dropped.
- Confirm each `GangsterImage` with a `caption` prop is followed immediately by
  a standalone `<br />`, and that uncaptioned images do not receive this
  caption spacer.
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
- whether the work is a one-post pilot awaiting approval or an explicitly
  approved batch;
- the correct local draft directory;
- how many drafts and images were validated;
- whether images were uploaded;
- that no MDX posts were uploaded unless publication was explicitly approved;
- any real blocker that still needs Shayan's decision.
