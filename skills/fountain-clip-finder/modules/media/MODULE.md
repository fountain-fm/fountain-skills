---
name: media
description: Resolve the file each clip is cut from, and map the transcript clock onto the clock of that file.
---

## Overview

A clip needs video, and this module looks in two places.
It first reads the `ContentHit` that module **discovery** loaded, because that already names the video.
It searches YouTube only when the show published none.
A YouTube cut of an episode carries different advertisements, so it does not run to the transcript clock.
This module therefore also builds a time map, which module **boundaries** uses to place a clip in that file.

## Input

- The scored moments from module **discovery**, and the `ContentHit` of each episode.
- Where the show publishes its video, from the Accounts section of the preferences, for the episodes
  that need it.
- The `ContentHitTranscript` of each episode that resolves to YouTube.

## Output

- The `SocialPostMediaSource` of each moment, with `ids` and `media` set.
  Module **boundaries** sets the three remaining fields, so it is complete only after that module.
- A time map for each moment that resolves to YouTube - the file that translates one clock into the other.
- A confidence tier for each moment that needed a YouTube match.
- A removal mark on each moment that has no usable video.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later.
- yt-dlp.

## Process

1. Write `ids` from the segments of the moment, which name the episode in `content` and the show in `parent`.
2. Read `info.video` of the episode from the `ContentHit` that module **discovery** loaded.
   Load the episode with the Content API when you do not hold it.
3. Use `info.video` as `media`, and stop here for that episode.
   The Content API gives it only when the episode has video, so its presence is the answer.
   Fountain cuts that file and the audio from one recording, so the clocks agree and no map is needed.
4. Read where the show publishes its video, usually a YouTube channel, from the Accounts section of the
   preferences.
   Ask the user one time when the preferences do not name a channel, then record the answer with the Project API.
   Do this only when an episode reaches this step.
5. Run the match one time for every episode that has no video:

   ```bash
   echo "$EPISODES_JSON" | scripts/find-episode-video.py --channel "@show"
   ```

   Give the script the `ContentHit` of each episode, and never the title of a clip.

6. Act on the confidence tier of each match:

   - `high` - use the match.
   - `medium` - compare the video title and duration with the episode before you use the match.
   - `low` - treat the match as a lead, and confirm it manually.
   - `unmatched` - mark the moment for removal.

7. Write the resolved URL into `media`.
8. Build the time map one time for each matched episode, with its `ContentHitTranscript`:

   ```bash
   TIME_MAP="fountain/outputs/time-map-$CONTENT_ID.json"
   echo "$TRANSCRIPT_JSON" | ../../scripts/build-time-map.py --build "$VIDEO_URL" > "$TIME_MAP"
   ```

   Name the file for the `content` id of `ids`, because one run can hold several episodes.
   Carry the path forward, because module **boundaries** translates each span with it.
   Read `anchor_coverage`, and mark the episode for removal when it is under 0.5.

## Additional notes

The `ContentHit` answer is the better source, and not only the cheaper one.
It gives the exact video of the episode, while a YouTube match is a judgment that can be wrong.

`info.video` names the free video, and never the file that subscribers pay for.
A clip MUST NOT use a file that the audience pays for.

The YouTube match lists the whole channel one time, then scores every episode against that list.
The listing costs approximately 9 seconds for 850 videos, whatever the number of episodes.
It carries no publish date, so the match reads the date of the best four videos every time.
A show repeats a segment every quarter with the same title, the same guest and the same length.
Only the date tells two of those apart, so a match with no date, or one more than 45 days out, is unmatched.

A show that rewrites titles for search usually keeps the guest name, and the guest then carries the match.
An episode with no guest in its title and a rewritten video title can stay unmatched, and that is correct.
You MUST NOT carry a `low` or an `unmatched` match forward without confirmation.

The time map exists because the two files hold the same words at different times.
A podcast inserts its advertisements into the audio and the video carries a different set, so the distance
between the two clocks changes at every break.
One offset for the whole episode is therefore wrong, and the map records each region on its own.

The map costs one caption download of approximately 6 seconds, whatever the length of the episode.
It holds the caption words, so a translation afterwards needs no network.
A low `anchor_coverage` means the captions and the transcript disagree, which usually means the match is wrong.

The map is an ephemeral output, and you MUST build it again in a later session.

Skill **fountain-clip-producer** opens `media` at render time, so it confirms there that the video is real.
