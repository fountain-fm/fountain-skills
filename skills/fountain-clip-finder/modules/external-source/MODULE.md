---
name: external-source
description: Read a video that Fountain does not hold, as transcript segments in the clock of that video.
---

## Overview

A talk on YouTube and an episode that is not published yet have the same problem.
Fountain holds no episode for either, so the Search API finds nothing and no transcript can be loaded.
This module reads the words from the best source of the video: the caption track of a watch page, a
subtitle file beside a local video, or whisper on the audio of that video.
The module groups the words into segments like a `TranscriptSegment`, so the later modules work as on an episode.
Those times are the clock of the video itself, so nothing translates the span at render time.

## Input

- One or more videos, each named as a watch page URL or as the path of a file on this machine.
  This module never searches for a video, because the request already names it.
- Optional: a subtitle file for a local video, when it does not sit beside the video.

## Output

- A partial `SocialPostMediaSource` for each media URL, with `ids` and `media`.
  The title and the segments go with it to the later modules.
  A YouTube watch page uses its `youtube:video:<id>`, and another external URL uses empty `ids`.
  The modules after this one fill `transcript`, `ts_start` and `ts_end`.
- An external source for each local video, with its path, title, and segments.
  A raw local path is not a valid `media` URL, so it cannot be stored on the post.
- The source of each set of segments.
  The source decides how far a span is padded, and how much a quote from it can be trusted.

## Requirements

- Python 3.11 or later, for every input, because the script of this module does the reading.
- yt-dlp, for a watch page URL.
- ffmpeg built with whisper, and a whisper.cpp model, for a local video that has no subtitle file.
  Skill **fountain-clip-producer** names both, and its module **preflight** finds them.
  A machine with neither still runs every other input of this skill.

## Process

1. Read the words of each video:

   ```bash
   scripts/read-segments.py "$VIDEO" > external-source.json
   ```

   `$VIDEO` is the watch page URL or the path of the file.
   For a watch page, the script reads the track that the channel uploaded.
   When there is no such track, it reads the generated track.
   For a local video, the script reads a subtitle file beside the video.
   When there is no subtitle file, it transcribes the audio.
   Name a subtitle file that is not beside the video with `--subtitles`.
   Stop and tell the user when a watch page has no English track, because nothing here can read it.

2. Read the title, the duration, and the publish date, so that module **copy** can credit the video:

   ```bash
   # --skip-download reads the metadata of the watch page and fetches no media.
   yt-dlp --skip-download --print "%(title)s | %(duration)s | %(channel)s | %(upload_date)s" "$VIDEO_URL"
   ```

   A local file has no such record, so ask the user who speaks and what the video is.
   Never take either from the file name.

3. Confirm that the segments cover the video.
   The last segment MUST end near the duration.
   A subtitle file or a caption track that stops early holds only a part of the talk.
   Say which part the search reaches.
4. Write `media` as the URL or the path the user gave.
   For a YouTube watch page, set `ids` to an array that contains only `youtube:video:<id>`.
   Use the video id from the watch page URL.
   Never put the watch page URL in `ids`, and never leave `ids` empty for a YouTube watch page.
   For another media URL, write empty `ids`.
   Keep a raw local path as an external source for this session, and do not call it a `SocialPostMediaSource`.
   Give the segments and `media` to module **discovery** as the passages to score.

## Additional notes

The module reads the words again in each session, and never keeps them.
The video is the record, and the segments are only a reading of it.

A speaker is named on the stage, and not in a transcript.
Thus this transcript also names no speaker.
The title of a watch page usually names the speaker, and module **copy** takes the name from there.

The three readings are not equally good.
The later modules need to know which reading they have:

- A subtitle file the show wrote itself is the best, because a person checked the words.
- A whisper transcript gives the times of the speech and adds punctuation.
  Thus a span cuts as cleanly as a span from an episode.
  But the words are still a machine transcription.
- An automatic caption track gives the time of a line and not of a word, and it guesses the punctuation.
  Thus a span from such a track is padded further.
  A name or a number in its machine transcription MUST be confirmed on the video.

A local video is a file and not an address.
Thus the clip MUST be rendered on the machine that holds the file, and no later session can find the file there.

An episode that is not published yet becomes an episode on the day it publishes.
After that day, clip it from the episode.
The post then has `source`, so the work is not limited to one session.
