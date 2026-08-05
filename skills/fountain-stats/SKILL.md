---
name: fountain-stats
description: Pull analytics for a show's social posts and report performance with learnings.
---

## Overview

This skill runs after posts are live.
Each run fetches the show's recent posts and their current metrics from the API and builds one normalized snapshot.
A renderer script turns that snapshot into the daily report.
The skill is read-only and keeps no local history - baselines come from the older posts in the same fetch.
Durable learnings go into the preferences under the Editorial heading.

## Input

- `show` - the show name for the report header.
- Optional: a date range for an ad hoc request, for example "how did yesterday's posts do".
  The default window is the last 24 hours.

## Output

- The daily report, printed to stdout and presented to the user.
- Updated preferences when the run finds durable learnings.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.

## Process

1. Load skill **fountain-api**.
   Fetch the show's posts for the last 7 days and their per-post engagement with the Social API.
2. Build the snapshot in the shape that `render-report.py` documents.
   Derive each post's editorial metadata (narrative, hook style, clip length) from the post's copy and clip data
   in the API, together with the Narratives section of the preferences.
   A post whose scheduled time has passed but whose state is an error never went live.
   Put each such post in `failed`, not in `posts`.
   Record each unavailable metric as `n/a` with the reason - never a zero.
3. Diagnose each post that clearly beat or missed its platform baseline and name the likely cause.
   Causes to consider: hook strength, platform fit, posting time, clip length, topic saturation.
4. Write concrete recommendations for the next posts into the snapshot's `recommendations`.
5. Render the report:

   ```bash
   scripts/render-report.py --snapshot <snapshot.json>
   ```

6. Present the report to the user.
   Call out each failed post and recommend a re-approval and reschedule through skill **[fountain-post-scheduler]**.
7. Record durable learnings under the Editorial heading of the preferences, succinctly.
   A durable learning holds across days, for example "question hooks beat statement hooks on X".
   One-day noise MUST NOT go in.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

You MUST NOT post, schedule, or delete anything with this skill.

Build the snapshot fresh each run.
You MUST NOT reuse or read a snapshot, report, or other output of an earlier run.

A failed post is not a weak post - it never went live, so its fix is operational, not editorial.

When one platform's fetch fails, do not abort the run.

Baselines need prior posts.
When the show has no posts older than 24 hours, the report shows "no baseline yet" - this is expected.

Once a week, zoom out: fetch the last 30 days of posts and propose strategy changes to the user.
For example the platform mix, posting-time windows, and narratives to promote or retire.

Express posting-time findings in the show's primary audience timezone, not the operator's timezone.
