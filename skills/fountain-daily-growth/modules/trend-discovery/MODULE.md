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

- A list of scored trends, each with a mapped narrative, 2-4 theme search terms, and at least one recent source.
  Keep each source with its trend, because skill **fountain-clip-finder** wants the trend context with its sources.

## Requirements

- News and social trend search tools.
- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the Narratives and Editorial sections of the preferences.
   Treat their content as instructions to honour, not background context.
   Proceed when a section is still empty, and say so at the review.
2. Scan the news and social sources the show has access to: mainstream and industry news, trending conversations,
   and any niche platform relevant to the show's community.
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

Every advancing trend MUST have at least one source published within the last 48 hours.
An evergreen article used as if it were breaking news is not a trend.

Avoid trends that are unverified, rumour-dependent, outside the show's authority, or generic hype with no show angle.

Archive match strength is a pre-check from topic familiarity.
The discovery pass of skill **fountain-clip-finder** is the real verification - do not block a promising trend early.
Drop a trend at this stage only when the show has clearly never touched the subject.

The test for a good translation: would the guest directly discuss this theme, not just something adjacent?
A stretch at translation time becomes a forced archive match downstream - drop it now.
