---
name: discovery
description: Search a show's transcripts for real moments, and score each one for substance and for fit.
---

## Overview

Discovery decides whether a moment is worth clipping, and not yet how to cut it.
A moment is a group of transcript segments less than 30 seconds apart: one continuous passage.
A moment runs for a few minutes, so it is longer than a clip and too coarse to cut on.
Discovery works from the segments alone, so it can look at many moments at one time.
Module **media** then removes what has no video, and module **boundaries** shapes the rest.

## Input

One of these:

- A topic, or the terms to search for.
- A kind of moment, for example funny, angry, or surprising.
- An episode, with an optional quote or approximate time.
- A person, to find the moments of one guest or host.

With:

- The show, resolved to its `ContentID`.

## Output

- The scored moments, each with its scores and each flag.
- The `ContentHit` of each episode, which the search returns and which already names the video.

## Requirements

- Skill **fountain-api**.

## Process

1. Load skill **fountain-api**, and resolve the show with the Search API when you have only a name.
   The Search API gives a bare id, and the rest of the API needs the prefixed form, so add the type prefix.
2. Search the show's transcripts with the Search API, scoping to the show.
   Scope to the episodes instead when the caller names them.
   Each `ContentHitSegments` gives the episode and the segments that matched, with their times.
   Check that each hit belongs to the show, and drop the ones that do not, because a scope the API
   does not recognise searches every show on Fountain and answers 200.
3. Search the theme, not the proper nouns of a headline, and use short keyword queries.
   Also search for disagreement, predictions, surprising statements, and changes of mind.
   For a kind of moment, search the show's recurring subjects, then let that kind lead the score.
   Use the quote or the approximate time to choose the moment when the caller gives one.
4. For a person, search their name.
   The transcript names nobody, so this finds where a name was said and never who said it - tell the
   caller that, and let module **copy** and skill **fountain-clip-producer** settle the speaker.
5. Sort the segments of one episode by time, then join the ones that touch or overlap, because a
   passage often returns as two and a hit gives them in the order of the score.
   The result is a moment: one continuous passage to judge.
   Load the whole transcript with the Content API only when a moment needs the words around it.
6. Score each moment 1-10 for controversy, insight, engagement, and relevance.
   Remove any moment under 24 of 40, and rank what remains.
7. Load the posts of the surviving moments' episodes with the Social API, in every lifecycle state.
   Ask per episode, and only for the ones that still hold a moment - another episode cannot overlap.
   Mark a moment `already-clipped` when it overlaps the `source` of one by more than half.
   Compare only with a `source` whose `media` is the `enclosure` of the segments, because the two clocks
   agree only then.
   Advance a marked moment only when the caller or the lessons ask for a new cut, and give what remains to
   module **media**.

## Additional notes

The search covers the episodes that hold a transcript, and never the whole show by default.
Coverage is decided one episode at a time, so a gap sits anywhere and not only in the oldest episodes.
An episode with no transcript is not in the search, so say which ones the search could not see.
A show with few transcripts looks the same as a show with nothing to say: several different searches
come back empty, or every one of them lands on the same episode.
Say that, rather than report that the archive holds no moment - a search that reaches one episode of a
thousand still answers with a real hit, and the user cannot tell the two apart from the result.

Keep every filter on the segments and group them last, because a filter after the group takes words
out of the middle of a moment.

A transcript search finds words and not tone, so the score decides a kind of moment and the query does not.

Judge whether the passage holds something worth clipping, and leave the exact cut to module **boundaries**.
A moment of several touching segments is a longer run on the theme, which is a signal in itself.

The bar here is lower than in module **boundaries**, deliberately: remove only what is clearly weak,
because a moment can improve when it is shaped, and some fail in the later modules.

A posted clip cut from another file cannot be compared here, because its `ts_start` is in that file's
clock. Such a clip is rare, and missing one costs a repeat rather than a wrong clip.

Do not force a match: the speaker MUST discuss the theme directly, and say so when nothing has substance.

Prefer surprising statistics, contrarian opinions, strong predictions, myth debunking, and confessions.
Avoid general discussion, long setup, hosts who agree with each other, and abstract talk with no takeaway.

Mark a moment higher-risk for an unverified claim, a legal or defamation risk, an election or geopolitics
claim, a claim about a named person, a price prediction, investment advice, or a misleading trim.
Carry the flag and the reason forward, because module **copy** runs the last safety check on the words.

Record the scores, so that a later reader can audit the ranking.
