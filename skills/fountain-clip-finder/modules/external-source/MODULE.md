---
name: external-source
description: Read a video that Fountain does not hold, as transcript segments in the clock of that video.
---

## Overview

A talk on YouTube can be worth clipping when it never reached the podcast feed.
Fountain holds no episode for it, so the Search API finds nothing and no transcript can be loaded.
This module reads the caption track of the video instead, and groups it into segments shaped like a
`TranscriptSegment`, so that the modules after it work as they do on an episode.
Those times are the clock of the video itself, so nothing translates the span at render time.

## Input

- One or more video URLs, which the user gives.
  This module never searches for a video, because the request already names it.

## Output

- An external source for each video: `media`, the video title, and the segments.
  An external source is a `SocialPostMediaSource` without `ids`, because no episode and no show hold
  the video. The modules after this one fill `transcript`, `ts_start` and `ts_end`.
- The caption track that each set of segments came from, manual or automatic.

## Requirements

- yt-dlp.

## Process

1. Read the captions of each video:

   ```bash
   scripts/fetch-captions.py "$VIDEO_URL" > external-source.json
   ```

   The script prefers the track the channel uploaded, and falls back to the generated one.
   Stop and tell the user when a video has no English track, because nothing here can read that video.

2. Read the title, the duration, and the publish date of the video, so that module **copy** can credit it:

   ```bash
   # --skip-download reads the metadata of the watch page and fetches no media.
   yt-dlp --skip-download --print "%(title)s | %(duration)s | %(channel)s | %(upload_date)s" "$VIDEO_URL"
   ```

3. Confirm that the segments cover the video: the last segment MUST end near the duration above.
   A track that stops early holds a part of the talk, so say which part the search reaches.
4. Write `media` as the watch page URL the user gave.
   Give the segments and `media` to module **discovery** as the passages to score.

## Additional notes

The captions are read again in each session, and never kept, because the video is the record and this
is a reading of it.

A speaker is named on the stage and not in the captions, so the transcript names nobody here either.
The video title usually names the speaker, and module **copy** takes the name from there.

An automatic track times a line rather than a word, and it punctuates by guess.
Two consequences follow, and both belong to the modules after this one:

- A segment edge sits within about a second of the speech, so an external span is padded further than
  an episode span, and skill **fountain-clip-producer** settles the exact edge on the render.
- The words are heard by a machine, so a name or a number in a quote MUST be confirmed on the video
  before it goes into a post.

A video with no caption track at all can still be clipped, but not by this skill: the user has to
transcribe it first, and nothing here does that.
