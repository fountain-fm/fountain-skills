---
name: discovery
description: Search a show's transcripts for real moments, and score each one for substance and for fit.
---

## Overview

This module decides whether a moment is worth clipping, and not yet how to cut it.
A moment is a group of transcript segments less than 30 seconds apart.
It is one continuous passage.
A moment runs for a few minutes, so it is longer than a clip and not precise enough to set a cut.
This module uses only the segments, so it can examine many moments at one time.
Module **media** then removes the moments that have no video, and module **boundaries** shapes the rest.

## Input

One of these:

- A topic, or the terms to search for.
- A kind of moment, for example funny, angry, or surprising.
- An episode, with an optional quote or approximate time.
- A person, to find the moments of one guest or host.

With one of:

- The show, resolved to its `ContentID`.
- The segments of a video that Fountain does not hold, from module **external-source**.

## Output

- The scored moments, each with its scores and each flag.
- The `ContentHit` of each episode.
  The search returns it, and it already names the video.
  A moment from one video has its external source instead.

## Requirements

- Fountain API.

## Process

For the segments of one video, read them in full and skip to step 6.
One talk is short enough to read, so choose the passages by reading, and never by search.
Also, no step before step 6 has a source to work on.

1. Resolve the show with the Search API when you have only a name.
   The Search API gives a bare id, but the rest of the API needs the prefixed form.
   Add the type prefix.
2. Read the transcript indexing progress with the Project API.
   The Project API gives one row for each connected show.
   The row counts all the episodes of the show, the episodes with an indexed transcript, and the episodes
   in the queue.
   Tell the caller how much of the show the search reaches, and say that the rest is out of reach.
   A show with no row is not connected, so no count is available.
   Then you must judge the coverage from the results.
   The progress request and the searches of step 3 need only the show, so send them together.
3. Search the show's transcripts with the Search API, and scope the search to the show.
   Scope to the show even when the caller names an episode.
   Then keep the hits of that episode, and drop the rest.
   A search scope that names an episode returns nothing.
   Each `ContentHitSegments` gives the episode and the segments that matched, with their times.
4. Search for the theme, and not for the proper nouns of a news headline.
   Use short keyword queries.
   When the caller names one episode, search the words of its own title and show notes, because those
   words are its theme.
   Also search for disagreement, predictions, surprising statements, and changes of mind.
   Send the queries together, in batches of 4 to 6, because no query needs the answer of another.
   For a kind of moment, search the recurring subjects of the show.
   Then make that kind of moment the main factor in the score.
   Use the quote or the approximate time to choose the moment when the caller gives one.
5. For a person, search their name.
   The transcript names no speaker.
   Thus this search finds where someone said the name, and never who spoke.
   Tell the caller that.
   Let module **copy** and skill **fountain-clip-producer** identify the speaker.
6. Sort the segments of one episode by time, then join the segments that touch or overlap.
   A passage often returns as two segments, and a hit gives them in the order of the score.
   The result is a moment, which is one continuous passage to judge.
   Load the whole transcript with the Content API only when a moment needs the words around it.
   Load one transcript for each episode, however many of its moments need it.
   Ask for all the transcripts at the same time.
7. Score each moment 1-10 for controversy, insight, engagement, and relevance.
   Remove any moment under 24 of 40, and rank what remains.
8. Load the posts of the surviving moments' episodes with the Social API, in every lifecycle state.
   Ask for each episode separately, and only for the episodes that still hold a moment.
   The posts of another episode cannot overlap a moment.
   The episodes are independent, so ask for them all at the same time.
   Mark a moment `already-clipped` when it overlaps the `source` of one of these posts by more than half.
   Compare only with a `source` whose `media` is the `info.audio` of the episode of the segments.
   The two clocks agree only in that case.
   For a moment from one media URL, list recent posts without a source filter.
   Compare it with the same YouTube video id, or with the same `media` when both sources have empty `ids`.
   Mark it `already-clipped` when the spans overlap by more than half.
   Pass a marked moment on only when the caller or the lessons ask for a new cut.
   Give the remaining moments to module **media**.

## Additional notes

The search covers the episodes that hold a transcript, and never the whole show by default.
The coverage is set one episode at a time, so a gap can be anywhere, and not only in the oldest episodes.
An episode with no transcript is not in the search, so say which ones the search could not see.
Most shows are not connected yet, so usually no count is available.
Without the count, a show with few transcripts looks the same as a show with nothing to say.
In both cases, several different searches return nothing, or all of them find the same episode.
Say that, and do not report that the archive holds no moment.
A search that reaches one episode of a thousand still returns a real hit.
The user cannot tell the two cases apart from the result.

Apply every filter to the segments, and group the segments last.
A filter after the grouping removes words from the middle of a moment.

A transcript search finds words, and not tone.
Thus the score decides the kind of moment, and the query does not.

Judge whether the passage holds something worth clipping, and leave the exact cut to module **boundaries**.
A moment of several touching segments is a longer discussion of the theme, and that is a signal in itself.

The bar here is deliberately lower than in module **boundaries**.
Remove only the moments that are clearly weak.
A moment can improve when it becomes a clip, and some moments fail in the later modules.

A posted clip cut from another file cannot be compared here, because its `ts_start` is in the clock of
that file.
Such a clip is rare.
If this module misses one, the result is a repeated clip, and not a wrong clip.

A moment from a raw local video is compared with nothing at step 8, because its post holds no `source`.
Ask the user whether that video was clipped already.

Do not force a match.
The speaker MUST discuss the theme directly.
Say so when no moment has substance.

Prefer surprising statistics, contrarian opinions, strong predictions, myth debunking, and confessions.
Avoid general discussion, long setup, hosts who agree with each other, and abstract talk with no takeaway.

Mark a moment higher-risk for an unverified claim, a legal or defamation risk, an election or geopolitics
claim, a claim about a named person, a price prediction, investment advice, or a misleading trim.
Keep the flag and the reason with the moment, because module **copy** does the last safety check on the words.

Record the scores, so that a later reader can audit the ranking.
