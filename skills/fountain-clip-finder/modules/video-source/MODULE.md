---
name: video-source
description: Resolve the video of each moment, from the Fountain API first and from YouTube when needed.
---

## Overview

A clip needs video, and this module looks in two places.
It first asks whether the show published a video of the episode, and module **discovery** already loaded that answer.
It searches YouTube only when the show published none.
A show may keep its feed title on YouTube or rewrite it, so the match scores the title and the guest together.
Duration and date confirm a match and never find one, because many episodes of a show share a length.

## Input

- The scored moments from module **discovery**, with the episode data that it loaded.
- The show's YouTube channel from the preferences, for the episodes that need it.

## Output

- `source_media` for each moment - the URL of the video to cut from.
- A confidence tier for each moment that needed a YouTube match.
- A removal mark on each moment that has no usable video.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.
- yt-dlp (Homebrew formula `yt-dlp`).

## Process

1. Read the video URL of each episode from the data that module **discovery** loaded.
   Load the episode with the Content API of skill **fountain-api** when you do not hold that data.
2. Use that URL as `source_media`, and stop here for that episode.
   The Content API gives the URL only when the episode has video, so the presence of the URL is the answer.
3. Read the show's YouTube channel from the Other section of the preferences.
   Ask the user one time when the preferences do not name a channel, then record the answer with the Project API.
   Do this only when an episode reaches this step.
4. Run the match one time for every episode that has no video:

   ```bash
   echo "$EPISODES_JSON" | scripts/find-episode-video.py --channel "@show"
   ```

   Each episode needs its own `title`, `published` date, and `duration_seconds`, and not the clip title.

5. Act on the confidence tier of each match:

   - `high` - use the match.
   - `medium` - compare the video title and duration with the episode before you use the match.
   - `low` - treat the match as a lead, and confirm it manually.
   - `unmatched` - mark the moment for removal.

6. Write the resolved URL into `source_media`.

## Additional notes

The Content API answer is the better source, and not only the cheaper one.
It gives the exact video of the episode, while a YouTube match is a judgment that can be wrong.

The Content API names the free video, and never the file that subscribers pay for.
A clip MUST NOT use a file that the audience pays for.

The YouTube match lists the whole channel one time, and then scores every episode against that list.
The listing costs approximately 9 seconds for 850 videos, whatever the number of episodes.

The listing carries no publish date, so the match reads the date of the best two videos only when they score close.
A listing of 850 videos can hold 29 inside one minute of an episode's length, so duration alone cannot decide.

The title alone finds an episode that the show published under its feed title, which is common in an archive.
A show that rewrites titles for search usually keeps the guest name, and the guest then carries the match.
An episode with no guest in its title and a rewritten video title can stay unmatched, and that is the correct answer.

You MUST NOT carry a `low` or an `unmatched` match forward without confirmation.
An `unmatched` result is often correct, because a show does not put every episode on YouTube.

Skill **[fountain-clip-producer]** opens the media at render time, so it confirms there that the video is real.
