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
- The report of the posts that wait, one time when the day's clips exist.
- Updated preferences: the narratives brought level with the show, and the lessons of module
  **performance-review**.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- An HTTP client, e.g. curl, for the Google News RSS route of module **trend-discovery**.
- Optional: a web search tool, and a social trend search tool such as one for X, when the machine has them.
- Fountain API.
- Skill **fountain-clip-finder**.
- Skill **fountain-reports**.

## Process

1. Bring the Narratives section level with the show, because both modules read it.
2. Run module **performance-review** to turn yesterday's posts and their numbers into lessons.
3. Run module **trend-discovery** to score today's trends and shape the strongest into briefs.
4. Hand each brief to skill **fountain-clip-finder**, and do not read its result - the chain
   continues without this skill.
5. Read the auto-render setting from the Automation section of the preferences, where on is the default.
   List the day's drafts with the Social API either way, because step 4 hands the briefs on and never
   reads what came back.
   With auto-render on, render them with skill **fountain-clip-producer** as a clean final, so the user
   reviews the clip and not a description of it.
   When the Brand section holds no confirmed kit, render the single strongest clip first, and present
   it as the style proof of that skill.
   Render the rest only after the user confirms or corrects the proof, because a batch in the wrong
   look is a batch rendered twice.
   Leave the rendering to a render machine instead when one works this show, and it sends the report.
   Send the day's clips as the `review-posts-simple` report of skill **fountain-reports** either way, and let
   its approve note say whether approving renders a clip or sends it.
   Present the day's clips in the chat on the clip card of skill **fountain-clip-finder**, whether or
   not this run made them, because a day at budget still has clips the user has not seen.

## Additional notes

This skill owns the two morning looks and nothing downstream.
Finding moments and writing the copy is the job of skill **fountain-clip-finder**.
Rendering is the job of skill **fountain-clip-producer**, run here or on a render machine that picks the
drafts up from the Social API.

Auto-render off means something else has to render, so say which: the user's word in the chat, or a
render machine that works this show.
Offer to set up a scheduled run that renders the approved drafts when they want the day to finish
without them, because a draft that nothing renders is a clip that never exists.

Before you set up a scheduled run, say which entries it will follow that the user has not confirmed,
and how much of the show it can search.

An empty Editorial section is not a wall: proceed, and say so plainly.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
