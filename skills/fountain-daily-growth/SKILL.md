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
The skill itself updates the narratives first, because both modules read them.

## Input

- `show` - the show to run the loop for.
- The Narratives and Editorial sections of the preferences.

## Output

- One brief per advancing trend, handed to skill **fountain-clip-finder**.
  A brief is a completed trend of module **trend-discovery**, carrying its share of the day's
  clip budget as `clip_count`.
- One report for the day: the posts that wait, then yesterday's numbers.
  With auto-render on it goes out when the videos exist, and it is the only mail of the day.
- Updated preferences: the narratives, and the lessons of module
  **performance-review**.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- An HTTP client, e.g. curl, for the Google News RSS route of module **trend-discovery**.
- Optional: a web search tool, and a social trend search tool such as one for X, when the machine has them.
- Fountain API.
- Skill **fountain-clip-finder**.
- Skill **fountain-reports**.
- Skill **fountain-onboarding**.

## Process

1. Update the Narratives section, because both modules read it.
2. Run module **performance-review** to turn yesterday's posts and their numbers into lessons.
   Skip it when a render machine sends the report of step 6, because that machine runs it.
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
   With auto-render on and a render machine named for this show in the Automation section, do not
   render here and stop after this step: the machine renders, and it sends the report of step 6.
6. Send the day one time, as the `review-posts` report of skill **fountain-reports**: the clips that wait,
   then the numbers of module **performance-review**.
   With auto-render on, send it only when the videos exist, so the reader reviews clips and not
   descriptions.
   With auto-render off, send it now, and let its approve note say what renders a clip.
   Give each source label and its publish date when known.
   Use the episode for a source with an episode id, and use the external video title from `context` otherwise.
   Ask that skill to print the same report here as well as sending it, so the user reads in the chat
   what the mail carries and the two never disagree.
   The printed report is the whole of what the chat shows about the day's clips, and it covers the
   clips this run did not make, because a day at budget still has clips the user has not seen.

## Additional notes

Where a step repeats one API call over many items - the numbers of each post, the news of each subject,
the drafts of each clip - the items do not depend on each other, so ask for them all at the same time.

This skill owns the two morning looks and nothing downstream.
Finding moments and writing the copy is the job of skill **fountain-clip-finder**.
Rendering is the job of skill **fountain-clip-producer**, run here or on a render machine that picks the
drafts up from the Social API.

Auto-render off means something else has to render, so say which: the user's word in the chat, or a
render machine that works this show.
Whatever renders later sends a second mail that the renders are ready, and it is the only other mail.

A caller that has just rendered the day's drafts can ask for the report alone.
Run steps 2 and 6 for it, with the drafts it gave up under warnings.
Skip it when the line that module **performance-review** writes in the Reporting section already carries
today's date, so a second pass of the render machine never mails the day twice.
Run skill **fountain-onboarding** to schedule a render of the approved drafts when they want the day to
finish without them, because a draft that nothing renders is a clip that never exists.

An empty Editorial section is not a wall: proceed, and say so plainly.

Use this skill for the recurring daily cycle.
For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
