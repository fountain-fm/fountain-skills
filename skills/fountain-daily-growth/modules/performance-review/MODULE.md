---
name: performance-review
description: Read yesterday's posts and their numbers fresh from the API, and write the durable lessons.
---

## Overview

This module turns yesterday's outcomes into tomorrow's instructions.
It loads the recent posts and their engagement fresh from the API, compares each post against the show's
own baseline, reads the user's decisions from the post metadata, and writes what holds beyond today
into the preferences.
The posts are the record, and the preferences are the memory.

## Input

- `show` - the show the loop runs for.
- The show's recent posts, listed via the Social API, each carrying its `SocialPostStats`.

## Output

- Updated Editorial, Narratives and Reporting sections of the preferences.
- The `performance` report of skill **fountain-reports**: the numbers, the diagnosis, the warnings,
  and the ids that its clip cards link by.

## Requirements

- Fountain API.
- Skill **fountain-reports**.

## Process

1. List the show's recent posts via the Social API.
   The last 14 days is enough.
   Each post carries its `SocialPostStats`, which Fountain refreshes, so the list is the whole read and
   there is nothing to ask for post by post.
   Treat a published post with no stats as one the platform has not answered for yet, and never as a
   post that no one saw.
2. Total each platform over the last 7 days: the published posts counted, the reactions, the
   engagement rate, and the views.
   Reactions are likes plus comments, and the engagement rate is reactions divided by views.
   Name the span you counted, e.g. "Last 7 days", because the clips below cover a shorter one.
   The load is wider than this, because the baseline of step 3 wants more posts than a week holds.
3. Compute the baseline from these posts alone: the median views, likes, and comments per platform.
   The baseline is computed each run, so it exists from the first run and needs no history file.
   It is what a post is measured against, and the report never shows it.
4. Group the posts by clip on `source.ids` with `source.ts_start` and `source.ts_end`, because no field
   identifies a clip.
   Report the clips that published since the last report, each one time, with every platform it went to
   and the total of those platforms.
   The Reporting section of the preferences records where the last report reached.
   Cover the last day when it records none, and say that this is the first one.
   The window stays wider than that span so that the baseline holds.
5. Find the posts that clearly beat or missed the baseline, and name the likely cause:
   the hook, the platform fit, the posting time, the clip length, or a saturated topic.
   A lesson from one clip names that clip, and a lesson that holds across clips names none.
   Both go in the lessons list, where the reader reads the day together rather than clip by clip.
6. Read the user's decisions from `meta.status` and the timestamps.
   A draft approved fast, edited before approval, or left untouched each says something.
   The user's edits to title, text, or context are the closest thing to a reason - diff them.
   Read the decisions on the posts that arrived since the last report, and not on the whole window,
   because an earlier run already read the older ones into the preferences.
7. Write each durable lesson under the matching heading of the preferences, dated, succinctly.
   When a new lesson contradicts an old entry, revise the old entry - do not append a duplicate.
8. Report a post in `ERROR`, or one whose `meta.scheduled` passed without publishing.
   That is an operational failure to surface, not a weak post to learn from.
   Give none when nothing failed, and the report leaves the section out.
9. Give the numbers, the diagnosis, and the warnings to skill **fountain-reports** as the
   `performance` preset - how the report reaches the user is that skill's decision, not this one's.
   Give the show and the posts by id as well, because a clip card links its title into the dashboard and
   every channel row into its own post.
   Name each platform the way the platform writes itself - Instagram, X, YouTube - and never as the API
   spells it.
   Give the episode each clip was cut from and the day it came out, which the Content API holds on the
   episode.
   Load each episode one time, however many clips came from it, and ask for them all in one turn.
10. Record where the report reached at the end of the Reporting section, as the publish time of the
    newest post it covered, e.g. `Reported up to 2026-08-17T16:41Z.`
    Move it only when the report was sent.

## Additional notes

The span is what the last report did not cover, and never a fixed day.
A loop that misses a morning would otherwise skip that day's clips in both runs, and nothing would ever
show them.
That is also why the marker moves only on a send: a report that failed has covered nothing.

A missing dashboard link is not an operational failure, so it never goes under the warnings.

The whole window gets fresh stats each run, because an older post keeps collecting views and the totals
and the baseline are counted again from the live numbers.
One list carries every post's numbers, so the width of the window costs nothing.

One-day noise MUST NOT go into the preferences.
"This clip beat the baseline" is noise.
"Question hooks beat statement hooks on X" is a lesson.

The baseline is the show's own recent posts, never a global number.
A show with one post has a weak baseline - say so instead of forcing a diagnosis.

A rate on few views is an artifact, and not a result.
Do not call a winner or a loser from a rate alone when the post has fewer views than the platform's median.

A lesson about a platform needs a platform that varied.
Compare the publish hours before you write one: when every post on a platform went out at the same hour,
say that instead, because the hour and the platform cannot be told apart.
The times are already on the cards, so the reader can see what the lesson could not separate.

A YouTube post is not settled for 72 hours, and its age comes from `meta.published`.
Do not diagnose one younger than that.
Do not mark the row either: the cards are yesterday's clips, so every YouTube row is young and a mark
on all of them tells the reader nothing.

The same guest in two clips a few days apart is a saturated topic, which is one of the causes step 5 names.
The window holds the evidence for it.

Untouched drafts are a signal with more than one reading: a rejected candidate and an unseen one look
the same.
Diagnose a pattern of untouched drafts, not any single one.

A reason the user already gave at a review is already in the preferences - do not re-derive it from
the outcomes, and do not write it twice.
