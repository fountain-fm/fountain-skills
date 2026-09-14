---
name: fountain-daily-growth
description: Run the recurring podcast growth cycle from recent results and current news.
---

## Overview

This skill reviews recent post performance, finds timely trends, and starts the best clip work.
It is for the recurring growth cycle, not for a one-off clip request.
Modules **performance-review** and **trend-discovery** own the two analysis workflows.

## Input

- The show to review.
- Its Narratives, Editorial, Automation, and Reporting preferences when those sections exist.

## Output

- Updated durable lessons and narratives.
- At most five sourced trend briefs with a shared daily clip budget.
- Draft or rendered clip candidates and the configured reports.

## Housekeeping

Read HOUSEKEEPING.md before you use the Fountain API or preferences.

## Requirements

- Fountain API.
- Read module **trend-discovery** for its news-source requirements.
- Skills **fountain-clip-finder**, **fountain-clip-producer**, and **fountain-reports**.

## Process

1. Load the relevant preferences and refresh Narratives only when recent episodes can change them.
   Do not audit unrelated setup or settings.
2. Read and run module **performance-review**.
3. Read and run module **trend-discovery** with the updated lessons and narratives.
4. Give each advancing brief to skill **fountain-clip-finder** with its `clip_count`.
5. Read auto-render from Automation, with on as the default.
   With auto-render on, use skill **fountain-clip-producer** to make clean finals.
   With auto-render off, leave verified drafts for the configured renderer or the user.
6. If no brand kit is confirmed, render only the strongest style proof and leave the other clips as drafts.
   State the one style decision that blocks the remaining renders.
7. Deliver the performance and review reports through skill **fountain-reports**.
   Also show the day's clips in chat with the clip cards from skill **fountain-clip-finder**.

The run is complete when the analysis is recorded, every advancing brief reached the clip finder,
and each resulting draft is rendered, assigned to a renderer, or held for one stated user decision.

## Additional notes

Process independent posts, episodes, and trends concurrently where their inputs do not depend on each other.
An empty Editorial section does not block a run.

Use skill **fountain-clip-finder** directly for a one-off clip request.
Use skill **fountain-onboarding** only when a missing setup item blocks this cycle.
