---
name: boundaries
description: Shape a scored moment into a clip - set a clean start and end, apply the gates, and cut the words.
---

## Overview

A moment is a passage of a few minutes, and a clip is a span of about a minute inside it.
Only the transcript carries sentence-level times, so only here can that span be cut and judged.
The agent reads the segments around the moment, selects a clean in and out point, and pads each cut
into the silence between segments.
That span is in the clock of the transcript, and it stays there: a YouTube match is translated into the
clock of its file at render time.
The clip MUST pass the gates below, because a moment with substance can still fail as a clip.

## Input

- Each moment from module **discovery**, with its scores and each flag.
- The `SocialPostMediaSource` of each moment from module **media**.
- The `TranscriptSegment` list of each episode, from the Content API.
- Optional: `clip_count`, `min_duration_seconds`, `max_duration_seconds`, and trend context from the caller.

## Output

- The complete `SocialPostMediaSource` of each clip.
- The clip scores, added to the scores of module **discovery**.
- A removal mark on each clip that fails a gate.

## Requirements

- Fountain API.

## Process

1. Load the transcript of the episode with the Content API.
   Load it one time per episode, and use it for each moment of that episode.
2. Read the segments from 90 seconds before the moment to 90 seconds after it.
   A clip can start or end anywhere inside that window, not only at the edges of the moment.
3. Select the in segment and the out segment that give the best clip:

   - The in point starts on the first word of the hook, and never on the words that lead up to it.
     A segment ident, a date, and a speaker naming themselves lead up to it, whatever they open, so
     start after them: a viewer who wanted the show's own opening would already be watching it.
   - The out point ends a complete thought, and never a list, an example, or a question with no answer.

4. Pad each cut into the silence between segments:

   - The in point is `start` of the in segment, minus half the gap to the segment before,
     and never more than 0.25 seconds.
   - The out point is `end` of the out segment, plus half the gap to the segment after,
     and never more than 0.5 seconds.

   The duration is the distance between the two padded cuts, and the duration gate reads that number.

5. Score the clip 1-5 for hook strength, novelty, emotional intensity, shareability, and independence.
   Remove any clip under 18 of 25.
   Score timeliness and platform fit 1-5 as well, but only when the caller gives trend context.
6. Apply the gates below, and remove a clip that fails one.
   Keep the best `clip_count` clips when the caller gives a count, and keep fewer when fewer pass.
   Returning fewer is the right answer and never a shortfall to make up.
7. Join `text` of every segment that overlaps the span, word for word, and write it into `transcript`.
8. Write the span into `ts_start` and `ts_end`, in the clock of the transcript.

## Additional notes

Gates - a clip MUST pass all of them:

- Direct hook - the first 1 to 3 seconds hold the claim, the question, or the surprising words.
- No late payoff - a viewer understands why the clip is important in 5 seconds or less.
- Complete end - the clip stops on a finished thought, and never in the middle of a list or an example.
- Tight duration - the target is 35 to 75 seconds, or the range the caller gives.
  A clip longer than 90 seconds needs a written reason.
- One idea - a clip is one compact claim, and not a wide topic window.

A sentence edge is the usual clean cut, but it is not the rule.
A thought can run across two sentences, and a long sentence can hold a complete thought in its second half.
Move the cut off a sentence edge when the words are better, and never cut in the middle of a word.

A segment edge usually falls between two words, and the gap to the next segment is silence, so each
cut sits inside that gap: a short breath at each end, and never more than half the gap, so two clips
cut from neighbouring segments cannot overlap.
A segment can stop before the speech does, so the out point reaches further than the in point.
Prefer an out point with silence after it, because a segment that abuts the next one leaves nothing to
reach into and the last word is cut.

The transcript carries no word timings, and captions do not need them from here.
Skill **fountain-clip-producer** makes them from the clip's own audio at render time.

`ts_start` and `ts_end` are always in the clock of the transcript.
For a Fountain file that is also the clock of `media`, because both come from one recording.
A YouTube cut runs behind the transcript by an amount that changes at every advertisement break, so
skill **fountain-clip-producer** translates the span there, where it opens the file.
A break inside the clip moves the end alone, so such a clip can fail at render time, after approval.
The renderer reports why, and the answer is a different pair of in and out points, never a shift.
Never end a span on a dangling conjunction - cut before the "and", because a caption must not end on one.

This module does not open `media`.
