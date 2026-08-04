This housekeeping file is the same for every Fountain skill. It is enough to read it once per session.

## Preferences

Preferences are the Fountain-skills-related user preferences.
They are the ONLY store for user data that later sessions need.

You MUST load the preferences with the Project API of skill fountain-api at the start of each session.
When the user gives a new preference, you MUST record it with the Project API in the same turn.
You MUST be succinct.
You MUST NOT keep a local copy for a later session.

Preferences are stored as Markdown.
It MUST NOT have frontmatter.

### H2 (##) headings

You MUST use only these headings:

- Narratives - stories and angles that the user wants for clips and posts.
- Editorial - tone, structure, and rules for what to make and when to publish it.
- Captions - caption style, e.g. font, position, and case.
- Other - all other preferences.

## Fountain assets

If a local file system is available, you MUST store Fountain-related assets in `fountain`:

```
your-project
└───fountain
    │   LOG.md // daily log, optional
    └───outputs // ephemeral outputs
```

You MUST keep your work as stateless as possible.
If data is available from an API, you MUST load it from the API, and you MUST NOT keep a local copy.

### LOG.md

You MUST keep this if a local file system is available.
It can help with debugging for yourself, the user, and Fountain support.

When you use Fountain skills, record what you do in this file after each turn.
You MUST NOT read this file in full, just the latest 7 days at the end of the file.

#### H2 (##) headings

MUST follow `## YYYY-MM-DD` format.
The oldest day MUST be first.

#### Body

Under today's heading, record one Markdown list item at the end of the turn.
This MUST include your actions, as well as new findings and failures if any.
You MUST be succinct.

### Outputs

Outputs are ephemeral.
You MUST NOT make an output for a later session to read.

## Fountain API

Skill fountain-api is the ONLY way to interact with the Fountain API.
