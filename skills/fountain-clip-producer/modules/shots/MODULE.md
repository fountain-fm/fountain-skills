---
name: shots
description: Decide which shot the clip holds when one frame carries two people, and keep the cuts continuous.
---

## Overview

Some footage never cuts.
A boxed side-by-side layout keeps one frame for the whole clip.
So does a locked-off wide shot of two people at a table.
Scene detection then finds no cut, and module **framing** keeps one crop.
This module supplies the missing signal.
The words tell who speaks.
This module turns that into a cut list, with the geometry for each shot.

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
   The plan guesses that the first speaker is on the left.
   Check one still, and correct the sides:

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

One ffmpeg filter cannot change the crop size at a cut, because the output size is fixed for the whole pass.
So the segments are rendered one at a time and then joined.
This is also what gives each speaker their own geometry.

These rules make one frame look like two cameras:

- Both faces end the same size on screen.
  This rule matters most, because a difference in face size shows most clearly that the shots share one frame.
  Each crop is sized from that speaker's own measured face, so a small face takes a tighter crop.
- Both faces sit at the same height, so the eye line holds across the cut.
- Each face sits away from the centre, on the side opposite to the direction it looks.
  Then the speaker looks into the frame.
- The cut comes a moment before the first word, as an editor cuts on the breath.
- A short answer never gets a cut, so the clip does not cut back for every "yes".
- No shot is held for less than the dwell, so the clip does not cut back and forth in a quick exchange.

You MUST cut.
You MUST NOT slide from one speaker to the other.
The background does not move in this footage, so a slide shows the audience that both shots come from one frame.

An exchange can be too quick to cut, and that is a valid result.
The plan then holds one shot, and says so.
For that clip, offer the user a two-shot or a letterbox, and do not force a cut list onto it.
The choice between the two is not yours, because each one changes how the viewer sees the clip.

This module needs the speaker of each word, and no source gives it.
Whisper hears the words, but not who says them.
The episode transcript does not name the speakers either.
That is a gap in the word data and not a fault of the render, so a new render does not fix it.

A clip without speaker labels can still get a crop.
Read the words of the refused segment first, because a frame that shows two people often has only one voice.
When the words are one uninterrupted utterance, a single crop is correct, and only the seat is still open.
An edit cuts to the person who starts to speak.
So when the next speaker's first word falls on the cut, the shot after the cut shows that speaker.
The seat that matches that shot is then not the seat of the person who talks in the wide shot.
Match the seat on a still of each.
Stop when the words change speaker inside the segment.
