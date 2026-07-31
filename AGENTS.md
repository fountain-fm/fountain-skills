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

### SKILL.md contents

#### Frontmatter

- `name` - skill name (REQUIRED)
- `description` - short description, max 60 chars (REQUIRED)

#### Body

H2 (##) headings:

- Overview - short description of how the skill works, do not repeat `description`, max 500 characters (REQUIRED)
- Input - list of what the skill requires, combination of variables (e.g. `start_time_seconds`) and/or unstructured user input (REQUIRED)
- Output - list of what the skill produces (REQUIRED)
- Housekeepig - "You MUST read HOUSEKEEPING.md", this section is the same in every skill (REQUIRED)
- Requirements - list of software requirements (e.g. python or Fountain API), when relevant you MUST specify version / formula, e.g. default Homebrew ffmpeg lacks features (OPTIONAL)
- Process - list of steps to complete the task, when relevant refer to modules (REQUIRED)
- Additional notes - anything else (OPTIONAL)

You MUST NOT add any other H2 headings

You MUST refer to modules by name (e.g. "module face-detection"). You MUST NOT refer to modules by path (e.g. "modules/face-detection/MODULE.md).
