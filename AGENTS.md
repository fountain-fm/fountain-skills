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
- `description` - short description, max 120 chars (REQUIRED)

### Body

Each line MUST be under 120 chars.
Body MUST be under 100 lines - the shorter the better.

Significant chunks of isolatable logic CAN be exported to a module.

You MUST refer to skills and modules by name (e.g. "module face-detection").
You MUST NOT refer to modules or skills by path (e.g. "modules/face-detection/MODULE.md").

You MUST NOT repeat information that is already in HOUSEKEEPING.md.

#### H2 (##) headings

- Overview (REQUIRED) - short description of how the skill works, do not repeat `description`, max 500 characters
- Input (REQUIRED) - list of what the skill requires: combination of variables (e.g. `clip_count`), API models,
  and/or unstructured user input
- Output (REQUIRED) - list of what the skill produces
- Housekeeping (REQUIRED) - "You MUST read HOUSEKEEPING.md if you haven't already".
  This section is the same in every skill.
- Requirements (OPTIONAL) - list of other skills and software requirements (e.g. skill fountain-api or python).
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
- `description` - short description, max 120 chars (REQUIRED)

### Body

Each line MUST be under 120 chars.
Body MUST be under 100 lines - the shorter the better.

You MUST refer to skills and other modules by name (e.g. "module face-detection").
You MUST NOT refer to skills and other modules by path (e.g. "modules/face-detection/MODULE.md").

#### H2 (##) headings

- Overview (REQUIRED) - short description of how the module works, do not repeat `description`, max 500 characters
- Input (REQUIRED) - list of what the module requires: combination of variables (e.g. `clip_count`), API models,
  and/or unstructured agent input
- Output (REQUIRED) - list of what the module produces
- Requirements (OPTIONAL) - list of skills and software requirements (e.g. skill fountain-api or python).
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

## State

A skill can run on the user's machine, where files are available, or elsewhere, where they are not.
Thus you MUST make each skill as stateless as possible.
If data is available from an API, the skill MUST load it from the API.
The skill MUST NOT keep a local copy of that data for a later session.
A module CAN give a model to another module in the same session.

Outputs are ephemeral.
A skill MUST NOT tell the agent to keep an output for a later session.
A skill MUST NOT tell the agent to read an output of an earlier session.

Fountain-hosted preferences are the ONLY store for data that later sessions need.
The agent loads and updates them with the Project API of skill fountain-api.

## Fountain API

Fountain API docs live at https://fountain.fm/docs.md
The docs have two parts: `## Endpoints` and `## Models`.

Skill fountain-api is the only way to interact with the API.
A skill or module that needs the API MUST list skill fountain-api in Requirements.
It MUST also tell the agent to load skill fountain-api before the first request.
It MUST NOT give instructions about authentication - skill fountain-api owns that.

### Endpoints

You MUST NOT refer to an endpoint, a path, a method, a request body, or a query parameter.
You MUST refer to the API only by its group (Project, Content, Search, People, Vaults, Publishing, Uploads, Social).
E.g., you CAN say "Load the latest episode via Publishing API of skill fountain-api".

Skill fountain-api is the only exception.
It CAN refer to authentication and the structure of the docs.
It still MUST NOT refer to an endpoint.

### Models

Models are the shared vocabulary of the API, and you CAN name them.
A model CAN be an Input or an Output of a skill or a module.

Before you describe a concept, look for it in the Models part of the docs.
If a model is close to the concept, you MUST use that model, and you MUST NOT define your own.
E.g., the source of a clip is a `SocialPostMediaSource`, and never a new object with the same five fields.

You MUST keep the name of the model and the names of its fields, and you MUST NOT rename or re-case them.
You MUST refer to a model by its name, and you MUST NOT restate its fields.
You CAN name a field when you say something that the docs do not.
E.g., "Set `ts_start` a short pause before the first word", or "Drop an episode when `info.video` is absent".

### Your own models

A concept that no model is close to belongs to the skill or the module that introduces it.
Give it a name when a skill or a module passes it on, and define it one time where you introduce it.
E.g., a moment is a group of `TranscriptSearchSegment` less than 30 seconds apart.

Write the name in lowercase prose, so that a reader can tell it from a model.
You MUST NOT give it the name of a model, or a name that is close to one.
Build it from models where you can, rather than copy fields out of them.

### Scripts

A script in a skill MUST NOT call the Fountain API.
The agent makes each request and gives the response to the script.

A script CAN take a model as input and give a model as output.
It MUST name each model that it reads, in its docstring or in its CLI help.
It MUST read only the fields that it uses.

You MUST NOT suggest idiosyncratic ways of interacting with the API.
If something is not working, you MUST investigate and suggest potential solutions before writing the skill.
E.g., if you encounter Cloudflare 1010 block, you MUST report back to us to fix it.

## Repository tooling

Install the tools one time with `npm run setup`.
It installs the npm packages, installs uv with Homebrew, and turns on the git hooks.

The agent hooks run at the end of each turn.
The git pre-commit hook runs the same steps before each commit.
