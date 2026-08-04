---
name: pack-assembly
description: Turn verified clip candidates into a rendered, safety-checked daily clip pack for operator review.
---

## Overview

Module trend-discovery hands this module scored trends with theme search terms.
This module gets candidates per trend from skill [fountain-clip-finder], selects the day's best ~5 across all trends,
renders the winners, writes platform copy, and formats the review pack.
It does not re-score archive matches or re-verify clip boundaries - skill [fountain-clip-finder] already did that.

## Input

- Scored, translated trends from module trend-discovery.
- The show's platforms, clip formats, and voice notes from fountain/PREFERENCES.md.

## Output

- `pack-<date>.md` - the review pack, sent to the operator exactly one time per run.
- A rendered, QA-passed clip for every proposed post.

## Requirements

- Skill fountain-api.

## Process

1. Invoke skill [fountain-clip-finder] in discovery mode with each trend's search terms.
   A trend that returns no clean candidate drops out of today's pack - do not lower the bar.
2. Load skill fountain-api and load the show's already-posted clips via the Social API.
   Drop each candidate that overlaps a clip the show already posted - the same moment MUST NOT go out twice.
3. Select the final ~5 candidates across all trends.
   Prefer a spread of narratives, at most one or two clips per trend, and fewer excellent clips over five mediocre ones.
4. Render the selected clips with skill [fountain-clip-producer] in the show's format(s).
   Every clip MUST be rendered and QA-passed before the review, not after approval.
5. Write a one-paragraph "why publish today" per clip: the live trend, the narrative it maps to, the archive-match
   strength, and any supporting signal from the editorial preferences in fountain/PREFERENCES.md.
6. Run the copy and safety pass (see the notes), then write per-platform copy and tag the on-camera speaker.
7. Assemble and send the pack one time.
   Each entry MUST include: working title, episode reference, thumbnail and preview links, duration, speaker and
   confirmed handle, narrative, the "why publish today" paragraph, the full clip transcript, per-platform copy,
   clip path, QA status, posting window in the audience timezone, and an approve / edit / reject prompt.
8. After the operator's review, build a brief per approved item and invoke skill [fountain-post-scheduler].
   Never construct a brief for anything not approved, and only for the platforms approved.

## Additional notes

A skill name in square brackets is planned but not in this repository yet.

Safety pass:

- Carry forward every risk flag from skill [fountain-clip-finder] - never drop one silently.
- Flag a post HIGHER-RISK when the copy adds a legal claim, an election or geopolitics claim, a claim about a named
  individual, a price prediction, or anything resembling investment advice.
- Soften higher-risk wording to a questioning framing, and never schedule one until the operator explicitly cleared it.
- Drop anything that cannot be made safe - do not soften it into something misleading.
- Never claim the guest responds to today's news unless the clip was recorded after the event.
- Never let a trimmed quote change what the speaker meant.
- Never fabricate guest quotes or statistics.

Speaker tagging:

- Tag whoever is on camera - verify it, because multi-host shows often cut to a reaction shot.
- Use only that platform's confirmed handle from the episode's show notes or the handle library in
  fountain/PREFERENCES.md.
- Credit by name when no handle is confirmed for that platform - never guess or reuse a handle across platforms.

Approval:

- Partial approval is normal - track approve / edit / reject per numbered item, not per pack.
- When the operator requests edits, revise and ask again before scheduling.
- Capture the reason behind every rejection - an outcome with no reason teaches nothing (see module feedback-capture).

Host a thumbnail and a preview link for every clip so the operator can review without local file access.
Upload only finished, QA-passed clips - a preview URL is typically public the moment it exists.
