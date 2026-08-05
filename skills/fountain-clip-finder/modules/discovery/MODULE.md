---
name: discovery
description: Search a show's transcripts for real moments, and score each one for substance and for fit.
---

## Overview

Discovery decides whether a moment is worth clipping, and not yet how to cut it.
It works from the matching segments alone, so it can look at many moments at one time.
A segment shows the words that matched and not the words around them, so a clip cannot be shaped here.
Module **video-source** then removes what has no video, and module **boundaries** shapes the rest.

## Input

One of these:

- A topic, or the terms to search for.
- A kind of moment, for example funny, angry, or surprising.
- An episode, with an optional quote or approximate time.
- A person, to find the moments of one guest or host.

With:

- The show, resolved to its `content_id`.

## Output

- Scored moments, each with `content_id`, `moment_start_seconds`, `moment_end_seconds`, the scores, and each flag.
- The episode data you loaded, because it already names the video of each episode.
- The speaker's confirmed name and synonyms, for a request about a person.

## Requirements

- Skill **fountain-api**.

## Process

1. Load skill **fountain-api**.
   Resolve the show with the Search API if you have only a name.
   The Search API gives a bare id, and the Content API needs the prefixed form, so add the type prefix.
   List the show's episodes with the Content API and remove the duplicates by podcast GUID.
2. Find the show's vault with the Project API, and bring it up to date with the Vaults API.
   Use one vault for the whole archive, and give it a name that shows its scope.
   An episode needs an analyzed transcript before it can join, and the Content API meters that work.
   Read the remaining credits with the Project API and get the user's approval before a bulk backfill.
3. Search the vault transcripts with the Vaults API.
   Search the theme, not the proper nouns of a headline, and use short keyword queries.
   Also search for disagreement, predictions, surprising statements, and changes of mind.
   For a kind of moment, search the show's recurring subjects, then let that kind lead the score.
   For an episode, keep only the segments of that episode.
   Use the quote or the approximate time to choose the moment when the caller gives one.
4. For a person, resolve them with the Search API, then keep only the segments that name them.
   Carry the confirmed name and the synonyms forward, because module **copy** names the speaker.
5. Group the matching segments of one episode into moments.
   Join segments that are less than 30 seconds apart.
6. Load the show's posted clips with the Social API, because they are the only record of what went out.
   Mark a moment `already-clipped` when its episode and span overlap a posted clip by more than half.
   Advance a marked moment only when the caller or the learnings ask for a new cut.
7. Score each moment 1-10 for controversy, insight, engagement, and relevance.
   Use the topics and the people that each segment reports, because they show discussion and not a passing word.
   Remove any moment under 24 of 40, then rank what remains and give it to module **video-source**.

## Additional notes

Keep every filter on the segments, and group them only when no filter is left.
A filter that runs after the group takes words out of the middle of a moment.

A transcript search finds words and not tone, so the score decides a kind of moment and the query does not.

A moment is a group of segments, and never one segment.
One segment holds about 10 words, and a score on a fragment is a guess.
The size of a group is a signal: many segments are sustained discussion, and one segment is a passing mention.

The bar here is lower than the bar of module **boundaries**, and that is deliberate.
This pass only removes the moments that are clearly weak, because a moment can improve when it is shaped.
Send every moment above the bar, because some of them fail in the later modules.

Do not force a match.
The speaker MUST discuss the theme directly, and you MUST remove a quote that you must bend to fit the topic.
Give the strongest moments you found and an honest explanation when nothing has substance.

Prefer surprising statistics, contrarian opinions, strong predictions, myth debunking, and confessions.
Avoid general discussion, long setup, hosts who agree with each other, and abstract talk with no takeaway.

Mark a moment higher-risk for an unverified claim, a legal or defamation risk, an election or geopolitics
claim, a claim about a named person, a price prediction, anything that reads as investment advice, or a quote
that a trim can make misleading.
Carry the flag and the reason forward, because the caller does the last safety check.

Record the scores, so that a later reader can audit the ranking.

Work out `already-clipped` on each run, and never keep a list of what the show posted.
The Social API holds that record, and a local copy of it goes stale the moment a post goes out.
