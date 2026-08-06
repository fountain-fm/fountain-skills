---
name: fountain-daily-growth
description: Read yesterday's results and today's news, then brief fountain-clip-finder on the best trends.
---

## Overview

This skill is the head of the daily content chain, and it runs the same two looks every morning.
Module **performance-review** looks backward: it turns yesterday's results into lessons in the preferences.
Module **trend-discovery** looks forward: it scores today's news and shapes the best trends into briefs.
Each brief goes to skill **fountain-clip-finder**, and nothing comes back - the later stages own the rest.

## Input

- `show` - the show to run the loop for.
- The Narratives and Editorial sections of the preferences.

## Output

- One brief per advancing trend, handed to skill **fountain-clip-finder**.
  A brief is a completed trend of module **trend-discovery**, with a `clip_count` of 1 or 2.
- Updated preferences: the lessons of module **performance-review**, and any proposed narrative.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- A web search tool, to find news published in the last 48 hours.
  Optional: a social trend search tool, such as one for X, when the machine has one.
- Skill **fountain-api**.
- Skill **fountain-clip-finder**.

## Process

1. Run module **performance-review** to turn yesterday's posts and their numbers into lessons.
2. Run module **trend-discovery** to score today's trends and shape the strongest into briefs.
3. Hand each brief to skill **fountain-clip-finder**, and do not read its result.
   The chain continues without this skill: the drafts wait in the Social API, and the operator decides
   in the Fountain dashboard.

## Additional notes

You MUST NOT approve, schedule, or publish a post - approval lives in the Fountain dashboard, not in a skill.

This skill owns the two morning looks and nothing downstream.
Finding moments and writing the copy is the job of skill **fountain-clip-finder**.
Rendering is the job of skill **fountain-clip-producer**, which picks the drafts up from the Social API.

An empty Narratives or Editorial section is not a wall: proceed, and say so plainly.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
