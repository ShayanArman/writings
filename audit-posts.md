# Post Audit Checkpoints

This file is the durable resume point for the read-only audit of all 408
Substack-to-MDX migrations. The audit exists to find missing, added, replaced,
or reordered words; changed capitalization, spelling, punctuation, links,
hashtags, images, or captions; incorrect metadata; broken MDX; and live routes
that do not render the exact published object.

This is a fidelity audit, not a spelling or grammar review. A historical typo
that exists in the source must remain in the migrated post. A post passes only
when the source, archive, published objects, and rendered page agree under the
narrow normalization rules below.

## Initial Collection Baseline

The following read-only baseline was confirmed on 2026-08-13:

- the archive contains exactly 408 numbered Markdown source files;
- the 21 range ledgers contain 408 entries with 408 unique post numbers, 408
  unique Substack URLs, 408 unique `draft_slug` values, and 408 unique
  `draft_file` values;
- no ledger entry is missing its number, title, Substack URL, slug, or MDX
  filename;
- `substack/dashboard.json` totals 408 imported posts, 408 published MDX
  objects, and 198 published images;
- the authorized S3 writings prefix contains exactly 408 `.mdx` objects;
- the first and last public routes both return HTTP 200:
  `https://www.shayanarman.com/writings/coming-soon` and
  `https://www.shayanarman.com/writings/a-new-mind`;
- `shayan-arman-blog/site/live-posts/shayan-arman-blog/writings/` contains
  exactly 408 MDX files, and its filename set exactly matches all 408 ledger
  `draft_file` values with no missing or extra files. Audit these local live
  MDX files directly, then prove each file matches its exact S3 object before
  awarding a publication-identity pass.

The baseline proves inventory only. It does not prove that any individual
post's content is correct.

## Audit Scope And Safety

- Audit posts 1 through 408, exactly one numbered post at a time.
- Run the collection-wide inventory preflight once before post 1 and once
  after post 408. Per-post work remains sequential so findings and evidence
  cannot be assigned to the wrong post.
- The audit is read-only. Do not upload, overwrite, copy, move, or delete any
  S3 object while auditing.
- Do not edit archive Markdown, range ledgers, the dashboard, live MDX, or
  source posts to make a comparison pass.
- Do not repair a confirmed defect during the audit. Record it and continue so
  all 408 posts receive the same independent review. Corrections require a
  separately authorized remediation pass.
- A public HTTP 500, a missing route, a wrong post rendered at a route, or
  evidence of data loss is a P0 finding. Record it and tell Shayan immediately,
  even though the remaining read-only audit should continue.
- Never run `yarn build` or `yarn dev`.
- Never create or update a file in `site/live-posts/` or `site/draft-post/`.
- Temporary audit files belong only in
  `/private/tmp/shayan-post-audit-<number>/` and must be removed after the
  checkpoint is recorded.
- Preserve unrelated user changes. Never stage, commit, revert, or clean them.
- S3 access is limited to the exact Shayan Arman site prefix:

  ```text
  s3://seo-gangster/sites/shayan-arman-blog/
  ```

- Collection listings must stay below:

  ```text
  s3://seo-gangster/sites/shayan-arman-blog/posts/writings/
  ```

- Image reads must use the exact current post prefix below:

  ```text
  s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/
  ```

## The Five Audit Surfaces

Every post must be checked across five surfaces. No single surface is enough.

1. **Current Substack API source**
   controls the canonical title, subtitle, exact publication timestamp,
   canonical URL, current visible body, link destinations, image order,
   captions, and direct original-image URLs.
2. **Archived Markdown** under `substack/<range>/<number>/`
   records the wording and layout captured for migration. It is especially
   important when the Substack post changed after it was archived.
3. **Local live MDX** under
   `shayan-arman-blog/site/live-posts/shayan-arman-blog/writings/`
   is the complete 408-file corpus to inspect for migration fidelity. Resolve
   each file only through the ledger's exact `draft_file` value.
4. **Exact published S3 objects**
   are the MDX and images actually stored for the Shayan Arman site. Prove the
   local live MDX is byte-identical to its exact ledger-derived S3 object. If
   the identity check cannot prove equality, download that exact S3 MDX into
   the post's temporary directory and audit both copies separately.
5. **Rendered public route** at
   `https://www.shayanarman.com/writings/<draft_slug>`
   proves that the deployed application serves and renders the intended S3
   content.

Use the range-ledger entry only to join these copies and to verify the expected
mapping. A ledger value agreeing with S3 does not prove the migration is
correct if both disagree with the source.

### How To Classify A Three-Way Text Result

The body comparison first considers Substack (`S`), archived Markdown (`A`),
and the local live MDX (`M`) after `M` is proven byte-identical to S3. The live
rendered body is checked separately against `M`. If local and S3 MDX differ,
neither copy receives a publication-identity pass; preserve and compare both.

| Result | Meaning | Action |
| --- | --- | --- |
| `S = A = M` | Exact source fidelity | Continue with links, media, and live checks. |
| `S = A != M` | Confirmed migration defect | Record P1 with the smallest exact diff. |
| `S != A = M` | Source changed later or the archive missed source content | Record `REVIEW`; do not auto-correct. |
| `S = M != A` | Archive-only divergence | Record `REVIEW`; preserve both hashes and inspect source history. |
| `A != M`, with `S` unavailable | Probable migration defect, not independently confirmed | Record `REVIEW`; do not guess. |
| All three differ | Ambiguous | Record `REVIEW` with all three excerpts and hashes. |

If the public rendered body differs from `M`, record a P0 when the wrong or
broken post is served and a P1 when deployed content is merely stale or
different.

## Narrow Normalization Rules

The audit must compare a sequence of semantic content events, not a loose bag
of words and not an edit-distance score. For example, a body can be represented
as ordered events such as `paragraph`, `heading`, `list-item`, `link`, `image`,
and `caption`.

Only these transformations may be ignored in the text lane:

- CRLF versus LF line endings;
- Unicode NFC normalization;
- leading or trailing whitespace around a block;
- runs of HTML layout whitespace between inline nodes collapsed to one ASCII
  space;
- HTML entity encoding after decoding to the same Unicode character;
- Markdown or HTML emphasis markers when the visible text is unchanged;
- a Markdown link target when comparing visible text, because destinations are
  compared exactly in the link lane;
- the first source title and optional subtitle removed once from the archived
  body;
- archive image tokens and MDX `GangsterImage` components removed from the text
  lane, because their exact positions are compared in the media lane;
- audit footer components removed from the body comparison:
  `ShareArticleClipboard`, `ArticleDivider`, and `ProductLinks`.

Do not normalize or ignore:

- words, numbers, spelling, capitalization, punctuation, apostrophes, smart
  quotes, dashes, ellipses, symbols, or literal hashtags;
- paragraph, heading, list-item, blockquote, or line-break order;
- repeated lines, even when they look accidental;
- visible link text;
- image positions, order, captions, or caption repetition that exists as real
  body text.

A fuzzy score may help prioritize a diff, but it can never produce `PASS`.
`PASS` requires exact equality after only the rules above.

## Required Audit Helper Before Post 1

Before auditing post 1, create a deterministic helper at:

```text
substack/scripts/audit_live_post.py
```

The helper does not exist yet. Implement and test it once, then keep its
behavior stable for the whole audit. It must default to read-only and fail
closed. It must never offer a `--fix` or upload mode.

The helper must:

1. accept one post number and resolve its one ledger entry, one archive file,
   one exact local live MDX file, one exact S3 MDX key, exact image prefix, and
   public route;
2. fetch the Substack API JSON from the ledger URL's `/p/<slug>` value;
3. use an AST or DOM parser for Markdown, MDX, and HTML; do not use a regex-only
   body parser;
4. emit the ordered source, archive, local MDX, and public semantic event
   streams, plus a separate S3 MDX stream whenever local-to-S3 byte identity
   does not pass;
5. compare metadata, visible text, block structure, links, literal hashtags,
   media, MDX contracts, S3 object metadata, and the public route in separate
   result lanes;
6. write a machine-readable JSON report inside the current temporary audit
   directory and print a short human-readable result;
7. report `PASS`, `FAIL`, `REVIEW`, or `BLOCKED` for each lane and exit nonzero
   unless every required lane passes;
8. include SHA-256 hashes of the archive source, API JSON, local live MDX, any
   downloaded differing S3 MDX, and normalized event streams so a later file
   or object change invalidates the old evidence;
9. show the smallest useful unified diff with event numbers and surrounding
   context, never only "content differs";
10. never print or store AWS credentials, signed URLs, cookies, or unrelated
    environment values.

Validate the helper against at least these fixtures before post 1:

- post 1: minimal text-only post without a subtitle;
- post 3: image, hashtags, and visible raw URLs;
- post 51: captions plus intentional repeated caption body lines;
- post 112: route slug intentionally differs from the original title slug;
- post 408: recent text-only post with a subtitle.

For each fixture, deliberately mutate a temporary MDX copy by deleting one
word, changing punctuation, changing a link target, moving an image, and
changing a caption. Each mutation must fail only the expected result lane.
Do not begin the durable post-1 audit until these negative controls work.

## Collection-Wide Inventory Preflight

Run this before post 1 and repeat it after post 408. Save the command output in
the current audit report, then summarize it in this file.

Confirm all of the following:

- archive post directories cover every integer from 1 through 408 exactly
  once, and each contains exactly one Markdown file;
- range-ledger keys cover 1 through 408 exactly once and each `file_number`
  equals its key;
- every entry has a title, Substack URL, `draft_slug`, `draft_file`,
  `published_at`, and `last_verified`;
- `draft_slug`, `draft_file`, and `substack_url` are globally unique;
- each `draft_file` is exactly `YYYY-MM-DD-<draft_slug>.mdx`, and its date is
  the `YYYY-MM-DD` portion of `published_at`;
- dashboard totals agree with the ledgers;
- the local live-posts writings directory contains exactly 408 `.mdx` files,
  and its filename set exactly equals the 408 ledger `draft_file` values;
- the set of 408 expected ledger-derived S3 MDX keys equals the set of `.mdx`
  objects below the authorized writings prefix, with no missing or extra MDX;
- every S3 filename derives a unique route slug;
- the public `/writings` collection route returns HTTP 200 and exposes all 408
  unique routes through pagination, the sitemap, or the site's content API;
- no two live routes declare the same canonical URL;
- no route returns 404, 500, a redirect to another post, or a Next.js error
  page.

The existing duplicate-source check is useful but is only one part of this
preflight:

```text
python3 substack/scripts/detect_duplicate_post_urls.py
```

Never make a bucket-wide S3 request. List only:

```text
sites/shayan-arman-blog/posts/writings/
```

## Per-Post Audit Procedure

### Step 1 - Resolve The Post And Capture Immutable Inputs

1. Read this file, `migration-checkpoints.md`, the post's range ledger, and the
   entire archived Markdown file.
2. Confirm the post number equals the ledger key and `file_number`.
3. Create `/private/tmp/shayan-post-audit-<number>/`.
4. Fetch the current Substack API response into `source.json` using the exact
   ledger URL slug. Record its HTTP status, retrieval time, and SHA-256.
5. Resolve the exact local live MDX at
   `shayan-arman-blog/site/live-posts/shayan-arman-blog/writings/<draft_file>`.
   Record its byte length, MD5, and SHA-256 without editing or copying it.
6. Run `head-object` on the exact ledger-derived S3 MDX key. Record
   `ContentLength`, `ContentType`, ETag, and `LastModified`. Require the local
   byte length and MD5 to match the S3 values. If the ETag is not a single-part
   MD5 or any value differs, download only that exact S3 object as
   `s3-published.mdx` in the temporary directory, hash it, and preserve a
   local-versus-S3 diff. Do not overwrite either copy.
7. Derive the public route only from `draft_slug`. Do not substitute the
   Substack URL slug because collision repairs intentionally make some route
   slugs different.
8. If any identity maps to another post, record P0 and stop this post before
   doing content comparisons.

### Step 2 - Audit Metadata And Identity

Compare exact values across the API, archive header, ledger, MDX frontmatter,
S3 key, public HTML metadata, and visible article header:

- post number and title;
- subtitle, including exact absence when it is null;
- exact `published_at` in the ledger and its date in the MDX filename,
  frontmatter, public visible date, and structured data;
- `Writings` category and collection;
- `Shayan Arman` author;
- exact canonical Substack `source-url` and rendered `Source article` href;
- `draft_slug`, MDX filename, S3 key, public pathname, canonical page URL, Open
  Graph URL, and structured-data `mainEntityOfPage`;
- literal normalized source hashtags in frontmatter and unchanged literal
  hashtag lines in the body;
- required excerpt, keywords, change frequency, and priority shape;
- thumbnail fields present only when appropriate and pointing to the current
  post's authorized image prefix.

Do not treat invented keywords or excerpts as source-copy errors unless they
are broken or misleading. Record those as P3 metadata findings. Title,
subtitle, date, source URL, canonical route, and literal hashtags are fidelity
fields and must be exact.

### Step 3 - Audit Every Word And Structural Event

1. Build the current Substack API event stream from human-authored body blocks.
   Exclude Substack chrome, scripts, styles, recommendation widgets, and
   iframe internals. Capture figure captions in the media lane.
2. Build the archive event stream after removing the first exact title and
   optional subtitle once. Convert image references and todo placeholders to
   position-preserving media events.
3. Build the local live MDX event stream after removing frontmatter, imports,
   the three standard footer components, `GangsterImage` code, and required
   caption spacer `<br />` nodes. Markdown links contribute visible text here
   and their destinations to the link lane. If local-to-S3 byte identity did
   not pass, build and compare a separate S3 MDX stream as well.
4. Compare the three streams using only the narrow normalization rules above.
5. Report the first differing event, the smallest complete diff, and whether
   words were missing, added, replaced, or reordered. Continue comparing the
   remainder so one early omission cannot hide later defects.
6. Separately compare block kinds and order. Identical words arranged into the
   wrong paragraphs, headings, list items, or blockquotes are not an exact
   structural pass.
7. Verify the MDX contains the footer exactly once and in this order:

   ```mdx
   <ShareArticleClipboard />

   <ArticleDivider />

   <ProductLinks />
   ```

8. Verify no archive placeholder, todo marker, raw Markdown image, raw source
   title/subtitle, migration comment, traceback, script, or network-error text
   remains.

### Step 4 - Audit Links And Literal Hashtags

Compare links as ordered pairs of exact visible text and exact destination.
The same visible wording with a different destination fails.

For every body link:

- compare source order, visible text, destination, query string, and fragment;
- distinguish a real source link from a visible raw URL converted to an
  explicit Markdown link;
- require external absolute URLs to retain their scheme and hostname;
- detect links lost during archive import as `S != A = M`, not as a clean pass;
- request each safe public destination with a lightweight method when
  practical, but record third-party blocking or rate limiting as a warning,
  not a content defect;
- never follow authenticated, destructive, unsubscribe, or account-action
  links.

Extract literal source hashtags without inventing any. Require the frontmatter
list to be lowercase and deduplicated while the visible body line stays exactly
as written in the source.

### Step 5 - Audit Images Sequentially

Process one image completely before moving to the next.

