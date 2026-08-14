#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import process from "node:process";

const requireFromSite = createRequire(
  new URL("../../../shayan-arman-blog/package.json", import.meta.url),
);

async function importFromSite(specifier) {
  const resolved = requireFromSite.resolve(specifier);
  return import(pathToFileURL(resolved).href);
}

const [{ compile }, matterModule, remarkMdxModule, remarkParseModule, { unified }] =
  await Promise.all([
    importFromSite("@mdx-js/mdx"),
    importFromSite("gray-matter"),
    importFromSite("remark-mdx"),
    importFromSite("remark-parse"),
    importFromSite("unified"),
  ]);
const matter = matterModule.default;
const remarkMdx = remarkMdxModule.default;
const remarkParse = remarkParseModule.default;

const STANDARD_FOOTERS = new Set([
  "ShareArticleClipboard",
  "ArticleDivider",
  "ProductLinks",
]);

function usage() {
  console.error("Usage: extract_audit_events.mjs <archive|mdx> <path>");
}

function normalizeText(value) {
  return String(value ?? "")
    .replaceAll("\r\n", "\n")
    .replaceAll("\r", "\n")
    .normalize("NFC")
    .replace(/[\t ]+/g, " ")
    .replace(/ *\n */g, "\n")
    .trim();
}

