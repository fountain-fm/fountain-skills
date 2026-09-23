---
name: queue
description: Work the render queue - find the drafts that wait for media, and render what auto-render allows.
---

## Overview

This module is the consumer end of the drafts-as-queue handoff.
A scheduler on the render machine starts it.
The module itself owns no schedule.
Each run asks the Social API one question: which drafts do not have their media?
It filters those drafts by the auto-render setting.
Then it gives the eligible posts to the process of the skill.
It gives them all at the same time, because the render of one post tells the next post nothing.

## Input

- The Automation section of the preferences: the shows this machine works, and the auto-render setting
  of each.
- Optional: `show`, to work one show instead of all of them.

## Output

- A rendered, attached video on each eligible draft.
- A plain statement of what rendered, what failed, and what remains.

## Requirements

- Fountain API.
- Skill **fountain-reports**.

## Process

1. Read the Automation section of the preferences.
   Work every show it names, unless the caller named one.
   When a show has no entry, auto-render is on by default.
2. List each show's posts via the Social API, and keep the drafts that do not have their media.
   Also list drafts by status, so that you can see a source with no show id.
   Keep such a source only when its channel or project context assigns it to a show that this machine works.
   When that context cannot name a show, leave the source in the queue, and report what is missing.
   After you join the two lists, remove duplicate posts by post id.
   With auto-render off, keep only the ones whose `meta.status` is `APPROVED`.
   With auto-render on, keep them all.
   Rendering a draft that the user later rejects wastes only CPU.
3. Run module **preflight** one time before any render, because the machine is the same for every post.
   Then share the eligible posts between the workers, and run at most three workers at a time.
   Each worker renders its posts one after another.
   Use one worker for three posts or fewer, because each new worker costs extra before it renders anything.
   Give each worker its posts, the preflight report, and an output folder for each post.
   Let the worker run the process of the skill from module **media** to the attachment.
   The worker makes each video in the shape that the platform of its post needs.
   The posts are independent.
   Each post names its own source, its own span, and its own render.
   So a worker reads no file that another worker writes, and decides nothing about another post.
   Wait for every worker, and read the result of each one.
4. When a worker fails, let it end alone, and let the other workers finish.
   Record each failure on the post itself.
   Write a renderer note in its `context` via the Social API, with the reason and the attempt count.
   Mark the note as the renderer's, because `context` is where the user reads why the clip is worth making.
   Remove the note when a later run renders the post.
   A failure that has been fixed only distracts the user, and it makes a working clip look broken.
   Retry on later runs while the count is under 3.
   At 3, stop retrying, because the draft then needs a person and not a fourth attempt.
5. The user gets the batch one time, when this run attached media and every draft is done or given up.
   With auto-render on, send nothing, and give the caller the drafts that you gave up.
   The day's report waited for these videos, and the caller sends it with those drafts under its warnings.
   With auto-render off, give the batch to skill **fountain-reports** as the `review-posts-simple` report.
   That report says that the renders are ready.
   It puts the given-up drafts under warnings, so that a failure is never hidden.
   Give the label of each source, and its publish date when it is known.
   For a source with an episode id, use the episode.
   Otherwise, use the external video title from `context`.
   Report only on a run that attached something.
   Otherwise, every idle poll repeats the report.
6. Report the run plainly, and stop.
   The schedule of the machine decides when the next run happens, and you do not.

## Additional notes

Three renders at a time do not finish three times faster.
ffmpeg uses every core that it gets, so the renders share those cores and do not add more.
Whisper also uses the same cores.
The gain is in the waiting time.
The reading, the deciding, and the network work of one post now happen while another post encodes.
The encoding itself does not get faster.
Lower the number on a machine with few cores.

Each new worker reads the skill, the modules and its own setup before its first render.
With one worker for each post, that cost comes again for every clip.
On 2026-09-22, three clips on three workers cost about 50% more than the same three clips in one session.
So use more workers only for a long queue, where running three at once saves real time.

The queue asks per show for a source with a show id, because that is the narrowest reliable list.
It also asks by status for YouTube-only and empty `ids`, because those sources cannot match a show filter.
A show comes to this machine when it has an Automation entry.
Skill **fountain-onboarding** writes that entry for the show.

Progress is stored on the posts themselves.
An attached upload is the only "done" mark.
So a run that stops in the middle of a batch loses nothing, and the next run does the rest.
The failure count is also stored there, in the renderer note.
So the count is kept when the machine changes, and the dashboard shows the reason beside the post.

A machine that was asleep sends the ready email late, but it still sends it.
The first run after the machine wakes empties the queue, and then sends the email.
So no cloud sweeper exists.
