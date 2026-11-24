---
name: fountain-onboarding
description: "Set up Fountain: show, channels, clip look, and automations, then make a first clip. Use on first use or on request."
---

## Overview

This skill gets a podcaster from a new Fountain account to a first clip draft in a few minutes.
It says what Fountain does, fixes what it can, and links to the docs for the rest.

## Input

- None.

## Output

- A project with a show, at least one connected channel, and its automations on.
- Updated Brand preferences, and Editorial and Accounts preferences when the user gives them.
- One clip draft from the latest episode, with its `post_url`.
- A summary in the chat: what changed, what is still missing, and where to read more.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Fountain API.

## Process

1. Tell the user what Fountain does, in a few lines:
   - Daily Growth: each day, Fountain finds moments in the archive that match the news, and drafts clips.
   - Latest Episode: when a new episode comes out, Fountain drafts clips from it.
   - On request: the agent makes a clip or a compilation about any subject, from any episode.
   - Each clip arrives as a draft with a rendered video and a post for each channel.
     Nothing goes out until the user approves it.
2. Fetch the projects of the user, to make sure that the Fountain API is reachable.
   An empty list is fine.
   If the API is not reachable, help the user connect it.
3. Make sure that the user has a project.
   Otherwise, link https://fountain.fm/studio/onboarding, where the user adds the show and chooses a plan.
   Ask the user to say "continue setup" when they are done.
4. Make sure that the project has a show.
   Otherwise, connect the show with the Project API.
   Fountain indexes each episode of the show for free.
5. Make sure that the project has at least one connected channel, e.g. X, YouTube, or Instagram.
   Connect it with the Social API, and send the user the link that approves access.
   Without a connected channel, Fountain makes no drafts.
6. Choose the look of the clips.
   Read the clip rendering page, and look at the artwork of the show and its existing clips.
   Choose one caption style with colors that match the show, record it under Brand, and link the clip rendering page.
7. Make one clip from the latest episode, so that the user sees a result now.
   Find it with the Search API, and draft it with the Social API, with one post for each connected channel.
   Give the `post_url`, and say that the video is ready in a few minutes.
8. Load the automations with the Project API, and explain each one in one sentence.
   Turn on Daily Growth and Latest Episode, unless the user declines.
   Tell the user when Daily Growth next runs.
   Its email goes to each project member who can access the show.
9. Finish with three example requests that the user can make, and these links:
   - Finding clips: https://fountain.fm/docs/finding-clips
   - Rendering clips: https://fountain.fm/docs/rendering-clips
   - Publishing clips: https://fountain.fm/docs/publishing-clips
   - Daily Growth: https://fountain.fm/docs/daily-growth
   - Credits: https://fountain.fm/faq/credits

## Additional notes

Record each preference with the Project API as soon as you or the user choose it.
Thus, if the user leaves the chat, the choices made so far are still recorded.

Onboarding must be fast:

- Choose the defaults yourself, record them, and then present them for the user to confirm.
  Say that the user can change each one.
- Do not present all options unless the user chooses to customize.
- Link the docs, and do not explain what they explain.
- Do not write Narratives during onboarding, because Daily Growth writes the first ones.
- Record Editorial and Accounts preferences only when the user gives them.

A request to run Daily Growth each day means: turn on the Daily Growth automation.
This skill installs no software, because Fountain renders the clips.

When no user is present, do only the steps that need no answer from the user.
Report what is still missing, so that the user can complete it in the next chat.

When this skill is triggered as part of a specific task, explain to the user why they need to go through this skill.
