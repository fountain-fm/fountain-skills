import fs from "node:fs";
import { execFileSync } from "node:child_process";

const MAX_BULLETS = 5;
const MIN_BULLETS = 1;
const MAX_BULLET_LENGTH = 100;
const MAX_TITLE_LENGTH = 72;
const SUMMARY_HEADING = "## Summary";

function readArgs(argv) {
  const args = { file: undefined, pr: undefined, title: undefined };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--pr") args.pr = argv[i++ + 1];
    else if (argv[i] === "--title") args.title = argv[i++ + 1];
    else if (!argv[i].startsWith("--")) args.file = argv[i];
  }
  return args;
}

function loadFromGitHub(number) {
  const raw = execFileSync("gh", ["pr", "view", number, "--json", "title,body"], { encoding: "utf8" });
  return JSON.parse(raw);
}

function loadInput(args) {
  if (args.pr) return loadFromGitHub(args.pr);
  const body = args.file ? fs.readFileSync(args.file, "utf8") : fs.readFileSync(0, "utf8");
  return { title: args.title, body };
}

function displayLength(bullet) {
  return bullet
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/[`*_]/g, "")
    .trim().length;
}

function lintTitle(title, issues) {
  if (title === undefined) return;
  const trimmed = title.trim();
  if (trimmed === "") issues.push("title must not be empty");
  if (trimmed.length > MAX_TITLE_LENGTH)
    issues.push(`title is ${trimmed.length} characters; keep it under ${MAX_TITLE_LENGTH}`);
  if (trimmed.endsWith(".")) issues.push("title must not end with a full stop");
  if (/^(wip\b|draft\b)/i.test(trimmed))
    issues.push('title must not start with "WIP" or "Draft"; use a draft pull request instead');
}

function lintBody(rawBody, issues) {
  if (rawBody.includes("<!--")) {
    issues.push("description still contains template comments; delete every <!-- ... --> block");
  }

  const body = rawBody.replace(/<!--[\s\S]*?(-->|$)/g, "");
  const lines = body.replace(/\r\n/g, "\n").split("\n");

  if (lines.every((line) => line.trim() === "")) {
    issues.push(`description is empty; start it with "${SUMMARY_HEADING}" and 1-${MAX_BULLETS} bullets`);
    return;
  }

  const start = lines.findIndex((line) => line.trim() !== "");
  if (lines[start].trim() !== SUMMARY_HEADING) {
    issues.push(`description must start with "${SUMMARY_HEADING}"`);
    return;
  }

  const detailsStart = lines.findIndex((line) => line.trim().toLowerCase().startsWith("<details"));
  const summary = lines.slice(start + 1, detailsStart === -1 ? lines.length : detailsStart);

  const bullets = [];
  for (const line of summary) {
    const trimmed = line.trim();
    if (trimmed === "") continue;
    if (trimmed === "-") continue;
    if (!/^- \S/.test(line)) {
      issues.push(`summary must be bullets only, one per line; found "${trimmed.slice(0, 60)}"`);
      continue;
    }
    bullets.push(trimmed.slice(2));
  }

  if (bullets.length < MIN_BULLETS) issues.push("summary needs at least one bullet");
  if (bullets.length > MAX_BULLETS) issues.push(`summary has ${bullets.length} bullets; keep it to ${MAX_BULLETS}`);

  for (const bullet of bullets) {
    const length = displayLength(bullet);
    if (length > MAX_BULLET_LENGTH) {
      issues.push(`bullet is ${length} characters; keep it under ${MAX_BULLET_LENGTH}: "${bullet.slice(0, 60)}..."`);
    }
  }

  if (detailsStart === -1) return;

  const detailsEnd = lines.findIndex(
    (line, index) => index >= detailsStart && line.trim().toLowerCase() === "</details>",
  );
  if (detailsEnd === -1) {
    issues.push("<details> block is never closed with </details>");
    return;
  }

  const inner = lines
    .slice(detailsStart + 1, detailsEnd)
    .filter((line) => line.trim() !== "" && !line.trim().toLowerCase().startsWith("<summary"));
  if (inner.length === 0) issues.push("the <details> block is empty; delete it");

  const trailing = lines.slice(detailsEnd + 1).filter((line) => line.trim() !== "");
  if (trailing.length > 0) {
    issues.push("everything after the summary must live inside the <details> block");
  }
}

const args = readArgs(process.argv.slice(2));
const { title, body } = loadInput(args);
const issues = [];

lintTitle(title, issues);
lintBody(body ?? "", issues);

if (issues.length > 0) {
  console.error("Pull request description lint failed:\n");
  for (const issue of issues) console.error(`- ${issue}`);
  console.error("\nExpected shape - see .github/pull_request_template.md:\n");
  console.error("  ## Summary\n");
  console.error("  - Drop `axios`; the fetch wrapper replaced it");
  console.error("  - Cache the show query so the dashboard stops refetching on every tab switch\n");
  console.error("  <details>");
  console.error("  <summary>Details</summary>\n");
  console.error("  Trade-offs, migration steps, screenshots, test notes. Omit when the summary is enough.\n");
  console.error("  </details>");
  process.exit(1);
}

console.log("Pull request description lint passed.");