1. Extract the source image events in body order from the Substack API,
   including the direct `substack-post-media.s3.amazonaws.com` original URL,
   caption, and source position.
2. Compare the source count and order with the archive image tokens, ledger
   `images` array, MDX `GangsterImage` components, and rendered figures.
3. Require every MDX and ledger S3 URI to stay under the exact current post
   image prefix. Reject cross-post image reuse unless Shayan explicitly
   documented it.
4. Download the direct source original and the exact S3 object into the
   temporary directory. Compare byte length, actual file type, native width and
   height, and MD5/S3 ETag. For an intentionally converted browser-incompatible
   source, require the ledger's processing note and compare source identity,
   full-resolution dimensions, conversion format, and visual contents instead
   of claiming byte identity.
5. Compare MDX `width` and `height` with the S3 object's native dimensions.
6. Compare exact captions, React-node link destinations inside captions, and
   the one required standalone `<br />` after each captioned image. Require no
   spacer after an uncaptioned image.
7. Verify meaningful `alt` text and ensure the public image loads with nonzero
   `naturalWidth` and `naturalHeight` and no browser console or network error.
8. Visually compare the source original with the rendered figure. Exact bytes
   prove identity, but the visual check also catches cropping, orientation,
   layout, and caption-placement mistakes.
9. Check the thumbnail selection, URI, alt text, and fallback text separately
   from body image order.

Text-only posts must have no source image events, no archive image tokens, an
empty ledger `images` array, null image-prefix/upload fields, no MDX image
components or thumbnail fields, and no rendered body figures.

### Step 6 - Compile And Inspect The Public Route

1. Compile the exact local live MDX with `@mdx-js/mdx` using the site
   application's real import aliases. If it differs from S3, compile the
   separately downloaded `s3-published.mdx` too.
2. Run `yarn validate-site` from the Shayan Arman site without modifying the
   site. Never run `yarn build` or `yarn dev`.
3. Request the exact public route with redirects disabled first. A redirect to
   a different pathname is a finding. Then load the final page in a real
   browser.
4. Require HTTP 200, the expected final URL, canonical URL, H1, optional
   subtitle, date, source link, and no Next.js error page.
5. Inside `main article`, isolate the final body container and stop before the
   section whose accessible heading is `Share this article`. Extract its
   semantic events and compare them exactly with the S3-verified local MDX
   event stream. If local and S3 differ, identify which copy the route renders.
6. Compare rendered link pairs and figure events with the MDX link and media
   lanes.
7. Confirm there are no uncaught console errors, failed first-party requests,
   broken images, duplicate H1s, or visible MDX/component syntax.
8. Test both desktop and mobile widths for image overflow, clipped text,
   malformed lists, and captions detached from their image. Visual layout does
   not replace the exact event comparison.

### Step 7 - Record The Result And Advance

Record one machine-readable audit result per post in
`substack/audit-results.json`. Create that file only when the audit begins. Its
post entry must include:

- post number, title, ledger path, archive path, local live MDX path, S3 MDX
  key, and public route;
- retrieval timestamps and SHA-256 hashes for archive, source API JSON, local
  live MDX, any differing downloaded S3 MDX, and all normalized event streams;
- `PASS`, `FAIL`, `REVIEW`, or `BLOCKED` for inventory, metadata, text,
  structure, links, hashtags, media, MDX compile, and live render;
- local MDX byte length, MD5, and SHA-256 plus S3 ETag and `LastModified`, so a
  file or object change invalidates the result;
- finding IDs, severity, smallest useful diff, and evidence paths;
- overall result and audit date.

Use these overall states:

- `PASS`: every required lane passed with exact evidence;
- `FAIL`: at least one confirmed defect exists;
- `REVIEW`: the copies disagree but the direction of truth is ambiguous;
- `BLOCKED`: required evidence could not be obtained after retrying safely.

A `FAIL` or `REVIEW` post is still fully audited once its evidence and finding
are durable. Advance to the next numbered post. A `BLOCKED` post does not
advance until its missing evidence is obtained or Shayan explicitly accepts a
documented limitation.

After saving the JSON result:

1. append a row to `Completed Audit Checkpoints` below;
2. append every non-pass result to `Findings` without removing earlier history;
3. update `Last audited post`, `Next post`, counts, date, and the range summary
   together in one patch;
4. validate `substack/audit-results.json` with `jq empty` and run
   `git diff --check`;
5. delete only the explicit files inside the exact temporary directory, remove
   the empty directory with `rmdir`, and confirm it is gone;
6. begin the next numbered post automatically.

## Finding Severity And Status

| Severity | Definition | Examples |
| --- | --- | --- |
| P0 | Public route failure, wrong-post identity, or serious data-loss risk | HTTP 500/404, one route serves another post, widespread route collision |
| P1 | Source-fidelity defect | missing/extra/replaced/reordered words, wrong punctuation, title, subtitle, date, source URL, link, image, or caption |
| P2 | Rendering, media, or accessibility defect without lost prose | broken dimensions, bad MIME, poor alt text, mobile overflow, caption layout |
| P3 | Non-source editorial or SEO concern | weak excerpt, misleading invented keyword, optional metadata quality |

Finding statuses are `OPEN`, `CONFIRMED`, `AMBIGUOUS`, `FIXED`, and
`RE-VERIFIED`. Never delete a finding after a repair. Record the old and new
S3 hashes and the re-verification date.

## Remediation Boundary

This file authorizes discovery and evidence collection only. It does not
authorize S3 writes or source edits.

After all 408 posts are audited, group confirmed findings by severity and
request one explicit remediation authorization. During remediation:

- correct one post at a time from a freshly downloaded S3 MDX object;
- change only confirmed defects;
- rerun every audit lane for that post, not just the previously failing lane;
- use exact-key preconditions and preserve the prior object's ETag and hash;
- follow the publication validation and checksum rules in
  `migration-checkpoints.md`;
- update the finding to `FIXED`, then `RE-VERIFIED` only after the public route
  serves the corrected object and the full audit passes.

## Active Audit

- Target: posts 1-408 inclusive
- Processing mode: one post at a time; no parallel per-post audit work
- Inventory preflight: PASS before post 1 and after post 408 (final: 2026-08-14T07:01:05Z)
- Audit helper: implemented; five fixture mutations and negative controls PASS
- Audit results ledger: `substack/audit-results.json`
- Last audited post: 408
- Next post: none; discovery audit complete
- Audited: 408 of 408
- Passed: 236
- Failed: 81
- Needs review: 91
- Blocked: 0
- Open P0 findings: 0
- Open P1 findings: 86
- Open P2 findings: 15
- Open P3 findings: 0
- Ambiguous findings: 218
- Last updated: 2026-08-14

## Completed Audit Checkpoints

Add one row only after the entire post has a durable machine-readable result.
`Findings` is `none` for a clean pass or a comma-separated list of finding IDs.

