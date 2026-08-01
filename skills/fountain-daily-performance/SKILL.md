---
name: fountain-daily-performance
description: Pull analytics for a show's social posts, keep a local history, and report performance with learnings.
---

## Overview

This skill is the read-only analytics counterpart of skill [fountain-daily-growth].
It runs after posts are live: it fetches what each platform reports and builds one normalized snapshot per day.
A renderer script turns the snapshot plus the local snapshot history into a daily report and a learnings file.
The local history makes growth and per-post baselines reliable, because live APIs give sparse point-in-time numbers.
Skill [fountain-daily-growth] reads the learnings file to improve the next day's posts.

## Input

- `show` - the show name for the report header.
- Optional: a date range for an ad hoc request, for example "how did yesterday's posts do".
  The default window is the last 24 hours.

## Output

Files in `fountain/outputs/daily-performance/`:

- `history/<date>.json` - one normalized snapshot per day.
- `reports/<date>.md` - the daily report, also printed to stdout.
- `learnings.md` - dated recommendations for the next posts, newest entry first.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill fountain-api.
- Python 3.11 or later.

## Process

1. Load skill fountain-api.
2. Fetch the show's posts and per-post engagement with the Social API.
3. Build the day's snapshot in the shape that `render-report.py` documents.
   Put each post that failed to publish in `failed`, not in `posts`.
   Record each unavailable metric as `n/a` with the reason - never a zero.
4. Diagnose each post that underperformed its platform baseline and name the likely cause.
   Common causes: weak hook, wrong platform for the clip, bad posting time, clip too long, saturated topic.
5. Write concrete recommendations for the next posts into the snapshot's `recommendations`.
6. Render the report:

   ```bash
   scripts/render-report.py --snapshot <snapshot.json>
   ```

7. Present the report to the user.
   Call out each failed post and recommend a re-approval and reschedule through skill [fountain-post-scheduler].

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

You MUST NOT post, schedule, or delete anything with this skill.

Run this skill each day before the [fountain-daily-growth] run.

A failed post is not a weak post - it never went live, so its fix is operational, not editorial.

On the first run there is no history, so baselines show "no baseline yet".
This is expected - the run still renders the report and seeds the history.

Once a week, zoom out: review the last 7 days of history and propose strategy changes to the user.
For example the platform mix, posting-time windows, and narratives to promote or retire.

Express posting-time findings in the show's primary audience timezone, not the operator's timezone.
