---
name: queue
description: Work the render queue - find the drafts that wait for media, and render what auto-render allows.
---

## Overview

This module is the consumer end of the drafts-as-queue handoff.
A scheduler on the render machine starts it; the module itself owns no schedule and keeps no state.
Each run asks the Social API one question - which drafts miss their media - filters them by the
auto-render setting, and hands each eligible post to the process of the skill.

## Input

- `show` - the show whose queue this machine works.
- The auto-render setting, from the Other section of the preferences.

## Output

- A rendered, attached video on each eligible draft.
- A run report, said plainly: what rendered, what failed, what remains.

## Requirements

- Skill **fountain-api**.
- Skill **fountain-reports**.

## Process

1. Load skill **fountain-api** and read the auto-render setting from the Other section of the preferences.
   Off is the default when the show has no entry.
2. List the show's posts via the Social API, and keep the drafts that miss their media.
   With auto-render off, keep only the ones whose `meta.status` is `APPROVED`.
   With auto-render on, keep them all - rendering a draft the operator later rejects wastes only CPU.
3. Run the process of the skill once per post, in the shape its platform needs, and attach the video.
4. Continue past a failed render: report it, leave its draft for the next run, and finish the rest.
5. When this run attached media and no draft now waits, send the `daily-pack` preset of skill
   **fountain-reports** as email - one email for the whole batch, with the dashboard review link.
   Send it only on a run that attached something, or every idle poll repeats the email.
6. Report the run plainly, and stop - when the next run happens is the machine's schedule, not yours.

## Additional notes

Progress lives on the posts themselves: an attached upload is the only "done" mark, so a run that dies
mid-batch loses nothing, and the next run picks up the remainder.

The transcript of an episode can be missing on the first clip of a show.
Generating it is metered, and the skill says the cost when it queues the job.

A machine that was asleep sends the ready email late rather than never: the first run after waking
drains the queue and then sends it, so no cloud sweeper exists.