| Post | Title | Text | Links | Media | Live | Overall | Findings | Audited |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Coming soon | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 2 | The Economics of Tourism | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 3 | Freedom from | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 4 | Starting a Billion Dollar Company | PASS | PASS | PASS | PASS | FAIL | AP-0004-HASHTAGS | 2026-08-14 |
| 5 | Thaly.AI will help Sales People sell more. | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 6 | The way of things | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 7 | On Canada and Democracy | REVIEW | PASS | FAIL | PASS | FAIL | AP-0007-TEXT, AP-0007-STRUCTURE, AP-0007-MEDIA | 2026-08-14 |
| 8 | Camino - Santiago? | REVIEW | PASS | PASS | PASS | REVIEW | AP-0008-TEXT, AP-0008-STRUCTURE | 2026-08-14 |
| 9 | The Art of Selling | PASS | REVIEW | PASS | PASS | REVIEW | AP-0009-LINKS | 2026-08-14 |
| 10 | Brands are | PASS | PASS | FAIL | PASS | FAIL | AP-0010-MEDIA | 2026-08-14 |
| 11 | On Fear and Opportunity | PASS | PASS | FAIL | PASS | FAIL | AP-0011-MEDIA | 2026-08-14 |
| 12 | Are Solo Entrepreneurs Atheletes | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 13 | On Definitions | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 14 | On Running | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0014-TEXT, AP-0014-STRUCTURE, AP-0014-LINKS | 2026-08-14 |
| 15 | Who did it? | REVIEW | REVIEW | FAIL | PASS | FAIL | AP-0015-TEXT, AP-0015-STRUCTURE, AP-0015-LINKS, AP-0015-MEDIA | 2026-08-14 |
| 16 | The Two Layers of the Universe | REVIEW | PASS | PASS | PASS | REVIEW | AP-0016-TEXT, AP-0016-STRUCTURE | 2026-08-14 |
| 17 | Inter-Conceptual Travel | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 18 | On Meditation | REVIEW | PASS | PASS | PASS | REVIEW | AP-0018-TEXT, AP-0018-STRUCTURE | 2026-08-14 |
| 19 | The Unsettled Mind | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 20 | Odysseus | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 21 | The Value of Value | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 22 | The little things | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 23 | Minor Deviations | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 24 | On Creation | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 25 | On Emergence | PASS | PASS | PASS | PASS | REVIEW | AP-0025-STRUCTURE | 2026-08-14 |
| 26 | On Values | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 27 | Emergent Properties | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 28 | What we are most concerned with | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 29 | Alive and Wed; Un-Reasonably Dead; | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 30 | Princep, August, Apex | REVIEW | PASS | PASS | PASS | REVIEW | AP-0030-TEXT, AP-0030-STRUCTURE | 2026-08-14 |
| 31 | What a mess | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 32 | a b c's | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 33 | Shaking Hands with Kings | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 34 | Selling your iPhone to God | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 35 | On Change | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 36 | Korea (internet is incredible) | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 37 | Its Easy | REVIEW | PASS | PASS | PASS | REVIEW | AP-0037-TEXT, AP-0037-STRUCTURE | 2026-08-14 |
| 38 | In the End: Equality | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 39 | The Greatest Cover Letter of all Time | FAIL | PASS | FAIL | PASS | FAIL | AP-0039-TEXT, AP-0039-STRUCTURE, AP-0039-MEDIA | 2026-08-14 |
| 40 | On Negotiation | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0040-TEXT, AP-0040-STRUCTURE, AP-0040-LINKS | 2026-08-14 |
| 41 | One Yellow Card | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0041-TEXT, AP-0041-STRUCTURE, AP-0041-LINKS | 2026-08-14 |
| 42 | Jahiliyyah | REVIEW | PASS | PASS | PASS | REVIEW | AP-0042-TEXT, AP-0042-STRUCTURE | 2026-08-14 |
| 43 | The Hidden Variable | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0043-TEXT, AP-0043-STRUCTURE, AP-0043-LINKS | 2026-08-14 |
| 44 | Theory of Similarities | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 45 | Genetics as a Novel | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 46 | The End of Email | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 47 | Art of the Deal | PASS | REVIEW | PASS | PASS | REVIEW | AP-0047-LINKS | 2026-08-14 |
| 48 | Intrepid, to the Stars | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 49 | On Creationism | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 50 | The Party | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 51 | On Work | REVIEW | PASS | PASS | PASS | REVIEW | AP-0051-TEXT, AP-0051-STRUCTURE | 2026-08-14 |
| 52 | On Life | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 53 | 2 Trees | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 54 |  .. / ..-. .. --. ..- .-. . -.. / .. - / --- ..- - | PASS | PASS | PASS | PASS | REVIEW | AP-0054-STRUCTURE | 2026-08-14 |
| 55 | Double Taxation | PASS | PASS | PASS | PASS | REVIEW | AP-0055-STRUCTURE | 2026-08-14 |
| 56 | On Suffering | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 57 | On Language | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 58 | On Infinity | PASS | PASS | PASS | PASS | REVIEW | AP-0058-STRUCTURE | 2026-08-14 |
| 59 | The Line | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 60 | The Depth of your Education | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 61 | On Meaning and Identity | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 62 | On Upward Mobility | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 63 | The Difference | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 64 | People don't appreciate this enough | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 65 | I ask you only one thing... | PASS | PASS | PASS | PASS | REVIEW | AP-0065-STRUCTURE | 2026-08-14 |
| 66 | How to catch a thief | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 67 | Who is Satoshi | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0067-TEXT, AP-0067-STRUCTURE, AP-0067-LINKS | 2026-08-14 |
| 68 | Never have you ever | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 69 | Where is God's place? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 70 | petri dish economics | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 71 | The Nuclear Umbrella | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 72 | Umbrellas Part 2 | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 73 | What is love? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 74 | Pain, Pleasure, and Redemption | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 75 | Your Lucky Week | PASS | FAIL | FAIL | PASS | FAIL | AP-0075-LINKS, AP-0075-MEDIA | 2026-08-14 |
| 76 | On the River | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 77 | (Ad) Zero Inbox Email Cleaner and Manager at ZeroInbox.ai | PASS | PASS | FAIL | PASS | FAIL | AP-0077-MEDIA | 2026-08-14 |
| 78 | Tariff Wars; and Email Inboxes | REVIEW | REVIEW | FAIL | PASS | FAIL | AP-0078-TEXT, AP-0078-STRUCTURE, AP-0078-LINKS, AP-0078-MEDIA | 2026-08-14 |
| 79 | The illusion of choice | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 80 | Warren Buffett | PASS | PASS | FAIL | PASS | FAIL | AP-0080-MEDIA | 2026-08-14 |
| 81 | Invest in Yourself | REVIEW | PASS | FAIL | PASS | FAIL | AP-0081-TEXT, AP-0081-STRUCTURE, AP-0081-MEDIA | 2026-08-14 |
| 82 | Given | PASS | PASS | FAIL | PASS | FAIL | AP-0082-MEDIA | 2026-08-14 |
| 83 | A Bottle of Wine for the Table | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 84 | A latte please | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 85 | Very truly, what is the problem? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 86 | On Thinking | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 87 | On listening | PASS | REVIEW | PASS | PASS | REVIEW | AP-0087-LINKS | 2026-08-14 |
| 88 | Listening part 2 | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 89 | !Ontological Man! | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 90 | The Beginning | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 91 | Little by little | PASS | REVIEW | PASS | PASS | REVIEW | AP-0091-LINKS | 2026-08-14 |
| 92 | Give give give | PASS | PASS | PASS | PASS | REVIEW | AP-0092-STRUCTURE | 2026-08-14 |
| 93 | Tell me one thing to rule your life. | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 94 | Czech Pilsner | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 95 | Tell me again | REVIEW | PASS | PASS | PASS | REVIEW | AP-0095-TEXT, AP-0095-STRUCTURE | 2026-08-14 |
| 96 | On Sickness | PASS | PASS | FAIL | PASS | FAIL | AP-0096-MEDIA | 2026-08-14 |
| 97 | The Apple of my Eye | PASS | PASS | FAIL | PASS | FAIL | AP-0097-MEDIA | 2026-08-14 |
| 98 | The Ugly Duckling | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 99 | Who is The Father of Silicon Valley? | PASS | REVIEW | FAIL | PASS | FAIL | AP-0099-LINKS, AP-0099-MEDIA | 2026-08-14 |
| 100 | Lost in Translation | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 101 | Divergence | PASS | PASS | FAIL | PASS | FAIL | AP-0101-HASHTAGS, AP-0101-MEDIA | 2026-08-14 |
| 102 | Quantum Coders | PASS | PASS | FAIL | PASS | FAIL | AP-0102-MEDIA | 2026-08-14 |
| 103 | Sign Here Please | PASS | PASS | FAIL | PASS | FAIL | AP-0103-MEDIA | 2026-08-14 |
| 104 | On Addiction | PASS | PASS | FAIL | FAIL | FAIL | AP-0104-MEDIA, AP-0104-LIVE-RENDER | 2026-08-14 |
| 105 | Generating the Absurd | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 106 | To Serve | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 107 | On Belief Systems | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 108 | Empires with Umpires | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 109 | Mykonos | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 110 | The Pillars | REVIEW | PASS | PASS | PASS | REVIEW | AP-0110-TEXT, AP-0110-STRUCTURE | 2026-08-14 |
| 111 | Nearology | PASS | PASS | FAIL | PASS | FAIL | AP-0111-MEDIA | 2026-08-14 |
| 112 | On Language | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 113 | Da Club | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 114 | The End of Labour | PASS | PASS | FAIL | PASS | FAIL | AP-0114-MEDIA | 2026-08-14 |
| 115 | The TRUTH! | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 116 | Specifically What? | PASS | PASS | FAIL | PASS | FAIL | AP-0116-MEDIA | 2026-08-14 |
| 117 | Is it worth it? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 118 | On Wealth | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 119 | The Funniest Shit | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 120 | All is Observance | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 121 | On Awakening | PASS | PASS | FAIL | PASS | FAIL | AP-0121-MEDIA | 2026-08-14 |
| 122 | On Philosophy | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 123 | Now is as good a time as … | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 124 | Courage to Venture | PASS | PASS | FAIL | PASS | FAIL | AP-0124-MEDIA | 2026-08-14 |
| 125 | On Desire | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 126 | an Even further discussion on Virtue | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 127 | El Vicco | PASS | REVIEW | PASS | PASS | REVIEW | AP-0127-LINKS | 2026-08-14 |
| 128 | The Champ | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 129 | My Cousin | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 130 | Wisdom | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 131 | The Most Gracious | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 132 | Aphorisms | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 133 | On Folding Sheets | PASS | PASS | FAIL | PASS | FAIL | AP-0133-MEDIA | 2026-08-14 |
| 134 | Friendly Magician | PASS | REVIEW | PASS | PASS | REVIEW | AP-0134-LINKS | 2026-08-14 |
| 135 | Abra Cadabra bitches! | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 136 | Inflation | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 137 | The shape of things | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 138 | An Athlete of Life | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 139 | The Drinker | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 140 | On Me | PASS | PASS | FAIL | PASS | FAIL | AP-0140-MEDIA | 2026-08-14 |
| 141 | On Equality | PASS | PASS | FAIL | PASS | FAIL | AP-0141-MEDIA | 2026-08-14 |
| 142 | Rule Breakers | PASS | REVIEW | PASS | PASS | REVIEW | AP-0142-LINKS | 2026-08-14 |
| 143 | Twisted Thinking | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 144 | The Don | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 145 | On Suffering | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 146 | Dreaming with God | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 147 | Belief Systems | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 148 | The Rise of Boogeymen | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 149 | On Marx | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 150 | Dying Twice | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 151 | The Most Beautiful | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 152 | Why not me? | REVIEW | PASS | PASS | PASS | REVIEW | AP-0152-TEXT, AP-0152-STRUCTURE | 2026-08-14 |
| 153 | The Train of Philosophy | REVIEW | PASS | FAIL | PASS | FAIL | AP-0153-TEXT, AP-0153-STRUCTURE, AP-0153-MEDIA | 2026-08-14 |
| 154 | Environmentalism | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 155 | You scratched it! | REVIEW | PASS | PASS | PASS | REVIEW | AP-0155-TEXT, AP-0155-STRUCTURE | 2026-08-14 |
| 156 | Conservative Closed Minded | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 157 | True Friend | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 158 | On Cleaning | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 159 | Question Master | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 160 | On Miracles | PASS | PASS | FAIL | PASS | FAIL | AP-0160-MEDIA | 2026-08-14 |
| 161 | Knowledge and Prediction | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 162 | Curses | REVIEW | PASS | PASS | PASS | REVIEW | AP-0162-TEXT, AP-0162-STRUCTURE | 2026-08-14 |
| 163 | Core Things | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 164 | Blame Games | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 165 | Habitual | REVIEW | PASS | PASS | PASS | REVIEW | AP-0165-TEXT, AP-0165-STRUCTURE | 2026-08-14 |
| 166 | Business Class Blues | REVIEW | PASS | PASS | PASS | REVIEW | AP-0166-TEXT, AP-0166-STRUCTURE | 2026-08-14 |
| 167 | On Sleep | PASS | PASS | FAIL | PASS | FAIL | AP-0167-MEDIA | 2026-08-14 |
| 168 | Andrew Tate | PASS | PASS | PASS | PASS | REVIEW | AP-0168-STRUCTURE | 2026-08-14 |
| 169 | To take a Stand | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 170 | Andrew Tate and Exceptionalism | REVIEW | PASS | PASS | PASS | REVIEW | AP-0170-TEXT, AP-0170-STRUCTURE | 2026-08-14 |
| 171 | Heights Unseen | PASS | PASS | PASS | PASS | REVIEW | AP-0171-STRUCTURE | 2026-08-14 |
| 172 | A Conceptual Proof of the Soul and How to Learn a Language | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 173 | Summative | PASS | PASS | PASS | PASS | REVIEW | AP-0173-STRUCTURE | 2026-08-14 |
| 174 | Vibe Coding | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 175 | Exceptionalism | REVIEW | PASS | PASS | FAIL | FAIL | AP-0175-TEXT, AP-0175-STRUCTURE, AP-0175-HASHTAGS, AP-0175-LIVE-RENDER | 2026-08-14 |
| 176 | Economic Spaces | REVIEW | PASS | PASS | PASS | REVIEW | AP-0176-TEXT, AP-0176-STRUCTURE | 2026-08-14 |
| 177 | The Conductor | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 178 | Perceptions | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 179 | Ontology | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 180 | End Theory | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 181 | Startup Weather | PASS | PASS | PASS | PASS | REVIEW | AP-0181-STRUCTURE | 2026-08-14 |
| 182 | Pre Donald Trump | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 183 | Fatal Attraction | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 184 | Random Wednesdays | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 185 | The Artists Life | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 186 | On Marketing | REVIEW | PASS | PASS | PASS | REVIEW | AP-0186-TEXT, AP-0186-STRUCTURE | 2026-08-14 |
| 187 | The Labourer | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 188 | The Label Maker | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 189 | The Good Friend | REVIEW | PASS | PASS | PASS | REVIEW | AP-0189-TEXT, AP-0189-STRUCTURE | 2026-08-14 |
| 190 | Starting a Startup | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 191 | Purpose and Direction | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 192 | Sam Altman | PASS | REVIEW | PASS | PASS | REVIEW | AP-0192-STRUCTURE, AP-0192-LINKS | 2026-08-14 |
| 193 | The Blind | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 194 | Me on a Walk | REVIEW | PASS | PASS | PASS | REVIEW | AP-0194-TEXT, AP-0194-STRUCTURE | 2026-08-14 |
| 195 | On Motivation | REVIEW | PASS | PASS | PASS | REVIEW | AP-0195-TEXT, AP-0195-STRUCTURE | 2026-08-14 |
| 196 | Slope Change Philosophy | PASS | PASS | PASS | PASS | REVIEW | AP-0196-STRUCTURE | 2026-08-14 |
| 197 | Globalism | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 198 | The Third Voice | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 199 | Nobody | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 200 | On Sleep | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 201 | On Bad Company | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 202 | On Failure | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 203 | On memories | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 204 | To Be | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 205 | Sinner | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 206 | Theory of Expressionism | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 207 | Heroes | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 208 | Modern Philosophy | PASS | PASS | PASS | PASS | REVIEW | AP-0208-STRUCTURE | 2026-08-14 |
| 209 | Programming | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 210 | Iterations | REVIEW | PASS | PASS | PASS | REVIEW | AP-0210-TEXT, AP-0210-STRUCTURE | 2026-08-14 |
| 211 | Sides Taken | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 212 | Layering Knowledge | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 213 | On Becoming Exceptional | REVIEW | PASS | PASS | PASS | REVIEW | AP-0213-TEXT, AP-0213-STRUCTURE | 2026-08-14 |
| 214 | Through Him; | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 215 | The Mind and Reality | FAIL | PASS | PASS | PASS | FAIL | AP-0215-TEXT, AP-0215-STRUCTURE | 2026-08-14 |
| 216 | The Shame of Exceptionalism | FAIL | PASS | PASS | PASS | FAIL | AP-0216-TEXT, AP-0216-STRUCTURE | 2026-08-14 |
| 217 | My Daughter did what? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 218 | Trying your Best | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 219 | Mykonos 2026 | REVIEW | PASS | PASS | PASS | REVIEW | AP-0219-TEXT, AP-0219-STRUCTURE | 2026-08-14 |
| 220 | On Loan | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 221 | ~The Jumper~ | PASS | PASS | PASS | PASS | REVIEW | AP-0221-STRUCTURE | 2026-08-14 |
| 222 | Loopy Thinkiiiiingggg | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 223 | We all want to be Goku | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 224 | On Production | REVIEW | PASS | PASS | PASS | REVIEW | AP-0224-TEXT, AP-0224-STRUCTURE | 2026-08-14 |
| 225 | Ask God Not | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 226 | The Don | PASS | PASS | FAIL | PASS | FAIL | AP-0226-MEDIA | 2026-08-14 |
| 227 | On Death | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 228 | On Business | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 229 | Summative Action | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 230 | Billion Dollar Baby | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 231 | 2 ways north | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 232 | On Famy | PASS | PASS | FAIL | PASS | FAIL | AP-0232-STRUCTURE, AP-0232-MEDIA | 2026-08-14 |
| 233 | Economy in Five | PASS | PASS | FAIL | PASS | FAIL | AP-0233-MEDIA | 2026-08-14 |
| 234 | Been a while | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 235 | The Red Purse | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 236 | The Global Religion | PASS | PASS | FAIL | PASS | FAIL | AP-0236-STRUCTURE, AP-0236-MEDIA | 2026-08-14 |
| 237 | (SUPER SUPER EMBARASSING) | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 238 | Opposing Reactions | PASS | PASS | FAIL | PASS | FAIL | AP-0238-MEDIA | 2026-08-14 |
| 239 | Internet Personalities and Trust Fund Babies | REVIEW | PASS | PASS | PASS | REVIEW | AP-0239-TEXT, AP-0239-STRUCTURE | 2026-08-14 |
| 240 | effects | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 241 | Belief Systems | PASS | PASS | PASS | PASS | REVIEW | AP-0241-STRUCTURE | 2026-08-14 |
| 242 | AI Subcontext Rule | REVIEW | PASS | FAIL | PASS | FAIL | AP-0242-TEXT, AP-0242-STRUCTURE, AP-0242-MEDIA | 2026-08-14 |
| 243 | Lucky Lucky Money Money | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 244 | Derivative Theory | PASS | REVIEW | PASS | PASS | FAIL | AP-0244-LINKS, AP-0244-HASHTAGS | 2026-08-14 |
| 245 | Golden Words | PASS | PASS | FAIL | PASS | FAIL | AP-0245-MEDIA | 2026-08-14 |
| 246 | 3 Steps to God | PASS | PASS | FAIL | PASS | FAIL | AP-0246-STRUCTURE, AP-0246-MEDIA | 2026-08-14 |
| 247 | MONEY | PASS | PASS | FAIL | FAIL | FAIL | AP-0247-MEDIA, AP-0247-LIVE-RENDER | 2026-08-14 |
| 248 | Money 2 | PASS | PASS | FAIL | PASS | FAIL | AP-0248-MEDIA | 2026-08-14 |
| 249 | Startups | PASS | PASS | FAIL | PASS | FAIL | AP-0249-MEDIA | 2026-08-14 |
| 250 | Exponential Chain Theory | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 251 | Single Step Theory | PASS | PASS | FAIL | PASS | FAIL | AP-0251-MEDIA | 2026-08-14 |
| 252 | priced in | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 253 | Onto-logic | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 254 | Paths, Journeys, Goals, and... | PASS | PASS | PASS | PASS | REVIEW | AP-0254-STRUCTURE | 2026-08-14 |
| 255 | The Hill | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 256 | Partner in Crime | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 257 | The Eye | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 258 | The Garbage Men | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 259 | The Garbage Men | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 260 | The Garbage Men | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 261 | The Garbage Men | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 262 | The Garbage Men | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 263 | Pain | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 264 | Network Topology - Pool Theory | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 265 | Useless Knowledge | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 266 | Circular Economies | REVIEW | PASS | PASS | PASS | REVIEW | AP-0266-TEXT, AP-0266-STRUCTURE | 2026-08-14 |
| 267 | Providence | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 268 | I meditated for 3 hours | PASS | PASS | FAIL | PASS | FAIL | AP-0268-STRUCTURE, AP-0268-MEDIA | 2026-08-14 |
| 269 | On Lying | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 270 | All is Fire | REVIEW | PASS | PASS | PASS | REVIEW | AP-0270-TEXT, AP-0270-STRUCTURE | 2026-08-14 |
| 271 | How I laughed! | PASS | PASS | PASS | PASS | REVIEW | AP-0271-STRUCTURE | 2026-08-14 |
| 272 | Its Easy Shy! | PASS | PASS | PASS | PASS | REVIEW | AP-0272-STRUCTURE | 2026-08-14 |
| 273 | Arbitrage | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 274 | Kafka? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 275 | My Phone Call with the CRA | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 276 | The Weighing Man | REVIEW | PASS | PASS | PASS | REVIEW | AP-0276-TEXT, AP-0276-STRUCTURE | 2026-08-14 |
| 277 | The Cra | REVIEW | PASS | PASS | PASS | REVIEW | AP-0277-TEXT, AP-0277-STRUCTURE | 2026-08-14 |
| 278 | Tojo's Lesson | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 279 | Aha Business!! | PASS | PASS | FAIL | PASS | FAIL | AP-0279-MEDIA | 2026-08-14 |
| 280 | A constant diagnosis | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 281 | On Youth | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 282 | On Sand | PASS | PASS | FAIL | PASS | FAIL | AP-0282-MEDIA | 2026-08-14 |
| 283 | On Suffering | PASS | PASS | PASS | PASS | REVIEW | AP-0283-STRUCTURE | 2026-08-14 |
| 284 | Take a Look | REVIEW | PASS | PASS | PASS | REVIEW | AP-0284-TEXT, AP-0284-STRUCTURE | 2026-08-14 |
| 285 | Inverted Living | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 286 | Working | REVIEW | PASS | FAIL | PASS | FAIL | AP-0286-TEXT, AP-0286-STRUCTURE, AP-0286-MEDIA | 2026-08-14 |
| 287 | The Mind and Suicide and Jesus | PASS | PASS | FAIL | PASS | FAIL | AP-0287-STRUCTURE, AP-0287-MEDIA | 2026-08-14 |
| 288 | Et tu, Brute? | REVIEW | PASS | PASS | PASS | REVIEW | AP-0288-TEXT, AP-0288-STRUCTURE | 2026-08-14 |
| 289 | Moments | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 290 | Genie in a Bottle | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 291 | Manifest Identity | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 292 | The Axe Man | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 293 | The One Person Billion Dollar Company | PASS | REVIEW | PASS | PASS | REVIEW | AP-0293-STRUCTURE, AP-0293-LINKS | 2026-08-14 |
| 294 | On the Unknown | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 295 | A Conversation with Gemini on Job Security | REVIEW | PASS | PASS | FAIL | FAIL | AP-0295-TEXT, AP-0295-STRUCTURE, AP-0295-HASHTAGS, AP-0295-LIVE-RENDER | 2026-08-14 |
| 296 | A Consensus Algorithm | REVIEW | PASS | PASS | PASS | REVIEW | AP-0296-TEXT, AP-0296-STRUCTURE | 2026-08-14 |
| 297 | How Ai Will Replace Us | REVIEW | PASS | FAIL | PASS | FAIL | AP-0297-TEXT, AP-0297-STRUCTURE, AP-0297-MEDIA | 2026-08-14 |
| 298 | A New Depression | PASS | PASS | FAIL | PASS | FAIL | AP-0298-MEDIA | 2026-08-14 |
| 299 | Thy Unholy Neighbour | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 300 | Forms of the Mind | REVIEW | PASS | FAIL | PASS | FAIL | AP-0300-TEXT, AP-0300-STRUCTURE, AP-0300-MEDIA | 2026-08-14 |
| 301 | A Guest | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 302 | Coding and Driving | PASS | PASS | PASS | PASS | REVIEW | AP-0302-STRUCTURE | 2026-08-14 |
| 303 | The News | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 304 | The Startup Algorithm | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0304-TEXT, AP-0304-STRUCTURE, AP-0304-LINKS | 2026-08-14 |
| 305 | The Steak | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 306 | Ai will Replace Us | REVIEW | PASS | PASS | PASS | REVIEW | AP-0306-TEXT, AP-0306-STRUCTURE | 2026-08-14 |
| 307 | On Party | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 308 | The Discombobulator | REVIEW | PASS | FAIL | PASS | FAIL | AP-0308-TEXT, AP-0308-STRUCTURE, AP-0308-MEDIA | 2026-08-14 |
| 309 | A Mirror | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 310 | Three Brothers | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 311 | Three Brothers | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 312 | Sentient | REVIEW | PASS | PASS | PASS | REVIEW | AP-0312-TEXT, AP-0312-STRUCTURE | 2026-08-14 |
| 313 | Sweet Fruits | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 314 | Growth Rates to Die For | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 315 | Tell her i said what? | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 316 | On Freedom | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 317 | On Vitamin C | REVIEW | PASS | PASS | PASS | REVIEW | AP-0317-TEXT, AP-0317-STRUCTURE | 2026-08-14 |
| 318 | Real Growth Baby | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 319 | The Empty Mall | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 320 | Universal Directional Travel | REVIEW | PASS | PASS | PASS | REVIEW | AP-0320-TEXT, AP-0320-STRUCTURE | 2026-08-14 |
| 321 | Loopy Beliefs | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 322 | Endearing | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 323 | Grandstanding | PASS | PASS | FAIL | PASS | FAIL | AP-0323-MEDIA | 2026-08-14 |
| 324 | Random Bird Flight Paths | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 325 | By Bye Nay-Toe | REVIEW | PASS | PASS | PASS | REVIEW | AP-0325-TEXT, AP-0325-STRUCTURE | 2026-08-14 |
| 326 | Private Wine Tastings in Italy | PASS | REVIEW | PASS | PASS | REVIEW | AP-0326-STRUCTURE, AP-0326-LINKS | 2026-08-14 |
| 327 | Proetic | REVIEW | PASS | PASS | PASS | REVIEW | AP-0327-TEXT, AP-0327-STRUCTURE | 2026-08-14 |
| 328 | A Friend in Logic | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 329 | How to Code with AI Agents | PASS | PASS | FAIL | PASS | FAIL | AP-0329-MEDIA | 2026-08-14 |
| 330 | Many Startups | PASS | PASS | FAIL | PASS | FAIL | AP-0330-MEDIA | 2026-08-14 |
| 331 | Pre Sin | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 332 | Duplicitous Moral Standards | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 333 | Meek | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 334 | Annals of Time | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 335 | An Immovable Boulder | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 336 | The Doctor | PASS | PASS | FAIL | PASS | FAIL | AP-0336-MEDIA | 2026-08-14 |
| 337 | One Thing | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 338 | GETTING BUSY | PASS | PASS | FAIL | PASS | FAIL | AP-0338-MEDIA | 2026-08-14 |
| 339 | 2 am coding session | PASS | REVIEW | FAIL | PASS | FAIL | AP-0339-LINKS, AP-0339-MEDIA | 2026-08-14 |
| 340 | Narcos | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 341 | Narcos | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 342 | Stars Misaligned | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 343 | Esha Bhatti | PASS | REVIEW | FAIL | FAIL | FAIL | AP-0343-LINKS, AP-0343-MEDIA, AP-0343-LIVE-RENDER | 2026-08-14 |
| 344 | Psycholo-G | FAIL | PASS | FAIL | PASS | FAIL | AP-0344-TEXT, AP-0344-STRUCTURE, AP-0344-MEDIA | 2026-08-14 |
| 345 | Justin Bieber Part 1 | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 346 | True Diversity | PASS | PASS | PASS | FAIL | FAIL | AP-0346-LIVE-RENDER | 2026-08-14 |
| 347 | Best Friends  | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 348 | The Night Sky | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 349 | Acronyms | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 350 | The New Boxing Gym | REVIEW | PASS | PASS | PASS | REVIEW | AP-0350-TEXT, AP-0350-STRUCTURE | 2026-08-14 |
| 351 | The Crow | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 352 | 7 Day Girlfriends | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 353 | The Mind | REVIEW | PASS | PASS | PASS | REVIEW | AP-0353-TEXT, AP-0353-STRUCTURE | 2026-08-14 |
| 354 | Winged Words | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 355 | Ontological Victimhood | REVIEW | PASS | PASS | PASS | REVIEW | AP-0355-TEXT, AP-0355-STRUCTURE | 2026-08-14 |
| 356 | Reverse Inference | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 357 | Conservatives | FAIL | PASS | PASS | FAIL | FAIL | AP-0357-TEXT, AP-0357-STRUCTURE, AP-0357-LIVE-RENDER | 2026-08-14 |
| 358 | The structure of the universe | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 359 | Advices | FAIL | PASS | PASS | PASS | FAIL | AP-0359-TEXT, AP-0359-STRUCTURE | 2026-08-14 |
| 360 | The Goose | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 361 | My Stalker | FAIL | REVIEW | PASS | PASS | FAIL | AP-0361-TEXT, AP-0361-STRUCTURE, AP-0361-LINKS | 2026-08-14 |
| 362 | Insufferable | FAIL | PASS | PASS | PASS | FAIL | AP-0362-TEXT, AP-0362-STRUCTURE | 2026-08-14 |
| 363 | My Efforts | FAIL | PASS | FAIL | PASS | FAIL | AP-0363-TEXT, AP-0363-STRUCTURE, AP-0363-MEDIA | 2026-08-14 |
| 364 | Perfectionists Part 1 | REVIEW | PASS | PASS | PASS | REVIEW | AP-0364-TEXT, AP-0364-STRUCTURE | 2026-08-14 |
| 365 | Definition Friday… | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 366 | A path laid for me | REVIEW | PASS | PASS | PASS | REVIEW | AP-0366-TEXT, AP-0366-STRUCTURE | 2026-08-14 |
| 367 | Shame Scores | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 368 | The Diplomat | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 369 | Marcus Aurelius | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 370 | The Calling | REVIEW | PASS | PASS | PASS | REVIEW | AP-0370-TEXT, AP-0370-STRUCTURE | 2026-08-14 |
| 371 | The Wolf | REVIEW | PASS | PASS | PASS | REVIEW | AP-0371-TEXT, AP-0371-STRUCTURE | 2026-08-14 |
| 372 | On Fame | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 373 | The Don part 4 | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 374 | A Definitive Understanding of Human Development | REVIEW | REVIEW | FAIL | PASS | FAIL | AP-0374-TEXT, AP-0374-STRUCTURE, AP-0374-LINKS, AP-0374-MEDIA | 2026-08-14 |
| 375 | Rambling | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 376 | A life well lived | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 377 | Cafe Coding | REVIEW | REVIEW | FAIL | PASS | FAIL | AP-0377-TEXT, AP-0377-STRUCTURE, AP-0377-LINKS, AP-0377-MEDIA | 2026-08-14 |
| 378 | The Happiness Fairy | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 379 | Please stop | REVIEW | FAIL | FAIL | PASS | FAIL | AP-0379-TEXT, AP-0379-STRUCTURE, AP-0379-LINKS, AP-0379-MEDIA | 2026-08-14 |
| 380 | Why Universities are Good Part 1 | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 381 | The Martian Child | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 382 | On Business | REVIEW | PASS | FAIL | PASS | FAIL | AP-0382-TEXT, AP-0382-STRUCTURE, AP-0382-MEDIA | 2026-08-14 |
| 383 | Outside | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 384 | Pause part 1 | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 385 | At the Pool | PASS | PASS | FAIL | PASS | FAIL | AP-0385-MEDIA | 2026-08-14 |
| 386 | Turns | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 387 | The New New Testament | REVIEW | PASS | PASS | PASS | REVIEW | AP-0387-TEXT, AP-0387-STRUCTURE | 2026-08-14 |
| 388 | Drinking in Japan | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0388-TEXT, AP-0388-STRUCTURE, AP-0388-LINKS | 2026-08-14 |
| 389 | Virality | PASS | PASS | FAIL | PASS | FAIL | AP-0389-MEDIA | 2026-08-14 |
| 390 | Ew | REVIEW | REVIEW | FAIL | PASS | FAIL | AP-0390-TEXT, AP-0390-STRUCTURE, AP-0390-LINKS, AP-0390-MEDIA | 2026-08-14 |
| 391 | The Salmon | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 392 | Three Dimensions | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0392-TEXT, AP-0392-STRUCTURE, AP-0392-LINKS | 2026-08-14 |
| 393 | Reflexivity | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0393-TEXT, AP-0393-STRUCTURE, AP-0393-LINKS | 2026-08-14 |
| 394 | The End of Labour | PASS | PASS | FAIL | PASS | FAIL | AP-0394-MEDIA | 2026-08-14 |
| 395 | Responsibility | REVIEW | PASS | PASS | PASS | REVIEW | AP-0395-TEXT, AP-0395-STRUCTURE | 2026-08-14 |
| 396 | Enterprise | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 397 | Good Fortune | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 398 | ai slop | PASS | PASS | FAIL | PASS | FAIL | AP-0398-MEDIA | 2026-08-14 |
| 399 | Why Siri Failed - an honest take | PASS | PASS | FAIL | PASS | FAIL | AP-0399-MEDIA | 2026-08-14 |
| 400 | Homeless Man | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0400-TEXT, AP-0400-STRUCTURE, AP-0400-LINKS | 2026-08-14 |
| 401 | Pages | REVIEW | PASS | PASS | PASS | REVIEW | AP-0401-TEXT, AP-0401-STRUCTURE | 2026-08-14 |
| 402 | Capitalism on Neptune | REVIEW | REVIEW | FAIL | PASS | FAIL | AP-0402-TEXT, AP-0402-STRUCTURE, AP-0402-LINKS, AP-0402-MEDIA | 2026-08-14 |
| 403 | Half Eaten | REVIEW | REVIEW | PASS | PASS | REVIEW | AP-0403-TEXT, AP-0403-STRUCTURE, AP-0403-LINKS | 2026-08-14 |
| 404 | On Depression | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 405 | War | REVIEW | PASS | PASS | PASS | REVIEW | AP-0405-TEXT, AP-0405-STRUCTURE | 2026-08-14 |
| 406 | Sharnification | PASS | PASS | PASS | PASS | PASS | none | 2026-08-14 |
| 407 | Arnold on the Value of Hard Work | PASS | REVIEW | PASS | PASS | REVIEW | AP-0407-LINKS | 2026-08-14 |
| 408 | A New Mind | PASS | REVIEW | PASS | PASS | REVIEW | AP-0408-LINKS | 2026-08-14 |

