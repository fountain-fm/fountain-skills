---
name: framing
description: Crop the landscape master to the target shape, and keep the active speaker in the centre of the frame.
---

## Overview

A vertical clip shows the person who speaks, and not the microphone, the table, or the empty room.
ffmpeg cannot find a face on its own, so this module measures the face and then crops to it.
It cuts a true full-frame crop of the video.
It stops and asks the user when no clean crop exists.

## Input

- `clip-landscape-master.mp4` from module **media**.
- The target shape, which is vertical, square, or landscape.

## Output

- One export for each requested shape, for example `clip-vertical.mp4`.
- A crop plan, with one row for each segment.
- A visual QA report, which module **qa** requires for a vertical export.

## Requirements

- ffmpeg and ffprobe.
- Python 3.11 or later.
- OpenCV 4.8 or later, importable from that same Python, and the first release to carry `FaceDetectorYN`.
- The YuNet model in `assets/models`, which the skill ships and the script finds on its own.

## Process

1. Find the scene cuts and the speaker changes first, because a crop must change on a cut:

   ```bash
   # select keeps each frame that differs enough to be a cut, showinfo prints its time, -f null drops it.
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "select='gt(scene,0.25)',showinfo" \
     -f null - 2>&1 | grep -oE 'pts_time:[0-9.]+'
   ```

2. Measure the face centre of the active speaker over each segment, and never estimate it:

   ```bash
   scripts/extract-face-framing.py clip-landscape-master.mp4 "$SEG_START" "$SEG_END"
   ```

   The script returns `crop_x` directly, already clamped to the frame.
   It stops when two faces share the frame, because one crop would then sit between them.
   Measure each scene-cut segment alone.
   Or, on static footage, run `--speakers 2` and give the anchors to module **shots**.

3. Write the crop plan, with the span, the speaker, the crop box, the face centre, and the reason for each row.
4. Apply the crop.
   When the clip has more than one segment, switch the crop at the cut times:

   ```bash
   # crop uses the cropW and frameH the script measured, scale fits the shape, fps steadies it.
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "crop=$CROP_W:$FRAME_H:'if(lt(t,$CUT_A),$SEG1_X,$SEG2_X)':0,scale=1080:1920,fps=30" \
     -pix_fmt yuv420p -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k -movflags +faststart \
     clip-vertical.mp4
   ```

5. Draw a centre line on a still of each segment, and confirm that the line is on the nose:

   ```bash
   # -frames:v 1 takes one still, and drawbox paints a 4px line down the middle of the crop.
   ffmpeg -hide_banner -y -ss "$T" -i clip-landscape-master.mp4 -frames:v 1 \
     -vf "drawbox=x=$CROP_X+$CROP_W/2-2:y=0:w=4:h=ih:color=lime@1:t=fill" center-check.jpg
   ```

6. Stop when a segment has no clean crop.
   Offer a span that leaves the segment out, and also offer this letterbox.
   Render the letterbox only after the user asks for it:

   ```bash
   # scale fits the whole width and keeps every pixel, and pad centres it in the taller shape.
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \
     -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart \
     clip-vertical.mp4
   ```

7. Make a contact sheet with one frame every 2 seconds, and a full-size frame at each crop change.
   Then sample the export for frames that show no person:

   ```bash
   scripts/visual-person-qa.py --video clip-vertical.mp4 --interval 2 --report visual-qa-report.json
   ```

## Additional notes

- Every sampled frame shows a face and an upper body.
  A frame that shows mostly background or empty room means a failed export.
- A frame that the detector calls empty is not a miss if you open it and find the speaker.
  Say which frame you opened and what you saw, because a detector error MUST NOT block a clean clip.
- A frame with a title card, a graphic, or a cutaway shows no person, because the show put no person in it.
  A cold open on the show's own card is normal for television.
  Name those frames and what each one shows.
  Then the gate records a graphic that the show chose, and not a missing speaker.
- The face sits a little off centre, on the side opposite to the direction it looks.
  Then the face looks into the frame.
- No edge cuts off the face, and the head has space above it.

You MUST NOT deliver a crop segment that nobody looked at.
You MUST NOT letterbox unless the user asks.

The crop stays still inside a shot, and changes only on a cut.
This is true even when the face moves inside the shot.
A crop that moves while the speaker talks looks like a pan across a still frame, and the viewer sees it.

A 9:16 crop fails on a wide two-shot, and it fails on screen content.
The script refuses both, and says which one it found.
Say what is lost.
Offer a letterbox, a blurred fill from module **overlays**, a crop from module **shots**, or a different span.
Render nothing until the user chooses.

The detector finds a turned head and a backlit head.
It is weakest on dark footage and on low contrast.
On that footage, the contact sheet and your own eyes decide.
