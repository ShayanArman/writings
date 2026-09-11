# writings

## Canonical S3 image hierarchy

Blog images always include the blog collection between `posts/` and the post
slug:

```text
s3://seo-gangster/sites/<site-id>/public/images/posts/<blog-collection-name>/<blog-post-slug>/<filename>
```

This repository migrates the `writings` collection, so every new Shayan Arman
writing image belongs at:

```text
s3://seo-gangster/sites/shayan-arman-blog/public/images/posts/writings/<slug>/<filename>
```

Never create a new writing image folder directly at
`public/images/posts/<slug>/`; that path incorrectly omits the collection.
An exact zero-byte marker at `.../writings/<slug>/` represents an empty folder;
actual image objects go beneath it.
All current ledger, audit, checkpoint, draft, and live-post image references
must use the collection-aware path. An old direct-under-`posts/` reference is
stale data and must not be treated as an alternate or legacy convention.
