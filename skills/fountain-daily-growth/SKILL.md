---
name: fountain-daily-growth
description: Read yesterday's results and today's news, then brief fountain-clip-finder on the best trends.
---

## Overview

This skill is the head of the daily content chain, and it runs two modules in order.
Module **performance-review** looks backward: it turns the numbers of yesterday's posts into lessons
in the preferences.
Module **trend-discovery** looks forward: it scores today's news and shapes the best trends into briefs
for skill **fountain-clip-finder**.
The skill itself keeps the narratives level with the show first, because both modules read them.

## Input

- `show` - the show to run the loop for.
- The Narratives and Editorial sections of the preferences.

## Output

- One brief per advancing trend, handed to skill **fountain-clip-finder**.
  A brief is a completed trend of module **trend-discovery**, carrying its share of the day's
  clip budget as `clip_count`.
- The draft-posts report, one time when the day's drafts exist and auto-render is off.
- Updated preferences: the narratives brought level with the show, and the lessons of module
  **performance-review**.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- An HTTP client, e.g. curl, for the Google News RSS route of module **trend-discovery**.
- Optional: a web search tool, and a social trend search tool such as one for X, when the machine has them.
- Skill **fountain-api**.
- Skill **fountain-clip-finder**.
- Skill **fountain-reports**.

## Process

1. Bring the Narratives section level with the show, because both modules read it.
2. Run module **performance-review** to turn yesterday's posts and their numbers into lessons.
3. Run module **trend-discovery** to score today's trends and shape the strongest into briefs.
4. Hand each brief to skill **fountain-clip-finder**, and do not read its result - the chain
   continues without this skill.
5. Read the auto-render setting from the Automation section of the preferences.
   With auto-render off, list today's drafts and send them as the `draft-posts` report of skill
   **fountain-reports**: the words, and the plain statement that approving is what makes a clip render.
   With auto-render on, skip the report - the render machine sends rendered-posts with the media in it.
   Either way this step reads the queue, not the result, and the drafts go on unchanged.

## Additional notes

This skill owns the two morning looks and nothing downstream.
Finding moments and writing the copy is the job of skill **fountain-clip-finder**.
Rendering is the job of skill **fountain-clip-producer**, which picks the drafts up from the Social API.

An empty Editorial section is not a wall: proceed, and say so plainly.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
