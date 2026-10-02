---
name: episode-watch
description: Find the episodes published since the last run, and brief fountain-clip-finder on each one.
---

## Overview

A new episode is the one story about the show that no news scan finds.
This module finds the episodes that the show published after its marker.
It makes each one into a brief for skill **fountain-clip-finder**.
It briefs an episode only when its transcript is searchable.
The marker stops before an episode that is not searchable yet, so that episode waits and does not lose its clips.

## Input

- `show` - the show to watch.
  When a scheduler starts this module alone, watch each show that has an Automation entry.
- The show's episodes, each one a `ContentHit`.
  Use the list that the caller read to update the Narratives section, when it gives one.
- The Narratives section of the preferences: the subjects the show returns to.
- The Automation section of the preferences: the new-episode clip budget, and the marker of this module.

## Output

One brief for each new episode, handed to skill **fountain-clip-finder**.
Each brief has:

- The episode, as its `ContentID`.
- The narrative that it fits, when one fits.
- 2-4 search terms.
- One sentence about the episode, and the day it came out as the reason it is live today.
- A `clip_count`, which is the new-episode clip budget.

And:

- The marker, moved in the Automation section.
- The new episodes that wait for a transcript, by name, for the day's report.

## Requirements

- Fountain API.
- Skill **fountain-clip-finder**.

## Process

1. Read the Automation section.
   The marker is the `info.published` of the last episode that this module briefed for the show, e.g.
   `- TFTC: new episodes clipped up to 2026-09-04T16:16Z (AGENT-2026-09-05)`.
   Read the new-episode clip budget from the same section, and use 2 when no entry names it.
2. When the caller gave no list, list the show's episodes with the Content API.
   Keep the episodes published after the marker.
   When the section has no marker, this is a first run: keep only the episodes of the last 48 hours.
   When no episode is new, say so in one line and stop, because most days have no new episode.
3. Keep the 3 oldest of the new episodes, and leave the rest for the next run.
4. Check that each kept episode is searchable.
   Search the transcript of that one episode with the Search API: give the episode as the episode to search,
   and not as the scope.
   Use one plain word that the episode surely says, e.g. a word of its title.
   An episode with no hit has no indexed transcript yet, so do not brief it.
   The searches do not depend on each other, so send them all at the same time.
5. Map each searchable episode to a narrative, and reduce it to 2-4 search terms.
   Take the terms from the words of `info.title` and `info.description`, because the show chose them.
   Use the narrative's words only when the episode's own words are too wide to search on.
   When the episode fits no narrative, propose one, because the show returned to the subject.
6. Hand each brief to skill **fountain-clip-finder**, oldest episode first, and do not read its result.
   The chain continues without this module.
7. Move the marker, and only after the briefs went out.
   Move it to the `info.published` of the newest episode of an unbroken run of briefed episodes.
   Never move it past an episode that waits for a transcript.
   On a first run with no episode kept, set the marker to the newest episode, so the watch starts there.
8. Give each episode that waits to the day's report as a warning, because the user waits for those clips.

## Additional notes

A scheduler can start this module alone, between two loops.
The result is the same, because the marker and the episodes are both on the API.
Then a show that publishes in the evening gets its clips that night, and not the next morning.
Its drafts wait for the next render, the same as every other draft.

This marker is not the `Read up to` line at the end of the Narratives section.
That line moves over every episode that was read, before any clip exists.
This marker moves only over the episodes that were briefed.

The marker stops before an episode that waits, and also before every episode after it.
This is because one line cannot record a gap, and an episode that is briefed twice gives the user the same
clip twice.
The cost is a delay for the later episodes, until the transcript arrives.
Let the marker pass an episode that is more than 7 days past its `info.published` and still has no
transcript.
Say which episode you passed, and that its clips will not come.
Without this rule, one episode that is never transcribed stops the watch for good.

The first run looks back 48 hours, and no further.
A user who sets up the loop on the day of a release gets clips of that release.
An archive of hundreds is not a day's work that the user asked for, so offer skill **fountain-clip-finder**
for older episodes that they want.

A search of the whole show gives at most 10 episodes, so a new episode can be missing from the results
while its transcript is searchable, seen 2026-09-30.
The search of step 4 names the one episode, so its answer is exact.
A scope that names the episode gives nothing, seen 2026-09-07.

The marker is not what makes a clip unique.
Module **discovery** of skill **fountain-clip-finder** compares each moment with the posts that exist.
So a repeated run costs a search, and never a duplicate clip.

Three episodes in one run clear a backlog faster than a show publishes, and give the user a day that they
can review.
A week away gives three days of clips, and never one report of fourteen.

The new-episode budget is its own entry, and never a share of the trend budget.
A new episode is the show's strongest material, so it does not compete with the news for clips.
`clip_count` is a maximum, and two strong clips are better than four weak ones.

The brief has no news source, because the release is the news.

The list of episodes has every episode of the show, and it cannot be made shorter, seen 2026-09-07.
Read the newest entries, and ignore the rest.
The list follows the show's own feed, so an episode added late with an old date does not look new.
