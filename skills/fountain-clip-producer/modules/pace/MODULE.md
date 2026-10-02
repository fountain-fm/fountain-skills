---
name: pace
description: Play a clip a little faster, and keep the pitch of the voice.
---

## Overview

A slow speaker makes a slow clip, and a viewer scrolls past a slow clip.
This module plays the whole clip at one faster speed, and keeps the pitch of the voice.
It changes time, so every module after it works on the new timeline.

## Input

- The word timings of the clip, and its duration.
  Use the rebased list of module **trims**, when that module cut the clip.
- `clip-landscape-master.mp4` from module **media**, or the trimmed master of module **trims**.
- A speed, e.g. 1.1.
  The request gives it, or the Brand section of the preferences records it for the show.

## Output

- A pace plan, with the speed, the frame count, and the duration before and after.
- The word timings on the new timeline.
- The paced master.

## Requirements

- Fountain API.
- ffmpeg and ffprobe.
- Python 3.11 or later.

## Process

1. Load the preferences with the Project API, and read the pace of the show from the Brand section.
   A speed that the request gives replaces the recorded one.
2. Plan the pace:

   ```bash
   # ffprobe gives the frame rate as a fraction, e.g. 30000/1001, and the plan counts frames in it.
   FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 \
     clip-landscape-master.mp4)
   
   scripts/plan-pace.py --words words.json --duration 50.48 --fps "$FPS" --speed 1.1 --out pace-plan.json
   ```

3. Read every warning.
4. Render the master at the speed of the plan:

   ```bash
   SPEED=$(python3 -c "import json; print(json.load(open('pace-plan.json'))['speed'])")
   FRAMES=$(python3 -c "import json; print(json.load(open('pace-plan.json'))['frames'])")
   
   # setpts divides each frame time by the speed, and fps keeps the frame rate of the master.
   # tpad repeats the last frame, so a clip that is one frame short still reaches its count.
   # atempo changes the speed of the audio and keeps its pitch, and apad fills a short end with silence.
   # -frames:v and -shortest stop both streams on the frame count of the plan.
   # -crf 18 and the aac bitrate match module **media**, so the paced master is as good as the master.
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 \
     -vf "setpts=PTS/$SPEED,fps=$FPS,tpad=stop_mode=clone:stop=1" -af "atempo=$SPEED,apad" \
     -frames:v "$FRAMES" -shortest \
     -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k clip-landscape-paced.mp4
   ```

5. Give the words of the plan to module **captions**, and the paced master to every module after this one.
   Give `speed` to module **captions** as `--speed`, because a faster clip has more words a second.
   Give `duration.after` to module **qa** as the expected duration.
6. Listen to the paced master, and confirm that the voice still sounds natural.

## Additional notes

You MUST NOT change the pace unless the request asks for it, or the Brand section of the preferences
records a pace for the show.
A faster clip is requested work, the same as a crop or an overlay.
Record the pace in the Brand section when the user asks to keep it for later clips.

Use module **trims** before this module, because a trim plan reads the timings of the original audio.

The range is 1.0 to 1.25.
At 1.0, the plan never slows a speaker down.
Above 1.25, most voices start to sound wrong, and the user hears the edit.
Raise `--max-speed` only when the user asks, and listen to the result.

This module changes the speed of the speech, and never the words.
Thus, unlike a trim, it cannot make the speaker seem to say something that they did not say.
