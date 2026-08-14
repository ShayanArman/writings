# Migration Checkpoints

This file is the durable resume point for the sequential Substack-to-MDX
migration. A post is recorded as complete only after its MDX and any original
full-resolution images have been validated, uploaded to their exact Shayan
Arman S3 keys, checksum-verified, reflected in the writings ledgers, and removed
from temporary storage.

## Explanation of what to do for each post migration

Migrate exactly one numbered post at a time. Never begin the next post until
the current post's source copy, metadata, images, MDX, S3 objects, writings
ledgers, temporary-file cleanup, and checkpoint update are all complete. Do not
perform parallel post work.

The publishable MDX must be created only in `/private/tmp/shayan-post-<number>/`.
Do not add it to the Shayan Arman site's `site/live-posts/` directory. Upload
the finished MDX directly to:

```text
s3://seo-gangster/sites/shayan-arman-blog/posts/writings/
```

Upload images only below the post-specific prefix:

```text
s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/<slug>/
```

Never write outside `sites/shayan-arman-blog/` in S3. Never run `yarn build`
or `yarn dev`.

## Migration Complete Through Post 401

Shayan has explicitly authorized direct publication of every remaining post in
the active batch through post 401, to the authorized Shayan Arman S3
prefix. Do not request approval between posts. Continue automatically after
each successful checkpoint unless a genuine unrecoverable blocker occurs.

Before beginning work, the next agent must read `agent.md`,
`agent-instructions.md`, and this file completely, then confirm this exact
durable state:

- post 304, “The Startup Algorithm,” is fully published, checksum-verified,
  reflected in its range ledger and dashboard, cleaned from temporary storage,
  and recorded in the completed-checkpoint table below;
- `Last completed post` is 401 and `Next post` is none;
- post 401 is fully published and `/private/tmp/shayan-post-401/` does not
  exist;
- the authorized migration through post 401 is complete.

Do not use a batch importer, do not parallelize posts, and do not create local
copies in `site/draft-post/` or `site/live-posts/`. Temporary post files belong
only in `/private/tmp/shayan-post-<number>/`. Run `yarn validate-site` for each
post; never run `yarn build` or `yarn dev` for this migration.

The global route-slug and image-folder uniqueness preflight is mandatory twice
for every post: once before creating its MDX and again immediately before its
first upload. A nonzero result blocks the post:

```text
python3 substack/scripts/verify_publication_slug_unique.py <slug> --post-number <number>
```

This preflight must check every local range ledger, all route slugs derived
from dated MDX filenames under the authorized S3 writings prefix, and the exact
candidate `public/images/posts/<slug>/` folder. A new post's image folder must
be empty. Never reuse another post's route slug or image folder.

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
two mandatory per-post uniqueness preflights for posts 120–401.

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
     `sites/shayan-arman-blog/public/images/posts/<slug>/` S3 folder is empty
     for a new post.
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
   For the active posts 78–401 direct-publication batch, this file and
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
5. Create exactly one temporary directory:
   `/private/tmp/shayan-post-<number>`.
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
   `sites/shayan-arman-blog/public/images/posts/<slug>/`; it must contain no
   objects for a new post. Never share or reuse another post's image folder.
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
   keywords, only literal normalized source hashtags, excerpt, changefreq, and
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
   placeholders, and footer order.
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
   `/private/tmp/shayan-post-<number>/` directory. Do not use a broad recursive
   delete, glob, `$HOME`, `~`, or an unresolved variable.
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

- Target: posts 93–401 inclusive (continuation of the completed 78–92 batch)
- Processing mode: strictly one post at a time; no parallel post work
- Last completed post: 401
- Next post: none
- Last updated: 2026-08-12

## Completed Checkpoints

