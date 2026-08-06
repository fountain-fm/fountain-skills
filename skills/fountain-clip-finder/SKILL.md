---
name: fountain-clip-finder
description: Find the strongest clip moments in a show, write the post copy, and open a draft post for each channel.
---

## Overview

This skill takes a brief and searches the podcast transcripts for moments that could become a strong clip.
Four modules narrow down the selection.
Module **discovery** scores the moments, and module **media** resolves the file each one is cut from.
Module **boundaries** sets the span of each clip, and module **copy** writes the words around it.
A draft holds the result and publishes nothing, so the user decides what goes out.

## Input

One of these:

- A topic, or the terms to search for.
- A kind of moment, for example funny, angry, or surprising.
- An episode, with an optional quote or approximate time.
- A person, to find the moments of one guest or host.

Optional:

- `clip_count` - how many clips the caller wants.
- `min_duration_seconds` and `max_duration_seconds` - the length to cut to.
- Trend context with its sources, when the clip must answer a news story.
  This skill does not search the news, so the caller gives the sources.

## Output

One draft `SocialPost` for each clip on each connected `SocialChannel`, ranked by the clip score of
module **boundaries**.
A draft publishes nothing until the user approves it.

A post targets one channel, and the platform of that channel decides how the text reads.
One clip on two channels is therefore two posts, each with its own text.

The API marks `source` optional, but this skill MUST write it.
Fountain shows a post as a candidate only when it holds `source`, and only then can a renderer cut the clip.
Module **copy** writes `content.title`, `content.text`, and `context`.
Module **media** and module **boundaries** build `source` between them.

The posts then wait in the Social API, and nothing here invokes the next stage:
skill **fountain-clip-producer** works from `source`, and attaches the video to the post.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.
- yt-dlp, for episodes that have no video on Fountain.

## Process

1. Load skill **fountain-api** and resolve the show.
2. Run module **discovery** to search the transcripts, score each moment, and drop the weak ones.
3. Run module **media** to resolve the file each moment is cut from, and the clock that file runs on.
   Drop a moment when its episode has no video to cut from.
4. Run module **boundaries** to shape each moment into a clip, and to drop the ones that fail a gate.
5. Run module **copy** to write `content.title`, `content.text`, and `context`.
6. Create one draft `SocialPost` for each clip on each channel with the Social API.
7. Present the posts in rank order, with their scores, their reasons, and each flag.

## Additional notes

Each module removes work from the next one, so you MUST run the four in the order above.

`ts_start` and `ts_end` are always in the time of `media`, and never in the time of another file.
A YouTube cut of an episode does not run to the clock of the transcript, so module **media** maps the two.

This skill never makes a video file.
It finds the moment, sets the span, and writes the words, and `source` holds all of that.
Skill **fountain-clip-producer** renders from the post, and it does not wait for the user to approve one.
Give the posts to that skill when the user asks for a video, and do not try to render one here.

You MUST NOT approve, schedule, or publish a post, because only the user decides that.

Give few strong clips rather than many weak ones, and say plainly when the show holds none.
