# Fountain Skills

Skills that turn a podcast archive into social clips: find the moments, cut and render them, then
report on how they did.
Each skill is one stage that hands its output to the next, so no skill has to know the whole chain.

- **fountain-api** - the only way to reach the Fountain API.
- **fountain-daily-growth** - reads yesterday's numbers and today's news, and briefs the chain.
- **fountain-clip-finder** - finds the moments, writes the copy, and opens a draft post for each clip.
- **fountain-clip-producer** - renders a draft into a finished video and attaches it to the post.
- **fountain-reports** - builds the reports the user reads, and sends them.

AGENTS.md says how a skill is written, and the HOUSEKEEPING.md inside each one holds the rules they share.
Install the tooling with `npm run setup`.

## Render runner

Rendering is the one stage of the daily chain that runs on a machine you own, not in the cloud.
No skill owns a schedule, so the machine does: give it a job (launchd, cron, or a Claude Code
scheduled task) that starts the agent every 15 minutes with a prompt such as:

```text
Work the render queue with fountain-clip-producer.
```

Module **queue** of skill **fountain-clip-producer** does the rest: it reads the Automation section of
the preferences for the shows this machine works and their auto-render settings, renders the drafts
those settings allow, and attaches each video to its post.
One job covers every show - name a show in the prompt only to work that one.
A machine that sleeps just resumes late - progress lives on the posts, so nothing is lost mid-batch.
