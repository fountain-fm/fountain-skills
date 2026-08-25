---
name: media
description: Resolve the file each clip is cut from, and map the transcript clock onto the clock of that file.
---

## Overview

A clip needs video, and this module looks in two places.
It first reads the `ContentHit` that module **discovery** loaded, because that already names the video.
It searches YouTube only when the show published none.
A YouTube cut of an episode carries different advertisements, so it does not run to the transcript clock.
The span of such a clip therefore stays in the clock of the transcript, and skill **fountain-clip-producer**
translates it at render time, because only the renderer must reach YouTube.

## Input

- The scored moments from module **discovery**, and the `ContentHit` of each episode.
- Where the show publishes its video, from the Accounts section of the preferences, for the episodes
  that need it.

## Output

- The `SocialPostMediaSource` of each moment, with `ids` and `media` set.
  Module **boundaries** sets the three remaining fields, so it is complete only after that module.
- A confidence tier for each moment that needed a YouTube match.
- A preview link for each moment, which opens the video at the moment so the user can watch it.
  Always `https://fountain.fm/episode/<id>?t=<seconds>`, with the bare episode id and the seconds in
  the clock of the transcript, which that player runs on for the audio and the Fountain video alike.
  For a YouTube match, add `https://www.youtube.com/watch?v=<id>&t=<seconds>s` with the transcript
  seconds, and call it approximate, because that file runs on its own clock and nothing here can
  translate into it - the drift is the advertisement difference, from zero to a few minutes.
- A removal mark on each moment that has no usable video.

## Requirements

- Fountain API.
- A web search tool, for the episodes that have no video on Fountain.

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
5. Match each episode that has no video with the web search tool.
   Search for the episode title of the `ContentHit` together with the name of the channel, and never
   the title of a clip.
   Search again for the guest when the title names one, because a rewritten video title keeps the guest.
   Read the title, the duration, and the publish date of each candidate.
6. Grade each match on the title, the guest, the duration, and the publish date, then act on the grade:

   - `high` - the title or the guest agrees, the duration agrees within a minute, and the publish
     dates are within 45 days of each other. Use the match.
   - `medium` - one of those signals disagrees, or cannot be read. Open the watch page and compare it
     with the episode before you use the match.
   - `low` - only a loose title fit. Treat the match as a lead, and confirm it manually.
   - `unmatched` - no candidate fits. Mark the moment for removal.

7. Write the resolved URL into `media`.

## Additional notes

The `ContentHit` answer is the better source, and not only the cheaper one.
It gives the exact video of the episode, while a YouTube match is a judgment that can be wrong.

`info.video` names the free video, and never the file that subscribers pay for.
A clip MUST NOT use a file that the audience pays for.

A show repeats a segment every quarter with the same title, the same guest and the same length.
Only the date tells two of those apart, so a match with no date, or one more than 45 days out, is unmatched.

A show that rewrites titles for search usually keeps the guest name, and the guest then carries the match.
An episode with no guest in its title and a rewritten video title can stay unmatched, and that is correct.
You MUST NOT carry a `low` or an `unmatched` match forward without confirmation.

Skill **fountain-clip-producer** opens `media` at render time, so it confirms there that the video is real,
and it translates the span of a YouTube match into the clock of that file there.
A wrong match stops there too: the renderer compares the words of the cut against `transcript`, and a
file that holds other words never renders.
That backstop catches the wrong video, and never a wrong span in the right video, so the grade above
still carries the judgment.
