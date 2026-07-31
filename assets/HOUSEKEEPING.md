This housekeeping file is the same for every Fountain skill. It is enough to read it once per session.

## Fountain assets

You MUST store Fountain-related assets in `fountain`:

```
your-project
└───fountain
    │   LOG.md // daily log
    │   PREFERENCES.md // Fountain-skills-related user preferences
    └───outputs // produced outputs, CAN be nested
```

You MUST always load fountain/PREFERENCES.md into memory.

### LOG.md

When interacting with Fountain skills and/or API, you MUST record what you do in this file after each turn.
This can help with debugging for yourself, the user, and Fountain support.
You MUST NOT read this file in full, just the latest 7 days.

#### H2 (##) headings

MUST follow `## YYYY-MM-DD` format.

#### Body

Under today's heading, record one line at the end of the turn.
This MUST include your actions, as well as new findings and failures if any.

### PREFERENCES.md

When interacting with Fountain skills and/or API, you MUST record user preferences in this file.
This can include posting schedule, captions styles, narratives for clips, etc.
You MUST be succinct.
This can also help with debugging for Fountain support.