## Findings

Keep the smallest exact evidence necessary to understand and reproduce the
problem. Do not paste an entire post when a short event diff is enough.

| ID | Post | Severity | Lane | Summary | Source evidence | Published evidence | Status |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| AP-0004-HASHTAGS | 4 | P1 | hashtags | Confirmed migration hashtag defect: Substack and archive agree but MDX differs. | source=["#1","#sellanything"]; archive=["#1","#sellanything"]; MDX=["#sellanything"] | audit-results.json posts[4].lanes.hashtags; MDX SHA-256 5190fb09ba5d; S3 identity PASS | OPEN |
| AP-0007-TEXT | 7 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[7].lanes.text; MDX SHA-256 5df1cabafd33; S3 identity PASS | AMBIGUOUS |
| AP-0007-STRUCTURE | 7 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[7].lanes.structure; MDX SHA-256 5df1cabafd33; S3 identity PASS | AMBIGUOUS |
| AP-0007-MEDIA | 7 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='Photo is of me in Kits Beach, Vancouver, BC, Canada on my boat!' | image 1 archive caption differs from MDX: archive=None MDX='Photo is of me in Kits Beach, Vancouver, BC, Canada on my boat!' | audit-results.json posts[7].lanes.media; MDX SHA-256 5df1cabafd33; S3 identity PASS | OPEN |
| AP-0008-TEXT | 8 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[8].lanes.text; MDX SHA-256 0d8cc76d7220; S3 identity PASS | AMBIGUOUS |
| AP-0008-STRUCTURE | 8 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[8].lanes.structure; MDX SHA-256 0d8cc76d7220; S3 identity PASS | AMBIGUOUS |
| AP-0009-LINKS | 9 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[9].lanes.links; MDX SHA-256 4ec894635679; S3 identity PASS | AMBIGUOUS |
| AP-0010-MEDIA | 10 | P1 | media | image 1 source MD5 differs from S3 ETag; image 1 source bytes differ from S3; image 2 source MD5 differs from S3 ETag; image 2 source bytes differ from S3; image 3 source MD5 differs from S3 ETag; image 3 source bytes differ from S3; image 4 source MD5 differs from S3 ETag; image 4 source bytes differ from S3 | image 1 source MD5 differs from S3 ETag; image 1 source bytes differ from S3; image 2 source MD5 differs from S3 ETag; image 2 source bytes differ from S3; image 3 source MD5 differs from S3 ETag; image 3 source bytes di | audit-results.json posts[10].lanes.media; MDX SHA-256 9373fc016bb3; S3 identity PASS | OPEN |
| AP-0011-MEDIA | 11 | P1 | media | image 3 source MD5 differs from S3 ETag; image 3 source bytes differ from S3; image 4 source MD5 differs from S3 ETag; image 4 source bytes differ from S3 | image 3 source MD5 differs from S3 ETag; image 3 source bytes differ from S3; image 4 source MD5 differs from S3 ETag; image 4 source bytes differ from S3 | audit-results.json posts[11].lanes.media; MDX SHA-256 6a3c33222f32; S3 identity PASS | OPEN |
| AP-0014-TEXT | 14 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[14].lanes.text; MDX SHA-256 4c652cecaec3; S3 identity PASS | AMBIGUOUS |
| AP-0014-STRUCTURE | 14 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[14].lanes.structure; MDX SHA-256 4c652cecaec3; S3 identity PASS | AMBIGUOUS |
| AP-0014-LINKS | 14 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[14].lanes.links; MDX SHA-256 4c652cecaec3; S3 identity PASS | AMBIGUOUS |
| AP-0015-TEXT | 15 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[15].lanes.text; MDX SHA-256 6d8d02043e43; S3 identity PASS | AMBIGUOUS |
| AP-0015-STRUCTURE | 15 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[15].lanes.structure; MDX SHA-256 6d8d02043e43; S3 identity PASS | AMBIGUOUS |
| AP-0015-LINKS | 15 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[15].lanes.links; MDX SHA-256 6d8d02043e43; S3 identity PASS | AMBIGUOUS |
| AP-0015-MEDIA | 15 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='Check out https://thaly.ai Kickstarter here: Thaly AI: Talk to my Agent'; image 2 archive caption differs from MDX: archive=None MDX='Get to Inbox Zero with https://zeroinbox.ai, Clear your Emails, Clear your mind with the Zero Inbox AI Email Cleaner and Organizer' | image 1 archive caption differs from MDX: archive=None MDX='Check out https://thaly.ai Kickstarter here: Thaly AI: Talk to my Agent'; image 2 archive caption differs from MDX: archive=None MDX='Get to Inbox Zero with htt | audit-results.json posts[15].lanes.media; MDX SHA-256 6d8d02043e43; S3 identity PASS | OPEN |
| AP-0016-TEXT | 16 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[16].lanes.text; MDX SHA-256 650659f874cc; S3 identity PASS | AMBIGUOUS |
| AP-0016-STRUCTURE | 16 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[16].lanes.structure; MDX SHA-256 650659f874cc; S3 identity PASS | AMBIGUOUS |
| AP-0018-TEXT | 18 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[18].lanes.text; MDX SHA-256 ccf82a81d301; S3 identity PASS | AMBIGUOUS |
| AP-0018-STRUCTURE | 18 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[18].lanes.structure; MDX SHA-256 ccf82a81d301; S3 identity PASS | AMBIGUOUS |
| AP-0025-STRUCTURE | 25 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[25].lanes.structure; MDX SHA-256 783a19c8580f; S3 identity PASS | AMBIGUOUS |
| AP-0030-TEXT | 30 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[30].lanes.text; MDX SHA-256 16d515a8e81d; S3 identity PASS | AMBIGUOUS |
| AP-0030-STRUCTURE | 30 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[30].lanes.structure; MDX SHA-256 16d515a8e81d; S3 identity PASS | AMBIGUOUS |
| AP-0037-TEXT | 37 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[37].lanes.text; MDX SHA-256 ab1a944d330a; S3 identity PASS | AMBIGUOUS |
| AP-0037-STRUCTURE | 37 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[37].lanes.structure; MDX SHA-256 ab1a944d330a; S3 identity PASS | AMBIGUOUS |
| AP-0039-TEXT | 39 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[39].lanes.text; MDX SHA-256 b6278ff0280d; S3 identity PASS | OPEN |
| AP-0039-STRUCTURE | 39 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[39].lanes.structure; MDX SHA-256 b6278ff0280d; S3 identity PASS | OPEN |
| AP-0039-MEDIA | 39 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='A photo I took in Paros Greece, my love for travel continued…'; image 2 archive caption differs from MDX: archive=None MDX='Another wonderful sunset in Greece'; image 3 archive caption differs from MDX: archive=None MDX='Me in Monaco with some friends I made from Quebec' | image 1 archive caption differs from MDX: archive=None MDX='A photo I took in Paros Greece, my love for travel continued…'; image 2 archive caption differs from MDX: archive=None MDX='Another wonderful sunset in Greece'; | audit-results.json posts[39].lanes.media; MDX SHA-256 b6278ff0280d; S3 identity PASS | OPEN |
| AP-0040-TEXT | 40 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[40].lanes.text; MDX SHA-256 ec8821a762fe; S3 identity PASS | AMBIGUOUS |
| AP-0040-STRUCTURE | 40 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[40].lanes.structure; MDX SHA-256 ec8821a762fe; S3 identity PASS | AMBIGUOUS |
| AP-0040-LINKS | 40 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[40].lanes.links; MDX SHA-256 ec8821a762fe; S3 identity PASS | AMBIGUOUS |
| AP-0041-TEXT | 41 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[41].lanes.text; MDX SHA-256 1a0634697c4c; S3 identity PASS | AMBIGUOUS |
| AP-0041-STRUCTURE | 41 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[41].lanes.structure; MDX SHA-256 1a0634697c4c; S3 identity PASS | AMBIGUOUS |
| AP-0041-LINKS | 41 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[41].lanes.links; MDX SHA-256 1a0634697c4c; S3 identity PASS | AMBIGUOUS |
| AP-0042-TEXT | 42 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[42].lanes.text; MDX SHA-256 2e9ee8c422b9; S3 identity PASS | AMBIGUOUS |
| AP-0042-STRUCTURE | 42 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[42].lanes.structure; MDX SHA-256 2e9ee8c422b9; S3 identity PASS | AMBIGUOUS |
| AP-0043-TEXT | 43 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[43].lanes.text; MDX SHA-256 e4bd8a337c35; S3 identity PASS | AMBIGUOUS |
| AP-0043-STRUCTURE | 43 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[43].lanes.structure; MDX SHA-256 e4bd8a337c35; S3 identity PASS | AMBIGUOUS |
| AP-0043-LINKS | 43 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[43].lanes.links; MDX SHA-256 e4bd8a337c35; S3 identity PASS | AMBIGUOUS |
| AP-0047-LINKS | 47 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[47].lanes.links; MDX SHA-256 c7e751479474; S3 identity PASS | AMBIGUOUS |
| AP-0051-TEXT | 51 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[51].lanes.text; MDX SHA-256 4adbfa01e039; S3 identity PASS | AMBIGUOUS |
| AP-0051-STRUCTURE | 51 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[51].lanes.structure; MDX SHA-256 4adbfa01e039; S3 identity PASS | AMBIGUOUS |
| AP-0054-STRUCTURE | 54 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[54].lanes.structure; MDX SHA-256 6b6f87bbf5d4; S3 identity PASS | AMBIGUOUS |
| AP-0055-STRUCTURE | 55 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[55].lanes.structure; MDX SHA-256 dc3324015098; S3 identity PASS | AMBIGUOUS |
| AP-0058-STRUCTURE | 58 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[58].lanes.structure; MDX SHA-256 8dbda90ef55e; S3 identity PASS | AMBIGUOUS |
| AP-0065-STRUCTURE | 65 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[65].lanes.structure; MDX SHA-256 0febf0e66d1f; S3 identity PASS | AMBIGUOUS |
| AP-0067-TEXT | 67 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[67].lanes.text; MDX SHA-256 8220a5e41207; S3 identity PASS | AMBIGUOUS |
| AP-0067-STRUCTURE | 67 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[67].lanes.structure; MDX SHA-256 8220a5e41207; S3 identity PASS | AMBIGUOUS |
| AP-0067-LINKS | 67 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[67].lanes.links; MDX SHA-256 8220a5e41207; S3 identity PASS | AMBIGUOUS |
| AP-0075-LINKS | 75 | P1 | links | Confirmed migration link defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[75].lanes.links; MDX SHA-256 f214ce6de647; S3 identity PASS | OPEN |
| AP-0075-MEDIA | 75 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[75].lanes.media; MDX SHA-256 f214ce6de647; S3 identity PASS | OPEN |
| AP-0077-MEDIA | 77 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[77].lanes.media; MDX SHA-256 4d4bcb84b55f; S3 identity PASS | OPEN |
| AP-0078-TEXT | 78 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[78].lanes.text; MDX SHA-256 b0a78b77957f; S3 identity PASS | AMBIGUOUS |
| AP-0078-STRUCTURE | 78 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[78].lanes.structure; MDX SHA-256 b0a78b77957f; S3 identity PASS | AMBIGUOUS |
| AP-0078-LINKS | 78 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[78].lanes.links; MDX SHA-256 b0a78b77957f; S3 identity PASS | AMBIGUOUS |
| AP-0078-MEDIA | 78 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX=' | audit-results.json posts[78].lanes.media; MDX SHA-256 b0a78b77957f; S3 identity PASS | OPEN |
| AP-0080-MEDIA | 80 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[80].lanes.media; MDX SHA-256 c671d88e35a8; S3 identity PASS | OPEN |
| AP-0081-TEXT | 81 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[81].lanes.text; MDX SHA-256 b8adb68cdd2f; S3 identity PASS | AMBIGUOUS |
| AP-0081-STRUCTURE | 81 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[81].lanes.structure; MDX SHA-256 b8adb68cdd2f; S3 identity PASS | AMBIGUOUS |
| AP-0081-MEDIA | 81 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[81].lanes.media; MDX SHA-256 b8adb68cdd2f; S3 identity PASS | OPEN |
| AP-0082-MEDIA | 82 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[82].lanes.media; MDX SHA-256 770f493645b0; S3 identity PASS | OPEN |
| AP-0087-LINKS | 87 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[87].lanes.links; MDX SHA-256 178bb00100af; S3 identity PASS | AMBIGUOUS |
| AP-0091-LINKS | 91 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[91].lanes.links; MDX SHA-256 ddd0b503987d; S3 identity PASS | AMBIGUOUS |
| AP-0092-STRUCTURE | 92 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[92].lanes.structure; MDX SHA-256 6f2dc494b3de; S3 identity PASS | AMBIGUOUS |
| AP-0095-TEXT | 95 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[95].lanes.text; MDX SHA-256 c1765420794c; S3 identity PASS | AMBIGUOUS |
| AP-0095-STRUCTURE | 95 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[95].lanes.structure; MDX SHA-256 c1765420794c; S3 identity PASS | AMBIGUOUS |
| AP-0096-MEDIA | 96 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[96].lanes.media; MDX SHA-256 2431bc194953; S3 identity PASS | OPEN |
| AP-0097-MEDIA | 97 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[97].lanes.media; MDX SHA-256 f489893f50e4; S3 identity PASS | OPEN |
| AP-0099-LINKS | 99 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[99].lanes.links; MDX SHA-256 de312e078124; S3 identity PASS | AMBIGUOUS |
| AP-0099-MEDIA | 99 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[99].lanes.media; MDX SHA-256 de312e078124; S3 identity PASS | OPEN |
| AP-0101-HASHTAGS | 101 | P1 | hashtags | Confirmed migration hashtag defect: Substack and archive agree but MDX differs. | source=["#1","#inboxzero","#zeroinbox","#email","#emailcleaner","#emailorganizer"]; archive=["#1","#inboxzero","#zeroinbox","#email","#emailcleaner","#emailorganizer"]; MDX=["#inboxzero","#zeroinbox","#email","#emailcleaner","#emailorganizer"] | audit-results.json posts[101].lanes.hashtags; MDX SHA-256 0dcac501ef5b; S3 identity PASS | OPEN |
| AP-0101-MEDIA | 101 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[101].lanes.media; MDX SHA-256 0dcac501ef5b; S3 identity PASS | OPEN |
| AP-0102-MEDIA | 102 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[102].lanes.media; MDX SHA-256 4c8bef759306; S3 identity PASS | OPEN |
| AP-0103-MEDIA | 103 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[103].lanes.media; MDX SHA-256 adc69c768d71; S3 identity PASS | OPEN |
| AP-0104-MEDIA | 104 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[104].lanes.media; MDX SHA-256 4e2649d1ce0f; S3 identity PASS | OPEN |
| AP-0104-LIVE-RENDER | 104 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[104].lanes.live_render; MDX SHA-256 4e2649d1ce0f; S3 identity PASS | OPEN |
| AP-0110-TEXT | 110 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[110].lanes.text; MDX SHA-256 e0f2d18f4f6a; S3 identity PASS | AMBIGUOUS |
| AP-0110-STRUCTURE | 110 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[110].lanes.structure; MDX SHA-256 e0f2d18f4f6a; S3 identity PASS | AMBIGUOUS |
| AP-0111-MEDIA | 111 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[111].lanes.media; MDX SHA-256 1a6aea51cf7c; S3 identity PASS | OPEN |
| AP-0114-MEDIA | 114 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[114].lanes.media; MDX SHA-256 433977f1925f; S3 identity PASS | OPEN |
| AP-0116-MEDIA | 116 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[116].lanes.media; MDX SHA-256 07722ff14556; S3 identity PASS | OPEN |
| AP-0121-MEDIA | 121 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[121].lanes.media; MDX SHA-256 006b1a670125; S3 identity PASS | OPEN |
| AP-0124-MEDIA | 124 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[124].lanes.media; MDX SHA-256 dbd89ba95083; S3 identity PASS | OPEN |
| AP-0127-LINKS | 127 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[127].lanes.links; MDX SHA-256 e21dcfe3b878; S3 identity PASS | AMBIGUOUS |
| AP-0133-MEDIA | 133 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[133].lanes.media; MDX SHA-256 bc021c5af6d8; S3 identity PASS | OPEN |
| AP-0134-LINKS | 134 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[134].lanes.links; MDX SHA-256 c381f66366f7; S3 identity PASS | AMBIGUOUS |
| AP-0140-MEDIA | 140 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[140].lanes.media; MDX SHA-256 620317adb975; S3 identity PASS | OPEN |
| AP-0141-MEDIA | 141 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[141].lanes.media; MDX SHA-256 73569ee9affd; S3 identity PASS | OPEN |
| AP-0142-LINKS | 142 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[142].lanes.links; MDX SHA-256 9c4ebed464f3; S3 identity PASS | AMBIGUOUS |
| AP-0152-TEXT | 152 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[152].lanes.text; MDX SHA-256 36e19eae825a; S3 identity PASS | AMBIGUOUS |
| AP-0152-STRUCTURE | 152 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[152].lanes.structure; MDX SHA-256 36e19eae825a; S3 identity PASS | AMBIGUOUS |
| AP-0153-TEXT | 153 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[153].lanes.text; MDX SHA-256 7e73718c1dd2; S3 identity PASS | AMBIGUOUS |
| AP-0153-STRUCTURE | 153 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[153].lanes.structure; MDX SHA-256 7e73718c1dd2; S3 identity PASS | AMBIGUOUS |
| AP-0153-MEDIA | 153 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[153].lanes.media; MDX SHA-256 7e73718c1dd2; S3 identity PASS | OPEN |
| AP-0155-TEXT | 155 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[155].lanes.text; MDX SHA-256 2412bd76ed44; S3 identity PASS | AMBIGUOUS |
| AP-0155-STRUCTURE | 155 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[155].lanes.structure; MDX SHA-256 2412bd76ed44; S3 identity PASS | AMBIGUOUS |
| AP-0160-MEDIA | 160 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 1 native width differs from ledger; image 1 native height differs from ledger | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 1 native width differs from ledger; image 1 native height differs from ledger | audit-results.json posts[160].lanes.media; MDX SHA-256 dd374e69561c; S3 identity PASS | OPEN |
| AP-0162-TEXT | 162 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[162].lanes.text; MDX SHA-256 bb3ce3ea838e; S3 identity PASS | AMBIGUOUS |
| AP-0162-STRUCTURE | 162 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[162].lanes.structure; MDX SHA-256 bb3ce3ea838e; S3 identity PASS | AMBIGUOUS |
| AP-0165-TEXT | 165 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[165].lanes.text; MDX SHA-256 47b41f458588; S3 identity PASS | AMBIGUOUS |
| AP-0165-STRUCTURE | 165 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[165].lanes.structure; MDX SHA-256 47b41f458588; S3 identity PASS | AMBIGUOUS |
| AP-0166-TEXT | 166 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[166].lanes.text; MDX SHA-256 6ca7e15c8ed9; S3 identity PASS | AMBIGUOUS |
| AP-0166-STRUCTURE | 166 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[166].lanes.structure; MDX SHA-256 6ca7e15c8ed9; S3 identity PASS | AMBIGUOUS |
| AP-0167-MEDIA | 167 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[167].lanes.media; MDX SHA-256 755adb15938a; S3 identity PASS | OPEN |
| AP-0168-STRUCTURE | 168 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[168].lanes.structure; MDX SHA-256 a19295179261; S3 identity PASS | AMBIGUOUS |
| AP-0170-TEXT | 170 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[170].lanes.text; MDX SHA-256 bd5e6ffdc4f5; S3 identity PASS | AMBIGUOUS |
| AP-0170-STRUCTURE | 170 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[170].lanes.structure; MDX SHA-256 bd5e6ffdc4f5; S3 identity PASS | AMBIGUOUS |
| AP-0171-STRUCTURE | 171 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[171].lanes.structure; MDX SHA-256 3f8005062e00; S3 identity PASS | AMBIGUOUS |
| AP-0173-STRUCTURE | 173 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[173].lanes.structure; MDX SHA-256 aeadfe049e35; S3 identity PASS | AMBIGUOUS |
| AP-0175-TEXT | 175 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[175].lanes.text; MDX SHA-256 264c4bf384a4; S3 identity PASS | AMBIGUOUS |
| AP-0175-STRUCTURE | 175 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[175].lanes.structure; MDX SHA-256 264c4bf384a4; S3 identity PASS | AMBIGUOUS |
| AP-0175-HASHTAGS | 175 | P1 | hashtags | Confirmed migration hashtag defect: Substack and archive agree but MDX differs. | source=["#1"]; archive=["#1"]; MDX=[] | audit-results.json posts[175].lanes.hashtags; MDX SHA-256 264c4bf384a4; S3 identity PASS | OPEN |
| AP-0175-LIVE-RENDER | 175 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[175].lanes.live_render; MDX SHA-256 264c4bf384a4; S3 identity PASS | OPEN |
| AP-0176-TEXT | 176 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[176].lanes.text; MDX SHA-256 4591132edbce; S3 identity PASS | AMBIGUOUS |
| AP-0176-STRUCTURE | 176 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[176].lanes.structure; MDX SHA-256 4591132edbce; S3 identity PASS | AMBIGUOUS |
| AP-0181-STRUCTURE | 181 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[181].lanes.structure; MDX SHA-256 2d19bfe631c7; S3 identity PASS | AMBIGUOUS |
| AP-0186-TEXT | 186 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[186].lanes.text; MDX SHA-256 e32ad75848a1; S3 identity PASS | AMBIGUOUS |
| AP-0186-STRUCTURE | 186 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[186].lanes.structure; MDX SHA-256 e32ad75848a1; S3 identity PASS | AMBIGUOUS |
| AP-0189-TEXT | 189 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[189].lanes.text; MDX SHA-256 72384fba75b7; S3 identity PASS | AMBIGUOUS |
| AP-0189-STRUCTURE | 189 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[189].lanes.structure; MDX SHA-256 72384fba75b7; S3 identity PASS | AMBIGUOUS |
| AP-0192-STRUCTURE | 192 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[192].lanes.structure; MDX SHA-256 171eb8ef0350; S3 identity PASS | AMBIGUOUS |
| AP-0192-LINKS | 192 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[192].lanes.links; MDX SHA-256 171eb8ef0350; S3 identity PASS | AMBIGUOUS |
| AP-0194-TEXT | 194 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[194].lanes.text; MDX SHA-256 4b907abc87ed; S3 identity PASS | AMBIGUOUS |
| AP-0194-STRUCTURE | 194 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[194].lanes.structure; MDX SHA-256 4b907abc87ed; S3 identity PASS | AMBIGUOUS |
| AP-0195-TEXT | 195 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[195].lanes.text; MDX SHA-256 779500c8fd3b; S3 identity PASS | AMBIGUOUS |
| AP-0195-STRUCTURE | 195 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[195].lanes.structure; MDX SHA-256 779500c8fd3b; S3 identity PASS | AMBIGUOUS |
| AP-0196-STRUCTURE | 196 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[196].lanes.structure; MDX SHA-256 417847891989; S3 identity PASS | AMBIGUOUS |
| AP-0208-STRUCTURE | 208 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[208].lanes.structure; MDX SHA-256 b2ac1c1db3a7; S3 identity PASS | AMBIGUOUS |
| AP-0210-TEXT | 210 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[210].lanes.text; MDX SHA-256 67f15643eae5; S3 identity PASS | AMBIGUOUS |
| AP-0210-STRUCTURE | 210 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[210].lanes.structure; MDX SHA-256 67f15643eae5; S3 identity PASS | AMBIGUOUS |
| AP-0213-TEXT | 213 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[213].lanes.text; MDX SHA-256 7a809d123657; S3 identity PASS | AMBIGUOUS |
| AP-0213-STRUCTURE | 213 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[213].lanes.structure; MDX SHA-256 7a809d123657; S3 identity PASS | AMBIGUOUS |
| AP-0215-TEXT | 215 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[215].lanes.text; MDX SHA-256 1367d16170da; S3 identity PASS | OPEN |
| AP-0215-STRUCTURE | 215 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[215].lanes.structure; MDX SHA-256 1367d16170da; S3 identity PASS | AMBIGUOUS |
| AP-0216-TEXT | 216 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[216].lanes.text; MDX SHA-256 fc57a6c2efec; S3 identity PASS | OPEN |
| AP-0216-STRUCTURE | 216 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[216].lanes.structure; MDX SHA-256 fc57a6c2efec; S3 identity PASS | OPEN |
| AP-0219-TEXT | 219 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[219].lanes.text; MDX SHA-256 48e2f5f3a0b3; S3 identity PASS | AMBIGUOUS |
| AP-0219-STRUCTURE | 219 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[219].lanes.structure; MDX SHA-256 48e2f5f3a0b3; S3 identity PASS | AMBIGUOUS |
| AP-0221-STRUCTURE | 221 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[221].lanes.structure; MDX SHA-256 b7c9c939b804; S3 identity PASS | AMBIGUOUS |
| AP-0224-TEXT | 224 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[224].lanes.text; MDX SHA-256 2a4ff2ae90f8; S3 identity PASS | AMBIGUOUS |
| AP-0224-STRUCTURE | 224 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[224].lanes.structure; MDX SHA-256 2a4ff2ae90f8; S3 identity PASS | AMBIGUOUS |
| AP-0226-MEDIA | 226 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[226].lanes.media; MDX SHA-256 de982a73d0f1; S3 identity PASS | OPEN |
| AP-0232-STRUCTURE | 232 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[232].lanes.structure; MDX SHA-256 9e16d1d47a78; S3 identity PASS | AMBIGUOUS |
| AP-0232-MEDIA | 232 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[232].lanes.media; MDX SHA-256 9e16d1d47a78; S3 identity PASS | OPEN |
| AP-0233-MEDIA | 233 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[233].lanes.media; MDX SHA-256 3e46be6cac3d; S3 identity PASS | OPEN |
| AP-0236-STRUCTURE | 236 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[236].lanes.structure; MDX SHA-256 b2df9ae03df8; S3 identity PASS | AMBIGUOUS |
| AP-0236-MEDIA | 236 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[236].lanes.media; MDX SHA-256 b2df9ae03df8; S3 identity PASS | OPEN |
| AP-0238-MEDIA | 238 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[238].lanes.media; MDX SHA-256 f5513a991fc4; S3 identity PASS | OPEN |
| AP-0239-TEXT | 239 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[239].lanes.text; MDX SHA-256 7d4ec545d64e; S3 identity PASS | AMBIGUOUS |
| AP-0239-STRUCTURE | 239 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[239].lanes.structure; MDX SHA-256 7d4ec545d64e; S3 identity PASS | AMBIGUOUS |
| AP-0241-STRUCTURE | 241 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[241].lanes.structure; MDX SHA-256 659275aa32f2; S3 identity PASS | AMBIGUOUS |
| AP-0242-TEXT | 242 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[242].lanes.text; MDX SHA-256 c190c533ff7a; S3 identity PASS | AMBIGUOUS |
| AP-0242-STRUCTURE | 242 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[242].lanes.structure; MDX SHA-256 c190c533ff7a; S3 identity PASS | AMBIGUOUS |
| AP-0242-MEDIA | 242 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX=' | audit-results.json posts[242].lanes.media; MDX SHA-256 c190c533ff7a; S3 identity PASS | OPEN |
| AP-0244-LINKS | 244 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[244].lanes.links; MDX SHA-256 14a4a795c012; S3 identity PASS | AMBIGUOUS |
| AP-0244-HASHTAGS | 244 | P1 | hashtags | Confirmed migration hashtag defect: Substack and archive agree but MDX differs. | source=[]; archive=[]; MDX=["#inboxzero","#zeroinbox","#ai","#workflows","#automations"] | audit-results.json posts[244].lanes.hashtags; MDX SHA-256 14a4a795c012; S3 identity PASS | OPEN |
| AP-0245-MEDIA | 245 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[245].lanes.media; MDX SHA-256 ca32ae7c0b6f; S3 identity PASS | OPEN |
| AP-0246-STRUCTURE | 246 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[246].lanes.structure; MDX SHA-256 ccb0a8688e57; S3 identity PASS | AMBIGUOUS |
| AP-0246-MEDIA | 246 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[246].lanes.media; MDX SHA-256 ccb0a8688e57; S3 identity PASS | OPEN |
| AP-0247-MEDIA | 247 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[247].lanes.media; MDX SHA-256 d5675ef2b87c; S3 identity PASS | OPEN |
| AP-0247-LIVE-RENDER | 247 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[247].lanes.live_render; MDX SHA-256 d5675ef2b87c; S3 identity PASS | OPEN |
| AP-0248-MEDIA | 248 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX='caption the image'; image 4 archive caption differs from MDX: archive=None MDX='caption the image'; image 5 archive caption differs from MDX: archive=None MDX='caption the image'; image 6 archive caption differs from MDX: archive=None MDX='caption the image'; image 7 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX=' | audit-results.json posts[248].lanes.media; MDX SHA-256 1d2cc1d4e6cd; S3 identity PASS | OPEN |
| AP-0249-MEDIA | 249 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[249].lanes.media; MDX SHA-256 b73a43e9e8e1; S3 identity PASS | OPEN |
| AP-0251-MEDIA | 251 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[251].lanes.media; MDX SHA-256 6bfae2aace75; S3 identity PASS | OPEN |
| AP-0254-STRUCTURE | 254 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[254].lanes.structure; MDX SHA-256 7247f4468d5a; S3 identity PASS | AMBIGUOUS |
| AP-0266-TEXT | 266 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[266].lanes.text; MDX SHA-256 d6f41745cfd5; S3 identity PASS | AMBIGUOUS |
| AP-0266-STRUCTURE | 266 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[266].lanes.structure; MDX SHA-256 d6f41745cfd5; S3 identity PASS | AMBIGUOUS |
| AP-0268-STRUCTURE | 268 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[268].lanes.structure; MDX SHA-256 21ee0931c1cf; S3 identity PASS | AMBIGUOUS |
| AP-0268-MEDIA | 268 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[268].lanes.media; MDX SHA-256 21ee0931c1cf; S3 identity PASS | OPEN |
| AP-0270-TEXT | 270 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[270].lanes.text; MDX SHA-256 93e09458d359; S3 identity PASS | AMBIGUOUS |
| AP-0270-STRUCTURE | 270 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[270].lanes.structure; MDX SHA-256 93e09458d359; S3 identity PASS | AMBIGUOUS |
| AP-0271-STRUCTURE | 271 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[271].lanes.structure; MDX SHA-256 e4f5bc1bd188; S3 identity PASS | AMBIGUOUS |
| AP-0272-STRUCTURE | 272 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[272].lanes.structure; MDX SHA-256 fe08f6532d8a; S3 identity PASS | AMBIGUOUS |
| AP-0276-TEXT | 276 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[276].lanes.text; MDX SHA-256 425b4457609b; S3 identity PASS | AMBIGUOUS |
| AP-0276-STRUCTURE | 276 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[276].lanes.structure; MDX SHA-256 425b4457609b; S3 identity PASS | AMBIGUOUS |
| AP-0277-TEXT | 277 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[277].lanes.text; MDX SHA-256 7e0c56b5067d; S3 identity PASS | AMBIGUOUS |
| AP-0277-STRUCTURE | 277 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[277].lanes.structure; MDX SHA-256 7e0c56b5067d; S3 identity PASS | AMBIGUOUS |
| AP-0279-MEDIA | 279 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[279].lanes.media; MDX SHA-256 9844ac421cc8; S3 identity PASS | OPEN |
| AP-0282-MEDIA | 282 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[282].lanes.media; MDX SHA-256 9adb1994e77f; S3 identity PASS | OPEN |
| AP-0283-STRUCTURE | 283 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[283].lanes.structure; MDX SHA-256 da3eee3a83e2; S3 identity PASS | AMBIGUOUS |
| AP-0284-TEXT | 284 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[284].lanes.text; MDX SHA-256 52913778c899; S3 identity PASS | AMBIGUOUS |
| AP-0284-STRUCTURE | 284 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[284].lanes.structure; MDX SHA-256 52913778c899; S3 identity PASS | AMBIGUOUS |
| AP-0286-TEXT | 286 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[286].lanes.text; MDX SHA-256 3c6f6683d9b5; S3 identity PASS | AMBIGUOUS |
| AP-0286-STRUCTURE | 286 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[286].lanes.structure; MDX SHA-256 3c6f6683d9b5; S3 identity PASS | AMBIGUOUS |
| AP-0286-MEDIA | 286 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[286].lanes.media; MDX SHA-256 3c6f6683d9b5; S3 identity PASS | OPEN |
| AP-0287-STRUCTURE | 287 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[287].lanes.structure; MDX SHA-256 76ca22099e76; S3 identity PASS | AMBIGUOUS |
| AP-0287-MEDIA | 287 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[287].lanes.media; MDX SHA-256 76ca22099e76; S3 identity PASS | OPEN |
| AP-0288-TEXT | 288 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[288].lanes.text; MDX SHA-256 336d38530fc7; S3 identity PASS | AMBIGUOUS |
| AP-0288-STRUCTURE | 288 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[288].lanes.structure; MDX SHA-256 336d38530fc7; S3 identity PASS | AMBIGUOUS |
| AP-0293-STRUCTURE | 293 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[293].lanes.structure; MDX SHA-256 f01a0e08a7c4; S3 identity PASS | AMBIGUOUS |
| AP-0293-LINKS | 293 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[293].lanes.links; MDX SHA-256 f01a0e08a7c4; S3 identity PASS | AMBIGUOUS |
| AP-0295-TEXT | 295 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[295].lanes.text; MDX SHA-256 287ea23a062f; S3 identity PASS | AMBIGUOUS |
| AP-0295-STRUCTURE | 295 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[295].lanes.structure; MDX SHA-256 287ea23a062f; S3 identity PASS | AMBIGUOUS |
| AP-0295-HASHTAGS | 295 | P1 | hashtags | Confirmed migration hashtag defect: Substack and archive agree but MDX differs. | source=["#property"]; archive=["#property"]; MDX=[] | audit-results.json posts[295].lanes.hashtags; MDX SHA-256 287ea23a062f; S3 identity PASS | OPEN |
| AP-0295-LIVE-RENDER | 295 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[295].lanes.live_render; MDX SHA-256 287ea23a062f; S3 identity PASS | OPEN |
| AP-0296-TEXT | 296 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[296].lanes.text; MDX SHA-256 32e3518a86f1; S3 identity PASS | AMBIGUOUS |
| AP-0296-STRUCTURE | 296 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[296].lanes.structure; MDX SHA-256 32e3518a86f1; S3 identity PASS | AMBIGUOUS |
| AP-0297-TEXT | 297 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[297].lanes.text; MDX SHA-256 5564ac36090d; S3 identity PASS | AMBIGUOUS |
| AP-0297-STRUCTURE | 297 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[297].lanes.structure; MDX SHA-256 5564ac36090d; S3 identity PASS | AMBIGUOUS |
| AP-0297-MEDIA | 297 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[297].lanes.media; MDX SHA-256 5564ac36090d; S3 identity PASS | OPEN |
| AP-0298-MEDIA | 298 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[298].lanes.media; MDX SHA-256 b30dce1d131b; S3 identity PASS | OPEN |
| AP-0300-TEXT | 300 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[300].lanes.text; MDX SHA-256 52a625b5aa3b; S3 identity PASS | AMBIGUOUS |
| AP-0300-STRUCTURE | 300 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[300].lanes.structure; MDX SHA-256 52a625b5aa3b; S3 identity PASS | AMBIGUOUS |
| AP-0300-MEDIA | 300 | P1 | media | image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[300].lanes.media; MDX SHA-256 52a625b5aa3b; S3 identity PASS | OPEN |
| AP-0302-STRUCTURE | 302 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[302].lanes.structure; MDX SHA-256 8367a10fd5f4; S3 identity PASS | AMBIGUOUS |
| AP-0304-TEXT | 304 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[304].lanes.text; MDX SHA-256 0cf62d1734d9; S3 identity PASS | AMBIGUOUS |
| AP-0304-STRUCTURE | 304 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[304].lanes.structure; MDX SHA-256 0cf62d1734d9; S3 identity PASS | AMBIGUOUS |
| AP-0304-LINKS | 304 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[304].lanes.links; MDX SHA-256 0cf62d1734d9; S3 identity PASS | AMBIGUOUS |
| AP-0306-TEXT | 306 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[306].lanes.text; MDX SHA-256 8d14b73fa806; S3 identity PASS | AMBIGUOUS |
| AP-0306-STRUCTURE | 306 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[306].lanes.structure; MDX SHA-256 8d14b73fa806; S3 identity PASS | AMBIGUOUS |
| AP-0308-TEXT | 308 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[308].lanes.text; MDX SHA-256 380b5d3ed297; S3 identity PASS | AMBIGUOUS |
| AP-0308-STRUCTURE | 308 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[308].lanes.structure; MDX SHA-256 380b5d3ed297; S3 identity PASS | AMBIGUOUS |
| AP-0308-MEDIA | 308 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[308].lanes.media; MDX SHA-256 380b5d3ed297; S3 identity PASS | OPEN |
| AP-0312-TEXT | 312 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[312].lanes.text; MDX SHA-256 2d0893ac89d2; S3 identity PASS | AMBIGUOUS |
| AP-0312-STRUCTURE | 312 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[312].lanes.structure; MDX SHA-256 2d0893ac89d2; S3 identity PASS | AMBIGUOUS |
| AP-0317-TEXT | 317 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[317].lanes.text; MDX SHA-256 a05e9a1a1b2b; S3 identity PASS | AMBIGUOUS |
| AP-0317-STRUCTURE | 317 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[317].lanes.structure; MDX SHA-256 a05e9a1a1b2b; S3 identity PASS | AMBIGUOUS |
| AP-0320-TEXT | 320 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[320].lanes.text; MDX SHA-256 09945d72ef31; S3 identity PASS | AMBIGUOUS |
| AP-0320-STRUCTURE | 320 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[320].lanes.structure; MDX SHA-256 09945d72ef31; S3 identity PASS | AMBIGUOUS |
| AP-0323-MEDIA | 323 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[323].lanes.media; MDX SHA-256 5ca300ec22c8; S3 identity PASS | OPEN |
| AP-0325-TEXT | 325 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[325].lanes.text; MDX SHA-256 755a348c49fb; S3 identity PASS | AMBIGUOUS |
| AP-0325-STRUCTURE | 325 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[325].lanes.structure; MDX SHA-256 755a348c49fb; S3 identity PASS | AMBIGUOUS |
| AP-0326-STRUCTURE | 326 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[326].lanes.structure; MDX SHA-256 8ffa1da3db21; S3 identity PASS | AMBIGUOUS |
| AP-0326-LINKS | 326 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[326].lanes.links; MDX SHA-256 8ffa1da3db21; S3 identity PASS | AMBIGUOUS |
| AP-0327-TEXT | 327 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[327].lanes.text; MDX SHA-256 5dde411db016; S3 identity PASS | AMBIGUOUS |
| AP-0327-STRUCTURE | 327 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[327].lanes.structure; MDX SHA-256 5dde411db016; S3 identity PASS | AMBIGUOUS |
| AP-0329-MEDIA | 329 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX=' | audit-results.json posts[329].lanes.media; MDX SHA-256 73543b28353f; S3 identity PASS | OPEN |
| AP-0330-MEDIA | 330 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image'; image 3 archive caption differs from MDX: archive=None MDX=' | audit-results.json posts[330].lanes.media; MDX SHA-256 5c3aaa4a5057; S3 identity PASS | OPEN |
| AP-0336-MEDIA | 336 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[336].lanes.media; MDX SHA-256 1d0b1351984e; S3 identity PASS | OPEN |
| AP-0338-MEDIA | 338 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[338].lanes.media; MDX SHA-256 fb613aba6104; S3 identity PASS | OPEN |
| AP-0339-LINKS | 339 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[339].lanes.links; MDX SHA-256 90c27fe17b09; S3 identity PASS | AMBIGUOUS |
| AP-0339-MEDIA | 339 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[339].lanes.media; MDX SHA-256 90c27fe17b09; S3 identity PASS | OPEN |
| AP-0343-LINKS | 343 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[343].lanes.links; MDX SHA-256 f560ae6e0b19; S3 identity PASS | AMBIGUOUS |
| AP-0343-MEDIA | 343 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[343].lanes.media; MDX SHA-256 f560ae6e0b19; S3 identity PASS | OPEN |
| AP-0343-LIVE-RENDER | 343 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[343].lanes.live_render; MDX SHA-256 f560ae6e0b19; S3 identity PASS | OPEN |
| AP-0344-TEXT | 344 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[344].lanes.text; MDX SHA-256 e56348ea3364; S3 identity PASS | OPEN |
| AP-0344-STRUCTURE | 344 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[344].lanes.structure; MDX SHA-256 e56348ea3364; S3 identity PASS | OPEN |
| AP-0344-MEDIA | 344 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image'; image 2 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[344].lanes.media; MDX SHA-256 e56348ea3364; S3 identity PASS | OPEN |
| AP-0346-LIVE-RENDER | 346 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[346].lanes.live_render; MDX SHA-256 1280b7e12e54; S3 identity PASS | OPEN |
| AP-0350-TEXT | 350 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[350].lanes.text; MDX SHA-256 97e55a6bf6ec; S3 identity PASS | AMBIGUOUS |
| AP-0350-STRUCTURE | 350 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[350].lanes.structure; MDX SHA-256 97e55a6bf6ec; S3 identity PASS | AMBIGUOUS |
| AP-0353-TEXT | 353 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[353].lanes.text; MDX SHA-256 bd64e8498deb; S3 identity PASS | AMBIGUOUS |
| AP-0353-STRUCTURE | 353 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[353].lanes.structure; MDX SHA-256 bd64e8498deb; S3 identity PASS | AMBIGUOUS |
| AP-0355-TEXT | 355 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[355].lanes.text; MDX SHA-256 8d560f076e16; S3 identity PASS | AMBIGUOUS |
| AP-0355-STRUCTURE | 355 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[355].lanes.structure; MDX SHA-256 8d560f076e16; S3 identity PASS | AMBIGUOUS |
| AP-0357-TEXT | 357 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[357].lanes.text; MDX SHA-256 a9fd64aa27e7; S3 identity PASS | OPEN |
| AP-0357-STRUCTURE | 357 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[357].lanes.structure; MDX SHA-256 a9fd64aa27e7; S3 identity PASS | OPEN |
| AP-0357-LIVE-RENDER | 357 | P2 | live_render | page overflows the viewport | page overflows the viewport | audit-results.json posts[357].lanes.live_render; MDX SHA-256 a9fd64aa27e7; S3 identity PASS | OPEN |
| AP-0359-TEXT | 359 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[359].lanes.text; MDX SHA-256 04af84036bdd; S3 identity PASS | OPEN |
| AP-0359-STRUCTURE | 359 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[359].lanes.structure; MDX SHA-256 04af84036bdd; S3 identity PASS | OPEN |
| AP-0361-TEXT | 361 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[361].lanes.text; MDX SHA-256 44dec2b5442a; S3 identity PASS | OPEN |
| AP-0361-STRUCTURE | 361 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[361].lanes.structure; MDX SHA-256 44dec2b5442a; S3 identity PASS | OPEN |
| AP-0361-LINKS | 361 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[361].lanes.links; MDX SHA-256 44dec2b5442a; S3 identity PASS | AMBIGUOUS |
| AP-0362-TEXT | 362 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[362].lanes.text; MDX SHA-256 a4051509d196; S3 identity PASS | OPEN |
| AP-0362-STRUCTURE | 362 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[362].lanes.structure; MDX SHA-256 a4051509d196; S3 identity PASS | OPEN |
| AP-0363-TEXT | 363 | P1 | text | Confirmed migration text defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[363].lanes.text; MDX SHA-256 9cdf09729dda; S3 identity PASS | OPEN |
| AP-0363-STRUCTURE | 363 | P2 | structure | Confirmed migration structure defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[363].lanes.structure; MDX SHA-256 9cdf09729dda; S3 identity PASS | OPEN |
| AP-0363-MEDIA | 363 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[363].lanes.media; MDX SHA-256 9cdf09729dda; S3 identity PASS | OPEN |
| AP-0364-TEXT | 364 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[364].lanes.text; MDX SHA-256 6cee9d6f9983; S3 identity PASS | AMBIGUOUS |
| AP-0364-STRUCTURE | 364 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M false | audit-results.json posts[364].lanes.structure; MDX SHA-256 6cee9d6f9983; S3 identity PASS | AMBIGUOUS |
| AP-0366-TEXT | 366 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[366].lanes.text; MDX SHA-256 565d423ad379; S3 identity PASS | AMBIGUOUS |
| AP-0366-STRUCTURE | 366 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[366].lanes.structure; MDX SHA-256 565d423ad379; S3 identity PASS | AMBIGUOUS |
| AP-0370-TEXT | 370 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[370].lanes.text; MDX SHA-256 97c956a6164a; S3 identity PASS | AMBIGUOUS |
| AP-0370-STRUCTURE | 370 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[370].lanes.structure; MDX SHA-256 97c956a6164a; S3 identity PASS | AMBIGUOUS |
| AP-0371-TEXT | 371 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[371].lanes.text; MDX SHA-256 7c7947070978; S3 identity PASS | AMBIGUOUS |
| AP-0371-STRUCTURE | 371 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[371].lanes.structure; MDX SHA-256 7c7947070978; S3 identity PASS | AMBIGUOUS |
| AP-0374-TEXT | 374 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[374].lanes.text; MDX SHA-256 7f93e59bb110; S3 identity PASS | AMBIGUOUS |
| AP-0374-STRUCTURE | 374 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[374].lanes.structure; MDX SHA-256 7f93e59bb110; S3 identity PASS | AMBIGUOUS |
| AP-0374-LINKS | 374 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[374].lanes.links; MDX SHA-256 7f93e59bb110; S3 identity PASS | AMBIGUOUS |
| AP-0374-MEDIA | 374 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[374].lanes.media; MDX SHA-256 7f93e59bb110; S3 identity PASS | OPEN |
| AP-0377-TEXT | 377 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[377].lanes.text; MDX SHA-256 b7fcb4ce5bb8; S3 identity PASS | AMBIGUOUS |
| AP-0377-STRUCTURE | 377 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[377].lanes.structure; MDX SHA-256 b7fcb4ce5bb8; S3 identity PASS | AMBIGUOUS |
| AP-0377-LINKS | 377 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[377].lanes.links; MDX SHA-256 b7fcb4ce5bb8; S3 identity PASS | AMBIGUOUS |
| AP-0377-MEDIA | 377 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[377].lanes.media; MDX SHA-256 b7fcb4ce5bb8; S3 identity PASS | OPEN |
| AP-0379-TEXT | 379 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[379].lanes.text; MDX SHA-256 db1765cb5db0; S3 identity PASS | AMBIGUOUS |
| AP-0379-STRUCTURE | 379 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[379].lanes.structure; MDX SHA-256 db1765cb5db0; S3 identity PASS | AMBIGUOUS |
| AP-0379-LINKS | 379 | P1 | links | Confirmed migration link defect: Substack and archive agree but MDX differs. | S=A true; A=M false; S=M false | audit-results.json posts[379].lanes.links; MDX SHA-256 db1765cb5db0; S3 identity PASS | OPEN |
| AP-0379-MEDIA | 379 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[379].lanes.media; MDX SHA-256 db1765cb5db0; S3 identity PASS | OPEN |
| AP-0382-TEXT | 382 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[382].lanes.text; MDX SHA-256 1bdc7b1602fd; S3 identity PASS | AMBIGUOUS |
| AP-0382-STRUCTURE | 382 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[382].lanes.structure; MDX SHA-256 1bdc7b1602fd; S3 identity PASS | AMBIGUOUS |
| AP-0382-MEDIA | 382 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[382].lanes.media; MDX SHA-256 1bdc7b1602fd; S3 identity PASS | OPEN |
| AP-0385-MEDIA | 385 | P1 | media | image 1 converted S3 dimensions differ from ledger | image 1 converted S3 dimensions differ from ledger | audit-results.json posts[385].lanes.media; MDX SHA-256 6b9fa7eaae06; S3 identity PASS | OPEN |
| AP-0387-TEXT | 387 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[387].lanes.text; MDX SHA-256 5f20aa8c27bc; S3 identity PASS | AMBIGUOUS |
| AP-0387-STRUCTURE | 387 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[387].lanes.structure; MDX SHA-256 5f20aa8c27bc; S3 identity PASS | AMBIGUOUS |
| AP-0388-TEXT | 388 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[388].lanes.text; MDX SHA-256 77d52c39567c; S3 identity PASS | AMBIGUOUS |
| AP-0388-STRUCTURE | 388 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[388].lanes.structure; MDX SHA-256 77d52c39567c; S3 identity PASS | AMBIGUOUS |
| AP-0388-LINKS | 388 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[388].lanes.links; MDX SHA-256 77d52c39567c; S3 identity PASS | AMBIGUOUS |
| AP-0389-MEDIA | 389 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[389].lanes.media; MDX SHA-256 9cf7cecf2d20; S3 identity PASS | OPEN |
| AP-0390-TEXT | 390 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[390].lanes.text; MDX SHA-256 6108f5e22f10; S3 identity PASS | AMBIGUOUS |
| AP-0390-STRUCTURE | 390 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[390].lanes.structure; MDX SHA-256 6108f5e22f10; S3 identity PASS | AMBIGUOUS |
| AP-0390-LINKS | 390 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[390].lanes.links; MDX SHA-256 6108f5e22f10; S3 identity PASS | AMBIGUOUS |
| AP-0390-MEDIA | 390 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[390].lanes.media; MDX SHA-256 6108f5e22f10; S3 identity PASS | OPEN |
| AP-0392-TEXT | 392 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[392].lanes.text; MDX SHA-256 ac31b15a2748; S3 identity PASS | AMBIGUOUS |
| AP-0392-STRUCTURE | 392 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[392].lanes.structure; MDX SHA-256 ac31b15a2748; S3 identity PASS | AMBIGUOUS |
| AP-0392-LINKS | 392 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[392].lanes.links; MDX SHA-256 ac31b15a2748; S3 identity PASS | AMBIGUOUS |
| AP-0393-TEXT | 393 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[393].lanes.text; MDX SHA-256 a51cfe93e9f3; S3 identity PASS | AMBIGUOUS |
| AP-0393-STRUCTURE | 393 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[393].lanes.structure; MDX SHA-256 a51cfe93e9f3; S3 identity PASS | AMBIGUOUS |
| AP-0393-LINKS | 393 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[393].lanes.links; MDX SHA-256 a51cfe93e9f3; S3 identity PASS | AMBIGUOUS |
| AP-0394-MEDIA | 394 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[394].lanes.media; MDX SHA-256 60198e3664b9; S3 identity PASS | OPEN |
| AP-0395-TEXT | 395 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[395].lanes.text; MDX SHA-256 7c7367acd224; S3 identity PASS | AMBIGUOUS |
| AP-0395-STRUCTURE | 395 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[395].lanes.structure; MDX SHA-256 7c7367acd224; S3 identity PASS | AMBIGUOUS |
| AP-0398-MEDIA | 398 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[398].lanes.media; MDX SHA-256 d78217dad13c; S3 identity PASS | OPEN |
| AP-0399-MEDIA | 399 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[399].lanes.media; MDX SHA-256 0862d2a57350; S3 identity PASS | OPEN |
| AP-0400-TEXT | 400 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[400].lanes.text; MDX SHA-256 56dffd43d484; S3 identity PASS | AMBIGUOUS |
| AP-0400-STRUCTURE | 400 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[400].lanes.structure; MDX SHA-256 56dffd43d484; S3 identity PASS | AMBIGUOUS |
| AP-0400-LINKS | 400 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[400].lanes.links; MDX SHA-256 56dffd43d484; S3 identity PASS | AMBIGUOUS |
| AP-0401-TEXT | 401 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[401].lanes.text; MDX SHA-256 9096cf3f7835; S3 identity PASS | AMBIGUOUS |
| AP-0401-STRUCTURE | 401 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[401].lanes.structure; MDX SHA-256 9096cf3f7835; S3 identity PASS | AMBIGUOUS |
| AP-0402-TEXT | 402 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[402].lanes.text; MDX SHA-256 3e96a5e4b63e; S3 identity PASS | AMBIGUOUS |
| AP-0402-STRUCTURE | 402 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[402].lanes.structure; MDX SHA-256 3e96a5e4b63e; S3 identity PASS | AMBIGUOUS |
| AP-0402-LINKS | 402 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[402].lanes.links; MDX SHA-256 3e96a5e4b63e; S3 identity PASS | AMBIGUOUS |
| AP-0402-MEDIA | 402 | P1 | media | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | image 1 archive caption differs from MDX: archive=None MDX='caption the image' | audit-results.json posts[402].lanes.media; MDX SHA-256 3e96a5e4b63e; S3 identity PASS | OPEN |
| AP-0403-TEXT | 403 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[403].lanes.text; MDX SHA-256 c24dc9687556; S3 identity PASS | AMBIGUOUS |
| AP-0403-STRUCTURE | 403 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[403].lanes.structure; MDX SHA-256 c24dc9687556; S3 identity PASS | AMBIGUOUS |
| AP-0403-LINKS | 403 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[403].lanes.links; MDX SHA-256 c24dc9687556; S3 identity PASS | AMBIGUOUS |
| AP-0405-TEXT | 405 | P1 | text | Substack, archive, and MDX text do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[405].lanes.text; MDX SHA-256 c1c3b69f9fba; S3 identity PASS | AMBIGUOUS |
| AP-0405-STRUCTURE | 405 | P2 | structure | Substack, archive, and MDX structure do not establish one unambiguous direction of truth. | S=A false; A=M true; S=M false | audit-results.json posts[405].lanes.structure; MDX SHA-256 c1c3b69f9fba; S3 identity PASS | AMBIGUOUS |
| AP-0407-LINKS | 407 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[407].lanes.links; MDX SHA-256 3886e19ea5f6; S3 identity PASS | AMBIGUOUS |
| AP-0408-LINKS | 408 | P1 | links | Substack, archive, and MDX links do not establish one unambiguous direction of truth. | S=A false; A=M false; S=M true | audit-results.json posts[408].lanes.links; MDX SHA-256 caf20b604169; S3 identity PASS | AMBIGUOUS |

