---
name: discovery
description: Search a show's transcripts for real moments, and score each one for substance and for fit.
---

## Overview

Discovery decides whether a moment is worth clipping, and not yet how to cut it.
A moment is a group of transcript segments less than 30 seconds apart, which is one continuous passage.
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
- The `ContentHit` of each episode, because it already names the video of that episode.
- The `CanonicalPerson` of the speaker, for a request about a person.

## Requirements

- Skill **fountain-api**.

## Process

1. Load skill **fountain-api**.
   Resolve the show with the Search API if you have only a name.
   The Search API gives a bare id, and the Content API needs the prefixed form, so add the type prefix.
   List the show's episodes with the Content API and remove the duplicates by `_guid`.
2. Choose the route under the rules below: a request about a person takes the vault, and the rest take either.
3. Take the vault route by reading the project's vault ids with the Project API, then loading and updating
   the `ProjectVault` with the Vaults API. Use one vault for the archive, and name it for its scope.
   Top up the archive vault first: add the episodes it misses from step 1, and say the credit cost.
   A vault nobody tops up goes stale, and a stale archive silently narrows every search.
4. Take the direct route instead by loading the transcript of each episode in scope with the Content API.
   Name the episodes the request needs, because this route reads one at a time.
5. Search what the route returned.
   Search the theme, not the proper nouns of a headline, and use short keyword queries.
   Also search for disagreement, predictions, surprising statements, and changes of mind.
   For a kind of moment, search the show's recurring subjects, then let that kind lead the score.
   For an episode, keep only the segments of that episode.
   Use the quote or the approximate time to choose the moment when the caller gives one.
6. For a person, resolve them with the Search API, then keep only the segments that name them in `mentions`.
   Carry the `CanonicalPerson` forward, because module **copy** names the speaker.
7. Join the segments of one episode that touch or overlap, because a passage often returns as two.
   The result is a moment: one continuous passage to judge.
8. Load the posts of these moments' episodes with the Social API, in every lifecycle state.
   Ask per episode and never for the whole show, because a post from another episode cannot overlap.
   Mark a moment `already-clipped` when it overlaps the `source` of one by more than half.
   Compare only with a `source` whose `media` is the `enclosure` of the segments, because the two clocks
   agree only then.
   Advance a marked moment only when the caller or the lessons ask for a new cut.
9. Score each moment 1-10 for controversy, insight, engagement, and relevance.
   Use `topics` and `mentions` when the route returned them, because they show discussion, not a passing word.
   Remove any moment under 24 of 40, then rank what remains and give it to module **media**.

## Additional notes

The vault route returns `TranscriptSearchSegment` with `mentions` and `topics`, and joining an episode
costs a credit for the analysis. The direct route reads `TranscriptSegment` from the Content API:
it has neither field, needs no vault, and suits a request that names its episodes.

Spending a credit is yours to start without asking: say what it cost and what remains as soon as the job
is queued, and never at the end of the run.

Keep every filter on the segments, and group them only when no filter is left.
A filter that runs after the group takes words out of the middle of a moment.

A transcript search finds words and not tone, so the score decides a kind of moment and the query does not.

Judge whether the passage holds something worth clipping, and leave the exact cut to module **boundaries**.
A moment of several touching segments is a longer run on the theme, which is a signal in itself.

The bar here is lower than in module **boundaries**, deliberately: remove only what is clearly weak,
because a moment can improve when it is shaped, and some fail in the later modules.

A posted clip that was cut from another file cannot be compared here, because its `ts_start` is in the
clock of that file. Such a clip is rare, and the cost of missing one is a repeat rather than a wrong clip.

Do not force a match - the speaker MUST discuss the theme directly - and say honestly when nothing has substance.

Prefer surprising statistics, contrarian opinions, strong predictions, myth debunking, and confessions.
Avoid general discussion, long setup, hosts who agree with each other, and abstract talk with no takeaway.

Mark a moment higher-risk for an unverified claim, a legal or defamation risk, an election or geopolitics
claim, a claim about a named person, a price prediction, investment advice, or a quote a trim can mislead with.
Carry the flag and the reason forward, because module **copy** runs the last safety check on the words.

Record the scores, so that a later reader can audit the ranking.
