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
- One or two sentences on what happened and why the trend is live today.
- Its sources, each with its headline, its publisher, its publish date and its link.
  Every item of the scan carries a link, so a source without one has been thrown away.
- A `clip_count`, which is this trend's share of the day's clip budget.

## Requirements

- An HTTP client, e.g. curl, for the Google News RSS route.
- Optional: a web search tool, and a social trend search tool such as one for X, when the machine has them.
- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the Narratives and Editorial sections of the preferences.
   Treat their content as instructions to honour, not background context.
   Proceed when the Editorial section is still empty, and say so plainly.
   The caller brings the Narratives section level with the show before this module runs, so it holds
   every subject the show covers.
2. Scan the news, one query per subject the show covers:

   ```bash
   curl -s "https://news.google.com/rss/search?q=<subject>+after:<48h ago>+before:<tomorrow>&hl=en-US&gl=US&ceid=US:en"
   ```

   Each item carries its title, its publisher and its date, so the 48-hour rule holds by construction.
   The `hl`, `gl` and `ceid` values above return news for the United States in English, so set them for
   the audience the show writes for, and say which you used.
   Then run the same query one more time on the subject of the whole show, which is the level that is
   too broad to be a narrative and right for a catch-all.
   A scan built from the narratives finds only what the show already returns to, and the story it
   cannot find that way is the one the archive answers one time and no rival can.
   Widen the scan with a web search tool or a social trend tool when the machine has one, and say what
   the scan covered.

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
   Share the day's clip budget across them as `clip_count`, most to the strongest, and none to a
   trend that earns none.
   Read the budget from the Automation section of the preferences, and use 3 when no setting names it.
5. Translate each advancing trend into the show's narrative language.
   Map it to a narrative in the Narratives section, then reduce it to 2-4 search terms that describe the theme.
   Use theme words, not the headline's proper nouns.
   Search the archive with the Search API for a trend that matches no narrative, and keep it when the
   show has covered the subject even one time.
   Propose a narrative for it, because the show has returned to the subject now.
   Drop it only when the archive holds nothing.

## Additional notes

Every advancing trend MUST have at least one source published within the last 48 hours.
An evergreen article used as if it were breaking news is not a trend.

Avoid trends that are unverified, rumour-dependent, outside the show's authority, or generic hype with no show angle.

A narrative says what the show returns to, and never what the show is allowed to talk about.
One episode from years ago, on a subject in today's news, is the clip that no other show can make,
and a list of recurring subjects is exactly what would lose it.

Archive match strength is a pre-check from topic familiarity.
The discovery pass of skill **fountain-clip-finder** is the real verification - do not block a promising trend early.
Drop a trend at this stage only when the show has clearly never touched the subject.

The test for a good translation: would the guest directly discuss this theme, not just something adjacent?
A stretch at translation time becomes a forced archive match downstream - drop it now.

The budget is for the day and never for one trend, because the user reviews the day.
Every draft waits in the dashboard until they decide, and each clip becomes one post on each connected
channel, so a budget of 3 is already 6 posts on two channels.
`clip_count` is a maximum that the archive may not fill, and fewer strong clips is the better outcome.