## Range Completion Summary

| Posts | Audited | Pass | Fail | Review | Blocked | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1-20 | 20/20 | 10 | 5 | 5 | 0 | complete |
| 21-40 | 20/20 | 15 | 1 | 4 | 0 | complete |
| 41-60 | 20/20 | 12 | 0 | 8 | 0 | complete |
| 61-80 | 20/20 | 14 | 4 | 2 | 0 | complete |
| 81-100 | 20/20 | 11 | 5 | 4 | 0 | complete |
| 101-120 | 20/20 | 12 | 7 | 1 | 0 | complete |
| 121-140 | 20/20 | 14 | 4 | 2 | 0 | complete |
| 141-160 | 20/20 | 14 | 3 | 3 | 0 | complete |
| 161-180 | 20/20 | 10 | 2 | 8 | 0 | complete |
| 181-200 | 20/20 | 13 | 0 | 7 | 0 | complete |
| 201-220 | 20/20 | 14 | 2 | 4 | 0 | complete |
| 221-240 | 20/20 | 12 | 5 | 3 | 0 | complete |
| 241-260 | 20/20 | 10 | 8 | 2 | 0 | complete |
| 261-280 | 20/20 | 12 | 2 | 6 | 0 | complete |
| 281-300 | 20/20 | 8 | 7 | 5 | 0 | complete |
| 301-320 | 20/20 | 13 | 1 | 6 | 0 | complete |
| 321-340 | 20/20 | 11 | 6 | 3 | 0 | complete |
| 341-360 | 20/20 | 12 | 5 | 3 | 0 | complete |
| 361-380 | 20/20 | 10 | 6 | 4 | 0 | complete |
| 381-400 | 20/20 | 7 | 7 | 6 | 0 | complete |
| 401-408 | 8/8 | 2 | 1 | 5 | 0 | complete |

