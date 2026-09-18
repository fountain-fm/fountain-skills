---
name: queue
description: Work the render queue - find the drafts that wait for media, and render what auto-render allows.
---

## Overview

This module is the consumer end of the drafts-as-queue handoff.
A scheduler on the render machine starts it; the module itself owns no schedule.
Each run asks the Social API one question - which drafts miss their media - filters them by the
auto-render setting, and hands the eligible posts to the process of the skill.
It hands them over together, because one post's render tells the next post nothing.

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
   Also list drafts by status so that a source with no show id is visible.
   Keep such a source only when its channel or project context assigns it to a show that this machine works.
   Leave it in the queue and report what is missing when that context cannot name a show.
   Remove duplicate posts by post id after the two lists are joined.
   With auto-render off, keep only the ones whose `meta.status` is `APPROVED`.
   With auto-render on, keep them all - rendering a draft the user later rejects wastes only CPU.
3. Run module **preflight** one time before any render, because the machine is the same for every post.
   Then dispatch the eligible posts together, one worker for each post, and at most three at a time.
   Give each worker the post, the preflight report, and its own output folder, and let it run the
   process of the skill from module **media** to the attachment, in the shape its platform needs.
   The posts are independent - each names its own source, its own span and its own render - so a
   worker reads no file another worker writes, and decides nothing about another post.
   Wait for every worker, and read the result of each one.
4. Let a failed worker end alone, and let the rest finish.
   Record each failure on the post itself: a renderer note in its `context` via the Social API, with
   the reason and the attempt count.
   Mark the note as the renderer's, because `context` is where the user reads why the clip is worth
   making, and remove it when a later run renders the post - a failure that has been fixed is noise
   in front of the user, and it makes a working clip look broken.
   Retry on later runs while the count is under 3.
   At 3, stop retrying - the draft needs a person, not a fourth attempt.
5. When this run gave up a draft, give the batch to skill **fountain-reports** as the
   `review-posts-simple` report - one report for the whole batch, the given-up drafts under warnings so
   a failure never hides, delivery decided by the Reporting section.
   Send it for a batch that rendered cleanly only when the Reporting section asks for one, because the
   report that named these drafts already reached the user, and a second mail of the same clips is noise.
   Give each source label and its publish date when known.
   Use the episode for a source with an episode id, and use the external video title from `context` otherwise.
   Report only on a run that attached something, or every idle poll repeats it.
6. Report the run plainly, and stop - when the next run happens is the machine's schedule, not yours.

## Additional notes

Three renders at a time do not finish three times faster.
ffmpeg uses every core it is given, so the renders share those cores rather than add to them, and
whisper competes for the same ones.
The win is the waiting - the reading, the deciding and the network of one post now happen while
another post encodes - and the encoding itself gets no faster.
Lower the number on a machine with few cores.

The queue asks per show for a source with a show id, because that is the narrowest reliable list.
It also asks by status for YouTube-only and empty `ids`, because those sources cannot match a show filter.
A show reaches this machine by having an Automation entry, which skill **fountain-onboarding** writes for it.

Progress lives on the posts themselves: an attached upload is the only "done" mark, so a run that dies
mid-batch loses nothing, and the next run picks up the remainder.
The failure count lives there too, in the renderer note, so it survives any machine and the dashboard
shows the reason beside the post.

A machine that was asleep sends the ready email late rather than never: the first run after waking
drains the queue and then sends it, so no cloud sweeper exists.
