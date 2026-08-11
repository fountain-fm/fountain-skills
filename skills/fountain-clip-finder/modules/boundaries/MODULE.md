---
name: boundaries
description: Shape a scored moment into a clip - set a clean start and end, apply the gates, and cut the words.
---

## Overview

A moment is a passage of a few minutes, and a clip is a span of about a minute inside it.
Only the transcript carries sentence-level times, so only here can that span be cut and judged.
A script offers every clean pair of start and end points inside the duration range, and the agent selects one.
That span is in the clock of the transcript, so this module then places it in `media` with the time map.
The clip MUST pass the gates below, because a moment with substance can still fail as a clip.

## Input

- Each moment from module **discovery**, with its scores and each flag.
- The `SocialPostMediaSource` of each moment from module **media**, and its time map when it has one.
- The `TranscriptSegment` list of each episode, from the Content API.
- Optional: `clip_count`, `min_duration_seconds`, `max_duration_seconds`, and trend context from the caller.

## Output

- The complete `SocialPostMediaSource` of each clip.
- The clip scores, added to the scores of module **discovery**.
- A removal mark on each clip that fails a gate.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.

## Process

1. Load skill **fountain-api** and load the transcript of the episode with the Content API.
   Load it one time per episode, write it to a file, and use that file for each moment of that episode.
2. Give the transcript to the script and read the pairs it finds:

   ```bash
   scripts/find-clip-boundaries.py --moment-start 820.06 --moment-end 858.56 < transcript.json
   ```

   Add `--min-dur` and `--max-dur` when the caller gives a duration range.
   The script uses 35 and 75 seconds when you do not, which is the default of the duration gate.

3. Select the pair that gives the best clip:

   - The in point starts on the first word of the hook, and never on the words that lead up to it.
   - The out point ends a complete thought, and never a list, an example, or a question with no answer.

4. Score the clip 1-5 for hook strength, novelty, emotional intensity, shareability, and independence.
   Remove any clip under 18 of 25.
   Score timeliness and platform fit 1-5 as well, but only when the caller gives trend context.
5. Apply the gates below, and remove a clip that fails one.
   Keep the best `clip_count` clips when the caller gives a count, and keep fewer when fewer pass.
   Returning fewer is the right answer and never a shortfall to make up.
6. Cut the text of the span and write it into `transcript`:

   ```bash
   scripts/find-clip-boundaries.py --span 812.40 869.10 < transcript.json
   ```

7. Write the span into `ts_start` and `ts_end`.
   For a moment that has a time map, translate the span first, because the span is in another clock:

   ```bash
   echo "$TRANSCRIPT_JSON" | ../../scripts/build-time-map.py --map "$TIME_MAP" --span 812.40 869.10
   ```

   Remove the clip when `aligned` is false, and give the user the note that says why.

## Additional notes

Gates - a clip MUST pass all of them:

- Direct hook - the first 1 to 3 seconds hold the claim, the question, or the surprising words.
- No late payoff - a viewer understands why the clip is important in 5 seconds or less.
- Complete end - the clip stops on a finished thought, and never in the middle of a list or an example.
- Tight duration - the target is 35 to 75 seconds, or the range the caller gives.
  A clip longer than 90 seconds needs a written reason.
- One idea - a clip is one compact claim, and not a wide topic window.
- Placed in the media - the two edges of the clip agree on where it sits in `media`.

A sentence edge is the usual clean cut, but it is not the rule.
A thought can run across two sentences, and a long sentence can hold a complete thought in its second half.
Move the cut off a sentence edge when the words are better, and never cut in the middle of a word.

A segment edge already falls between two words, and the gap to the next segment is silence, so the
script places each cut inside that gap: a short breath at each end, and never more than half the gap,
so two clips cut from neighbouring segments cannot overlap.
An edge therefore needs no checking here, and a clip that opens on the tail of a word is not a cut this
module can make.

The transcript carries no word timings, and captions do not need them from here.
Skill **fountain-clip-producer** makes them from the clip's own audio at render time.

`ts_start` and `ts_end` MUST always be in the clock of `media`.
A YouTube cut runs behind the transcript by an amount that changes at every advertisement break.
The placement gate therefore reads both edges, because a break inside the clip moves the end alone.
Such a clip cannot be shifted, only removed, and the answer is a different pair of in and out points.
Never end a span on a dangling conjunction - cut before the "and", because a caption must not end on one.

This module does not open `media`.
