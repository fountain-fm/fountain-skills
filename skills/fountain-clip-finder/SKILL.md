---
name: fountain-clip-finder
description: Find podcast clip moments and create channel-specific draft social posts.
---

## Overview

This skill turns a clip request into ranked draft posts.
It routes episode footage through modules **discovery**, **media**, **boundaries**, and **copy**.
It uses module **external-source** only for a video that Fountain does not hold.
It does not render, approve, schedule, or publish a clip.

## Input

- A show, episode, person, topic, quote, approximate time, or kind of moment.
- Or one or more user-supplied video URLs or local files that Fountain does not hold.
- Optional clip count, duration range, required link, or sourced trend context.

## Output

- Ranked clip cards.
- One draft `SocialPost` per suitable clip and connected `SocialChannel`.
- A complete `SocialPostMediaSource` for an episode clip.
- An in-session render handoff for an external video clip.

## Housekeeping

Read HOUSEKEEPING.md before you use the Fountain API, preferences, or local outputs.

## Requirements

- Fountain API.
- A web search tool only when module **media** must find episode video outside Fountain.
- Read module **external-source** for its conditional software requirements.

## Process

1. Resolve the show and list its connected `SocialChannel` records.
   Use skill **fountain-onboarding** only when channel setup blocks the requested draft posts.
   Continue without drafts when the user asked only for clip candidates.
2. For Fountain episodes, read and run module **discovery**.
   For a user-supplied external video, read module **external-source** first, then run module **discovery**
   on the returned segments.
3. For Fountain episodes, read and run module **media**.
   Skip it for an external video, because module **external-source** already resolved the file.
4. Read and run module **boundaries** on each surviving moment.
5. Read and run module **copy** on each surviving clip.
6. Create the draft posts with the Social API.
   Write each post's text with the required second call, then verify that the text landed.
   Process independent clips and channels concurrently in small batches.
7. Present the ranked clip cards from `assets/clip-card.md`.

The run is complete when each selected clip has a card and each intended channel has a verified draft,
or when the result states why no draft could be created.

## Additional notes

The module order is fixed only where one module produces the input of the next one.
Return fewer clips than requested when fewer pass the gates.

An external video post has no `source`, episode id, or show id.
Render it in the same session and give the external source directly to skill **fountain-clip-producer**.

Always write `source` on an episode draft.
Fountain can offer the draft to a renderer only when that field is present.

Do not say that an unpublished episode is available to hear now.
Do not create a video file in this skill.
