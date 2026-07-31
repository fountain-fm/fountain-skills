# Fountain Skills

Your job is to write Fountain Skills for agents.
These skills utilize Fountain API, our own learnings, and tools like ffmpeg.

## Writing style

You MUST write in ASD-STE100 Simplified Technical English

## Skill structure

```
fountain-skills
└───skills
    └───fountain-abc // skill name
        │   SKILL.md // skill
        │   HOUSEKEEPING.md // rules, copy-pasted with a script
        └───scripts // skill-wide scripts
        │   | def.py
        └───assets // skill-wide non-script assets
        │   | example-ghi.srt
        └───modules // parts of a skill
            │ MODULE.md // module
            └───scripts // module-wide scripts
            │   | jkl.py
            └───assets // module-wide non-script assets
                | template-mno.json
```

### File names

Files names MUST be in kebab-case.extension, except SKILL.md and MODULE.md

Skill names MUST start with `fountain-`

## SKILL.md contents

### Frontmatter

- `name` - skill name (REQUIRED)
- `description` - short description, max 60 chars (REQUIRED)

### Body

MUST be under 100 lines - the shorter the better. Significant chunks of isolatable logic can be exported to a module.

You MUST refer to skills and modules by name (e.g. "module face-detection"). You MUST NOT refer to modules or skills by path (e.g. "modules/face-detection/MODULE.md).

#### H2 (##) headings

- Overview (REQUIRED) - short description of how the skill works, do not repeat `description`, max 500 characters
- Input (REQUIRED) - list of what the skill requires: combination of variables (e.g. `start_time_seconds`) and/or unstructured user input
- Output (REQUIRED) - list of what the skill produces
- Housekeeping (REQUIRED) - "You MUST read HOUSEKEEPING.md if you haven't already", this section is the same in every skill
- Requirements (OPTIONAL) - list of other skills and software requirements (e.g. python or Fountain API). When relevant you MUST specify version / formula, e.g. default Homebrew ffmpeg lacks features. Modules' requirements MUST be included here.
- Process (REQUIRED) - list of steps to complete the task, when relevant refer to modules or other skills. Steps and the usage of certain skills and modules can be optional
- Additional notes (OPTIONAL) - anything else

You MUST NOT add any other H2 headings

## MODULE.md contents

### Frontmatter

- `name` - module name (REQUIRED)
- `description` - short description, max 60 chars (REQUIRED)

### Body

MUST be under 100 lines - the shorter the better.

You MUST refer to skills and other modules by name (e.g. "module face-detection"). You MUST NOT refer to skills and other modules by path (e.g. "modules/face-detection/MODULE.md).

#### H2 (##) headings

- Overview (REQUIRED) - short description of how the module works, do not repeat `description`, max 500 characters
- Input (REQUIRED) - list of what the module requires: combination of variables (e.g. `start_time_seconds`) and/or unstructured agent input
- Output (REQUIRED) - list of what the module produces
- Requirements (OPTIONAL) - list of skills and software requirements (e.g. python or Fountain API). When relevant you MUST specify version / formula, e.g. default Homebrew ffmpeg lacks features.
- Process (REQUIRED) - list of steps to complete the task, when relevant refer to other modules or skills
- Additional notes (OPTIONAL) - anything else

You MUST NOT add any other H2 headings

## Code conventions

You MUST use snake_case for variables and SCREAMING_SNAKE_CASE for constants.

You MUST use each programming language's standard variable naming pactise.
