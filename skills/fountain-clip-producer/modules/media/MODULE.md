---
name: media
description: Cut the accurate landscape master that every other module of the skill builds on.
---

## Overview

The caller gives a reference and not a file.
This module opens `media`, cuts the span between `ts_start` and `ts_end`, and writes `clip-landscape-master.mp4`.
This module makes no editorial decision, because the caller already chose the span.
A mistake at this step is a sync fault or a timing fault.
Every module after this one inherits the fault.

## Input

- The `SocialPostMediaSource` of the post, which names the file in `media` and the span in `ts_start` and `ts_end`.
- Or the external source of a raw local video for this session.
- The `transcript` of that source, to confirm that the cut holds the expected words.
- The `TranscriptSegment` list from the Content API when `ids` names an episode, a show, and a YouTube video.
- The id of that episode, which names its saved time map.

## Output

- `clip-landscape-master.mp4`, cut to the span and cropped to the camera area.
- Or `clip-base.mp4`, for a source that carries no video.
  This file is the audio of the span on an empty frame of the target shape.
  Module **overlays** then paints on that frame.
- An alignment report, for a source that needed the content check.

## Requirements

- ffmpeg and ffprobe.
- yt-dlp, for a source that ffmpeg cannot seek directly.
  Keep it current, because YouTube changes what a client must send.
  A build a few weeks old gets a 403 error on every download, while the captions still download.
- Python 3.11 or later.

## Process

1. Open `media` and read what kind of source it is.
   You can cut a local file and an HLS playlist directly.
   You cannot cut a watch-page URL directly.
2. Translate the span first when `ids` names an episode, a show, and a YouTube video.
   Its `ts_start` and `ts_end` are in the clock of the Fountain transcript.
   The video file is not in that clock:

   ```bash
   # The cache sits in the workings of the show, so that every clip of that show reads it.
   CACHE_DIR="fountain/outputs/$SHOW/workings/offsets"
   # --build downloads the captions of the video one time and anchors them against the transcript.
   # --cache-dir and --episode read the map this episode already has, and write it when it has none.
   echo "$TRANSCRIPT_JSON" | scripts/build-time-map.py --build "$MEDIA_URL" \
     --cache-dir "$CACHE_DIR" --episode "$EPISODE_ID" > time-map.json
   # --span translates the clip span into the clock of the video, with no further network work.
   echo "$TRANSCRIPT_JSON" | scripts/build-time-map.py --map time-map.json --span "$TS_START" "$TS_END"
   ```

   Cut with the translated span from here on.
   Read the map when `aligned` is false, because there are two different reasons why the two edges
   disagree.
   Check the tail even when `aligned` is true.
   An anchor near the head hides drift that grows towards the end, and the clip then loses its last
   sentence.
   Stop and report when a region boundary is inside the span.
   That means that an advertisement break is inside the clip.
   The fix is a different span, and never a shift.
   When both edges are inside one region, they disagree because of anchor drift.
   In that case, cut the padded window, and use the words of the rough cut to set the edges.
   A Fountain file and an HLS playlist need no translation, because their clock is the clock of the
   transcript.
   A source with only a YouTube video id needs no translation.
   The caller read its span from that video, so the two clocks are the same.
   Empty `ids` and a raw local source also use the clock of `media`.

3. Cut an HLS source with one `-ss` and an explicit program map, always on the tallest video program:

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

4. Fetch a watch-page URL with yt-dlp instead, and take only the padded window:

   ```bash
   # -f takes the best video under 1080p and pairs it with the best audio.
   # --download-sections fetches the window alone, and --force-keyframes-at-cuts lands near the cut.
   # --merge-output-format decides the container, because -o names the file and never the format.
   yt-dlp -f "bestvideo[height<=1080]+bestaudio" \
     --download-sections "*$ROUGH_START-$ROUGH_END" \
     --force-keyframes-at-cuts \
     --merge-output-format mp4 \
     -o clip-rough.mp4 "$MEDIA_URL"
   ```

