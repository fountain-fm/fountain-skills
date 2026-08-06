---
name: pack-assembly
description: Turn scored trends into a rendered, safety-checked daily clip pack for operator review.
---

## Overview

Module **trend-discovery** hands this module scored trends with theme search terms.
This module gets draft posts per trend from skill **fountain-clip-finder**, selects the day's best ~5 across all
trends, renders the winners with skill **fountain-clip-producer**, and formats the review pack.
It does not re-score archive matches or re-verify clip boundaries - skill **fountain-clip-finder** already did that.

## Input

- `show` - the show the loop runs for.
- Scored, translated trends from module **trend-discovery**, each with its sources.
- The show's platforms, clip shapes, and voice notes, from the Editorial and Other sections of the preferences.

## Output

- `pack-<date>.md` - the review pack, written to the output folder that the skill names.
- A rendered, QA-passed clip attached to every proposed post.

## Requirements

- Skill **fountain-api**.
- Skills **fountain-clip-finder** and **fountain-clip-producer**.

## Process

1. Give skill **fountain-clip-finder** a brief per trend: the search terms, the trend itself as the trend
   context, and a `clip_count` of 2 or 3, because at most one or two clips per trend survive selection.
   It opens one draft `SocialPost` for each clip on each channel, with `source` and the first copy.
   A trend that returns no clean candidate drops out of today's pack - do not lower the bar.
2. Load skill **fountain-api** and load the show's earlier posts via the Social API.
   Drop each candidate whose `source` names the episode of an earlier post and overlaps its span - the same
   moment MUST NOT go out twice.
   The API holds every earlier post, so this check needs no local history.
3. Select the final ~5 candidates across all trends.
   Prefer a spread of narratives, at most one or two clips per trend, and fewer excellent clips over five
   mediocre ones.
4. Ask skill **fountain-clip-producer** to produce each selected post in the shape its platform needs, and to
   attach the video to the post.
   Every clip MUST be rendered and QA-passed before the review, not after approval.
5. Write a one-paragraph "why publish today" per clip: the live trend, the narrative it maps to, the archive-match
   strength, and any supporting signal from the Editorial section of the preferences.
   Add it to the `context` of the post via the Social API, under the note that skill **fountain-clip-finder** wrote.
6. Run the copy and safety pass (see the notes) over the copy that skill **fountain-clip-finder** wrote, and tag
   the on-camera speaker.
   Update each post that changes via the Social API.
7. Assemble and send the pack one time.
   Each entry MUST include: working title, episode reference, the post id, duration, speaker and
   confirmed handle, narrative, the "why publish today" paragraph, the full clip transcript, per-platform copy,
   clip path, QA status, posting window in the audience timezone, and an approve / edit / reject prompt.
8. After the operator's review, schedule each approved post via the Social API, at the posting window from
   its pack entry.
   Never schedule anything not approved, and only on the platforms approved.

## Additional notes

Safety pass:

- Carry forward every risk flag from skill **fountain-clip-finder** - never drop one silently.
- Flag a post HIGHER-RISK when the copy adds a legal claim, an election or geopolitics claim, a claim about a named
  individual, a price prediction, or anything resembling investment advice.
- Soften higher-risk wording to a questioning framing, and never schedule one until the operator explicitly cleared it.
- Drop anything that cannot be made safe - do not soften it into something misleading.
- Never claim the guest responds to today's news unless the clip was recorded after the event.
- Never let a trimmed quote change what the speaker meant, and never fabricate quotes or statistics.

Speaker tagging:

- Tag whoever is on camera - verify it, because multi-host shows often cut to a reaction shot.
- Use only that platform's confirmed handle from the episode's show notes or the handle library in the
  Other section of the preferences.
- Credit by name when no handle is confirmed for that platform - never guess or reuse a handle across platforms.

Posting windows:

- Choose each window from the Editorial section of the preferences: the times the operator ruled out, and
  the times that worked or failed on that channel.
- Load the posts that already hold a `meta.scheduled` time via the Social API, and space new ones around them.
  Two posts on one channel MUST NOT share a window.
- The operator can veto a window at the review, because the pack entry carries it.
- An approval can land after its window has passed.
  Shift to the next window that obeys these rules and note the change.
  When a day or more has passed, ask the operator again before you schedule - a pack is a claim about today.

Approval:

- Partial approval is normal - track approve / edit / reject per numbered item, not per pack.
- When the operator requests edits, revise and ask again before scheduling.
- Capture the reason behind every rejection - an outcome with no reason teaches nothing (see module
  **feedback-capture**).

The upload on the post is the preview: the dashboard shows a candidate post with its media.
So the pack names each post by its id rather than hosting files, and the operator reviews from anywhere.
Attach only finished, QA-passed clips - never a work-in-progress render.

A candidate that the pack passes over stays a draft in the dashboard, because the API has no way to retire
a post.
List the passed-over drafts at the end of the pack, so the operator is not surprised by them.
