---
name: fountain-daily-growth
description: Run a daily trend-to-content loop - find trends, build a reviewed clip pack, and schedule approved posts.
---

## Overview

This skill is the standing loop that turns today's news into a reviewed batch of scheduled posts.
Module **trend-discovery** maps trends to the show's own narratives.
Module **pack-assembly** briefs skill **fountain-clip-finder** and **fountain-clip-producer** to build the pack.
The operator reviews the pack, and module **feedback-capture** writes the lessons into the preferences.
Skill **[fountain-stats]** closes the loop: its learnings feed the next run.

## Input

- `show` - the show to run the loop for.
- The Narratives and Editorial sections of the preferences.

## Output

- `fountain/outputs/daily-growth/<show>/pack-<date>.md` - the day's clip pack, where `<show>` is the show title.
- One draft `SocialPost` for each proposed clip, with its rendered video attached.
- Scheduled posts, created through skill **[fountain-post-scheduler]**.
- Updated preferences after the review.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- A web search tool, to find news published in the last 48 hours.
  Optional: a social trend search tool, such as one for X, when the machine has one.
- Skill **fountain-api**.
- Skills **fountain-clip-finder** and **fountain-clip-producer**.
- Skill **[fountain-post-scheduler]**.
- Skill **[fountain-stats]**, for the learnings that feed each run.

## Process

1. Run module **trend-discovery** to score today's trends and translate the strongest into theme search terms.
2. Run module **pack-assembly** to turn those trends into a rendered, safety-checked clip pack.
3. Present the pack to the operator and collect approve / edit / reject per item.
4. Schedule only the approved posts through skill **[fountain-post-scheduler]**.
5. Run module **feedback-capture** to write what the operator taught you into the preferences.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

You MUST NOT approve, schedule, or publish a post, because only the operator decides that.

This skill owns everything upstream of scheduling.
Finding and rendering clips is the job of skill **fountain-clip-finder** and skill **fountain-clip-producer**.
Scheduling and timing are the job of skill **[fountain-post-scheduler]**.
Analytics and reports are the job of skill **[fountain-stats]** - do not re-implement them here.

Run skill **[fountain-stats]** earlier in the day, so fresh learnings exist to apply.

When a dependency fails, degrade honestly:

- No trend data - build the pack from news sources alone and say so at the review.
- No clean candidate for a trend - drop the trend, do not force a match.
- A render or scheduling failure - report it, keep the assets, and never claim a post was scheduled that was not.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
