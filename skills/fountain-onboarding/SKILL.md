---
name: fountain-onboarding
description: "Set up Fountain: show, channels, clip look, and automations, then make a first clip. Use on first use or on request."
---

## Overview

This skill gets a podcaster from a new Fountain account to a first clip draft in a few minutes.
It finishes the setup, makes a first clip, and links the docs for the rest.

## Input

- None.

## Output

- A project with a show, at least one connected channel, and its automations on.
- Updated Brand preferences, and Editorial and Accounts preferences when the user gives them.
- Custom sources for Daily Growth, when major news sites rarely cover the show.
- One draft from the latest episode, with its `post_url`.
- A summary in the chat: what changed, what is still missing, and where to read more.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Fountain MCP.

## Process

1. Tell the user what Fountain does, in a few lines:
   - Daily Growth: each day, Fountain finds clips in the archive that match the news.
   - Latest Episode: when a new episode comes out, Fountain makes clips from it.
   - On request: the agent makes a clip or a compilation about any subject.
   - Each clip arrives as a draft with a rendered video and a post for each channel.
     Nothing goes out until the user approves it.
2. List the projects with `list-projects`, to make sure that the MCP works.
   An empty list is fine.
   If the call fails, help the user connect the MCP.
3. Make sure that the user has a project.
   Otherwise, link https://fountain.fm/studio/onboarding, where the user adds the show and chooses a plan.
   Ask the user to say "continue setup" when they are done.
4. Make sure that the project has a show.
   Otherwise, connect the show with `connect-project-show`.
5. Make sure that the project has at least one connected channel, e.g. X, YouTube, Instagram, or Facebook.
   Connect it with `add-social-channel`, and send the user the link that approves access.
   Without a connected channel, Fountain makes no drafts.
6. Choose the look of the clips.
   Read the clip rendering page, and look at the artwork of the show and its existing clips.
   Choose one caption style with colors that match the show, and record it under Brand.
   Tell the user what you chose, and link the clip rendering page.
7. If the latest episode has no video, ask the user whether Fountain makes audiograms for episodes without video.
   If the user says no, turn audiograms off with `update-project`.
8. Make one clip from the latest episode, so that the user sees a result now.
   Find it with `search-clips`, and draft it with `add-social-post` for each connected channel.
   Give the `post_url`, and say that the video is ready in a few minutes.
9. Load the project with `load-project`.
   Daily Growth and Latest Episode are on by default.
   Tell the user how many clips each one makes, and when Daily Growth next runs.
   The user can change the number of clips, or turn an automation off.
10. If major news sites rarely cover the subject of the show, choose a few custom sources for Daily Growth.
    E.g. trade publications or blogs in the niche of the show.
    Add them with `update-project`, and link https://fountain.fm/faq/daily-growth-sources.
11. Finish with three example requests that the user can make, and these links:
    - Finding clips: https://fountain.fm/docs/finding-clips
    - Rendering clips: https://fountain.fm/docs/rendering-clips
    - Publishing clips: https://fountain.fm/docs/publishing-clips
    - Daily Growth: https://fountain.fm/docs/daily-growth
    - Credits: https://fountain.fm/faq/credits

## Additional notes

Record each preference as soon as you or the user choose it.
Thus, if the user leaves the chat, the choices made so far are still recorded.

Onboarding must be fast and not overwhelming:

- Choose the defaults yourself, record them, and tell the user what you chose.
  Say that the user can change each one, and continue without waiting for an answer.
- Do not present all options unless the user chooses to customize.
- Do not provide unnecessary information.
- Link the docs, and do not explain what they explain.
- Do not write Narratives during onboarding, because Daily Growth writes the first ones.
- Record Editorial and Accounts preferences only when the user gives them.

A request to run Daily Growth each day means: turn on the Daily Growth automation.

When no user is present, do only the steps that need no answer from the user.
Report what is still missing, so that the user can complete it in the next chat.

When this skill is triggered as part of a specific task, explain to the user why they need to go through this skill.
