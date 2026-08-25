---
name: fountain-clip-finder
description: Find the strongest clip moments in a show, write the post copy, and open a draft post for each channel.
---

## Overview

This skill searches a show's transcripts for the moments that could become a strong clip.
Four modules narrow the field: module **discovery** scores the moments, module **media** resolves the file
each one is cut from, module **boundaries** sets the span, and module **copy** writes the words around it.
Module **external-source** replaces the search for a video that Fountain does not hold.
Each clip becomes a draft post, so the user decides what goes out.

## Input

One of these:

- A topic, or the terms to search for.
- A kind of moment, for example funny, angry, or surprising.
- An episode, with an optional quote or approximate time.
- A person, to find the moments of one guest or host.
- One or more videos that the show never published as an episode, each a URL or a file on this
  machine, with an optional topic or quote.

Optional:

- `clip_count` - the most clips to return, which the show's archive may not fill.
- `min_duration_seconds` and `max_duration_seconds` - the length to cut to.
- A link that every post MUST carry, for example the page a campaign drives to.
- Trend context with its sources, when the clip must answer a news story.
  This skill does not search the news, so the caller gives the sources.

## Output

One draft `SocialPost` for each clip on each connected `SocialChannel`, ranked by the clip score of
module **boundaries**.

A post targets one channel, and the platform of that channel decides how the text reads.
One clip on two channels is therefore two posts, each with its own text.

The API marks `source` optional, but this skill MUST write it.
Fountain shows a post as a candidate only when it holds `source`, and only then can a renderer cut the clip.
Module **copy** writes `content.title`, `content.text`, and `context`.
Module **media** and module **boundaries** build `source` between them.

A clip from a video that is not an episode carries an external source instead, which module
**external-source** defines, and the post holds no `source` at all: `ids` names an episode and a show,
and this clip has neither.
Such a post is a draft with words and no clip behind it, so the render MUST happen in the same session.

The posts then wait in the Social API, and nothing here invokes the next stage: skill
**fountain-clip-producer** works from `source` and attaches the video to the post.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Fountain API.
- A web search tool, for episodes that have no video on Fountain.
- yt-dlp, for a video URL, and ffmpeg with whisper for a local video that has no subtitle file.
  Module **external-source** names both, and a machine without them runs every other input.

## Process

1. Resolve the show, and list the connected `SocialChannel` with the Social API.
   Ask the user to connect a channel in the dashboard when the show has none, because a clip becomes a
   draft post on a channel, and there is no other place to keep the work.
   Continue only when the user asks for the clips without a channel.
2. Run module **discovery** to search the transcripts, score each moment, and drop the weak ones.
   For a video that is not an episode, run module **external-source** first, and give its segments to
   module **discovery** as the passages to score.
3. Run module **media** to resolve the file each moment is cut from, and the clock that file runs on.
   Drop a moment when its episode has no video to cut from.
   Skip this module for such a video, because module **external-source** already named the file.
4. Run module **boundaries** to shape each moment into a clip, and to drop the ones that fail a gate.
5. Run module **copy** to write `content.title`, `content.text`, and `context`.
6. Create one draft `SocialPost` for each clip on each channel with the Social API.
   Creating a post does not carry its text, so write the text with a second call, and check that it
   landed - a draft with no words looks finished in the dashboard and publishes as an empty post.
7. Present the posts in rank order, with their scores, their reasons, and each flag.
   Give the external source of each clip to the renderer in this session, and say that these posts
   cannot be rendered from a later one.

## Additional notes

Each module removes work from the next one, so you MUST run them in the order above.

A clip from a video that is not an episode is a post about something the audience cannot find on the
feed, so the words carry the link that the request gives, and the user approves both together.
An episode that is not published yet is the other case: the clip goes out before the episode does, so
the words MUST NOT say that the audience can hear the rest of it today.

`ts_start` and `ts_end` are always in the clock of the transcript.
A YouTube cut of an episode runs to its own clock, and skill **fountain-clip-producer** translates the
span into it at render time.
A video that is not an episode is its own transcript, so those two clocks are one and nothing
translates the span.

This skill never makes a video file: it finds the moment, sets the span, and writes the words, and
`source` holds all of that.

Give few strong clips rather than many weak ones, and say plainly when the show holds none.
