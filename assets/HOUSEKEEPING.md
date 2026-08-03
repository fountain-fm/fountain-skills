This housekeeping file is the same for every Fountain skill. It is enough to read it once per session.

## Fountain assets

You MUST store Fountain-related assets in `fountain`:

```
your-project
└───fountain
    │   LOG.md // daily log
    │   PREFERENCES.md // Fountain-skills-related user preferences
    └───outputs // ephemeral outputs
```

You MUST always load fountain/PREFERENCES.md into memory.

You MUST keep your work as stateless as possible.
If data is available from an API, you MUST load it from the API, and you MUST NOT keep a local copy.

### LOG.md

When interacting with Fountain skills and/or API, you MUST record what you do in this file after each turn.
This can help with debugging for yourself, the user, and Fountain support.
You MUST NOT read this file in full, just the latest 7 days.

#### H2 (##) headings

MUST follow `## YYYY-MM-DD` format.

#### Body

Under today's heading, record one Markdown list item at the end of the turn.
This MUST include your actions, as well as new findings and failures if any.
You MUST be succinct.

### PREFERENCES.md

When interacting with Fountain skills, you MUST record user preferences in this file.
You MUST be succinct.
This is the ONLY file that keeps data for later sessions.
This can also help with debugging for Fountain support.

#### H2 (##) headings

You MUST use only these headings:

- Narratives - stories and angles that the user wants for clips and posts.
- Editorial - tone, structure, and rules for what to make and when to publish it.
- Captions - caption style, e.g. font, position, and case.
- Other - all other preferences.

### Outputs

Outputs are ephemeral.
You MUST NOT make an output for a later session to read.

## Fountain API

Skill fountain-api is the ONLY way to interact with the Fountain API.
