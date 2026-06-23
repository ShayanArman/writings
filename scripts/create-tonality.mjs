#!/usr/bin/env node

import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const workspaceRoot = path.resolve(path.dirname(scriptPath), "..");
const inputDir = path.join(workspaceRoot, "substack");
const tmpDir = path.join(workspaceRoot, "corpus", "tmp");
const finalToneDir = path.join(workspaceRoot, "corpus", "tone");

const STOP_WORDS = new Set([
  "a",
  "about",
  "above",
  "after",
  "again",
  "against",
  "all",
  "also",
  "am",
  "an",
  "and",
  "any",
  "are",
  "as",
  "at",
  "be",
  "because",
  "been",
  "before",
  "being",
  "below",
  "between",
  "both",
  "but",
  "by",
  "can",
  "could",
  "did",
  "do",
  "does",
  "doing",
  "down",
  "during",
  "each",
  "few",
  "for",
  "from",
  "further",
  "had",
  "has",
  "have",
  "having",
  "he",
  "her",
  "here",
  "hers",
  "herself",
  "him",
  "himself",
  "his",
  "how",
  "i",
  "if",
  "in",
  "into",
  "is",
  "it",
  "its",
  "itself",
  "just",
  "me",
  "more",
  "most",
  "my",
  "myself",
  "no",
  "nor",
  "not",
  "now",
  "of",
  "off",
  "on",
  "once",
  "only",
  "or",
  "other",
  "our",
  "ours",
  "ourselves",
  "out",
  "over",
  "own",
  "same",
  "she",
  "should",
  "so",
  "some",
  "such",
  "than",
  "that",
  "the",
  "their",
  "theirs",
  "them",
  "themselves",
  "then",
  "there",
  "these",
  "they",
  "this",
  "those",
  "through",
  "to",
  "too",
  "under",
  "until",
  "up",
  "very",
  "was",
  "we",
  "were",
  "what",
  "when",
  "where",
  "which",
  "while",
  "who",
  "whom",
  "why",
  "will",
  "with",
  "would",
  "you",
  "your",
  "yours",
  "yourself",
  "yourselves",
]);

function usage() {
  return [
    "Usage: node scripts/create-tonality.mjs",
    "",
    "Reads every Markdown post under substack and writes draft tone files:",
    "- corpus/tmp/tonality.json",
    "- corpus/tmp/tonality.txt",
    "",
    "The draft files contain stable final-output shapes, source inventory,",
    "mechanical corpus stats, and source-backed pattern banks. An AI agent",
    "should fill them, ask for approval, and only then promote them to corpus/tone.",
  ].join("\n");
}

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function normalizeText(text) {
  return text
    .replace(/\r\n?/g, "\n")
    .replace(/\\u([0-9a-fA-F]{4})/g, (_match, hex) =>
      String.fromCharCode(Number.parseInt(hex, 16)),
    )
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, "\"")
    .replace(/\u00a0/g, " ");
}

function normalizeWhitespace(text) {
  return normalizeText(text).replace(/[ \t]+/g, " ").trim();
}

function relativeToWorkspace(filePath) {
  return path.relative(workspaceRoot, filePath).split(path.sep).join("/");
}

function round(value, places = 1) {
  if (!Number.isFinite(value)) {
    return 0;
  }

  const multiplier = 10 ** places;
  return Math.round(value * multiplier) / multiplier;
}

function median(values) {
  if (values.length === 0) {
    return 0;
  }

  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);

  if (sorted.length % 2 === 1) {
    return sorted[middle];
  }

  return (sorted[middle - 1] + sorted[middle]) / 2;
}

function postNumberFromPath(filePath) {
  const directoryName = path.basename(path.dirname(filePath));
  const numeric = Number.parseInt(directoryName, 10);
  return Number.isFinite(numeric) ? numeric : Number.POSITIVE_INFINITY;
}

function compareDocumentPaths(left, right) {
  const leftNumber = postNumberFromPath(left);
  const rightNumber = postNumberFromPath(right);

  if (leftNumber !== rightNumber) {
    return leftNumber - rightNumber;
  }

  return relativeToWorkspace(left).localeCompare(relativeToWorkspace(right));
}

