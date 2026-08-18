# Fountain Skills

Skills that make an agent useful to a podcaster: find the clip, render it, report on it, and run the
day.
Every skill works on the Fountain API, so it needs an account at [fountain.fm](https://fountain.fm).

## Install

### MCP

Connect `https://api.fountain.fm/v1/mcp` to your client and sign in.
The `fountain-skills` tool serves the manifest and the files; the `fountain-api` tool makes the
requests, so no API key is involved.

### Skills CLI

```bash
claude plugin marketplace add fountain-fm/fountain-skills
claude plugin install fountain@fountain
```

The plugin carries the four skills and the Fountain MCP server.
Run `/mcp` once to sign in.

Without the MCP server, the skills fall back to HTTP: make a project API key at
[fountain.fm/studio/api](https://fountain.fm/studio/api) and put it in `.env` as `FOUNTAIN_API_KEY`.

## The skills

| Skill                    | Job                                                                           |
| ------------------------ | ----------------------------------------------------------------------------- |
| `fountain-clip-finder`   | Search the transcripts, score the moments, write the copy, open a draft post. |
| `fountain-clip-producer` | Cut the draft into a finished video with framing, captions, and overlays.     |
| `fountain-daily-growth`  | Read yesterday's numbers and today's news, then brief the clip finder.        |
| `fountain-reports`       | Compose the reports the user reads, and email or print them.                  |

Each skill ships `HOUSEKEEPING.md`, the rules that hold across all of them.
Read it once per session.

## Develop

```bash
npm run setup
npm run check
```

`AGENTS.md` holds the rules for writing a skill.
`assets/SCHEMA.json` is generated: the pre-commit hook rebuilds it from the frontmatter of each
`SKILL.md` and `MODULE.md`.
