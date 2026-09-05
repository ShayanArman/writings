# Migrate a Substack post

Copy this prompt and replace the URL:

```text
Migrate this Substack post to shayan-arman-blog: [SUBSTACK URL]

First read writings/agent-instructions.md, writings/agent.md, and the current
instructions in writings/migration-checkpoints.md.

Make an exact migration: word for word, image for image. Preserve the title,
subtitle, original date, body, links, hashtags, image order, and captions.
Use the full-resolution original images without changing their bytes.
Never rewrite or invent copy, including metadata. If an excerpt is needed,
copy a passage verbatim from the source. Use the required MDX format and footer.

Create the local draft in shayan-arman-blog/site/draft-post/ and validate it
against the source, including the excerpt and images. Give me the draft link.
I will sign off first; only then upload this post and its images to their
correct Shayan Arman S3 keys and verify the uploads.

Work only on this post and its assets. Do not change other posts, drafts,
live posts, sites, or S3 objects. Keep any writings record updates specific
to this post. Do not run yarn build or yarn dev.
```
