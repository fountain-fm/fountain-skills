# Fountain Skills

Your job is to write Fountain Skills for agents.
These skills use Fountain API, our own learnings, and tools like ffmpeg.

## Writing style

You MUST write in ASD-STE100 Simplified Technical English.

## Markdown

Each sentence MUST be on a different line.

```md
Sentence 1.
Sentence 2.

- Item 1.
  Item 1 continued.
- Item 2.
```

## Skill structure

```
fountain-skills
└───skills
    └───fountain-abc // skill name
        │   SKILL.md // skill
        │   HOUSEKEEPING.md // rules, copy-pasted with a script
        ├───scripts // skill-wide scripts
        │       def.py
        ├───assets // skill-wide non-script assets
        │       example-ghi.srt
        └───modules // parts of a skill
            └───jkl // module name
                │   MODULE.md // module
                ├───scripts // module-wide scripts
                │       mno.py
                └───assets // module-wide non-script assets
                        template-pqr.json
```

### File names

File names MUST be in kebab-case.extension, except SKILL.md and MODULE.md.

Skill names MUST start with `fountain-`.

## SKILL.md

### Frontmatter

- `name` - skill name (REQUIRED)
- `description` - short description, max 60 chars (REQUIRED)

### Body

Each line MUST be under 120 chars.
Body MUST be under 100 lines - the shorter the better.

Significant chunks of isolatable logic CAN be exported to a module.

You MUST refer to skills and modules by name (e.g. "module face-detection").
You MUST NOT refer to modules or skills by path (e.g. "modules/face-detection/MODULE.md").

You MUST NOT repeat information that is already in assets/HOUSEKEEPING.md.

#### H2 (##) headings

- Overview (REQUIRED) - short description of how the skill works, do not repeat `description`, max 500 characters
- Input (REQUIRED) - list of what the skill requires: combination of variables (e.g. `start_time_seconds`) and/or unstructured user input
- Output (REQUIRED) - list of what the skill produces
- Housekeeping (REQUIRED) - "You MUST read HOUSEKEEPING.md if you haven't already".
  This section is the same in every skill.
- Requirements (OPTIONAL) - list of other skills and software requirements (e.g. python or Fountain API).
  When relevant you MUST specify version / formula, e.g. default Homebrew ffmpeg lacks features.
  Modules' requirements MUST be included here.
- Process (REQUIRED) - list of steps to complete the task, when relevant refer to modules or other skills.
  Steps and the usage of certain skills and modules can be optional.
  You MUST NOT overdescribe edge cases, failure modes, etc. here - use "Additional notes" for that.
- Additional notes (OPTIONAL) - anything else

You MUST NOT add any other H2 headings.

## MODULE.md

Module is a mini skill - an isolatable chunk of skill logic.

### Frontmatter

- `name` - module name (REQUIRED)
- `description` - short description, max 60 chars (REQUIRED)

### Body

Each line MUST be under 120 chars.
Body MUST be under 100 lines - the shorter the better.

You MUST refer to skills and other modules by name (e.g. "module face-detection").
You MUST NOT refer to skills and other modules by path (e.g. "modules/face-detection/MODULE.md").

#### H2 (##) headings

- Overview (REQUIRED) - short description of how the module works, do not repeat `description`, max 500 characters
- Input (REQUIRED) - list of what the module requires: combination of variables (e.g. `start_time_seconds`)
  and/or unstructured agent input
- Output (REQUIRED) - list of what the module produces
- Requirements (OPTIONAL) - list of skills and software requirements (e.g. python or Fountain API).
  When relevant you MUST specify version / formula, e.g. default Homebrew ffmpeg lacks features.
- Process (REQUIRED) - list of steps to complete the task, when relevant refer to other modules or skills.
  Steps and the usage of certain skills and modules can be optional.
  You MUST NOT overdescribe edge cases, failure modes, etc. here - use "Additional notes" for that.
- Additional notes (OPTIONAL) - anything else

You MUST NOT add any other H2 headings.

## Code conventions

You MUST use snake_case for variables and SCREAMING_SNAKE_CASE for constants.
Aside from variable naming, you MUST use each programming language's standard variable naming practice.

You MUST write robust, easy-to-read code.
You MUST use comments sparingly, only to explain separate blocks of code and non-obvious logic.
In ffmpeg commands, you MUST use comments to explain every argument.
All comments MUST be at most one line and 120 chars.

## Fountain API

Fountain API docs live at https://fountain.fm/docs.md

Each skill will have loaded HOUSEKEEPING.md and know how to use the API.
In the skills, you MUST NOT refer to individual endpoints, request shapes, or response shapes.
You MUST refer to the API only by its group (Project, Content, Search, People, Vaults, Publishing, Uploads, Social).
E.g., you CAN say "Before creating an episode, load the latest episode via Fountain Publishing API".

You MUST NOT write scripts for interacting with the Fountain API.
You MUST NOT suggest idiosyncratic ways of interacting with the API.
If something is not working, you MUST investigate and suggest potential solutions before writing the skill.
E.g., if you encounter Cloudflare 1010 block, you MUST report back to us to fix it.

## Repository tooling

Install the tools one time with `npm run setup`.
It installs the npm packages, installs uv with Homebrew, and turns on the git hooks.

Dependencies:

- Node.js 22 or later, with npm.
  It runs prettier and prettier-plugin-sh, which format Markdown, JSON, YAML, and shell scripts.
- uv.
  It runs ruff 0.16.1, which formats and lints Python.

The agent hooks run at the end of each turn.
Claude Code also formats each file directly after it writes the file.
The git pre-commit hook runs the same steps before each commit.
