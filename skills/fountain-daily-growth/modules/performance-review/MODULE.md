---
name: performance-review
description: Read yesterday's posts and their numbers fresh from the API, and write the durable lessons.
---

## Overview

This module is how the loop learns without local state.
It loads the recent posts and their engagement fresh from the API, compares each post against the show's
own baseline, reads the user's decisions from the post metadata, and writes what holds beyond today
into the preferences.
The posts are the record, and the preferences are the memory - nothing else persists.

## Input

- `show` - the show the loop runs for.
- The show's recent posts and their `SocialPostStats`, loaded fresh via the Social API.

## Output

- Updated Editorial and Narratives sections of the preferences.
- The `performance` report of skill **fountain-reports**: the numbers, the diagnosis, the warnings.

## Requirements

- Skill **fountain-api**.
- Skill **fountain-reports**.

## Process

1. Load skill **fountain-api** and list the show's recent posts via the Social API.
   The last 14 days is enough.
   Load the `SocialPostStats` of each published post.
2. Compute the baseline from these posts alone: the median views, likes, and comments per platform.
   The baseline is computed each run, so it exists from the first run and needs no history file.
3. Find the posts that clearly beat or missed the baseline, and name the likely cause:
   the hook, the platform fit, the posting time, the clip length, or a saturated topic.
4. Read the user's decisions from `meta.status` and the timestamps.
   A draft approved fast, edited before approval, or left untouched each says something.
   The user's edits to title, text, or context are the closest thing to a reason - diff them.
5. Write each durable lesson under the matching heading of the preferences, dated, succinctly.
   When a new lesson contradicts an old entry, revise the old entry - do not append a duplicate.
6. Report a post in `ERROR`, or one whose `meta.scheduled` passed without publishing.
   That is an operational failure to surface, not a weak post to learn from.
7. Give the numbers, the diagnosis, and the warnings to skill **fountain-reports** as the
   `performance` preset - how the report reaches the user is that skill's decision, not this one's.

## Additional notes

One-day noise MUST NOT go into the preferences.
"This clip beat the baseline" is noise.
"Question hooks beat statement hooks on X" is a lesson.

The baseline is the show's own recent posts, never a global number.
A show with one post has a weak baseline - say so instead of forcing a diagnosis.

Untouched drafts are a signal with more than one reading: a rejected candidate and an unseen one look
the same.
Diagnose a pattern of untouched drafts, not any single one.

A reason the user already gave at a review is already in the preferences - do not re-derive it from
the outcomes, and do not write it twice.

You MUST NOT keep a local log of posts, numbers, or lessons for a later session.
