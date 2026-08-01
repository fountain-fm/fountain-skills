---
name: fountain-youtube-sync
description: Match a show's episodes to its public YouTube videos, to find the video version of audio-only episodes.
---

## Overview

Many shows are audio-only in their feed, but have a video version on YouTube.
This skill scores each episode against each video on title, duration, and publication date.
It then writes the best video per episode to a per-show index, with a confidence level.
Build the index one time per show and use it many times, because a full channel scrape is slow.

## Input

- The show: a name, a Fountain URL, or a content ID.
- `youtube_sources`: one or more YouTube channel `/videos` URLs and/or playlist URLs.

## Output

- `fountain/outputs/youtube-sync/<show_slug>/matches.json`: a `meta` block and one match per episode.
  See `assets/example-matches.json`.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill fountain-api.
- uv, to run the script.
  The script installs its own dependencies, thus you do not need yt-dlp on the PATH.

## Process

1. Load skill fountain-api before the first request.
2. Find the show with the Search API if you have only a name or a URL.
3. Load the episodes of the show with the Content API.
   Keep the enclosure format of each episode, because it tells you which episodes have no video.
4. Write the episodes to a temporary JSON file, in the shape of `assets/example-episodes.json`.
   Set `has_video` to true only if the episode has a video enclosure.
5. Ask the user for the YouTube sources if you do not have them.
   Tell the user to look at the Playlists tab of the channel.
   A show playlist and the Videos tab are frequently different sets, thus give both.
6. Run `scripts/match-youtube.py` with `uv run --script`.
   Give it `--episodes`, one `--youtube-source` per source, and `--show-slug`.
7. Tell the user the counts per confidence level, and where the index is.
8. Look at each `medium` match before you use it.
   Compare the title and the duration of the video with the episode.
9. Do not use a `low` or an `unmatched` match before the user confirms it.
   Search the channel manually for these episodes.

## Additional notes

The index shows the state of the show and the channel at build time.
It becomes stale when the show gets a new episode, or when the channel gets a new video.
Compare `meta.latest_episode_published` and `meta.latest_video_uploaded` with the current data before you use it.
Build the index again when either one is behind.

A wrong video makes every timestamp of that episode wrong.
Thus give a first index of a show a quick check, even at the `high` level.

The script removes common English words from the titles before it compares them.
Matches for shows in other languages are less reliable at each confidence level.

A large channel is slow to scrape, and YouTube can apply a rate limit.
To try different data without a new scrape, keep the video list and give it to the script:

```bash
uv run --with yt-dlp yt-dlp --dump-json --skip-download "https://www.youtube.com/@Example/videos" > /tmp/videos.jsonl
uv run --script scripts/match-youtube.py --episodes /tmp/episodes.json --youtube-jsonl /tmp/videos.jsonl
```
