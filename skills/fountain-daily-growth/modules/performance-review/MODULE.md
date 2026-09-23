---
name: performance-review
description: Read yesterday's posts and their numbers fresh from the API, and write the durable lessons.
---

## Overview

This module turns the results of yesterday's posts into instructions for the next runs.
It loads the recent posts and their engagement fresh from the API.
It compares each post against the show's own baseline.
It reads the user's decisions from the post metadata.
It writes the lessons that stay true beyond today into the preferences.
The posts keep the record of what happened, and the preferences keep what later runs remember.

## Input

- `show` - the show the loop runs for.
- The show's recent posts, listed via the Social API, each with its `SocialPostStats`.

## Output

- Updated Editorial, Narratives and Reporting sections of the preferences.
- The numbers, the diagnosis, the warnings, and the ids that the clip cards link by, for the report
  that skill **fountain-reports** builds. The caller chooses which report carries them.

## Requirements

- Fountain API.
- Skill **fountain-reports**.

## Process

1. List the show's recent posts via the Social API.
   The last 14 days is enough.
   Each post has its `SocialPostStats`, and Fountain refreshes them.
   So the list gives all the data, and there is nothing to ask for post by post.
   Treat a published post with no stats as a post that the platform has not reported yet.
   Never treat it as a post that no one saw.
   Leave it out of the totals of step 2 and the baseline of step 3.
   This is because its zero is not a real result, and that zero pulls both down.
2. For each platform, total these values over the last 7 days: the count of published posts, the
   reactions, the engagement rate, and the views.
   Reactions are likes plus comments.
   The engagement rate is reactions divided by views.
   Name the span you counted, e.g. "Last 7 days", because the clips below cover a shorter one.
   Step 1 loads more than these 7 days, because the baseline of step 3 needs more posts than a week holds.
3. Compute the baseline from these posts alone.
   The baseline is the median views, likes, and comments per platform.
   The module computes the baseline each run, so it exists from the first run and needs no history file.
   The module measures each post against the baseline, and the report never shows the baseline.
4. Group the posts by clip on one source key, because no field identifies a clip.
   Sort `source.ids`, then combine them with `source.media`, `source.ts_start` and `source.ts_end`.
   The media value keeps two empty-ID sources with the same span separate.
   A post without `source` cannot join its other channel posts, so report it alone by post id.
   Report each clip that published since the last report, one time only.
   Give every platform that the clip went to, and the total of those platforms.
   The Reporting section of the preferences records where the last report reached.
   When the section records no point, cover the last day, and say that this is the first report.
   The loaded window stays wider than that span, so that the baseline stays valid.
5. Find the posts that clearly beat or missed the baseline, and name the likely cause:
   the hook, the platform fit, the posting time, the clip length, or a saturated topic.
   A lesson from one clip names that clip.
   A lesson that is true across clips names no clip.
   Put both kinds in the lessons list, where the reader reads the day as a whole and not clip by clip.
6. Read the user's decisions from `meta.status` and the timestamps.
   Each of these tells you something: a draft approved fast, a draft edited before approval, and a
   draft left untouched.
   Diff the user's edits to label, title, text, or context.
   These edits are the closest thing to a reason from the user.
   Read the decisions on the posts that arrived since the last report, and not on the whole window.
   This is because an earlier run already wrote the older decisions into the preferences.
7. Write each durable lesson under the matching heading of the preferences.
   Add the date to each lesson, and keep it short.
   When a new lesson contradicts an old entry, revise the old entry.
   Do not append a duplicate.
8. Report a post in `ERROR`, or one whose `meta.scheduled` passed without publishing.
   Such a post is an operational failure to show to the user, and not a weak post to learn from.
   When nothing failed, give no failures, and the report then leaves the section out.
9. Give the numbers, the diagnosis, and the warnings to skill **fountain-reports**.
   The caller decides which preset holds them.
   Skill **fountain-reports** decides how the report reaches the user.
   So this module names neither.
   Also give the project, the show, and the posts by id.
   A clip card needs them, because it links its label to the dashboard and every channel row to its own post.
   Name each platform the way the platform writes its own name - Instagram, X, YouTube.
   Never name it the way the API spells it.
   For a source with an episode id, give the episode and the day it came out.
   The Content API holds both.
   Load each episode one time, however many clips came from it.
   Ask for all the episodes at the same time.
   For another source, give the source label in the post context when it is available.
   Otherwise use `External source`, and omit the source date.
10. At the end of the Reporting section, record where the report reached.
    Record it as the publish time of the newest post that the report covered,
    e.g. `- Reported up to 2026-08-17T16:41Z (AGENT-2026-08-18)`.
    Move this marker only when the report was sent.

## Additional notes

The span is the time that the last report did not cover.
It is never a fixed day.
With a fixed day, a loop that misses a morning would skip that day's clips in both runs.
Then no report would ever show them.
For the same reason, the marker moves only when a report is sent.
A report that failed has covered nothing.

A missing dashboard link is not an operational failure, so it never goes under the warnings.

The whole window gets fresh stats each run.
This is because an older post keeps collecting views.
The module counts the totals and the baseline again from the live numbers.
One list holds the numbers of every post, so a wide window adds no cost.

One-day noise MUST NOT go into the preferences.
"This clip beat the baseline" is noise.
"Question hooks beat statement hooks on X" is a lesson.

The baseline is the show's own recent posts, never a global number.
A show with one post has a weak baseline.
Say so, and do not force a diagnosis.

A rate on few views comes from the small count, and is not a real result.
Do not call a winner or a loser from a rate alone when the post has fewer views than the platform's median.

A lesson about a platform needs posts on that platform that varied.
Compare the publish hours before you write one.
When every post on a platform went out at the same hour, say that instead.
In that case, the effect of the hour and the effect of the platform cannot be told apart.
The times are already on the cards, so the reader can see what the lesson could not separate.

The numbers of a YouTube post are not settled for 72 hours.
The age of the post comes from `meta.published`.
Do not diagnose a YouTube post younger than that.
Do not mark the row either.
The cards show yesterday's clips, so every YouTube row is young.
A mark on all of them tells the reader nothing.

The same guest in two clips a few days apart is a saturated topic.
A saturated topic is one of the causes that step 5 names.
The window holds the posts that show it.

An untouched draft can mean more than one thing.
A rejected candidate and an unseen candidate look the same.
Diagnose a pattern of untouched drafts, not any single one.

A reason that the user already gave at a review is already in the preferences.
Do not re-derive it from the outcomes, and do not write it twice.
