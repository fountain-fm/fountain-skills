# Fountain Skills

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
