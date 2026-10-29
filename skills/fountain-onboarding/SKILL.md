---
name: fountain-onboarding
description: "Set up Fountain: show, channels, clip look, preferences, and Daily Growth. Use on first use or on request."
---

## Overview

This skill gets a podcaster from a new Fountain account to fresh clips in their own style each morning.
It walks the user through the setup, fixes what it can, and links to the rest.
The last step is a short guide to the daily drafts.

## Input

- None.

## Output

- A project with a show, connected channels, and Daily Growth on.
- Updated preferences: Brand, Editorial, Accounts, and the Narratives of the show.
- A summary in the chat: what changed, what is still missing, and who must act on it.
- A short guide to the daily work with the drafts.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Fountain API.

## Process

1. Fetch the projects of the user, to make sure that Fountain API is reachable.
   An empty array is fine, as long as the status is 200.
   If the API is not reachable, install the plugin from https://github.com/fountain-fm/fountain-skills
2. Make sure that the user has at least one project.
   Otherwise, link to https://fountain.fm/studio/onboarding, where the user also chooses a plan.
3. Make sure that the project has at least one show.
   Otherwise, connect the show with the Project API, or link to
   https://fountain.fm/studio/{project_id}/onboarding?kind=PODCAST
   A connected show costs one credit for each episode with no transcript.
   Tell the user this cost before you connect the show.
4. Make sure that the project has at least one social channel, e.g. X, YouTube, or Instagram.
   Connect it with the Social API, and send the user the link that approves access.
   Daily Growth writes one post for each connected channel.
5. Choose the look of the clips.
   Read the caption styles and the settings that Fountain renders on the clip rendering page.
   Look at the artwork of the show, its website, and its existing clips.
   Propose one caption style, with colors and a font that match the show, and record them under Brand.
   Link the clip rendering page, where the user can preview each style.
6. Record the rules for the words of each post under Editorial, e.g. emoji, hashtags, and tone.
   Record the handles of people that posts tag under Accounts.
7. Show the user the Narratives of the show, and change them as the user says.
   When the show has none, write a few from its recent episodes.
8. Load the automations of the project with the Project API, and explain each one in one sentence.
   Turn on Daily Growth, unless the user declines.
   Another automation stays off until the user agrees to it.
9. Describe the daily routine to the user, in a few lines:
   - With Daily Growth on, Fountain finds new clips each day, drafts their posts, renders the videos, and emails
     a report.
     The report goes to each project member who can access the show.
   - The user approves and schedules each draft at the `drafts_url`, or tells the agent to do it.
   - To change a clip, the user tells the agent, e.g. "make the captions bigger on my latest clip".
   - Each post that goes out uses one credit.

## Additional notes

Record each preference with the Project API as soon as you or the user choose it.
Any preference that the agent asks to confirm MUST already be recorded in project preferences.
Therefore, if the user leaves the chat, the choices made so far are still recorded.

Onboarding must not feel overwhelming:

- Choose the defaults yourself, record them, and then present them for the user to confirm.
  Say that the user can change each one.
- Do not present all options unless the user chooses to customize.
- Do not provide unnecessary information.

A request to run Daily Growth each day means: turn on the Daily Growth automation.
This skill installs no software, because Fountain renders the clips.

When no user is present, do only the steps that need no answer from the user.
Report what is still missing, so that the user can complete it in the next chat.

When this skill is triggered as part of a specific task, explain to the user why they need to go through this skill.