## Final Audit Summary

The discovery audit completed on 2026-08-14 without changing any post or S3
object. All 408 durable results are in `substack/audit-results.json`.

| Result | Posts |
| --- | ---: |
| PASS | 236 |
| FAIL | 81 |
| REVIEW | 91 |
| BLOCKED | 0 |

| Lane | Pass | Fail | Review | Blocked |
| --- | ---: | ---: | ---: | ---: |
| Inventory | 408 | 0 | 0 | 0 |
| Local/S3 MDX identity | 408 | 0 | 0 | 0 |
| Metadata | 408 | 0 | 0 | 0 |
| Text | 321 | 9 | 78 | 0 |
| Structure | 294 | 8 | 106 | 0 |
| Links | 372 | 2 | 34 | 0 |
| Literal hashtags | 403 | 5 | 0 | 0 |
| Media | 338 | 70 | 0 | 0 |
| MDX compile/contract | 408 | 0 | 0 | 0 |
| Live render | 401 | 7 | 0 | 0 |

Confirmed source-fidelity findings are 86 open P1s: nine text posts (39,
215, 216, 344, 357, 359, 361, 362, 363), two link posts (75, 379), five
hashtag posts (4, 101, 175, 244, 295), and 70 media posts. The media group
contains 67 posts with archive-to-MDX caption differences and four posts with
source-byte or native-dimension differences (10, 11, 160, 385); those
categories overlap on one post.

