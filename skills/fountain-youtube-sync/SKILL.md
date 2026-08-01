---
name: fountain-youtube-sync
description: Match a podcast's RSS episodes to its YouTube videos and build a per-show index of video sources.
---

## Overview

Many podcast RSS feeds are audio-only, while a video version of the same episode often exists on YouTube.
The skill's script scores each (episode, video) pair on title similarity, duration delta, and publish-date distance.
It combines them into one 0-100 score and gives each episode its best video and a confidence tier.
The result is a per-show index of each episode's video source.
Skills [fountain-clip-finder] and [fountain-clip-producer] read this index.

## Input

- `rss_url` - the RSS feed URL of the show.
- `youtube_sources` - one or more YouTube channel `/videos` URLs or playlist URLs for the show.

## Output

Files in `fountain/outputs/youtube-sync/<show-slug>/`:

- `rss-youtube-matches.csv` and `rss-youtube-matches.json` - one row per episode with its best match,
  confidence tier, and score breakdown.
- `summary.json` - source counts and match counts per confidence tier, also printed to stdout.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill fountain-api, only when you must resolve a show name to an RSS feed URL.
- Python 3.11 or later.
- yt-dlp (Homebrew formula `yt-dlp`).

## Process

1. If you do not have `rss_url`, load skill fountain-api and resolve the show with the Search API.
2. Find the show's YouTube sources.
   Use the channel's `/videos` tab.
   Also include a dedicated episodes playlist if the channel has one.
3. Run `match-rss-to-youtube.py` with all sources:

   ```bash
   scripts/match-rss-to-youtube.py \
     --rss-url "https://feeds.example.com/show/" \
     --youtube-source "https://www.youtube.com/@show/videos" \
     --youtube-source "https://www.youtube.com/playlist?list=PLxxxx"
   ```

4. Report the match counts per confidence tier to the user and act on each tier:

   - `high` - use the match directly.
   - `medium` - compare the YouTube title and duration with the RSS episode before you use the match.
   - `low` - treat the match as a lead only and verify it manually.
   - `unmatched` - no video passed the confidence bar, search the channel manually.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

Skip this skill when you already know the episode's YouTube URL.
Give that URL straight to skill [fountain-clip-producer] - it does not care how the URL was found.

The index reflects the feed and the channel at build time.
Build the index one time per show, then refresh it when the feed or the channel gets new items.
Do not rebuild the index for each episode lookup.

A wrong video makes every clip timestamp wrong.
You MUST NOT use a `low` or `unmatched` result without manual confirmation.

A live fetch of a large channel is slow and can hit rate limits.
Cache the yt-dlp dump one time and replay it with `--youtube-jsonl`.

Title normalization strips common English stopwords.
Review matches for non-English shows with extra care, whatever the reported confidence tier.
