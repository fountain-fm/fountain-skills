---
name: pace
description: Play a clip a little faster, at one speed or at a speed that follows how fast the speaker talks.
---

## Overview

A slow speaker makes a slow clip, and a viewer scrolls past a slow clip.
This module plays the clip faster, and keeps the pitch of the voice.
It plays the whole clip at one speed, or it gives each phrase its own speed.
A phrase starts and ends in a pause, so the speed never changes inside a word.
It changes time, so every module after it works on the new timeline.

## Input

- The word timings of the clip, and its duration.
  Use the rebased list of module **trims**, when that module cut the clip.
- `clip-landscape-master.mp4` from module **media**, or the trimmed master of module **trims**.
- One speed, e.g. 1.1, or a target rate in syllables a second, e.g. 5.
  The request gives it, or the Brand section of the preferences records it for the show.

## Output

- A pace plan, with the speed of each segment and the duration before and after.
- The word timings on the new timeline.
- The paced master, joined from the segments.

## Requirements

- Fountain API.
- ffmpeg and ffprobe.
- Python 3.11 or later.

## Process

1. Load the preferences with the Project API, and read the pace of the show from the Brand section.
   A pace that the request gives replaces the recorded one.
2. Plan the pace.
   Give `--speed` for one speed, or `--target-rate` for a speed that follows the speaker:

   ```bash
   # ffprobe gives the frame rate as a fraction, e.g. 30000/1001, and the plan counts frames in it.
   FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 \
     clip-landscape-master.mp4)
   
   scripts/plan-pace.py --words words.json --duration 50.48 --fps "$FPS" --target-rate 5 \
     --out pace-plan.json
   ```

3. Read every warning.
4. Render each segment of the plan with its own speed, all with the same settings, then join them:

   ```bash
   # -nostdin stops ffmpeg from reading the next lines of the loop as keys.
   # -ss and -to before -i cut the segment from the master.
   # setpts divides each frame time by the speed, and fps keeps the frame rate of the master.
   # tpad repeats the last frame, so a segment that is one frame short still reaches its count.
   # atempo changes the speed of the audio and keeps its pitch, and apad fills a short end with silence.
   # -frames:v and -t stop both streams on the frame count of the plan.
   # -crf 18 and the aac bitrate match module **trims**, so the segments join without a second encode.
   python3 -c "import json; [print(f'{i:02d}', s['start'], s['end'], s['speed'], s['frames'], s['length']) \
     for i, s in enumerate(json.load(open('pace-plan.json'))['segments'])]" \
     | while read -r INDEX START END SPEED FRAMES LENGTH; do
       ffmpeg -nostdin -hide_banner -y -ss "$START" -to "$END" -i clip-landscape-master.mp4 \
         -vf "setpts=(PTS-STARTPTS)/$SPEED,fps=$FPS,tpad=stop_mode=clone:stop=1" \
         -af "asetpts=PTS-STARTPTS,atempo=$SPEED,apad" -frames:v "$FRAMES" -t "$LENGTH" \
         -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k "pace-$INDEX.mp4"
     done
   
   # The concat demuxer reads one "file ..." line for each segment, in play order.
   printf "file '%s'\n" pace-*.mp4 > pace-segments.txt
   
   # -c copy is safe here, because every segment was just encoded the same way.
   ffmpeg -hide_banner -y -f concat -safe 0 -i pace-segments.txt -c copy clip-landscape-paced.mp4
   ```

5. Give the words of the plan to module **captions**, and the paced master to every module after this one.
   Give `max_speed` to module **captions** as `--speed`, because a faster clip has more words a second.
   Give `duration.after` to module **qa** as the expected duration.
6. Listen to the start of each segment, and confirm that no change of speed is easy to hear.

## Additional notes

You MUST NOT change the pace unless the request asks for it, or the Brand section of the preferences
records a pace for the show.
A faster clip is requested work, the same as a crop or an overlay.
Record the pace in the Brand section when the user asks to keep it for later clips.

Use module **trims** before this module, because a trim plan reads the timings of the original audio.

The default range is 1.0 to 1.25.
At 1.0, the plan never slows a speaker down.
Above 1.25, most voices start to sound wrong, and the user hears the edit.
Raise `--max-speed` only when the user asks, and listen to the result.

A target rate of 4.5 to 5 syllables a second is a quick, natural pace for conversation.
A phrase that is already faster than the target plays at 1.0.
The syllable count is an estimate from the letters of each word, so compare phrases with it,
and never quote it as a measurement.

A phrase grows over the next pause until it lasts two seconds.
A speed that changes every second sounds like a fault, and not like a style.

Give the plan the word timings of the recogniser.
A caption stream often ends each word where the next word starts, so it holds no pause.
Then the whole clip is one phrase, and the plan says so.

This module changes the speed of the speech, and never the words.
Thus, unlike a trim, it cannot make the speaker seem to say something that they did not say.
