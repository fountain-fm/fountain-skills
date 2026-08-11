---
name: shots
description: Decide which shot the clip holds when one frame carries two people, and keep the cuts continuous.
---

## Overview

Some footage never cuts.
A boxed side-by-side layout and a locked-off wide shot of two people at a table both hold one frame
for the whole clip, so scene detection finds nothing and module **framing** holds one crop.
This module supplies the missing signal.
The words say who speaks, and this module turns that into a cut list with the geometry for each shot.

## Input

- The anchors of module **framing**, one for each speaker, with `face_cx`, `face_cy`, and `face_h`.
- The word timings of the clip, where each word carries the speaker that said it.
- The duration of the clip, and the target size.

## Output

- A crop plan, with one segment for each held shot and the crop box of that shot.
- The render commands, because the segments are cut apart and joined again.
- The vertical export, joined from those segments, in place of the single crop of module **framing**.
- A warning for each rule that the footage broke.

## Requirements

- Python 3.11 or later.
- ffmpeg, to render and join the segments.

## Process

1. Measure both speakers with module **framing**, and confirm that it reports two anchors.
2. Plan the cut list:

   ```bash
   scripts/plan-shots.py --anchors anchors.json --words words.json \
     --duration 50.48 --emit-commands --out crop-plan.json
   ```

3. Read `sides` in the plan, and confirm that each speaker sits on the side the plan gives them.
   The plan guesses that the first speaker is on the left, so check one still and correct it:

   ```bash
   scripts/plan-shots.py … --map "A=right,B=left"
   ```

4. Read every warning before you render, because each one names a cut that will look wrong.
5. Render each segment on its own, with the commands that `--emit-commands` printed.
6. List the segments in order, then join them:

   ```bash
   # The concat demuxer reads one "file ..." line for each segment, in play order.
   printf "file '%s'\n" seg-*.mp4 > segments.txt
   
   # -f concat joins the list, -safe 0 accepts the paths, and -c copy avoids a second encode
   # because every segment already carries the same codec and size.
   ffmpeg -hide_banner -y -f concat -safe 0 -i segments.txt -c copy clip-vertical.mp4
   ```

7. Watch each cut at full speed, and confirm that the head size and the eye line hold across it.

## Additional notes

A cut change of crop size cannot happen inside one ffmpeg filter, because the output size is fixed
for the whole pass.
The segments are therefore rendered one at a time and joined, which is also what gives each speaker
their own geometry.

These are the rules that make one frame read as two cameras:

- Both faces end the same size on screen, which is the strongest tell of all.
  Each crop is sized from that speaker's own measured face, so a small face takes a tighter crop.
- Both faces sit at the same height, so the eye line holds across the cut.
- Each face sits away from the centre, on the side it looks away from, so the speaker looks into the frame.
- The cut lands a moment before the first word, the way an editor cuts on the breath.
- A short answer never earns a cut, so a clip does not flick back for every "yes".
- No shot is held for less than the dwell, so a quick exchange does not swing between the two.

You MUST cut, and you MUST NOT slide from one speaker to the other.
The background does not move in this footage, so a slide shows the audience that one frame is behind both shots.

An exchange too quick to cut is a real outcome, and the plan then holds one shot and says so.
Offer the user a two-shot or a letterbox for that clip rather than force a cut list onto it.
Neither one is yours to choose, because both change how the clip reads.

This module needs the speaker of each word, and nothing supplies one: whisper hears the words and not
who says them, and the episode transcript names nobody either.
That is a gap in the words and not a fault of the render, so no new render fixes it.

No speaker labels does not always mean no crop.
Read the words of the refused segment first, because a frame that holds two people often holds one voice.
When they carry one uninterrupted utterance, a single crop is right after all, and only the seat is open.
An edit cuts to the person who starts to speak, so when the next speaker's first word lands on the cut,
the shot after it holds that speaker, and the seat that matches it is not the one talking in the wide shot.
Match the seat on a still of each, and stop when the words change speaker inside the segment.