function stableHash(value) {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function attributeValue(attribute) {
  if (!attribute || attribute.type !== "mdxJsxAttribute") {
    return null;
  }

  if (typeof attribute.value === "string") {
    return attribute.value;
  }

  if (attribute.value?.type === "mdxJsxAttributeValueExpression") {
    const raw = attribute.value.value.trim();
    if (/^-?\d+(?:\.\d+)?$/.test(raw)) {
      return Number(raw);
    }
    if (
      (raw.startsWith('"') && raw.endsWith('"')) ||
      (raw.startsWith("'") && raw.endsWith("'"))
    ) {
      return raw.slice(1, -1);
    }
    return raw;
  }

  return attribute.value ?? null;
}

function attributesObject(node) {
  const output = {};
  for (const attribute of node.attributes ?? []) {
    if (attribute.type === "mdxJsxAttribute") {
      output[attribute.name] = attributeValue(attribute);
    }
  }
  return output;
}

function expressionVisibleText(value) {
  return normalizeText(
    String(value ?? "")
      .replace(/<>|<\/>/g, "")
      .replace(/<a\b[^>]*>/gi, "")
      .replace(/<\/a>/gi, "")
      .replace(/<\/?(?:strong|em|span)\b[^>]*>/gi, "")
      .replaceAll("&amp;", "&")
      .replaceAll("&lt;", "<")
      .replaceAll("&gt;", ">")
      .replaceAll("&quot;", '"')
      .replaceAll("&#39;", "'"),
  );
}

function expressionLinks(value) {
  const links = [];
  const pattern = /<a\b[^>]*\bhref=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  for (const match of String(value ?? "").matchAll(pattern)) {
    links.push({
      text: expressionVisibleText(match[2]),
      url: match[1].normalize("NFC"),
    });
  }
  return links;
}

function isOnlyImageParagraph(node) {
  return (
    node.type === "paragraph" &&
    node.children?.length === 1 &&
    node.children[0]?.type === "image"
  );
}

function inlineText(node, state, options = {}) {
  if (!node) return "";

  if (node.type === "text") {
    if (!options.suppressLinks) {
      for (const match of String(node.value ?? "").matchAll(/https?:\/\/[^\s<>]+/g)) {
        const url = match[0].replace(/[.,;:!?]+$/, "").normalize("NFC");
        state.links.push({ text: url, url });
      }
    }
    return node.value ?? "";
  }
  if (node.type === "inlineCode" || node.type === "code") {
    return node.value ?? "";
  }
  if (node.type === "break") return "\n";
  if (node.type === "html") return node.value ?? "";
  if (node.type === "image") {
    state.rawMarkdownImages += 1;
    return "";
  }
  if (node.type === "link") {
    const text = normalizeText(
      (node.children ?? [])
        .map((child) => inlineText(child, state, { ...options, suppressLinks: true }))
        .join(""),
    );
    if (!options.suppressLinks) {
      state.links.push({ text, url: String(node.url ?? "").normalize("NFC") });
    }
    return text;
  }
  if (node.type === "linkReference") {
    return (node.children ?? []).map((child) => inlineText(child, state, options)).join("");
  }
  if (node.type === "mdxTextExpression" || node.type === "mdxFlowExpression") {
    return node.value ?? "";
  }
  if (node.type === "mdxJsxTextElement") {
    const text = (node.children ?? [])
      .map((child) => inlineText(child, state, options))
      .join("");
    if (node.name === "a" && !options.suppressLinks) {
      const attributes = attributesObject(node);
      state.links.push({ text: normalizeText(text), url: String(attributes.href ?? "") });
    }
    return text;
  }
  if (Array.isArray(node.children)) {
    return node.children.map((child) => inlineText(child, state, options)).join("");
  }
  return node.value ?? "";
}

function emitEvent(state, kind, text, node) {
  const normalized = normalizeText(text);
  if (!normalized) return;
  state.events.push({
    kind,
    text: normalized,
    line: node?.position?.start?.line ?? null,
  });
}

function mediaFromMdx(node, state) {
  const attributes = attributesObject(node);
  const rawCaption = attributes.caption;
  const caption =
    typeof rawCaption === "string" ? expressionVisibleText(rawCaption) : normalizeText(rawCaption);
  const captionLinks = typeof rawCaption === "string" ? expressionLinks(rawCaption) : [];

  state.media.push({
    src: attributes.src ?? null,
    width: attributes.width ?? null,
    height: attributes.height ?? null,
    alt: attributes.alt ?? null,
    caption: caption || null,
    caption_links: captionLinks,
    event_index: state.events.length,
    line: node?.position?.start?.line ?? null,
    has_caption_spacer: false,
  });
}

function emitBlock(node, state, context = null) {
  switch (node.type) {
    case "paragraph": {
      if (isOnlyImageParagraph(node)) {
        const image = node.children[0];
        state.rawMarkdownImages += 1;
        state.media.push({
          src: image.url ?? null,
          width: null,
          height: null,
          alt: image.alt ?? null,
          caption: null,
          caption_links: [],
          event_index: state.events.length,
          line: node.position?.start?.line ?? null,
          has_caption_spacer: false,
        });
        return;
      }
      const kind = context === "blockquote" ? "blockquote" : context === "list-item" ? "list-item" : "paragraph";
      emitEvent(state, kind, inlineText(node, state), node);
      return;
    }
    case "heading":
      emitEvent(state, `heading${node.depth}`, inlineText(node, state), node);
      return;
    case "blockquote":
      for (const child of node.children ?? []) emitBlock(child, state, "blockquote");
      return;
    case "list":
      for (const item of node.children ?? []) {
        const text = (item.children ?? [])
          .map((child) => inlineText(child, state))
          .join("\n");
        emitEvent(state, "list-item", text, item);
      }
      return;
    case "code":
      emitEvent(state, "code", node.value ?? "", node);
      return;
    case "thematicBreak":
      emitEvent(state, "thematic-break", "---", node);
      return;
    case "html":
      emitEvent(state, "html", node.value ?? "", node);
      return;
    case "mdxjsEsm":
      state.imports.push(node.value ?? "");
      return;
    case "mdxJsxFlowElement": {
      if (node.name === "GangsterImage") {
        mediaFromMdx(node, state);
      } else if (STANDARD_FOOTERS.has(node.name)) {
        state.footerSequence.push(node.name);
      } else if (node.name === "br") {
        state.flowBreaks += 1;
      } else {
        state.unknownFlowElements.push(node.name ?? "fragment");
        const text = inlineText(node, state);
        emitEvent(state, `component:${node.name ?? "fragment"}`, text, node);
      }
      return;
    }
    default:
      if (Array.isArray(node.children)) {
        for (const child of node.children) emitBlock(child, state, context);
      } else if (typeof node.value === "string") {
        emitEvent(state, node.type, node.value, node);
      }
  }
}

function extractTree(tree) {
  const state = {
    events: [],
    links: [],
    media: [],
    footerSequence: [],
    imports: [],
    rawMarkdownImages: 0,
    flowBreaks: 0,
    unknownFlowElements: [],
  };

  const children = tree.children ?? [];
  for (let index = 0; index < children.length; index += 1) {
    const node = children[index];
    const mediaBefore = state.media.length;
    emitBlock(node, state);
    if (
      state.media.length > mediaBefore &&
      node.type === "mdxJsxFlowElement" &&
      node.name === "GangsterImage"
    ) {
      const next = children[index + 1];
      if (next?.type === "mdxJsxFlowElement" && next.name === "br") {
        state.media.at(-1).has_caption_spacer = true;
        index += 1;
      }
    }
  }

  state.eventHash = stableHash(state.events.map(({ kind, text }) => ({ kind, text })));
  state.textHash = stableHash(state.events.map(({ text }) => text));
  state.linkHash = stableHash(state.links);
  state.mediaHash = stableHash(state.media);
  return state;
}

async function main() {
  const [kind, filePath] = process.argv.slice(2);
  if (!new Set(["archive", "mdx"]).has(kind) || !filePath) {
    usage();
    process.exitCode = 2;
    return;
  }

  const raw = await readFile(filePath, "utf8");
  let content = raw;
  let metadata = {};
  let compileResult = { status: "SKIP", error: null };

  const processor = unified().use(remarkParse);
  if (kind === "mdx") {
    const parsedMatter = matter(raw);
    content = parsedMatter.content;
    metadata = parsedMatter.data;
    processor.use(remarkMdx);
    try {
      await compile(raw, { outputFormat: "function-body" });
      compileResult = { status: "PASS", error: null };
    } catch (error) {
      compileResult = {
        status: "FAIL",
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  let tree;
  try {
    tree = processor.parse(content);
  } catch (error) {
    console.log(
      JSON.stringify({
        kind,
        path: filePath,
        parse: { status: "FAIL", error: error instanceof Error ? error.message : String(error) },
        compile: compileResult,
      }),
    );
    process.exitCode = 1;
    return;
  }

  const extracted = extractTree(tree);
  const rawMarkers = [
    "<todo-image-shayan:",
    "Network error while fetching Substack post",
    "Traceback (most recent call last)",
    "window._preloads",
  ].filter((marker) => raw.includes(marker));

  console.log(
    JSON.stringify({
      kind,
      path: filePath,
      metadata,
      parse: { status: "PASS", error: null },
      compile: compileResult,
      rawMarkers,
      ...extracted,
    }),
  );
}

await main();