function listMarkdownFiles(dir) {
  if (!existsSync(dir)) {
    fail(`Missing input directory: ${relativeToWorkspace(dir)}`);
  }

  const files = [];
  const entries = readdirSync(dir, { withFileTypes: true }).sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  for (const entry of entries) {
    const entryPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      if (entry.name.startsWith(".") || entry.name === "__pycache__") {
        continue;
      }

      files.push(...listMarkdownFiles(entryPath));
      continue;
    }

    if (entry.isFile() && entry.name.toLowerCase().endsWith(".md")) {
      files.push(entryPath);
    }
  }

  return files.sort(compareDocumentPaths);
}

function visibleLines(rawText) {
  return normalizeText(rawText)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !isBoilerplateLine(line))
    .filter((line) => !/^<todo-image-shayan:/i.test(line))
    .filter((line) => !/^<[^>\n]+>$/.test(line))
    .filter((line) => !/^!\[[^\]]*]\([^)]+\)/.test(line));
}

function extractTitle(rawText, filePath) {
  const lines = visibleLines(rawText);
  const firstLine = lines[0]?.replace(/^#+\s*/, "");

  if (firstLine) {
    return normalizeWhitespace(firstLine);
  }

  return path.basename(filePath, ".md").replace(/[_-]+/g, " ");
}

function extractSubtitle(rawText) {
  const lines = visibleLines(rawText);
  const candidate = lines[1]?.replace(/^#+\s*/, "");

  if (!candidate || candidate.length > 180) {
    return null;
  }

  if (/[.!?]\s*$/.test(candidate) && wordsFrom(candidate).length > 8) {
    return null;
  }

  return normalizeWhitespace(candidate);
}

function stripCodeBlocks(text) {
  return normalizeText(text).replace(/```[\s\S]*?```/g, "\n");
}

function isBoilerplateLine(line) {
  const clean = normalizeWhitespace(line).toLowerCase();

  if (!clean) {
    return false;
  }

  if (/^(#|hashtag#)/.test(clean)) {
    return true;
  }

  return /(\bget to inbox zero\b|\bzero inbox ai\b|zeroinbox\.ai is the official|samaltmanprize|email organizer and cleaner|email cleaner and organizer|ai email assistant|ai workflows|this post (was )?brought to you|brought to you by|sponsored by|clear your emails?|manage your emails?|organize your email inbox|join 15000|world'?s first.*email|try out zeroinbox|check us out at .*zeroinbox|go to zeroinbox\.ai)/i.test(
    clean,
  );
}

function stripMarkdownNoise(rawText) {
  const title = extractTitle(rawText, "");
  const subtitle = extractSubtitle(rawText);
  let lineIndex = 0;

  return stripCodeBlocks(rawText)
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => {
      const clean = normalizeWhitespace(line).replace(/^#+\s*/, "");

      if (lineIndex === 0 && clean === title) {
        lineIndex += 1;
        return false;
      }

      if (lineIndex <= 1 && subtitle && clean === subtitle) {
        lineIndex += 1;
        return false;
      }

      if (clean) {
        lineIndex += 1;
      }

      return true;
    })
    .filter((line) => !isBoilerplateLine(line))
    .filter((line) => !/^<todo-image-shayan:/i.test(line.trim()))
    .filter((line) => !/^<[^>\n]+>$/.test(line.trim()))
    .filter((line) => !/^!\[[^\]]*]\([^)]+\)/.test(line.trim()))
    .map((line) =>
      line
        .replace(/^#{1,6}\s+/, "")
        .replace(/\[([^\]]+)]\(([^)]+)\)/g, "$1")
        .replace(/<https?:\/\/[^>\s]+>/g, "")
        .replace(/https?:\/\/\S+/g, "")
        .replace(/[*_~`]+/g, ""),
    )
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function wordsFrom(text) {
  return (
    normalizeText(text).match(/[\p{L}\p{N}]+(?:['-][\p{L}\p{N}]+)*/gu) ?? []
  );
}

function lowerWordsFrom(text) {
  return wordsFrom(text).map((word) => word.toLowerCase());
}

function sentencesFrom(text) {
  const blocks = normalizeText(text)
    .split(/\n\s*\n/g)
    .map((block) => normalizeWhitespace(block))
    .filter(Boolean);
  const matches = blocks.flatMap((block) =>
    block.match(/[^.!?]+(?:[.!?]+|$)(?=\s+|$)/g) ?? [],
  );

  return matches
    .map((sentence) => normalizeWhitespace(sentence))
    .filter((sentence) => wordsFrom(sentence).length >= 4);
}

function paragraphsFrom(text) {
  return normalizeText(text)
    .split(/\n\s*\n/g)
    .map((paragraph) => normalizeWhitespace(paragraph))
    .filter((paragraph) => wordsFrom(paragraph).length >= 4);
}

function looksLikeHeading(line) {
  const clean = normalizeWhitespace(line).replace(/^#+\s*/, "");
  const words = wordsFrom(clean);

  if (!clean || words.length === 0 || words.length > 14) {
    return false;
  }

  if (/[@{}[\]|\\]/.test(clean)) {
    return false;
  }

  if (/^[-*+]\s+/.test(clean)) {
    return false;
  }

  return /^#+\s+/.test(line.trim()) || /[:]\s*$/.test(clean);
}

function extractHeadings(sourceText) {
  const seen = new Set();
  const headings = [];

  for (const line of normalizeText(sourceText).split("\n")) {
    const clean = normalizeWhitespace(line).replace(/^#+\s*/, "");
    const key = clean.toLowerCase();

    if (!looksLikeHeading(line) || seen.has(key)) {
      continue;
    }

    seen.add(key);
    headings.push(clean);
  }

  return headings;
}

function countMatches(text, pattern) {
  return (text.match(pattern) ?? []).length;
}

function countPronouns(words, pronouns) {
  return words.filter((word) => pronouns.has(word.toLowerCase())).length;
}

function buildTermCounts(words, limit = 60) {
  const counts = new Map();

  for (const word of words) {
    const lower = word.toLowerCase();

    if (lower.length < 3 || STOP_WORDS.has(lower) || /^\d+$/.test(lower)) {
      continue;
    }

    counts.set(lower, (counts.get(lower) ?? 0) + 1);
  }

  return [...counts.entries()]
    .map(([term, count]) => ({ term, count }))
    .sort((a, b) => b.count - a.count || a.term.localeCompare(b.term))
    .slice(0, limit);
}

function buildRepeatedPhrases(words, limit = 50) {
  const lowerWords = words.map((word) => word.toLowerCase());
  const counts = new Map();

  for (let size = 2; size <= 5; size += 1) {
    for (let index = 0; index <= lowerWords.length - size; index += 1) {
      const phraseWords = lowerWords.slice(index, index + size);
      const first = phraseWords[0];
      const last = phraseWords[phraseWords.length - 1];

      if (
        STOP_WORDS.has(first) ||
        STOP_WORDS.has(last) ||
        phraseWords.every((word) => STOP_WORDS.has(word)) ||
        phraseWords.some((word) => /^\d+$/.test(word))
      ) {
        continue;
      }

      const phrase = phraseWords.join(" ");
      counts.set(phrase, (counts.get(phrase) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .filter(([, count]) => count > 2)
    .map(([phrase, count]) => ({ phrase, count }))
    .sort(
      (a, b) =>
        b.count - a.count ||
        b.phrase.split(" ").length - a.phrase.split(" ").length ||
        a.phrase.localeCompare(b.phrase),
    )
    .slice(0, limit);
}

function lexicalDensity(text) {
  const words = lowerWordsFrom(text);

  if (words.length === 0) {
    return 0;
  }

  const contentWords = words.filter(
    (word) => word.length > 2 && !STOP_WORDS.has(word) && !/^\d+$/.test(word),
  );

  return contentWords.length / words.length;
}

function sentenceScore(sentence, targetWordCount) {
  const words = wordsFrom(sentence);
  const lengthScore = 1 / (1 + Math.abs(words.length - targetWordCount));
  const densityScore = lexicalDensity(sentence);
  const pointOfViewScore = /\b(i|i'm|i'd|me|my|we|our|you|your)\b/i.test(sentence)
    ? 0.2
    : 0;
  const punctuationScore = /[!?;:]/.test(sentence) ? 0.1 : 0;

  return densityScore + lengthScore + pointOfViewScore + punctuationScore;
}

function sentenceLooksUsable(sentence) {
  return (
    wordsFrom(sentence).length >= 6 &&
    wordsFrom(sentence).length <= 42 &&
    !/@|https?:\/\/|www\.|<todo-image/i.test(sentence) &&
    countMatches(sentence, /\d/g) < 5
  );
}

function pickRepresentativeSentences(documents, limit = 80) {
  const allSentences = documents.flatMap((document) =>
    document.sentences.map((sentence, index) => ({
      text: sentence,
      source_path: document.relative_path,
      title: document.title,
      post_number: document.post_number,
      index,
      word_count: wordsFrom(sentence).length,
    })),
  );

  if (allSentences.length === 0) {
    return [];
  }

  const targetWordCount = median(allSentences.map((sentence) => sentence.word_count));
  const seen = new Set();

  return allSentences
    .filter((sentence) => sentenceLooksUsable(sentence.text))
    .filter((sentence) => {
      const key = sentence.text.toLowerCase();
      if (seen.has(key)) {
        return false;
      }

      seen.add(key);
      return true;
    })
    .map((sentence) => ({
      ...sentence,
      score: sentenceScore(sentence.text, targetWordCount),
    }))
    .sort(
      (a, b) =>
        b.score - a.score ||
        a.post_number - b.post_number ||
        a.index - b.index,
    )
    .slice(0, limit)
    .sort((a, b) => a.post_number - b.post_number || a.index - b.index)
    .map(({ score, index, ...sentence }) => sentence);
}

function pickOpenings(documents, limit = 40) {
  const seen = new Set();
  const candidates = [];

  for (const document of documents) {
    const firstSentence = document.sentences.find(sentenceLooksUsable);

    if (!firstSentence) {
      continue;
    }

    const key = firstSentence.toLowerCase();
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    candidates.push({
      text: firstSentence,
      source_path: document.relative_path,
      title: document.title,
      post_number: document.post_number,
      word_count: wordsFrom(firstSentence).length,
    });
  }

  return candidates.slice(0, limit);
}

function pickClosings(documents, limit = 40) {
  const seen = new Set();
  const candidates = [];

  for (const document of documents) {
    const lastSentence = [...document.sentences].reverse().find(sentenceLooksUsable);

    if (!lastSentence) {
      continue;
    }

    const key = lastSentence.toLowerCase();
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    candidates.push({
      text: lastSentence,
      source_path: document.relative_path,
      title: document.title,
      post_number: document.post_number,
      word_count: wordsFrom(lastSentence).length,
    });
  }

  return candidates.slice(-limit);
}

function titleStyleStats(documents) {
  const titles = documents.map((document) => document.title);
  const titleWordCounts = titles.map((title) => wordsFrom(title).length);

  return {
    average_title_words: round(
      titleWordCounts.reduce((sum, count) => sum + count, 0) /
        Math.max(titleWordCounts.length, 1),
    ),
    median_title_words: round(median(titleWordCounts)),
    on_titles: titles.filter((title) => /^on\b/i.test(title)).length,
    the_titles: titles.filter((title) => /^the\b/i.test(title)).length,
    question_titles: titles.filter((title) => /\?$/.test(title)).length,
    exclamation_titles: titles.filter((title) => /!/.test(title)).length,
    one_word_titles: titles.filter((title) => wordsFrom(title).length === 1).length,
    sample_titles: titles.slice(0, 40),
  };
}

function buildCorpusStats(documents) {
  const combinedText = documents.map((document) => document.sourceText).join("\n\n");
  const allWords = wordsFrom(combinedText);
  const lowerWords = allWords.map((word) => word.toLowerCase());
  const sentenceWordCounts = documents.flatMap((document) =>
    document.sentences.map((sentence) => wordsFrom(sentence).length),
  );
  const paragraphWordCounts = documents.flatMap((document) =>
    document.paragraphs.map((paragraph) => wordsFrom(paragraph).length),
  );
  const pointOfViewCounts = {
    first_person: countPronouns(
      lowerWords,
      new Set(["i", "me", "my", "mine", "myself", "we", "us", "our", "ours"]),
    ),
    second_person: countPronouns(
      lowerWords,
      new Set(["you", "your", "yours", "yourself", "yourselves"]),
    ),
    third_person: countPronouns(
      lowerWords,
      new Set(["he", "him", "his", "she", "her", "hers", "they", "them", "their"]),
    ),
  };
  const dominantPointOfView = Object.entries(pointOfViewCounts).sort(
    (a, b) => b[1] - a[1] || a[0].localeCompare(b[0]),
  )[0]?.[0] ?? "undetermined";

  return {
    document_count: documents.length,
    total_characters: combinedText.length,
    total_words: allWords.length,
    total_sentences: sentenceWordCounts.length,
    total_paragraphs: paragraphWordCounts.length,
    average_sentence_words: round(
      sentenceWordCounts.reduce((sum, count) => sum + count, 0) /
        Math.max(sentenceWordCounts.length, 1),
    ),
    median_sentence_words: round(median(sentenceWordCounts)),
    average_paragraph_words: round(
      paragraphWordCounts.reduce((sum, count) => sum + count, 0) /
        Math.max(paragraphWordCounts.length, 1),
    ),
    median_paragraph_words: round(median(paragraphWordCounts)),
    sentence_length_distribution: {
      short_1_to_10_words: sentenceWordCounts.filter((count) => count <= 10).length,
      medium_11_to_20_words: sentenceWordCounts.filter(
        (count) => count >= 11 && count <= 20,
      ).length,
      long_21_plus_words: sentenceWordCounts.filter((count) => count >= 21).length,
    },
    punctuation_counts: {
      exclamation: countMatches(combinedText, /!/g),
      question: countMatches(combinedText, /\?/g),
      colon: countMatches(combinedText, /:/g),
      semicolon: countMatches(combinedText, /;/g),
      dash: countMatches(combinedText, /[\u2013\u2014-]/g),
      ellipsis: countMatches(combinedText, /\.\.\.|…/g),
      parentheses: countMatches(combinedText, /[()]/g),
    },
    point_of_view: {
      counts: pointOfViewCounts,
      dominant: dominantPointOfView,
    },
    contractions_count: countMatches(
      combinedText,
      /\b[\p{L}\p{N}]+(?:n't|'m|'re|'ve|'ll|'d|'s)\b/giu,
    ),
    title_style: titleStyleStats(documents),
  };
}

function readCorpusDocuments() {
  const files = listMarkdownFiles(inputDir);

  if (files.length === 0) {
    fail(`No .md files found under ${relativeToWorkspace(inputDir)}`);
  }

  return files.map((filePath) => {
    const rawText = readFileSync(filePath, "utf8");
    const sourceText = stripMarkdownNoise(rawText);
    const sentences = sentencesFrom(sourceText);
    const paragraphs = paragraphsFrom(sourceText);

    return {
      path: filePath,
      relative_path: relativeToWorkspace(filePath),
      post_number: postNumberFromPath(filePath),
      title: extractTitle(rawText, filePath),
      subtitle: extractSubtitle(rawText),
      source_character_count: sourceText.length,
      source_word_count: wordsFrom(sourceText).length,
      sentence_count: sentences.length,
      paragraph_count: paragraphs.length,
      headings: extractHeadings(sourceText),
      sourceText,
      sentences,
      paragraphs,
    };
  });
}

function buildTemplateJson(documents) {
  const combinedWords = wordsFrom(
    documents.map((document) => document.sourceText).join("\n\n"),
  );

  return {
    schema_version: "1.0",
    artifact_type: "shayan_arman_tonality_agent_draft",
    status: "pending_agent_completion",
    purpose:
      "Temporary draft for an AI agent. This is not the approved tone guide yet.",
    source_policy: {
      input_dir: relativeToWorkspace(inputDir),
      tmp_output_dir: relativeToWorkspace(tmpDir),
      final_output_dir: relativeToWorkspace(finalToneDir),
      read_scope:
        "The script reads Markdown posts under substack, strips local image placeholders and Markdown image syntax, and writes temporary helper files under corpus/tmp.",
      temporary_artifacts_to_fill_by_agent: [
        "corpus/tmp/tonality.json",
        "corpus/tmp/tonality.txt",
      ],
      final_artifacts_after_user_approval: [
        "corpus/tone/tonality.json",
        "corpus/tone/tonality.txt",
      ],
    },
    agent_instructions: [
      "Use every Markdown source listed in corpus_inventory.documents[].path as the source corpus.",
      "Use the generated structure, stats, and source-backed pattern banks as scaffolding, not as a substitute for tone interpretation.",
      "Fill corpus/tmp/tonality.json and corpus/tmp/tonality.txt by extracting Shayan Arman's voice, rhetorical habits, audience relationship, vocabulary, and reusable examples from the Substack archive.",
      "Do not invent literal sentences. Use short source-backed examples and explain patterns in reusable language.",
      "Keep final output useful for drafting new writing in Shayan Arman's voice.",
      "After the tmp files are complete, ask the user whether to promote them to corpus/tone. Do not move or overwrite approved tone files without approval.",
    ],
    corpus_inventory: {
      documents: documents.map((document) => ({
        path: document.relative_path,
        post_number: document.post_number,
        title: document.title,
        subtitle: document.subtitle,
        source_character_count: document.source_character_count,
        source_word_count: document.source_word_count,
        sentence_count: document.sentence_count,
        paragraph_count: document.paragraph_count,
        headings: document.headings,
      })),
    },
    mechanical_stats: buildCorpusStats(documents),
    pattern_banks: {
      frequent_terms: buildTermCounts(combinedWords),
      repeated_phrases: buildRepeatedPhrases(combinedWords),
      representative_sentences: pickRepresentativeSentences(documents),
      representative_openings: pickOpenings(documents),
      representative_closings: pickClosings(documents),
    },
    draft_tonality_json_shape: {
      schema_version: "1.0",
      generated_from: [
        {
          path: "TODO: source file path",
          title: "TODO: source title",
          source_type: "substack_post",
          notes: "TODO: what this source contributes to the tone profile",
        },
      ],
      voice_profile: {
        summary: "TODO: agent-authored interpretation",
        point_of_view: "TODO",
        audience_relationship: "TODO",
        core_personality: ["TODO"],
        authority_basis: ["TODO"],
        emotional_center: ["TODO"],
      },
      tone_axes: {
        warmth: "TODO",
        formality: "TODO",
        confidence: "TODO",
        pace: "TODO",
        specificity: "TODO",
        abstraction: "TODO",
        provocation: "TODO",
      },
      style_rules: {
        sentence_rhythm: "TODO",
        paragraph_rhythm: "TODO",
        punctuation: ["TODO"],
        word_choice: ["TODO"],
        rhetorical_moves: ["TODO"],
        avoid: ["TODO"],
      },
      source_backed_examples: [
        {
          quote_or_phrase: "TODO: short source-backed example",
          source_path: "TODO",
          pattern: "TODO: what the example teaches",
        },
      ],
      drafting_guidance: {
        titles: ["TODO"],
        openings: ["TODO"],
        body: ["TODO"],
        closings: ["TODO"],
        do: ["TODO"],
        avoid: ["TODO"],
      },
    },
    draft_tonality_text_sections: [
      "Corpus Tonality Guide",
      "Generated From",
      "Voice Profile",
      "Tone Axes",
      "Style Rules",
      "Source-Backed Examples",
      "Drafting Guidance",
    ],
  };
}

function renderTemplateText(template) {
  const lines = [
    "# Tonality Draft",
    "",
    "This is a temporary draft file, not the approved tone guide yet.",
    "",
    "## Agent Instructions",
  ];

  for (const instruction of template.agent_instructions) {
    lines.push(`- ${instruction}`);
  }

  lines.push(
    "",
    "## Source Policy",
    `Input: ${template.source_policy.input_dir}`,
    `Temporary output: ${template.source_policy.tmp_output_dir}`,
    `Approved output after user approval: ${template.source_policy.final_output_dir}`,
    "",
    "## Source Files",
  );

  for (const document of template.corpus_inventory.documents) {
    const subtitle = document.subtitle ? ` | ${document.subtitle}` : "";
    lines.push(`- ${document.path}`);
    lines.push(`  Title: ${document.title}${subtitle}`);
    lines.push(`  Words: ${document.source_word_count}`);
    lines.push(`  Sentences: ${document.sentence_count}`);
    lines.push(`  Paragraphs: ${document.paragraph_count}`);

    if (document.headings.length > 0) {
      lines.push("  Headings:");
      for (const heading of document.headings.slice(0, 8)) {
        lines.push(`  - ${heading}`);
      }
    }
  }

  const stats = template.mechanical_stats;
  lines.push(
    "",
    "## Mechanical Stats",
    `- Documents: ${stats.document_count}`,
    `- Words: ${stats.total_words}`,
    `- Sentences: ${stats.total_sentences}`,
    `- Paragraphs: ${stats.total_paragraphs}`,
    `- Average sentence length: ${stats.average_sentence_words} words`,
    `- Median sentence length: ${stats.median_sentence_words} words`,
    `- Average paragraph length: ${stats.average_paragraph_words} words`,
    `- Median paragraph length: ${stats.median_paragraph_words} words`,
    `- Dominant point of view: ${stats.point_of_view.dominant}`,
    `- Contractions: ${stats.contractions_count}`,
    "",
    "## Punctuation Counts",
  );

  for (const [name, count] of Object.entries(stats.punctuation_counts)) {
    lines.push(`- ${name}: ${count}`);
  }

  lines.push("", "## Title Style");
  for (const [name, value] of Object.entries(stats.title_style)) {
    if (name === "sample_titles") {
      continue;
    }
    lines.push(`- ${name}: ${value}`);
  }

  lines.push("", "## Frequent Terms");
  for (const item of template.pattern_banks.frequent_terms.slice(0, 40)) {
    lines.push(`- ${item.term}: ${item.count}`);
  }

  lines.push("", "## Repeated Phrases");
  for (const item of template.pattern_banks.repeated_phrases.slice(0, 40)) {
    lines.push(`- ${item.phrase}: ${item.count}`);
  }

  lines.push("", "## Representative Sentences");
  for (const item of template.pattern_banks.representative_sentences.slice(0, 40)) {
    lines.push(`- ${item.text} (${item.source_path})`);
  }

  lines.push(
    "",
    "## Draft Tonality JSON Shape",
    "",
    "The agent should fill `corpus/tmp/tonality.json` using this shape:",
    "",
    "```json",
    JSON.stringify(template.draft_tonality_json_shape, null, 2),
    "```",
    "",
    "## Draft Tonality Text Sections",
    "",
    "The agent should fill `corpus/tmp/tonality.txt` with these sections:",
  );

  for (const section of template.draft_tonality_text_sections) {
    lines.push(`- ${section}`);
  }

  lines.push(
    "",
    "## Promotion",
    "",
    "After these tmp files are complete, ask the user whether to move them to `corpus/tone/tonality.json` and `corpus/tone/tonality.txt`.",
  );

  lines.push("");
  return lines.join("\n");
}

function writeTemplateFiles(template) {
  mkdirSync(tmpDir, { recursive: true });

  const jsonPath = path.join(tmpDir, "tonality.json");
  const textPath = path.join(tmpDir, "tonality.txt");

  writeFileSync(jsonPath, `${JSON.stringify(template, null, 2)}\n`);
  writeFileSync(textPath, renderTemplateText(template));

  return { jsonPath, textPath };
}

function run() {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.includes("-h")) {
    console.log(usage());
    return;
  }

  if (args.length > 0) {
    fail("This script does not accept input paths. Put source Markdown files in substack.");
  }

  const documents = readCorpusDocuments();
  const template = buildTemplateJson(documents);
  const { jsonPath, textPath } = writeTemplateFiles(template);

  console.log(`Read ${documents.length} Substack post(s) from ${relativeToWorkspace(inputDir)}.`);
  console.log(`Wrote ${relativeToWorkspace(jsonPath)}`);
  console.log(`Wrote ${relativeToWorkspace(textPath)}`);
  console.log("Next: have the AI agent fill corpus/tmp/tonality.*.");
  console.log("After review, ask before promoting tmp files to corpus/tone.");
}

run();
