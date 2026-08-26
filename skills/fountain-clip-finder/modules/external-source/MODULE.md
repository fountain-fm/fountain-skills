---
name: external-source
description: Read a video that Fountain does not hold, as transcript segments in the clock of that video.
---

## Overview

A talk on YouTube and an episode that is not published yet have the same problem.
Fountain holds no episode for either, so the Search API finds nothing and no transcript can be loaded.
This module reads the words from the best source the video has - the caption track of a watch page, a
subtitle file beside a local video, or whisper on the audio of that video - and groups them into
segments shaped like a `TranscriptSegment`, so the modules after it work as they do on an episode.
Those times are the clock of the video itself, so nothing translates the span at render time.

## Input

- One or more videos, each named as a watch page URL or as the path of a file on this machine.
  This module never searches for a video, because the request already names it.
- Optional: a subtitle file for a local video, when it does not sit beside the video.

## Output

- An external source for each video: `media`, the title, and the segments.
  An external source is a `SocialPostMediaSource` without `ids`, because no episode and no show hold
  the video. The modules after this one fill `transcript`, `ts_start` and `ts_end`.
- What each set of segments was read from, which decides how far a span is padded and how much a
  quote from it can be trusted.

## Requirements

- Python 3.11 or later, for every input: the reading is done by the script of this module.
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
   The script reads a watch page from the track the channel uploaded, and falls back to the generated
   one; it reads a local video from a subtitle file beside it, and transcribes the audio when there is
   none. Name a subtitle file that sits elsewhere with `--subtitles`.
   Stop and tell the user when a watch page has no English track, because nothing here can read it.

2. Read the title, the duration, and the publish date, so that module **copy** can credit the video:

   ```bash
   # --skip-download reads the metadata of the watch page and fetches no media.
   yt-dlp --skip-download --print "%(title)s | %(duration)s | %(channel)s | %(upload_date)s" "$VIDEO_URL"
   ```

   A local file carries no such record, so ask the user who speaks and what the video is, and never
   take either from the file name.

3. Confirm that the segments cover the video: the last segment MUST end near the duration.
   A subtitle file or a caption track that stops early holds a part of the talk, so say which part the
   search reaches.
4. Write `media` as the URL or the path the user gave.
   Give the segments and `media` to module **discovery** as the passages to score.

## Additional notes

The words are read again in each session, and never kept, because the video is the record and this is
a reading of it.

A speaker is named on the stage and not in a transcript, so the transcript names nobody here either.
The title of a watch page usually names the speaker, and module **copy** takes the name from there.

The three readings are not equally good, and the modules after this one need to know which one they hold:

- A subtitle file the show wrote itself is the best, because a person checked the words.
- A whisper transcript times the speech and punctuates it, so a span cuts as cleanly as one from an
  episode, and the words are still a machine's hearing.
- An automatic caption track times a line rather than a word and punctuates by guess, so a span from
  one is padded further and a machine's hearing of a name or a number MUST be confirmed on the video.

A local video is a file and not an address, so the clip MUST be rendered on the machine that holds it,
and no later session finds it there.

An episode that is not published yet becomes an episode on the day it publishes.
Clip it from the episode after that, because the post then carries `source` and the work is not
trapped in one session.