5. Re-trim the rough cut locally, because neither step 3 nor step 4 is frame-accurate:

   ```bash
   # -ss and -to on a local file give the exact span, measured on the rough cut.
   # The re-encode is what makes this pass frame-accurate, so do not copy the streams.
   ffmpeg -hide_banner -y -i clip-rough.mp4 \
     -ss "$TS_START_LOCAL" -to "$TS_END_LOCAL" \
     -c:v libx264 -crf 18 -c:a aac -movflags +faststart \
     clip-landscape-master.mp4
   ```

6. Confirm the cut holds the expected words, for a source that carries advertisements of its own:

   ```bash
   scripts/verify-content-alignment.py --video-url "$MEDIA_URL" \
     --start "$TS_START" --end "$TS_END" --expected-text "$SOURCE_TRANSCRIPT"
   ```

   Stop and report to the user when the score is under the threshold.

7. Inspect a still of the master for a show frame, a border, a sidebar, or a decorative background.
   Measure the inset, and crop to the camera area before any other module runs.
8. Run ffprobe on the master, and confirm the duration, the audio stream, and the height of the tallest rendition.
9. Build an empty base instead when the source carries no video at all.
   Every module after this one paints onto a frame, and such a source has none:

   ```bash
   # -f lavfi draws an empty frame of the target shape, and -shortest ends it with the audio.
   # The frame is black because the audiogram package covers it; nothing here is ever seen.
   ffmpeg -hide_banner -y -f lavfi -i color=c=black:s=1080x1920 -ss "$TS_START" -to "$TS_END" \
     -i "$SOURCE" -shortest -map 0:v -map 1:a \
     -c:v libx264 -preset veryfast -crf 20 -c:a aac -movflags +faststart clip-base.mp4
   ```

## Additional notes

The deliverable is always edge-to-edge camera video.
An export that still shows the graphic frame of the show is a failed export.
This module prevents that fault.

Never give an HLS video and an HLS audio playlist their own `-ss`.
Many masters carry the audio as a separate rendition whose segments do not line up with the video.
Two seeks then go to two different real positions, and ffmpeg muxes the two streams with a constant offset.
The result looks like lip-sync drift of several seconds.
The offset is constant for the whole clip, and a quick look misses it.

A bare master playlist with no map makes ffmpeg take the lowest bandwidth, which is often 360p.
A vertical crop keeps about a third of the width.
Thus 720p gives 405x720 of real picture for a 1080x1920 delivery, and 1080p gives 608x1080.
No later module can put back picture that this module did not fetch.

The map of an episode does not change, and one episode gives several clips over the weeks.
Thus the cache saves the caption download and the anchoring for every clip after the first.
The cached maps are working files, and never settings.
A run that finds no cache measures the map as before, and is only slower.
The cache returns a map only when that map names the same video, because an episode whose video
changed needs a new map.
The cache holds one file for each episode.
Each worker writes only the file of the episode that it is clipping.
Thus workers on different episodes cannot lose each other's maps.
This layout exists because the day's clips are from three different episodes, and the workers measure
them at the same time.

The time map exists because the two files hold the same words at different times.
A podcast inserts its advertisements into the audio, and the video carries a different set.
Thus the distance between the two clocks changes at every break.
One offset for the whole episode is therefore wrong, so the map records each region separately.
The map costs one caption download of approximately 6 seconds, whatever the length of the episode.
A low `anchor_coverage` means that the captions and the transcript disagree.
Usually, that means that the video is not the episode.
Stop and report it, because the cut would hold the wrong words.

To confirm sync on an HLS source, cut a short reference and compare the audio envelopes.
Use a window of at least ±5 seconds, because a narrow window reports a small wrong offset and hides a large one.

This module also serves a rough cut, which the caller can use to check a span against real audio.