There are 15 open P2s: eight confirmed structure findings (39, 216, 344, 357,
359, 361, 362, 363) and seven mobile horizontal-overflow findings (104, 175,
247, 295, 343, 346, 357). There are no P0 or P3 findings.

The 218 ambiguous findings belong to 91 `REVIEW` posts where current Substack,
the archived Markdown, and published MDX do not establish one unambiguous
history. They are not authorized for automatic correction.

The final inventory passed with 408 ledger entries, 408 archive Markdown
files, 408 local live MDX files, 408 exact S3 MDX objects, 408 dashboard MDX
records, and 408 imported dashboard records. Expected, local, and S3 filename
sets all have SHA-256
`920de792c887782e16176a5d1b0446b3e28bc428a520e4cdceec55c72bde045f`.

## Authorized Remediation Log

The summary above is the immutable discovery snapshot. The following changes
were authorized and completed on 2026-08-14 after that read-only audit:

- `AP-0010-MEDIA` is resolved. All four images for `brands-are` were replaced
  at their existing S3 keys with the full direct Substack objects. Their
  current S3 MD5/ETags now match the canonical source bytes. A fresh complete
  post audit passes inventory, S3 identity, metadata, text, structure, links,
  hashtags, media, MDX compile, and live browser rendering.
- `AP-0011-MEDIA` is resolved. Images 3 and 4 for
  `on-fear-and-opportunity` were replaced the same way. A fresh complete post
  audit passes every lane, including live browser rendering.
