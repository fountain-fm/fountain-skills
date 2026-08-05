---
name: framing
description: Crop the landscape master to the target shape, and keep the active speaker in the centre of the frame.
---

## Overview

A vertical clip shows the person who speaks, and not the microphone, the table, or the empty room.
ffmpeg cannot find a face on its own, so this module measures the face and then crops to it.
It cuts a true full-frame crop of the video, and it never puts a wide frame on a taller decorated canvas.
Screen content is the one exception, and it takes a letterbox.

## Input

- `clip-landscape-master.mp4` from module **media**.
- The target shape, which is vertical, square, or landscape.

## Output

- One export for each requested shape, for example `clip-vertical.mp4`.
- A crop plan, with one row for each segment.
- A visual QA report, which module **qa** requires for a vertical export.

## Requirements

- ffmpeg and ffprobe.
- Python 3.11 or later, with OpenCV.

## Process

1. Find the scene cuts and the speaker changes first, because a crop must change on a cut:

   ```bash
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "select='gt(scene,0.25)',showinfo" \  # report each frame that differs enough to be a cut
   -f null - 2>&1 | grep -oE 'pts_time:[0-9.]+'
   ```

2. Measure the face centre of the active speaker over each segment, and never estimate it:

   ```bash
   scripts/extract-face-framing.py clip-landscape-master.mp4 "$SEG_START" "$SEG_END"
   ```

   The script returns `crop_x` directly, already clamped to the frame.
   It stops when it finds two separated faces, because one crop then lands between them.
   Measure both with `--speakers 2`, and give the anchors to module **speakers** to plan the cuts.

3. Write the crop plan, with the span, the speaker, the crop box, the face centre, and the reason for each row.
4. Apply the crop, and switch it on the cut times when the clip holds more than one segment:

   ```bash
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "crop=608:1080:'if(between(t,$CUT_A,$CUT_B),$HOST_X,$GUEST_X)':0,scale=1080:1920,fps=30" \
     -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k -movflags +faststart \
     clip-vertical.mp4
   ```

5. Draw a centre line on a still of each segment, and confirm that it lands on the nose:

   ```bash
   ffmpeg -y -ss "$T" -i clip-landscape-master.mp4 -frames:v 1 \
     -vf "drawbox=x=$CROP_X+$CROP_W/2-2:y=0:w=4:h=ih:color=lime@1:t=fill" center-check.jpg
   ```

6. Letterbox a screen-content segment rather than crop it:

   ```bash
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \  # keep every pixel, pad to the shape
   -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart clip-vertical.mp4
   ```

7. Make a contact sheet that samples every 2 seconds, and a full-size frame at each crop change.
8. Sample the export for frames that hold no person:

   ```bash
   scripts/visual-person-qa.py --video clip-vertical.mp4 --interval 2 --report visual-qa-report.json
   ```

## Additional notes

These are the rules for a delivered crop:

- Every sampled frame holds a face and an upper body.
- The face of the active speaker is in the horizontal centre.
- No edge clips the face, and the head keeps room above it.

A frame that is mostly background, table, or empty room is a failed export.
You MUST NOT deliver a crop segment that nobody looked at.

Screen content is a slide, a chart, an article, or a shared screen.
The script reports no face, or it finds only a small inset camera in a corner.
A 9:16 crop of that content is a failed export by definition, because it cuts off the thing the clip exists to show.
The letterbox keeps the whole frame, keeps the corner camera, and leaves the lower band free for captions.
Confirm on a still that the text is still readable, because some screen content does not work as a vertical clip.

The detector misfires on dark footage and on low contrast.
The contact sheet and your own eyes are the authority there, and the script is only evidence.

When no clean crop of talking-head footage is possible, stop before the render.
Record why the crop fails, what is lost, and which layout you propose instead.
A different layout needs the approval of the user.
