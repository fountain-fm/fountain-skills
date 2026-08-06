---
name: media
description: Cut the accurate landscape master that every other module of the skill builds on.
---

## Overview

The caller gives a reference and not a file.
This module opens `media`, cuts the span between `ts_start` and `ts_end`, and writes `clip-landscape-master.mp4`.
There is no editorial judgment here, because the span is already settled.
A mistake at this step is a sync fault or a timing fault, and every module after it inherits the fault.

## Input

- The `SocialPostMediaSource` of the post, which names the file in `media` and the span in `ts_start` and `ts_end`.
- The `transcript` of that source, to confirm that the cut holds the expected words.

## Output

- `clip-landscape-master.mp4`, cut to the span and cropped to the camera area.
- An alignment report, for a source that needed the content check.

## Requirements

- ffmpeg and ffprobe.
- yt-dlp, for a source that ffmpeg cannot seek directly.
- Python 3.11 or later.

## Process

1. Open `media` and read what kind of source it is.
   A local file and an HLS playlist are cuttable directly, and a watch-page URL is not.
2. Cut an HLS source with one `-ss` and an explicit program map, always on the tallest video program:

   ```bash
   # -show_entries lists each program with the size of its video, and the tallest of them wins.
   PROGRAM=$(ffprobe -v error -show_entries program=program_id:stream=width,height,codec_type \
     -of json "$MEDIA_URL" | python3 -c "import json,sys; ps=json.load(sys.stdin)['programs']; \
     print(max((max((s.get('height') or 0) for s in p['streams']), p['program_id']) for p in ps)[1])")
   
   # -ss before -i seeks the master one time, so the video and its audio group move together.
   # -map takes the chosen program, which pairs that video with its own audio.
   # -t fetches the span alone, and never the whole episode.
   # -crf 18 and the aac bitrate keep the master good enough for every module after this one.
   ffmpeg -hide_banner -y -ss "$ROUGH_START" -i "$MEDIA_URL" \
     -map "0:p:$PROGRAM:v:0" -map "0:p:$PROGRAM:a:0" -t "$ROUGH_DURATION" \
     -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k \
     -movflags +faststart clip-rough.mp4
   ```

3. Fetch a watch-page URL with yt-dlp instead, and take only the padded window:

   ```bash
   # -f takes the best video under 1080p and pairs it with the best audio.
   # --download-sections fetches the window alone, and --force-keyframes-at-cuts lands near the cut.
   yt-dlp -f "bestvideo[height<=1080]+bestaudio" \
     --download-sections "*$ROUGH_START-$ROUGH_END" \
     --force-keyframes-at-cuts \
     -o clip-rough.mp4 "$MEDIA_URL"
   ```

4. Re-trim the rough cut locally, because neither step 2 nor step 3 is frame-accurate:

   ```bash
   # -ss and -to on a local file give the exact span, measured on the rough cut.
   # The re-encode is what makes this pass frame-accurate, so do not copy the streams.
   ffmpeg -hide_banner -y -i clip-rough.mp4 \
     -ss "$TS_START_LOCAL" -to "$TS_END_LOCAL" \
     -c:v libx264 -crf 18 -c:a aac -movflags +faststart \
     clip-landscape-master.mp4
   ```

5. Confirm the cut holds the expected words, for a source that carries advertisements of its own:

   ```bash
   scripts/verify-content-alignment.py --video-url "$MEDIA_URL" \
     --start "$TS_START" --end "$TS_END" --expected-text "$SOURCE_TRANSCRIPT"
   ```

   Stop and report to the user when the score is under the threshold.

6. Inspect a still of the master for a show frame, a border, a sidebar, or a decorative background.
   Measure the inset and crop to the camera area before any other module runs.
7. Run ffprobe on the master, and confirm the duration, the audio stream, and the height of the tallest rendition.

## Additional notes

The deliverable is always edge-to-edge camera video.
An export that still shows the graphic frame of the show is a failed export, and this module prevents it.

Never give an HLS video and an HLS audio playlist their own `-ss`.
Many masters carry the audio as a separate rendition whose segments do not line up with the video.
Two seeks then land at two real positions, and ffmpeg muxes them with a constant offset.
That reads as lip-sync drift of several seconds, it is constant for the whole clip, and a quick look misses it.

A bare master playlist with no map makes ffmpeg take the lowest bandwidth, which is often 360p.
A vertical crop keeps about a third of the width, so 720p gives 405x720 of real picture for a 1080x1920
delivery, and 1080p gives 608x1080. No later module puts back what this one did not fetch.

To confirm sync on an HLS source, cut a short reference and compare the audio envelopes.
Use a window of at least ±5 seconds, because a narrow window reports a small wrong offset and hides a large one.

This module also serves a rough cut, which the caller can use to check a span against real audio.
