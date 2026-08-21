---
name: queue
description: Work the render queue - find the drafts that wait for media, and render what auto-render allows.
---

## Overview

This module is the consumer end of the drafts-as-queue handoff.
A scheduler on the render machine starts it; the module itself owns no schedule.
Each run asks the Social API one question - which drafts miss their media - filters them by the
auto-render setting, and hands each eligible post to the process of the skill.

## Input

- The Automation section of the preferences: the shows this machine works, and the auto-render setting
  of each.
- Optional: `show`, to work one show instead of all of them.

## Output

- A rendered, attached video on each eligible draft.
- What rendered, what failed, and what remains, said plainly.

## Requirements

- Fountain API.
- Skill **fountain-reports**.

## Process

1. Read the Automation section of the preferences.
   Work every show it names, unless the caller named one.
   On is the default auto-render when a show has no entry.
2. List each show's posts via the Social API, and keep the drafts that miss their media.
   With auto-render off, keep only the ones whose `meta.status` is `APPROVED`.
   With auto-render on, keep them all - rendering a draft the user later rejects wastes only CPU.
3. Run the process of the skill once per post, in the shape its platform needs, and attach the video.
4. Continue past a failed render and finish the rest.
   Record each failure on the post itself: a renderer note in its `context` via the Social API, with
   the reason and the attempt count.
   Mark the note as the renderer's, because `context` is where the user reads why the clip is worth
   making, and remove it when a later run renders the post - a failure that has been fixed is noise
   in front of the user, and it makes a working clip look broken.
   Retry on later runs while the count is under 3.
   At 3, stop retrying - the draft needs a person, not a fourth attempt.
5. When this run attached media and every draft is done or given up, give the batch to skill
   **fountain-reports** as the `clips-waiting` report - one report for the whole batch, the given-up
   drafts under warnings so a failure never hides, delivery decided by the Reporting section.
   Report only on a run that attached something, or every idle poll repeats it.
6. Report the run plainly, and stop - when the next run happens is the machine's schedule, not yours.

## Additional notes

The queue asks per show because the Social API lists posts by their source, and names no wider set.
A show reaches this machine by having an Automation entry, which the first run of the loop writes for it.

Progress lives on the posts themselves: an attached upload is the only "done" mark, so a run that dies
mid-batch loses nothing, and the next run picks up the remainder.
The failure count lives there too, in the renderer note, so it survives any machine and the dashboard
shows the reason beside the post.

A machine that was asleep sends the ready email late rather than never: the first run after waking
drains the queue and then sends it, so no cloud sweeper exists.
