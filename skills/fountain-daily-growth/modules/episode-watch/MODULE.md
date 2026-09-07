---
name: episode-watch
description: Find the episodes published since the last run, and brief fountain-clip-finder on each one.
---

## Overview

A show's own new episode is the one story that no news scan finds.
This module lists the show's episodes, keeps the ones published after the marked episode, and shapes
each into a brief for skill **fountain-clip-finder**.
It briefs an episode only when the transcript is searchable, and holds the marker before one that is not.
An episode then waits for its transcript instead of losing its clips.

## Input

- Optional: `show`, to watch one show instead of every show the preferences name.
- The show's episodes, listed with the Content API, each one a `ContentHit`.
- The Narratives section of the preferences: the subjects the show returns to.
- The Automation section of the preferences: the new-episode clip budget, and the episode this module
  reached last time.

## Output

One brief for each new episode, handed to skill **fountain-clip-finder**, where each brief carries:

- The episode, as its `ContentID`.
- The narrative it fits, when one does.
- 2-4 search terms, from that narrative and from the words of the episode's own `info.title` and
  `info.description`.
- One sentence on what the episode is about, and the day it came out as the reason it is live today.
- A `clip_count`, which is the new-episode clip budget.

And:

- The moved marker in the Automation section of the preferences.
- The new episodes that wait for a transcript, named, because the user is waiting for those clips.

## Requirements

- Fountain API.
- Skill **fountain-clip-finder**.

## Process

1. Read the Automation section of the preferences.
   Work every show it names, unless the caller named one.
   It records the episode this module reached, as the `info.published` of that episode, e.g.
   `Clipped up to 2026-09-04T16:16Z.`
   Read the new-episode clip budget from the same section, and use 2 when no setting names it.
2. List the show's episodes with the Content API, and order them by `info.published`.
   Keep the ones published after the marker.
   Say so in one line and stop when none is new, because most days hold no new episode.
3. Record the newest episode as the marker and brief nothing when the section records none.
   That is a first run, and an archive of hundreds is not a day's work that the user asked for.
   Say that the watch starts here, and offer skill **fountain-clip-finder** for the older episodes they
   want worked.
4. Keep the 3 oldest of the new episodes, and leave the rest for the next run.
5. Check that each kept episode is searchable: search the show's transcripts with the Search API on the
   strongest words of the episode's title, and keep the hits that belong to that episode.
   An episode that answers nothing holds no indexed transcript yet, so brief nothing for it.
   No episode's answer reads another's, so ask for them together in one turn.
6. Map each remaining episode to a narrative, then reduce it to 2-4 search terms.
   Take the terms from the narrative first, and from the words of `info.title` and `info.description`
   where the narrative is too wide to search on.
   Use the words the episode itself uses, because the show already chose them.
   Propose a narrative when the episode fits none, because the show has returned to the subject now.
7. Hand each brief to skill **fountain-clip-finder**, oldest episode first, and do not read its result -
   the chain continues without this module.
8. Move the marker to the `info.published` of the newest episode you briefed.
   Move it over an unbroken run of briefed episodes, and never past one that waits for a transcript.
   Move it only when the briefs went out.
9. Report the run plainly, and name each episode that waits.

## Additional notes

A scheduler can start this module on its own; the module itself owns no schedule.
It reaches the same answer either way, because the marker and the episodes both live on the API.
A show that publishes in the evening then gets its clips that night rather than the next morning.

This marker is not the one at the end of the Narratives section.
That one moves over every episode that was read, before any clip exists.
This one moves over every episode that was briefed, so an episode that could not be briefed is still
ahead of it.

The marker stops before an episode that waits for a transcript, and before every episode published after
that one, however ready those look.
One line cannot record a gap, and an episode briefed twice is a clip the user sees twice.
The cost is a day of delay for the later episode, and the delay ends when the transcript arrives.

Let the marker pass an episode that is more than 7 days past its `info.published` and still holds no
indexed transcript.
Say which episode you passed, and that its clips will not come without one.
An episode that is never transcribed would otherwise stop every episode after it for good.

The marker is not what makes a clip unique.
Module **discovery** of skill **fountain-clip-finder** compares each moment against the posts that
exist, so a repeated run costs a search and never a duplicate clip.

Three episodes in one run drains a backlog faster than a show publishes, and still gives the user a day
they can review.
A week away comes back as three days of clips, and never as one report of fourteen.

The new-episode budget is its own entry, and never a share of the day's trend budget.
A new episode is the show's strongest material and the one the audience is already reading about, so it
does not compete with the news for the same clips.
`clip_count` is a maximum that the episode may not fill, and two strong clips beat four weak ones.

The brief carries no news source, because the release is the news.
The day the episode came out is why the clip is live, and it is not a source to cite.

The listing answers with every episode of the show, however long the show has run, and it cannot be
narrowed to the newest few, seen 2026-09-07.
Read the newest entries of it and leave the rest.

The list is the show's own feed, so an episode added late with an old date sorts by that date and does
not read as new.
