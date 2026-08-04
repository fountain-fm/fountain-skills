---
name: fountain-daily-growth
description: Run a daily trend-to-content loop - find trends, build a reviewed clip pack, and schedule approved posts.
---

## Overview

This skill is the standing orchestration loop that turns today's news into a reviewed batch of scheduled posts.
It reads the news, maps trends to the show's own narratives, and assembles the strongest clip candidates into a pack.
The operator reviews the pack, and only approved posts move on to scheduling.
Module trend-discovery, module pack-assembly, and module feedback-capture do the phase work.
Skill fountain-stats closes the loop: its learnings feed the next run through the preferences.

## Input

- `show` - the show to run the loop for.
- The per-show decisions, narrative library, and editorial rules in the preferences.

## Output

- `fountain/outputs/daily-growth/<show-slug>/pack-<date>.md` - the day's clip pack.
- Scheduled posts, created through skill [fountain-post-scheduler].
- Updated preferences after the review.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- News and social trend search tools.
- Skills [fountain-clip-finder], [fountain-clip-producer], and [fountain-post-scheduler].
- Skill fountain-stats, for the learnings that feed each run.
- Skill fountain-api.

## Process

1. Run module trend-discovery to score today's trends and translate the strongest into theme search terms.
2. Run module pack-assembly to turn those trends into a rendered, safety-checked clip pack.
3. Present the pack to the operator and collect approve / edit / reject per item.
4. Schedule only the approved posts through skill [fountain-post-scheduler].
5. Run module feedback-capture to write what the operator taught you into the preferences.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

You MUST NOT publish or schedule anything without explicit operator approval.

This skill owns everything upstream of scheduling.
Finding, scoring, and rendering clips is the job of skills [fountain-clip-finder] and [fountain-clip-producer].
Routing, uploads, and timing are the job of skill [fountain-post-scheduler].
Analytics and reports are the job of skill fountain-stats - do not re-implement them here.

Run skill fountain-stats earlier in the day, so fresh learnings exist to apply.

When a dependency fails, degrade honestly:

- No trend data - build the pack from news sources alone and say so at the review.
- No clean candidate for a trend - drop the trend, do not force a match.
- A render or scheduling failure - report it, keep the assets, and never claim a post was scheduled that was not.

On early runs the preferences may hold little signal yet.
Proceed and note at the review that less signal was applied than usual.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill [fountain-clip-finder] directly.