| Post | Title | MDX S3 key | Images | Completed |
| ---: | --- | --- | ---: | --- |
| 77 | (Ad) Zero Inbox Email Cleaner and Manager at ZeroInbox.ai | `sites/shayan-arman-blog/posts/writings/2025-04-16-ad-zero-inbox-email-cleaner-and-manager.mdx` | 2 | 2026-08-11 |
| 78 | Tariff Wars; and Email Inboxes | `sites/shayan-arman-blog/posts/writings/2025-04-20-tariff-wars-and-email-inboxes.mdx` | 3 | 2026-08-11 |
| 79 | The illusion of choice | `sites/shayan-arman-blog/posts/writings/2025-04-27-the-illusion-of-choice.mdx` | 0 | 2026-08-11 |
| 80 | Warren Buffett | `sites/shayan-arman-blog/posts/writings/2025-05-04-warren-buffett.mdx` | 1 | 2026-08-11 |
| 81 | Invest in Yourself | `sites/shayan-arman-blog/posts/writings/2025-05-05-invest-in-yourself.mdx` | 1 | 2026-08-11 |
| 82 | Given | `sites/shayan-arman-blog/posts/writings/2025-05-08-given.mdx` | 2 | 2026-08-11 |
| 83 | A Bottle of Wine for the Table | `sites/shayan-arman-blog/posts/writings/2025-05-11-a-bottle-of-wine-for-the-table.mdx` | 0 | 2026-08-11 |
| 84 | A latte please | `sites/shayan-arman-blog/posts/writings/2025-05-11-a-latte-please.mdx` | 0 | 2026-08-11 |
| 85 | Very truly, what is the problem? | `sites/shayan-arman-blog/posts/writings/2025-05-13-very-truly-what-is-the-problem.mdx` | 0 | 2026-08-11 |
| 86 | On Thinking | `sites/shayan-arman-blog/posts/writings/2025-05-14-on-thinking.mdx` | 0 | 2026-08-11 |
| 87 | On listening | `sites/shayan-arman-blog/posts/writings/2025-05-14-on-listening.mdx` | 0 | 2026-08-11 |
| 88 | Listening part 2 | `sites/shayan-arman-blog/posts/writings/2025-05-16-listening-part-2.mdx` | 0 | 2026-08-11 |
| 89 | !Ontological Man! | `sites/shayan-arman-blog/posts/writings/2025-05-21-ontological-man.mdx` | 0 | 2026-08-11 |
| 90 | The Beginning | `sites/shayan-arman-blog/posts/writings/2025-05-21-the-beginning.mdx` | 0 | 2026-08-11 |
| 91 | Little by little | `sites/shayan-arman-blog/posts/writings/2025-05-25-little-by-little.mdx` | 0 | 2026-08-11 |
| 92 | Give give give | `sites/shayan-arman-blog/posts/writings/2025-06-01-give-give-give.mdx` | 0 | 2026-08-11 |
| 93 | Tell me one thing to rule your life. | `sites/shayan-arman-blog/posts/writings/2025-06-02-tell-me-one-thing-to-rule-your-life.mdx` | 0 | 2026-08-11 |
| 94 | Czech Pilsner | `sites/shayan-arman-blog/posts/writings/2025-06-03-czech-pilsner.mdx` | 0 | 2026-08-11 |
| 95 | Tell me again | `sites/shayan-arman-blog/posts/writings/2025-06-06-tell-me-again.mdx` | 0 | 2026-08-11 |
| 96 | On Sickness | `sites/shayan-arman-blog/posts/writings/2025-06-07-on-sickness.mdx` | 1 | 2026-08-11 |
| 97 | The Apple of my Eye | `sites/shayan-arman-blog/posts/writings/2025-06-07-the-apple-of-my-eye.mdx` | 1 | 2026-08-11 |
| 98 | The Ugly Duckling | `sites/shayan-arman-blog/posts/writings/2025-06-08-the-ugly-duckling.mdx` | 0 | 2026-08-11 |
| 99 | Who is The Father of Silicon Valley? | `sites/shayan-arman-blog/posts/writings/2025-06-08-who-is-the-father-of-silicon-valley.mdx` | 1 | 2026-08-11 |
| 100 | Lost in Translation | `sites/shayan-arman-blog/posts/writings/2025-06-09-lost-in-translation.mdx` | 0 | 2026-08-11 |
| 101 | Divergence | `sites/shayan-arman-blog/posts/writings/2025-06-09-divergence.mdx` | 1 | 2026-08-11 |
| 102 | Quantum Coders | `sites/shayan-arman-blog/posts/writings/2025-06-12-quantum-coders.mdx` | 1 | 2026-08-11 |
| 103 | Sign Here Please | `sites/shayan-arman-blog/posts/writings/2025-06-13-sign-here-please.mdx` | 1 | 2026-08-11 |
| 104 | On Addiction | `sites/shayan-arman-blog/posts/writings/2025-06-14-on-addiction.mdx` | 1 | 2026-08-11 |
| 105 | Generating the Absurd | `sites/shayan-arman-blog/posts/writings/2025-06-14-generating-the-absurd.mdx` | 1 | 2026-08-11 |
| 106 | To Serve | `sites/shayan-arman-blog/posts/writings/2025-06-14-to-serve.mdx` | 1 | 2026-08-11 |
| 107 | On Belief Systems | `sites/shayan-arman-blog/posts/writings/2025-06-14-on-belief-systems.mdx` | 1 | 2026-08-11 |
| 108 | Empires with Umpires | `sites/shayan-arman-blog/posts/writings/2025-06-15-empires-with-umpires.mdx` | 1 | 2026-08-11 |
| 109 | Mykonos | `sites/shayan-arman-blog/posts/writings/2025-06-16-mykonos.mdx` | 1 | 2026-08-11 |
| 110 | The Pillars | `sites/shayan-arman-blog/posts/writings/2025-06-16-the-pillars.mdx` | 1 | 2026-08-11 |
| 111 | Nearology | `sites/shayan-arman-blog/posts/writings/2025-06-17-nearology.mdx` | 1 | 2026-08-11 |
| 112 | On Language | `sites/shayan-arman-blog/posts/writings/2025-06-18-on-language-parts-and-position.mdx` | 0 | 2026-08-11 |
| 113 | Da Club | `sites/shayan-arman-blog/posts/writings/2025-06-20-da-club.mdx` | 0 | 2026-08-11 |
| 114 | The End of Labour | `sites/shayan-arman-blog/posts/writings/2025-06-20-the-end-of-labour.mdx` | 1 | 2026-08-11 |
| 115 | The TRUTH! | `sites/shayan-arman-blog/posts/writings/2025-06-21-the-truth.mdx` | 1 | 2026-08-11 |
| 116 | Specifically What? | `sites/shayan-arman-blog/posts/writings/2025-06-22-specifically-what.mdx` | 1 | 2026-08-11 |
| 117 | Is it worth it? | `sites/shayan-arman-blog/posts/writings/2025-06-23-is-it-worth-it.mdx` | 0 | 2026-08-11 |
| 118 | On Wealth | `sites/shayan-arman-blog/posts/writings/2025-06-24-on-wealth.mdx` | 1 | 2026-08-11 |
| 119 | The Funniest Shit | `sites/shayan-arman-blog/posts/writings/2025-06-24-the-funniest-shit.mdx` | 1 | 2026-08-11 |
| 120 | All is Observance | `sites/shayan-arman-blog/posts/writings/2025-06-25-all-is-observance.mdx` | 1 | 2026-08-11 |
| 121 | On Awakening | `sites/shayan-arman-blog/posts/writings/2025-06-26-on-awakening.mdx` | 1 | 2026-08-11 |
| 122 | On Philosophy | `sites/shayan-arman-blog/posts/writings/2025-06-27-on-philosophy.mdx` | 0 | 2026-08-11 |
| 123 | Now is as good a time as … | `sites/shayan-arman-blog/posts/writings/2025-06-27-now-is-as-good-a-time-as.mdx` | 0 | 2026-08-11 |
| 124 | Courage to Venture | `sites/shayan-arman-blog/posts/writings/2025-06-27-courage-to-venture.mdx` | 1 | 2026-08-11 |
| 125 | On Desire | `sites/shayan-arman-blog/posts/writings/2025-06-28-on-desire.mdx` | 0 | 2026-08-11 |
| 126 | an Even further discussion on Virtue | `sites/shayan-arman-blog/posts/writings/2025-06-30-an-even-further-discussion-on-virtue.mdx` | 0 | 2026-08-11 |
| 127 | El Vicco | `sites/shayan-arman-blog/posts/writings/2025-07-01-el-vicco.mdx` | 1 | 2026-08-11 |
| 128 | The Champ | `sites/shayan-arman-blog/posts/writings/2025-07-02-the-champ.mdx` | 0 | 2026-08-11 |
| 129 | My Cousin | `sites/shayan-arman-blog/posts/writings/2025-07-03-my-cousin.mdx` | 1 | 2026-08-11 |
| 130 | Wisdom | `sites/shayan-arman-blog/posts/writings/2025-07-05-wisdom.mdx` | 1 | 2026-08-11 |
| 131 | The Most Gracious | `sites/shayan-arman-blog/posts/writings/2025-07-05-the-most-gracious.mdx` | 1 | 2026-08-11 |
| 132 | Aphorisms | `sites/shayan-arman-blog/posts/writings/2025-07-05-aphorisms.mdx` | 0 | 2026-08-11 |
| 133 | On Folding Sheets | `sites/shayan-arman-blog/posts/writings/2025-07-06-on-folding-sheets.mdx` | 1 | 2026-08-11 |
| 134 | Friendly Magician | `sites/shayan-arman-blog/posts/writings/2025-07-07-friendly-magician.mdx` | 0 | 2026-08-11 |
| 135 | Abra Cadabra bitches! | `sites/shayan-arman-blog/posts/writings/2025-07-07-abra-cadabra-bitches.mdx` | 0 | 2026-08-11 |
| 136 | Inflation | `sites/shayan-arman-blog/posts/writings/2025-07-07-inflation.mdx` | 0 | 2026-08-11 |
| 137 | The shape of things | `sites/shayan-arman-blog/posts/writings/2025-07-07-the-shape-of-things.mdx` | 0 | 2026-08-11 |
| 138 | An Athlete of Life | `sites/shayan-arman-blog/posts/writings/2025-07-07-an-athlete-of-life.mdx` | 1 | 2026-08-11 |
| 139 | The Drinker | `sites/shayan-arman-blog/posts/writings/2025-07-08-the-drinker.mdx` | 1 | 2026-08-11 |
| 140 | On Me | `sites/shayan-arman-blog/posts/writings/2025-07-08-on-me.mdx` | 1 | 2026-08-11 |
| 141 | On Equality | `sites/shayan-arman-blog/posts/writings/2025-07-09-on-equality.mdx` | 1 | 2026-08-11 |
| 142 | Rule Breakers | `sites/shayan-arman-blog/posts/writings/2025-07-15-rule-breakers.mdx` | 1 | 2026-08-11 |
| 143 | Twisted Thinking | `sites/shayan-arman-blog/posts/writings/2025-07-15-twisted-thinking.mdx` | 0 | 2026-08-11 |
| 144 | The Don | `sites/shayan-arman-blog/posts/writings/2025-07-20-the-don.mdx` | 0 | 2026-08-11 |
| 145 | On Suffering | `sites/shayan-arman-blog/posts/writings/2025-07-20-on-suffering-c06.mdx` | 1 | 2026-08-11 |
| 146 | Dreaming with God | `sites/shayan-arman-blog/posts/writings/2025-07-20-dreaming-with-god.mdx` | 0 | 2026-08-11 |
| 147 | Belief Systems | `sites/shayan-arman-blog/posts/writings/2025-07-21-belief-systems.mdx` | 1 | 2026-08-11 |
| 148 | The Rise of Boogeymen | `sites/shayan-arman-blog/posts/writings/2025-07-21-the-rise-of-boogeymen.mdx` | 0 | 2026-08-11 |
| 149 | On Marx | `sites/shayan-arman-blog/posts/writings/2025-07-23-on-marx.mdx` | 0 | 2026-08-11 |
| 150 | Dying Twice | `sites/shayan-arman-blog/posts/writings/2025-07-23-dying-twice.mdx` | 1 | 2026-08-11 |
| 151 | The Most Beautiful | `sites/shayan-arman-blog/posts/writings/2025-07-23-the-most-beautiful.mdx` | 1 | 2026-08-11 |
| 152 | Why not me? | `sites/shayan-arman-blog/posts/writings/2025-07-24-why-not-me.mdx` | 1 | 2026-08-11 |
| 153 | The Train of Philosophy | `sites/shayan-arman-blog/posts/writings/2025-07-24-the-train-of-philosophy.mdx` | 1 | 2026-08-11 |
| 154 | Environmentalism | `sites/shayan-arman-blog/posts/writings/2025-07-25-environmentalism.mdx` | 1 | 2026-08-11 |
| 155 | You scratched it! | `sites/shayan-arman-blog/posts/writings/2025-07-25-you-scratched-it.mdx` | 1 | 2026-08-11 |
| 156 | Conservative Closed Minded | `sites/shayan-arman-blog/posts/writings/2025-07-29-conservative-closed-minded.mdx` | 0 | 2026-08-11 |
| 157 | True Friend | `sites/shayan-arman-blog/posts/writings/2025-08-03-true-friend.mdx` | 1 | 2026-08-11 |
| 158 | On Cleaning | `sites/shayan-arman-blog/posts/writings/2025-08-06-on-cleaning.mdx` | 0 | 2026-08-11 |
| 159 | Question Master | `sites/shayan-arman-blog/posts/writings/2025-08-06-question-master.mdx` | 1 | 2026-08-11 |
| 160 | On Miracles | `sites/shayan-arman-blog/posts/writings/2025-08-08-on-miracles.mdx` | 1 | 2026-08-11 |
| 161 | Knowledge and Prediction | `sites/shayan-arman-blog/posts/writings/2025-08-09-knowledge-and-prediction.mdx` | 0 | 2026-08-11 |
| 162 | Curses | `sites/shayan-arman-blog/posts/writings/2025-08-09-curses.mdx` | 0 | 2026-08-11 |
| 163 | Core Things | `sites/shayan-arman-blog/posts/writings/2025-08-10-core-things.mdx` | 0 | 2026-08-11 |
| 164 | Blame Games | `sites/shayan-arman-blog/posts/writings/2025-08-10-blame-games.mdx` | 0 | 2026-08-11 |
| 165 | Habitual | `sites/shayan-arman-blog/posts/writings/2025-08-10-habitual.mdx` | 0 | 2026-08-11 |
| 166 | Business Class Blues | `sites/shayan-arman-blog/posts/writings/2025-08-13-business-class-blues.mdx` | 1 | 2026-08-11 |
| 167 | On Sleep | `sites/shayan-arman-blog/posts/writings/2025-08-13-on-sleep.mdx` | 1 | 2026-08-11 |
| 168 | Andrew Tate | `sites/shayan-arman-blog/posts/writings/2025-08-14-andrew-tate.mdx` | 1 | 2026-08-11 |
| 169 | To take a Stand | `sites/shayan-arman-blog/posts/writings/2025-08-14-to-take-a-stand.mdx` | 1 | 2026-08-11 |
| 170 | Andrew Tate and Exceptionalism | `sites/shayan-arman-blog/posts/writings/2025-08-14-andrew-tate-and-exceptionalism.mdx` | 1 | 2026-08-12 |
| 171 | Heights Unseen | `sites/shayan-arman-blog/posts/writings/2025-08-15-heights-unseen.mdx` | 1 | 2026-08-12 |
| 172 | A Conceptual Proof of the Soul and How to Learn a Language | `sites/shayan-arman-blog/posts/writings/2025-08-16-a-conceptual-proof-of-the-soul-and.mdx` | 0 | 2026-08-12 |
| 173 | Summative | `sites/shayan-arman-blog/posts/writings/2025-08-16-summative.mdx` | 1 | 2026-08-12 |
| 174 | Vibe Coding | `sites/shayan-arman-blog/posts/writings/2025-08-16-vibe-coding.mdx` | 0 | 2026-08-12 |
| 175 | Exceptionalism | `sites/shayan-arman-blog/posts/writings/2025-08-16-exceptionalism.mdx` | 1 | 2026-08-12 |
| 176 | Economic Spaces | `sites/shayan-arman-blog/posts/writings/2025-08-17-economic-spaces.mdx` | 0 | 2026-08-12 |
| 177 | The Conductor | `sites/shayan-arman-blog/posts/writings/2025-08-17-the-conductor.mdx` | 0 | 2026-08-12 |
| 178 | Perceptions | `sites/shayan-arman-blog/posts/writings/2025-08-17-perceptions.mdx` | 0 | 2026-08-12 |
| 179 | Ontology | `sites/shayan-arman-blog/posts/writings/2025-08-17-ontology.mdx` | 0 | 2026-08-12 |
| 180 | End Theory | `sites/shayan-arman-blog/posts/writings/2025-08-17-end-theory.mdx` | 0 | 2026-08-12 |
| 181 | Startup Weather | `sites/shayan-arman-blog/posts/writings/2025-08-18-startup-weather.mdx` | 1 | 2026-08-12 |
| 182 | Pre Donald Trump | `sites/shayan-arman-blog/posts/writings/2025-08-21-pre-donald-trump.mdx` | 1 | 2026-08-12 |
| 183 | Fatal Attraction | `sites/shayan-arman-blog/posts/writings/2025-08-21-fatal-attraction.mdx` | 0 | 2026-08-12 |
| 184 | Random Wednesdays | `sites/shayan-arman-blog/posts/writings/2025-08-21-random-wednesdays.mdx` | 1 | 2026-08-12 |
| 185 | The Artists Life | `sites/shayan-arman-blog/posts/writings/2025-08-21-the-artists-life.mdx` | 1 | 2026-08-12 |
| 186 | On Marketing | `sites/shayan-arman-blog/posts/writings/2025-08-22-on-marketing.mdx` | 1 | 2026-08-12 |
| 187 | The Labourer | `sites/shayan-arman-blog/posts/writings/2025-08-23-the-labourer.mdx` | 0 | 2026-08-12 |
| 188 | The Label Maker | `sites/shayan-arman-blog/posts/writings/2025-08-23-the-label-maker.mdx` | 0 | 2026-08-12 |
| 189 | The Good Friend | `sites/shayan-arman-blog/posts/writings/2025-08-27-the-good-friend.mdx` | 1 | 2026-08-12 |
| 190 | Starting a Startup | `sites/shayan-arman-blog/posts/writings/2025-08-28-starting-a-startup.mdx` | 1 | 2026-08-12 |
| 191 | Purpose and Direction | `sites/shayan-arman-blog/posts/writings/2025-08-28-purpose-and-direction.mdx` | 0 | 2026-08-12 |
| 192 | Sam Altman | `sites/shayan-arman-blog/posts/writings/2025-08-28-sam-altman.mdx` | 0 | 2026-08-12 |
| 193 | The Blind | `sites/shayan-arman-blog/posts/writings/2025-08-28-the-blind.mdx` | 0 | 2026-08-12 |
| 194 | Me on a Walk | `sites/shayan-arman-blog/posts/writings/2025-08-29-me-on-a-walk.mdx` | 0 | 2026-08-12 |
| 195 | On Motivation | `sites/shayan-arman-blog/posts/writings/2025-08-29-on-motivation.mdx` | 1 | 2026-08-12 |
| 196 | Slope Change Philosophy | `sites/shayan-arman-blog/posts/writings/2025-08-29-slope-change-philosophy.mdx` | 1 | 2026-08-12 |
| 197 | Globalism | `sites/shayan-arman-blog/posts/writings/2025-08-29-globalism.mdx` | 0 | 2026-08-12 |
| 198 | The Third Voice | `sites/shayan-arman-blog/posts/writings/2025-08-30-the-third-voice.mdx` | 0 | 2026-08-12 |
| 199 | Nobody | `sites/shayan-arman-blog/posts/writings/2025-08-31-nobody.mdx` | 0 | 2026-08-12 |
| 200 | On Sleep | `sites/shayan-arman-blog/posts/writings/2025-08-31-on-sleep-9b5.mdx` | 0 | 2026-08-12 |
| 201 | On Bad Company | `sites/shayan-arman-blog/posts/writings/2025-08-31-on-bad-company.mdx` | 0 | 2026-08-12 |
| 202 | On Failure | `sites/shayan-arman-blog/posts/writings/2025-09-02-on-failure.mdx` | 0 | 2026-08-12 |
| 203 | On memories | `sites/shayan-arman-blog/posts/writings/2025-09-02-on-memories.mdx` | 0 | 2026-08-12 |
| 204 | To Be | `sites/shayan-arman-blog/posts/writings/2025-09-03-to-be.mdx` | 0 | 2026-08-12 |
| 205 | Sinner | `sites/shayan-arman-blog/posts/writings/2025-09-04-sinner.mdx` | 0 | 2026-08-12 |
| 206 | Theory of Expressionism | `sites/shayan-arman-blog/posts/writings/2025-09-04-theory-of-expressionism.mdx` | 0 | 2026-08-12 |
| 207 | Heroes | `sites/shayan-arman-blog/posts/writings/2025-09-04-heroes.mdx` | 0 | 2026-08-12 |
| 208 | Modern Philosophy | `sites/shayan-arman-blog/posts/writings/2025-09-05-modern-philosophy.mdx` | 1 | 2026-08-12 |
| 209 | Programming | `sites/shayan-arman-blog/posts/writings/2025-09-06-programming.mdx` | 0 | 2026-08-12 |
| 210 | Iterations | `sites/shayan-arman-blog/posts/writings/2025-09-06-iterations.mdx` | 0 | 2026-08-12 |
| 211 | Sides Taken | `sites/shayan-arman-blog/posts/writings/2025-09-06-sides-taken.mdx` | 0 | 2026-08-12 |
| 212 | Layering Knowledge | `sites/shayan-arman-blog/posts/writings/2025-09-06-layering-knowledge.mdx` | 0 | 2026-08-12 |
| 213 | On Becoming Exceptional | `sites/shayan-arman-blog/posts/writings/2025-09-07-on-becoming-exceptional.mdx` | 1 | 2026-08-12 |
| 214 | Through Him; | `sites/shayan-arman-blog/posts/writings/2025-09-07-through-him.mdx` | 1 | 2026-08-12 |
| 215 | The Mind and Reality | `sites/shayan-arman-blog/posts/writings/2025-09-08-the-mind-and-reality.mdx` | 1 | 2026-08-12 |
| 216 | The Shame of Exceptionalism | `sites/shayan-arman-blog/posts/writings/2025-09-10-the-shame-of-exceptionalism.mdx` | 1 | 2026-08-12 |
| 217 | My Daughter did what? | `sites/shayan-arman-blog/posts/writings/2025-09-11-my-daughter-did-what.mdx` | 1 | 2026-08-12 |
| 218 | Trying your Best | `sites/shayan-arman-blog/posts/writings/2025-09-12-trying-your-best.mdx` | 0 | 2026-08-12 |
| 219 | Mykonos 2026 | `sites/shayan-arman-blog/posts/writings/2025-09-14-mykonos-2026.mdx` | 1 | 2026-08-12 |
| 220 | On Loan | `sites/shayan-arman-blog/posts/writings/2025-09-15-on-loan.mdx` | 1 | 2026-08-12 |
| 221 | ~The Jumper~ | `sites/shayan-arman-blog/posts/writings/2025-09-17-the-jumper.mdx` | 0 | 2026-08-12 |
| 222 | Loopy Thinkiiiiingggg | `sites/shayan-arman-blog/posts/writings/2025-09-17-loopy-thinkiiiiingggg.mdx` | 0 | 2026-08-12 |
| 223 | We all want to be Goku | `sites/shayan-arman-blog/posts/writings/2025-09-17-we-all-want-to-be-goku.mdx` | 1 | 2026-08-12 |
| 224 | On Production | `sites/shayan-arman-blog/posts/writings/2025-09-18-on-production.mdx` | 1 | 2026-08-12 |
| 225 | Ask God Not | `sites/shayan-arman-blog/posts/writings/2025-09-18-ask-god-not.mdx` | 1 | 2026-08-12 |
| 226 | The Don | `sites/shayan-arman-blog/posts/writings/2025-09-18-the-don-15b.mdx` | 1 | 2026-08-12 |
| 227 | On Death | `sites/shayan-arman-blog/posts/writings/2025-09-19-on-death.mdx` | 0 | 2026-08-12 |
| 228 | On Business | `sites/shayan-arman-blog/posts/writings/2025-09-19-on-business.mdx` | 0 | 2026-08-12 |
| 229 | Summative Action | `sites/shayan-arman-blog/posts/writings/2025-09-19-summative-action.mdx` | 0 | 2026-08-12 |
| 230 | Billion Dollar Baby | `sites/shayan-arman-blog/posts/writings/2025-09-21-billion-dollar-baby.mdx` | 1 | 2026-08-12 |
| 231 | 2 ways north | `sites/shayan-arman-blog/posts/writings/2025-09-22-2-ways-north.mdx` | 0 | 2026-08-12 |
| 232 | On Famy | `sites/shayan-arman-blog/posts/writings/2025-09-23-on-famy.mdx` | 1 | 2026-08-12 |
| 233 | Economy in Five | `sites/shayan-arman-blog/posts/writings/2025-09-25-economy-in-five.mdx` | 1 | 2026-08-12 |
| 234 | Been a while | `sites/shayan-arman-blog/posts/writings/2025-09-29-been-a-while.mdx` | 0 | 2026-08-12 |
| 235 | The Red Purse | `sites/shayan-arman-blog/posts/writings/2025-09-30-the-red-purse.mdx` | 1 | 2026-08-12 |
| 236 | The Global Religion | `sites/shayan-arman-blog/posts/writings/2025-10-03-the-global-religion.mdx` | 1 | 2026-08-12 |
| 237 | (SUPER SUPER EMBARASSING) | `sites/shayan-arman-blog/posts/writings/2025-10-03-super-super-embarassing.mdx` | 0 | 2026-08-12 |
| 238 | Opposing Reactions | `sites/shayan-arman-blog/posts/writings/2025-10-04-opposing-reactions.mdx` | 1 | 2026-08-12 |
| 239 | Internet Personalities and Trust Fund Babies | `sites/shayan-arman-blog/posts/writings/2025-10-04-internet-personalities-and-trust.mdx` | 0 | 2026-08-12 |
| 240 | effects | `sites/shayan-arman-blog/posts/writings/2025-10-04-effects.mdx` | 0 | 2026-08-12 |
| 241 | Belief Systems | `sites/shayan-arman-blog/posts/writings/2025-10-05-belief-systems-341.mdx` | 0 | 2026-08-12 |
| 242 | AI Subcontext Rule | `sites/shayan-arman-blog/posts/writings/2025-10-05-ai-subcontext-rule.mdx` | 3 | 2026-08-12 |
| 243 | Lucky Lucky Money Money | `sites/shayan-arman-blog/posts/writings/2025-10-06-lucky-lucky-money-money.mdx` | 0 | 2026-08-12 |
| 244 | Derivative Theory | `sites/shayan-arman-blog/posts/writings/2025-10-07-derivative-theory.mdx` | 0 | 2026-08-12 |
| 245 | Golden Words | `sites/shayan-arman-blog/posts/writings/2025-10-07-golden-words.mdx` | 1 | 2026-08-12 |
| 246 | 3 Steps to God | `sites/shayan-arman-blog/posts/writings/2025-10-09-3-steps-to-god.mdx` | 2 | 2026-08-12 |
| 247 | MONEY | `sites/shayan-arman-blog/posts/writings/2025-10-09-money.mdx` | 1 | 2026-08-12 |
| 248 | Money 2 | `sites/shayan-arman-blog/posts/writings/2025-10-09-money-2.mdx` | 7 | 2026-08-12 |
| 249 | Startups | `sites/shayan-arman-blog/posts/writings/2025-10-09-startups.mdx` | 2 | 2026-08-12 |
| 250 | Exponential Chain Theory | `sites/shayan-arman-blog/posts/writings/2025-10-12-exponential-chain-theory.mdx` | 0 | 2026-08-12 |
| 251 | Single Step Theory | `sites/shayan-arman-blog/posts/writings/2025-10-15-single-step-theory.mdx` | 1 | 2026-08-12 |
| 252 | priced in | `sites/shayan-arman-blog/posts/writings/2025-10-17-priced-in.mdx` | 0 | 2026-08-12 |
| 253 | Onto-logic | `sites/shayan-arman-blog/posts/writings/2025-10-19-onto-logic.mdx` | 1 | 2026-08-12 |
| 254 | Paths, Journeys, Goals, and... | `sites/shayan-arman-blog/posts/writings/2025-10-19-paths-journeys-goals-and.mdx` | 1 | 2026-08-12 |
| 255 | The Hill | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-hill.mdx` | 0 | 2026-08-12 |
| 256 | Partner in Crime | `sites/shayan-arman-blog/posts/writings/2025-10-20-partner-in-crime.mdx` | 0 | 2026-08-12 |
| 257 | The Eye | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-eye.mdx` | 0 | 2026-08-12 |
| 258 | The Garbage Men | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-garbage-men.mdx` | 0 | 2026-08-12 |
| 259 | The Garbage Men | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-garbage-men-257.mdx` | 0 | 2026-08-12 |
| 260 | The Garbage Men | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-garbage-men-a70.mdx` | 0 | 2026-08-12 |
| 261 | The Garbage Men | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-garbage-men-fca.mdx` | 0 | 2026-08-12 |
| 262 | The Garbage Men | `sites/shayan-arman-blog/posts/writings/2025-10-20-the-garbage-men-d06.mdx` | 0 | 2026-08-12 |
| 263 | Pain | `sites/shayan-arman-blog/posts/writings/2025-10-23-pain.mdx` | 0 | 2026-08-12 |
| 264 | Network Topology - Pool Theory | `sites/shayan-arman-blog/posts/writings/2025-10-24-network-topology-pool-theory.mdx` | 0 | 2026-08-12 |
| 265 | Useless Knowledge | `sites/shayan-arman-blog/posts/writings/2025-10-24-useless-knowledge.mdx` | 0 | 2026-08-12 |
| 266 | Circular Economies | `sites/shayan-arman-blog/posts/writings/2025-10-25-circular-economies.mdx` | 0 | 2026-08-12 |
| 267 | Providence | `sites/shayan-arman-blog/posts/writings/2025-10-29-providence.mdx` | 0 | 2026-08-12 |
| 268 | I meditated for 3 hours | `sites/shayan-arman-blog/posts/writings/2025-11-11-i-meditated-for-3-hours.mdx` | 1 | 2026-08-12 |
| 269 | On Lying | `sites/shayan-arman-blog/posts/writings/2025-11-11-on-lying.mdx` | 1 | 2026-08-12 |
| 270 | All is Fire | `sites/shayan-arman-blog/posts/writings/2025-11-14-all-is-fire.mdx` | 0 | 2026-08-12 |
| 271 | How I laughed! | `sites/shayan-arman-blog/posts/writings/2025-11-15-how-i-laughed.mdx` | 0 | 2026-08-12 |
| 272 | Its Easy Shy! | `sites/shayan-arman-blog/posts/writings/2025-11-15-its-easy-shy.mdx` | 0 | 2026-08-12 |
| 273 | Arbitrage | `sites/shayan-arman-blog/posts/writings/2025-11-18-arbitrage.mdx` | 0 | 2026-08-12 |
| 274 | Kafka? | `sites/shayan-arman-blog/posts/writings/2025-11-19-kafka.mdx` | 0 | 2026-08-12 |
| 275 | My Phone Call with the CRA | `sites/shayan-arman-blog/posts/writings/2025-11-19-my-phone-call-with-the-cra.mdx` | 0 | 2026-08-12 |
| 276 | The Weighing Man | `sites/shayan-arman-blog/posts/writings/2025-11-20-the-weighing-man.mdx` | 0 | 2026-08-12 |
| 277 | The Cra | `sites/shayan-arman-blog/posts/writings/2025-11-20-the-cra.mdx` | 0 | 2026-08-12 |
| 278 | Tojo's Lesson | `sites/shayan-arman-blog/posts/writings/2025-11-21-tojos-lesson.mdx` | 0 | 2026-08-12 |
| 279 | Aha Business!! | `sites/shayan-arman-blog/posts/writings/2025-11-21-aha-business.mdx` | 1 | 2026-08-12 |
| 280 | A constant diagnosis | `sites/shayan-arman-blog/posts/writings/2025-11-22-a-constant-diagnosis.mdx` | 0 | 2026-08-12 |
| 281 | On Youth | `sites/shayan-arman-blog/posts/writings/2025-11-24-on-youth.mdx` | 1 | 2026-08-12 |
| 282 | On Sand | `sites/shayan-arman-blog/posts/writings/2025-11-24-on-sand.mdx` | 1 | 2026-08-12 |
| 283 | On Suffering | `sites/shayan-arman-blog/posts/writings/2025-11-25-on-suffering-ad7.mdx` | 0 | 2026-08-12 |
| 284 | Take a Look | `sites/shayan-arman-blog/posts/writings/2025-11-28-take-a-look.mdx` | 0 | 2026-08-12 |
| 285 | Inverted Living | `sites/shayan-arman-blog/posts/writings/2025-11-30-inverted-living.mdx` | 0 | 2026-08-12 |
| 286 | Working | `sites/shayan-arman-blog/posts/writings/2025-12-02-working.mdx` | 1 | 2026-08-12 |
| 287 | The Mind and Suicide and Jesus | `sites/shayan-arman-blog/posts/writings/2025-12-05-the-mind-and-suicide-and-jesus.mdx` | 1 | 2026-08-12 |
| 288 | Et tu, Brute? | `sites/shayan-arman-blog/posts/writings/2025-12-06-et-tu-brute.mdx` | 0 | 2026-08-12 |
| 289 | Moments | `sites/shayan-arman-blog/posts/writings/2025-12-08-moments.mdx` | 1 | 2026-08-12 |
| 290 | Genie in a Bottle | `sites/shayan-arman-blog/posts/writings/2025-12-09-genie-in-a-bottle.mdx` | 1 | 2026-08-12 |
| 291 | Manifest Identity | `sites/shayan-arman-blog/posts/writings/2025-12-09-manifest-identity.mdx` | 0 | 2026-08-12 |
| 292 | The Axe Man | `sites/shayan-arman-blog/posts/writings/2025-12-12-the-axe-man.mdx` | 0 | 2026-08-12 |
| 293 | The One Person Billion Dollar Company | `sites/shayan-arman-blog/posts/writings/2025-12-14-the-one-person-billion-dollar-company.mdx` | 1 | 2026-08-12 |
| 294 | On the Unknown | `sites/shayan-arman-blog/posts/writings/2025-12-19-on-the-unknown.mdx` | 0 | 2026-08-12 |
| 295 | A Conversation with Gemini on Job Security | `sites/shayan-arman-blog/posts/writings/2026-02-04-a-conversation-with-gemini-on-job.mdx` | 0 | 2026-08-12 |
| 296 | A Consensus Algorithm | `sites/shayan-arman-blog/posts/writings/2026-02-04-a-consensus-algorithm.mdx` | 0 | 2026-08-12 |
| 297 | How Ai Will Replace Us | `sites/shayan-arman-blog/posts/writings/2026-02-24-how-ai-will-replace-us.mdx` | 2 | 2026-08-12 |
| 298 | A New Depression | `sites/shayan-arman-blog/posts/writings/2026-03-04-a-new-depression.mdx` | 1 | 2026-08-12 |
| 299 | Thy Unholy Neighbour | `sites/shayan-arman-blog/posts/writings/2026-03-10-thy-unholy-neighbour.mdx` | 0 | 2026-08-12 |
| 300 | Forms of the Mind | `sites/shayan-arman-blog/posts/writings/2026-03-12-forms-of-the-mind.mdx` | 2 | 2026-08-12 |
| 301 | A Guest | `sites/shayan-arman-blog/posts/writings/2026-03-12-a-guest.mdx` | 0 | 2026-08-12 |
| 302 | Coding and Driving | `sites/shayan-arman-blog/posts/writings/2026-03-22-coding-and-driving.mdx` | 0 | 2026-08-12 |
| 303 | The News | `sites/shayan-arman-blog/posts/writings/2026-03-23-the-news.mdx` | 0 | 2026-08-12 |
| 304 | The Startup Algorithm | `sites/shayan-arman-blog/posts/writings/2026-03-24-the-startup-algorithm.mdx` | 2 | 2026-08-12 |
| 305 | The Steak | `sites/shayan-arman-blog/posts/writings/2026-03-25-the-steak.mdx` | 0 | 2026-08-12 |
| 306 | Ai will Replace Us | `sites/shayan-arman-blog/posts/writings/2026-03-25-ai-will-replace-us.mdx` | 0 | 2026-08-12 |
| 307 | On Party | `sites/shayan-arman-blog/posts/writings/2026-03-29-on-party.mdx` | 1 | 2026-08-12 |
| 308 | The Discombobulator | `sites/shayan-arman-blog/posts/writings/2026-03-30-the-discombobulator.mdx` | 2 | 2026-08-12 |
| 309 | A Mirror | `sites/shayan-arman-blog/posts/writings/2026-04-06-a-mirror.mdx` | 0 | 2026-08-12 |
| 310 | Three Brothers | `sites/shayan-arman-blog/posts/writings/2026-04-06-three-brothers.mdx` | 0 | 2026-08-12 |
| 311 | Three Brothers | `sites/shayan-arman-blog/posts/writings/2026-04-06-three-brothers-7a9.mdx` | 0 | 2026-08-12 |
| 312 | Sentient | `sites/shayan-arman-blog/posts/writings/2026-04-07-sentient.mdx` | 0 | 2026-08-12 |
| 313 | Sweet Fruits | `sites/shayan-arman-blog/posts/writings/2026-04-08-sweet-fruits.mdx` | 0 | 2026-08-12 |
| 314 | Growth Rates to Die For | `sites/shayan-arman-blog/posts/writings/2026-04-10-growth-rates-to-die-for.mdx` | 0 | 2026-08-12 |
| 315 | Tell her i said what? | `sites/shayan-arman-blog/posts/writings/2026-04-10-tell-her-i-said-what.mdx` | 0 | 2026-08-12 |
| 316 | On Freedom | `sites/shayan-arman-blog/posts/writings/2026-04-10-on-freedom.mdx` | 0 | 2026-08-12 |
| 317 | On Vitamin C | `sites/shayan-arman-blog/posts/writings/2026-04-10-on-vitamin-c.mdx` | 0 | 2026-08-12 |
| 318 | Real Growth Baby | `sites/shayan-arman-blog/posts/writings/2026-04-10-real-growth-baby.mdx` | 0 | 2026-08-12 |
| 319 | The Empty Mall | `sites/shayan-arman-blog/posts/writings/2026-04-10-the-empty-mall.mdx` | 0 | 2026-08-12 |
| 320 | Universal Directional Travel | `sites/shayan-arman-blog/posts/writings/2026-04-10-universal-directional-travel.mdx` | 0 | 2026-08-12 |
| 321 | Loopy Beliefs | `sites/shayan-arman-blog/posts/writings/2026-04-10-loopy-beliefs.mdx` | 0 | 2026-08-12 |
| 322 | Endearing | `sites/shayan-arman-blog/posts/writings/2026-04-11-endearing.mdx` | 0 | 2026-08-12 |
| 323 | Grandstanding | `sites/shayan-arman-blog/posts/writings/2026-04-12-grandstanding.mdx` | 1 | 2026-08-12 |
| 324 | Random Bird Flight Paths | `sites/shayan-arman-blog/posts/writings/2026-04-13-random-bird-flight-paths.mdx` | 0 | 2026-08-12 |
| 325 | By Bye Nay-Toe | `sites/shayan-arman-blog/posts/writings/2026-04-15-by-bye-nay-toe.mdx` | 0 | 2026-08-12 |
| 326 | Private Wine Tastings in Italy | `sites/shayan-arman-blog/posts/writings/2026-04-15-private-wine-tastings-in-italy.mdx` | 3 | 2026-08-12 |
| 327 | Proetic | `sites/shayan-arman-blog/posts/writings/2026-04-15-proetic.mdx` | 0 | 2026-08-12 |
| 328 | A Friend in Logic | `sites/shayan-arman-blog/posts/writings/2026-04-15-a-friend-in-logic.mdx` | 0 | 2026-08-12 |
| 329 | How to Code with AI Agents | `sites/shayan-arman-blog/posts/writings/2026-04-17-how-to-code-with-ai-agents.mdx` | 3 | 2026-08-12 |
| 330 | Many Startups | `sites/shayan-arman-blog/posts/writings/2026-04-17-many-startups.mdx` | 3 | 2026-08-12 |
| 331 | Pre Sin | `sites/shayan-arman-blog/posts/writings/2026-04-18-pre-sin.mdx` | 0 | 2026-08-12 |
| 332 | Duplicitous Moral Standards | `sites/shayan-arman-blog/posts/writings/2026-04-19-duplicitous-moral-standards.mdx` | 0 | 2026-08-12 |
| 333 | Meek | `sites/shayan-arman-blog/posts/writings/2026-04-20-meek.mdx` | 0 | 2026-08-12 |
| 334 | Annals of Time | `sites/shayan-arman-blog/posts/writings/2026-04-20-annals-of-time.mdx` | 0 | 2026-08-12 |
| 335 | An Immovable Boulder | `sites/shayan-arman-blog/posts/writings/2026-04-20-an-immovable-boulder.mdx` | 0 | 2026-08-12 |
| 336 | The Doctor | `sites/shayan-arman-blog/posts/writings/2026-04-21-the-doctor.mdx` | 1 | 2026-08-12 |
| 337 | One Thing | `sites/shayan-arman-blog/posts/writings/2026-04-21-one-thing.mdx` | 0 | 2026-08-12 |
| 338 | GETTING BUSY | `sites/shayan-arman-blog/posts/writings/2026-04-22-getting-busy.mdx` | 1 | 2026-08-12 |
| 339 | 2 am coding session | `sites/shayan-arman-blog/posts/writings/2026-04-22-2-am-coding-session.mdx` | 1 | 2026-08-12 |
| 340 | Narcos | `sites/shayan-arman-blog/posts/writings/2026-04-22-narcos.mdx` | 0 | 2026-08-12 |
| 341 | Narcos | `sites/shayan-arman-blog/posts/writings/2026-04-22-narcos-35d.mdx` | 0 | 2026-08-12 |
| 342 | Stars Misaligned | `sites/shayan-arman-blog/posts/writings/2026-04-23-stars-misaligned.mdx` | 0 | 2026-08-12 |
| 343 | Esha Bhatti | `sites/shayan-arman-blog/posts/writings/2026-04-23-esha-bhatti.mdx` | 1 | 2026-08-12 |
| 344 | Psycholo-G | `sites/shayan-arman-blog/posts/writings/2026-04-23-psycholo-g.mdx` | 2 | 2026-08-12 |
| 345 | Justin Bieber Part 1 | `sites/shayan-arman-blog/posts/writings/2026-04-24-justin-bieber-part-1.mdx` | 0 | 2026-08-12 |
| 346 | True Diversity | `sites/shayan-arman-blog/posts/writings/2026-04-24-true-diversity.mdx` | 0 | 2026-08-12 |
| 347 | Best Friends | `sites/shayan-arman-blog/posts/writings/2026-04-24-best-friends.mdx` | 0 | 2026-08-12 |
| 348 | The Night Sky | `sites/shayan-arman-blog/posts/writings/2026-04-24-the-night-sky.mdx` | 0 | 2026-08-12 |
| 349 | Acronyms | `sites/shayan-arman-blog/posts/writings/2026-04-24-acronyms.mdx` | 0 | 2026-08-12 |
| 350 | The New Boxing Gym | `sites/shayan-arman-blog/posts/writings/2026-04-24-the-new-boxing-gym.mdx` | 0 | 2026-08-12 |
| 351 | The Crow | `sites/shayan-arman-blog/posts/writings/2026-04-24-the-crow.mdx` | 0 | 2026-08-12 |
| 352 | 7 Day Girlfriends | `sites/shayan-arman-blog/posts/writings/2026-04-26-7-day-girlfriends.mdx` | 0 | 2026-08-12 |
| 353 | The Mind | `sites/shayan-arman-blog/posts/writings/2026-04-27-the-mind.mdx` | 0 | 2026-08-12 |
| 354 | Winged Words | `sites/shayan-arman-blog/posts/writings/2026-04-27-winged-words.mdx` | 0 | 2026-08-12 |
| 355 | Ontological Victimhood | `sites/shayan-arman-blog/posts/writings/2026-04-27-ontological-victimhood.mdx` | 0 | 2026-08-12 |
| 356 | Reverse Inference | `sites/shayan-arman-blog/posts/writings/2026-04-28-reverse-inference.mdx` | 0 | 2026-08-12 |
| 357 | Conservatives | `sites/shayan-arman-blog/posts/writings/2026-04-28-conservatives.mdx` | 0 | 2026-08-12 |
| 358 | The structure of the universe | `sites/shayan-arman-blog/posts/writings/2026-04-29-the-structure-of-the-universe.mdx` | 0 | 2026-08-12 |
| 359 | Advices | `sites/shayan-arman-blog/posts/writings/2026-04-29-advices.mdx` | 0 | 2026-08-12 |
| 360 | The Goose | `sites/shayan-arman-blog/posts/writings/2026-04-29-the-goose.mdx` | 0 | 2026-08-12 |
| 361 | My Stalker | `sites/shayan-arman-blog/posts/writings/2026-04-30-my-stalker.mdx` | 0 | 2026-08-12 |
| 362 | Insufferable | `sites/shayan-arman-blog/posts/writings/2026-04-30-insufferable.mdx` | 0 | 2026-08-12 |
| 363 | My Efforts | `sites/shayan-arman-blog/posts/writings/2026-04-30-my-efforts.mdx` | 1 | 2026-08-12 |
| 364 | Perfectionists Part 1 | `sites/shayan-arman-blog/posts/writings/2026-04-30-perfectionists-part-1.mdx` | 0 | 2026-08-12 |
| 365 | Definition Friday… | `sites/shayan-arman-blog/posts/writings/2026-05-01-definition-friday.mdx` | 0 | 2026-08-12 |
| 366 | A path laid for me | `sites/shayan-arman-blog/posts/writings/2026-05-01-a-path-laid-for-me.mdx` | 0 | 2026-08-12 |
| 367 | Shame Scores | `sites/shayan-arman-blog/posts/writings/2026-05-01-shame-scores.mdx` | 0 | 2026-08-12 |
| 368 | The Diplomat | `sites/shayan-arman-blog/posts/writings/2026-05-01-the-diplomat.mdx` | 0 | 2026-08-12 |
| 369 | Marcus Aurelius | `sites/shayan-arman-blog/posts/writings/2026-05-02-marcus-aurelius.mdx` | 0 | 2026-08-12 |
| 370 | The Calling | `sites/shayan-arman-blog/posts/writings/2026-05-03-the-calling.mdx` | 0 | 2026-08-12 |
| 371 | The Wolf | `sites/shayan-arman-blog/posts/writings/2026-05-03-the-wolf.mdx` | 0 | 2026-08-12 |
| 372 | On Fame | `sites/shayan-arman-blog/posts/writings/2026-05-03-on-fame.mdx` | 0 | 2026-08-12 |
| 373 | The Don part 4 | `sites/shayan-arman-blog/posts/writings/2026-05-03-the-don-part-4.mdx` | 0 | 2026-08-12 |
| 374 | A Definitive Understanding of Human Development | `sites/shayan-arman-blog/posts/writings/2026-05-05-a-definitive-understanding-of-human.mdx` | 1 | 2026-08-12 |
| 375 | Rambling | `sites/shayan-arman-blog/posts/writings/2026-05-06-rambling.mdx` | 0 | 2026-08-12 |
| 376 | A life well lived | `sites/shayan-arman-blog/posts/writings/2026-05-06-a-life-well-lived.mdx` | 0 | 2026-08-12 |
| 377 | Cafe Coding | `sites/shayan-arman-blog/posts/writings/2026-05-07-cafe-coding.mdx` | 1 | 2026-08-12 |
| 378 | The Happiness Fairy | `sites/shayan-arman-blog/posts/writings/2026-05-07-the-happiness-fairy.mdx` | 1 | 2026-08-12 |
| 379 | Please stop | `sites/shayan-arman-blog/posts/writings/2026-05-07-please-stop.mdx` | 1 | 2026-08-12 |
| 380 | Why Universities are Good Part 1 | `sites/shayan-arman-blog/posts/writings/2026-05-12-why-universities-are-good-part-1.mdx` | 0 | 2026-08-12 |
| 381 | The Martian Child | `sites/shayan-arman-blog/posts/writings/2026-05-12-the-martian-child.mdx` | 0 | 2026-08-12 |
| 382 | On Business | `sites/shayan-arman-blog/posts/writings/2026-05-15-on-business-5ad.mdx` | 1 | 2026-08-12 |
| 383 | Outside | `sites/shayan-arman-blog/posts/writings/2026-05-15-outside.mdx` | 0 | 2026-08-12 |
| 384 | Pause part 1 | `sites/shayan-arman-blog/posts/writings/2026-05-21-pause-part-1-308.mdx` | 0 | 2026-08-12 |
| 385 | At the Pool | `sites/shayan-arman-blog/posts/writings/2026-05-22-at-the-pool.mdx` | 1 | 2026-08-12 |
| 386 | Turns | `sites/shayan-arman-blog/posts/writings/2026-05-26-turns-593.mdx` | 0 | 2026-08-12 |
| 387 | The New New Testament | `sites/shayan-arman-blog/posts/writings/2026-05-26-the-new-new-testament.mdx` | 0 | 2026-08-12 |
| 388 | Drinking in Japan | `sites/shayan-arman-blog/posts/writings/2026-05-26-drinking-in-japan.mdx` | 0 | 2026-08-12 |
| 389 | Virality | `sites/shayan-arman-blog/posts/writings/2026-05-27-virality.mdx` | 1 | 2026-08-12 |
| 390 | Ew | `sites/shayan-arman-blog/posts/writings/2026-05-29-ew.mdx` | 1 | 2026-08-12 |
| 391 | The Salmon | `sites/shayan-arman-blog/posts/writings/2026-05-30-the-salmon.mdx` | 0 | 2026-08-12 |
| 392 | Three Dimensions | `sites/shayan-arman-blog/posts/writings/2026-05-30-three-dimensions.mdx` | 0 | 2026-08-12 |
| 393 | Reflexivity | `sites/shayan-arman-blog/posts/writings/2026-05-31-reflexivity.mdx` | 0 | 2026-08-12 |
| 394 | The End of Labour | `sites/shayan-arman-blog/posts/writings/2026-06-01-the-end-of-labour-fab.mdx` | 1 | 2026-08-12 |
| 395 | Responsibility | `sites/shayan-arman-blog/posts/writings/2026-06-01-responsibility.mdx` | 0 | 2026-08-12 |
| 396 | Enterprise | `sites/shayan-arman-blog/posts/writings/2026-06-01-enterprise-73f.mdx` | 0 | 2026-08-12 |
| 397 | Good Fortune | `sites/shayan-arman-blog/posts/writings/2026-06-06-good-fortune.mdx` | 0 | 2026-08-12 |
| 398 | ai slop | `sites/shayan-arman-blog/posts/writings/2026-06-06-ai-slop.mdx` | 1 | 2026-08-12 |
| 399 | Why Siri Failed - an honest take | `sites/shayan-arman-blog/posts/writings/2026-06-11-why-siri-failed-an-honest-take.mdx` | 1 | 2026-08-12 |
| 400 | Homeless Man | `sites/shayan-arman-blog/posts/writings/2026-06-11-homeless-man.mdx` | 0 | 2026-08-12 |
| 401 | Pages | `sites/shayan-arman-blog/posts/writings/2026-06-12-pages.mdx` | 0 | 2026-08-12 |

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
- Post 401: done
