---
name: boundaries
description: Shape a scored moment into a clip - set a clean start and end, apply the gates, and cut the words.
---

## Overview

A moment marks where the search matched, and not where a sentence starts or stops.
Only the transcript shows the words around it, so only here can a clip be shaped and judged.
A script offers every clean pair of start and end points inside the duration range, and the agent selects one.
The clip then MUST pass the gates below, because a moment with substance can still fail as a clip.

## Input

- Each moment from module **discovery**, with `content_id`, `moment_start_seconds`, and `moment_end_seconds`.
- The scores and each flag from module **discovery**.
- Optional: `clip_count`, `min_duration_seconds`, `max_duration_seconds`, and trend context from the caller.

## Output

- `start_time_seconds` and `end_time_seconds` - the clean span.
- `transcript` - the text of the span, with the speaker labels and word timings the transcript holds.
- The clip scores, added to the scores of module **discovery**.
- A removal mark on each clip that fails a gate.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.

## Process

1. Load skill **fountain-api** and load the episode transcript with the Content API.
   Load it one time per episode, then use it for each moment of that episode.
2. Give the transcript to the script and read the pairs it finds:

   ```bash
   echo "$TRANSCRIPT_JSON" | scripts/find-clip-boundaries.py --moment-start 820.06 --moment-end 858.56
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
6. Cut the words of the span, and carry them forward with the span and the scores:

   ```bash
   echo "$TRANSCRIPT_JSON" | scripts/find-clip-boundaries.py --span 812.40 869.10
   ```

## Additional notes

Gates.
A clip MUST pass all of them:

- Direct hook - the first 1 to 3 seconds hold the claim, the question, or the surprising words.
- No late payoff - a viewer understands why the clip is important in 5 seconds or less.
- Complete end - the clip stops on a finished thought, and never in the middle of a list or an example.
- Tight duration - the target is 35 to 75 seconds, or the range the caller gives.
  A clip longer than 90 seconds needs a written reason.
- One idea - a clip is one compact claim, and not a wide topic window.

A sentence edge is the usual clean cut, but it is not the rule.
A thought can run across two sentences, and a long sentence can hold a complete thought in its second half.
Move the cut off a sentence edge when the words are better, and never cut in the middle of a word.

The transcript times mark speech, not silence.
Give the start a short pause before the first word, and the end a short pause after the last.

The script prefers the transcript that Fountain generated, because it comes from the episode audio.
Its times therefore agree with the media.
A transcript that the feed declares can be off by minutes, because the feed can carry a different advertisement cut.
Such a clip looks correct on paper and holds the wrong words.

Only the transcript that Fountain generated holds word timings, and captions need them.
Tell the user that captions need a generated transcript, which the Content API meters.

This module does not open the media.
