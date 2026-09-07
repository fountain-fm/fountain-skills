---
name: fountain-daily-growth
description: Read yesterday's results, the new episodes and today's news, then brief fountain-clip-finder.
---

## Overview

This skill is the head of the daily content chain, and it runs three modules in order.
Module **performance-review** turns the numbers of yesterday's posts into lessons in the preferences.
Module **episode-watch** briefs skill **fountain-clip-finder** on each episode the show published since
the last run.
Module **trend-discovery** scores today's news and shapes the best trends into briefs for the same skill.
The skill itself keeps the narratives level with the show first, because every module reads them.

## Input

- `show` - the show to run the loop for.
- The Narratives, Editorial and Automation sections of the preferences.

## Output

- One brief per advancing trend, handed to skill **fountain-clip-finder**.
  A brief is a completed trend of module **trend-discovery**, carrying its share of the day's
  clip budget as `clip_count`.
- One brief per new episode, from module **episode-watch**, handed to the same skill and carrying the
  new-episode clip budget as `clip_count`.
- The report of the posts that wait, one time when the day's clips exist.
- Updated preferences: the narratives brought level with the show, the lessons of module
  **performance-review**, and the episode that module **episode-watch** reached.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- An HTTP client, e.g. curl, for the Google News RSS route of module **trend-discovery**.
- Optional: a web search tool, and a social trend search tool such as one for X, when the machine has them.
- Fountain API.
- Skill **fountain-clip-finder**.
- Skill **fountain-reports**.

## Process

1. Bring the Narratives section level with the show, because every module reads it.
2. Run module **performance-review** to turn yesterday's posts and their numbers into lessons.
3. Run module **episode-watch** to brief the episodes the show published since the last run.
   It hands its own briefs on, so step 5 covers the trends alone.
4. Run module **trend-discovery** to score today's trends and shape the strongest into briefs.
5. Hand each brief to skill **fountain-clip-finder**, and do not read its result - the chain
   continues without this skill.
6. Read the auto-render setting from the Automation section of the preferences, where on is the default.
   List the day's drafts with the Social API either way, because steps 3 and 5 hand the briefs on and
   never read what came back.
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

Where a step repeats one API call over many items - the numbers of each post, the news of each subject,
the drafts of each clip - the items do not depend on each other, so ask for them together in one turn.

This skill owns the three morning looks and nothing downstream.
Finding moments and writing the copy is the job of skill **fountain-clip-finder**.
Rendering is the job of skill **fountain-clip-producer**, run here or on a render machine that picks the
drafts up from the Social API.

Auto-render off means something else has to render, so say which: the user's word in the chat, or a
render machine that works this show.
Offer to set up a scheduled run that renders the approved drafts when they want the day to finish
without them, because a draft that nothing renders is a clip that never exists.

Before you set up a scheduled run, say which entries it will follow that the user has not confirmed,
and how much of the show it can search.

A scheduler can start module **episode-watch** on its own between two loops, so a show that publishes in
the evening does not wait for the next morning.

An empty Editorial section is not a wall: proceed, and say so plainly.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
