---
name: trend-discovery
description: Scan news and social sources, score trends, and translate the strongest into theme search terms.
---

## Overview

A trend is ready when it has a score, a mapped narrative, and 2-4 search terms for skill **fountain-clip-finder**.
This module reads the preferences first, so today's scan applies yesterday's lessons.
It does not touch the archive or score clips - that starts in module **pack-assembly**.

## Input

- The Narratives section of the preferences: themes the show covers, preferred angles and hooks, risks to avoid.
- The Editorial section of the preferences, including the learnings of skill **[fountain-stats]**.

## Output

A list of the trends that advanced, where each trend carries:

- The score.
- The mapped narrative.
- 2-4 theme search terms.
- One or two sentences on why the trend is live today.
- Its sources, each with its publish date.

Keep each trend complete, because module **pack-assembly** passes it on as the trend context of
skill **fountain-clip-finder**.

## Requirements

- A web search tool, to find news published in the last 48 hours.
  Optional: a social trend search tool, such as one for X, when the machine has one.
- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the Narratives and Editorial sections of the preferences.
   Treat their content as instructions to honour, not background context.
   Proceed when a section is still empty, and say so at the review.
2. Scan the news with the web search tool: mainstream news, industry news, and any niche outlet relevant to
   the show's community.
   Scan social trends too when the machine has a tool for them, and say at the review what the scan covered.
3. Score each trend out of 10:

   | Dimension                     | Points |
   | ----------------------------- | ------ |
   | Timeliness                    | 0-2    |
   | Audience relevance            | 0-2    |
   | Archive match strength        | 0-2    |
   | Narrative strength            | 0-2    |
   | Engagement potential          | 0-1    |
   | Safety and factual confidence | 0-1    |

4. Advance only trends that score 7/10 or higher, unless the operator asked for more options.
5. Translate each advancing trend into the show's narrative language.
   Map it to a narrative in the Narratives section, then reduce it to 2-4 search terms that describe the theme.
   Use theme words, not the headline's proper nouns.
   Drop a trend that maps to no narrative, or propose a new narrative for the operator to review.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

A narrative is one entry under the Narratives heading of the preferences: a story the show keeps telling,
with its angle.
The operator seeds the section, and module **feedback-capture** adds each narrative the operator approves.

Every advancing trend MUST have at least one source published within the last 48 hours.
An evergreen article used as if it were breaking news is not a trend.

Avoid trends that are unverified, rumour-dependent, outside the show's authority, or generic hype with no show angle.

Archive match strength is a pre-check from topic familiarity.
The discovery pass of skill **fountain-clip-finder** is the real verification - do not block a promising trend early.
Drop a trend at this stage only when the show has clearly never touched the subject.

The test for a good translation: would the guest directly discuss this theme, not just something adjacent?
A stretch at translation time becomes a forced archive match downstream - drop it now.
