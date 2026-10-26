---
name: fountain-daily-growth
description: Run Daily Growth on this agent instead of on Fountain, only when the user asks for a local run.
---

## Overview

This skill reads yesterday's numbers and today's news, then briefs skill **fountain-clip-finder**.
It runs two modules in order.
Module **performance-review** turns the numbers of yesterday's posts into lessons in the preferences.
Module **trend-discovery** scores today's news and makes the best trends into briefs.
The skill itself updates the narratives first, because both modules read them.

## Input

- `show` - the show to run the loop for.
- The Narratives and Editorial sections of the preferences.
- The `ProjectOverview` of the project, for the Daily Growth setting.

## Output

- One brief per advancing trend, handed to skill **fountain-clip-finder**.
  A brief is a completed trend of module **trend-discovery**.
  Each brief holds its share of the day's clip budget as `clip_count`.
- One report for the day.
  It shows the posts that wait, then yesterday's numbers.
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

1. Load the `ProjectOverview` with the Project API.
   When Daily Growth is on, Fountain also makes drafts today.
   Tell the user, and continue only when they confirm.
2. Update the Narratives section, because both modules read it.
3. Run module **performance-review** to turn yesterday's posts and their numbers into lessons.
4. Run module **trend-discovery** to score today's trends and shape the strongest into briefs.
5. Hand each brief to skill **fountain-clip-finder**, and do not read its result.
   The chain continues without this skill.
6. List the day's drafts with the Social API, because step 5 hands the briefs on and never reads them back.
7. Send the day's report one time, as the `review-posts` report of skill **fountain-reports**.
   The report shows the clips that wait, then the numbers of module **performance-review**.
   Ask skill **fountain-reports** to send the report and also to print the same report here.

## Additional notes

Some steps repeat one API call over many items.
Examples are the numbers of each post, the news of each subject, and the drafts of each clip.
These items do not depend on each other, so ask for them all at the same time.

This skill owns the two morning modules, and none of the work after them.
Finding moments and writing the copy is the job of skill **fountain-clip-finder**.
Fountain renders the video of each draft.

Give the label of each source, and its publish date when known.
For a source with an episode id, the label is the episode.
For other sources, the label is the external video title from `context`.
The printed report is all that the chat shows about the day's clips.
It also covers the clips that this run did not make.
This is because a day at budget still has clips that the user has not seen.

Skip the report when the line that module **performance-review** writes in the Reporting section already
has today's date.
This makes sure that a second run never mails the day twice.

An empty Editorial section does not stop the skill.
Proceed, and tell the user plainly that the section is empty.

For a one-off "find me a clip about X", use skill **fountain-clip-finder** directly.
