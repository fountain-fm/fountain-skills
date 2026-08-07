---
name: trend-discovery
description: Scan the news, score the trends, and shape the strongest into briefs for fountain-clip-finder.
---

## Overview

A brief is a completed trend: a score, a mapped narrative, 2-4 search terms, a why-now, and the sources.
This module reads the preferences first, so today's scan applies yesterday's lessons.
It curates hard: at most the 5 best trends advance, because the chain downstream multiplies each one.
It does not touch the archive or score clips - that work starts in skill **fountain-clip-finder**.

## Input

- `show` - the show the loop runs for.
- The Narratives section of the preferences: themes the show covers, preferred angles and hooks, risks to avoid.
- The Editorial section of the preferences, including the lessons of module **performance-review**.

## Output

At most 5 briefs, one per advancing trend, where each brief carries:

- The score.
- The mapped narrative.
- 2-4 theme search terms.
- One or two sentences on why the trend is live today.
- Its sources, each with its publish date.
- A `clip_count` of 1 or 2.

## Requirements

- A web search tool, to find news published in the last 48 hours.
  Optional: a social trend search tool, such as one for X, when the machine has one.
- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the Narratives and Editorial sections of the preferences.
   Treat their content as instructions to honour, not background context.
   Proceed when a section is still empty, and say so plainly.
2. Scan the news with the web search tool: mainstream news, industry news, and any niche outlet relevant to
   the show's community.
   Scan social trends too when the machine has a tool for them, and say what the scan covered.
3. Score each trend out of 10:

   | Dimension                     | Points |
   | ----------------------------- | ------ |
   | Timeliness                    | 0-2    |
   | Audience relevance            | 0-2    |
   | Archive match strength        | 0-2    |
   | Narrative strength            | 0-2    |
   | Engagement potential          | 0-1    |
   | Safety and factual confidence | 0-1    |

4. Advance only trends that score 7/10 or higher, and at most the 5 best.
   Prefer a spread of narratives over five takes on one story.
5. Translate each advancing trend into the show's narrative language.
   Map it to a narrative in the Narratives section, then reduce it to 2-4 search terms that describe the theme.
   Use theme words, not the headline's proper nouns.
   Drop a trend that maps to no narrative, or propose a new narrative (see the notes).

## Additional notes

A narrative is one entry under the Narratives heading of the preferences: a story the show keeps telling,
with its angle.
The user seeds the section.
Propose a new narrative by writing it there marked as proposed, and let the user keep or cut it.

Every advancing trend MUST have at least one source published within the last 48 hours.
An evergreen article used as if it were breaking news is not a trend.

Avoid trends that are unverified, rumour-dependent, outside the show's authority, or generic hype with no show angle.

Archive match strength is a pre-check from topic familiarity.
The discovery pass of skill **fountain-clip-finder** is the real verification - do not block a promising trend early.
Drop a trend at this stage only when the show has clearly never touched the subject.

The test for a good translation: would the guest directly discuss this theme, not just something adjacent?
A stretch at translation time becomes a forced archive match downstream - drop it now.

`clip_count` stays at 1 or 2 because every draft the chain makes waits in the dashboard until the user
decides, and a small queue of strong candidates beats a long queue of maybes.
