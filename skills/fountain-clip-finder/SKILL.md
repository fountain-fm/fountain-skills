---
name: fountain-clip-finder
description: Find the strongest clip moments in a show, write the post copy, and open a draft post for each channel.
---

## Overview

This skill takes a brief and searches the podcast transcript for moments that could become a strong clip.
Four modules narrow down the selection.
Module **discovery** scores the moments, and module **video-source** removes the ones with no video.
Module **boundaries** sets the start and the end of each clip, and module **copy** writes the words around it.
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

One draft post for each clip on each connected channel, ranked by the clip score of module **boundaries**.
A draft post publishes nothing until the user approves it.

A channel is one connected account, and its platform decides how the text reads.

Each draft MUST hold:

- `channel` - the connected channel this draft posts to.
- `post_text` - the post text for that channel's platform.
- `title` - a short title for the dashboard and the email digest.
- `context` - a Markdown note that gives the reason to post the clip.
- The clip source: `content_id`, `source_media`, `transcript`, `start_time_seconds`, and `end_time_seconds`.

Fountain shows a draft as a candidate only when it holds `title`, `context`, and the clip source.
Module **copy** defines `title`, `context`, and `post_text`.
Skill **[fountain-clip-producer]** works from the clip source, and attaches the video file after approval.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.
- yt-dlp (Homebrew formula `yt-dlp`), for episodes that the API reports as audio only.

## Process

1. Load skill **fountain-api** and resolve the show.
2. Run module **discovery** to search the transcripts, score each moment, and drop the weak ones.
3. Run module **video-source** to resolve the video of each moment.
   Drop a moment when its episode has no video to cut from.
4. Run module **boundaries** to shape each moment into a clip, and to drop the ones that fail a gate.
5. Run module **copy** to write `title`, `context`, and `post_text`.
6. Create the drafts with the Social API, one per clip per channel.
   Write every part that the Output section lists.
7. Present the drafts in rank order, with their scores, their reasons, and each flag.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

The four modules run in cost order, so that cheap judgment runs before slow work.
Scoring is free, the video check reads data the search already loaded, and only a transcript costs a call.
Each module therefore removes work from the next one, and you MUST NOT change that order.

This skill never makes a video file.
It finds the moment, sets the span, and writes the words, and the draft holds all of that.
Skill **[fountain-clip-producer]** renders from the draft after the user approves it.
Give the drafts to that skill when the user asks for a video, and do not try to render one here.

You MUST NOT approve, schedule, or publish a draft, because only the user decides that.

Give few strong clips rather than many weak ones, and say plainly when the show holds none.