- The native-dimension portions of `AP-0160-MEDIA` and `AP-0385-MEDIA` were
  false positives caused by EXIF orientation `6`. Their original S3 JPEG
  bytes were already exact Substack matches and were not rewritten. The audit
  helper now records encoded dimensions separately and compares the displayed
  dimensions after orientation; both posts pass the corrected media lane.
- Post 160's invented `caption the image` ledger value was removed. Its local
  MDX caption remediation remains local under the earlier no-MDX-upload scope.
  No MDX post object was uploaded during this image remediation.

All S3 replacements were exact-key, versioned writes under the authorized site
prefix. The six new objects were re-read after upload and verified for byte
length, content type, and MD5/ETag identity.

### Final Finding Closure

The remaining findings were adjudicated and remediated on 2026-08-14:

- All 81 posts that were `FAIL` in the discovery snapshot are resolved. The 78
  local MDX corrections are captured by site commit `812dd49` (`cool fixes`),
  and posts 10, 11, and 385 were completed by the asset/EXIF work above. A
  fresh sequential sweep of all 81 posts passed inventory, metadata, media,
  and MDX compilation. Their local MDX files were also exact S3 matches at the
  time of that sweep.
- All 101 discovery findings marked `OPEN` are closed: nine text, eight
  structure, two link, five hashtag, 70 media, and seven mobile-overflow
  findings. The seven overflow repairs preserve visible URL text while adding
  safe word-break opportunities.
- All 91 `REVIEW` posts and their 218 conservative three-way findings were
  manually adjudicated. Seventy-nine required no change because the local MDX
  was supported exactly by either the migration archive or current Substack;
  these were source-history, archive-extraction, platform-chrome, formatting,
  or malformed-source-link differences rather than missing migrated content.
- Twelve `REVIEW` posts did contain source-supported leftovers and were fixed
  locally: posts 9, 14, 40, 41, 43, 67, 195, 213, 266, 296, 304, and 364. The
  changes restore seven current source-link mappings, ordered-list semantics,
  blockquotes, a code block, source line breaks, and removal of one Substack
  subscription-widget sentence. For every changed lane, the corrected MDX now
  matches the current Substack semantic text, structure, or links exactly, and
  all twelve files compile.
- Post 326 keeps its valid local URL because the current source contains a
  malformed `href` whose value is an entire paragraph. Post 402 keeps its
  archived image because the archive records its position and the stored S3
  object is an exact match to the recorded direct Substack original, even
  though the image is no longer present in the current Substack body.

After separate explicit authorization, all twelve final `REVIEW` corrections
were uploaded from `site/live-posts` to their exact existing S3 writing keys.
Each new version was re-read and verified for byte length and local-MD5/S3-ETag
identity; no other MDX key was changed. The discovery JSON remains unchanged as
the immutable before-state; this section is the durable after-state. The final
collection inventory at `2026-08-14T08:01:02Z` passed with 408 ledger entries,
408 archive files, 408 local MDX files, 408 S3 MDX objects, and identical
expected/local/S3 filename-set hashes.

## Resume Rule

Resume from `Next post`. Before starting it, verify that the preceding post has
one complete JSON result and one matching checkpoint row. Re-fetch every
external input for the new post; never reuse another post's temporary source,
MDX, image, browser page, or event stream.

If the session stops before the JSON result and this file are both updated,
the `Next post` intentionally remains unchanged. On resume, discard incomplete
temporary comparison outputs only after identifying their exact paths, then
restart that post's read-only audit from fresh inputs.

After post 408, rerun the collection-wide inventory preflight, verify all 408
result records and checkpoint rows exist, verify the summary counts add to
408, and produce a remediation report grouped by P0, P1, P2, P3, and ambiguous
source divergence.
