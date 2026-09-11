---
name: fountain-onboarding
description: Set up Fountain. Trigger when the user starts using Fountain, when the project preferences are empty, when a Fountain skill is missing something, or when the user asks to set up Fountain.
---

## Overview

This skill ensures that the user can effectively use Fountain API and skills.

It makes sure

- Fountain API is reachable
- Fountain skills are installed
- user preferences are recorded: caption style, posting schedule, etc.
- relevant software is installed
- any other blockers are resolved

Even if the task does not require some of the above, you MUST go through each outstanding item.
That is so that you would not need to ask it again later.

## Input

- None.

## Output

- Summary of what has been updated.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Process

1. Ensure you are in a fully capable agent environemnt, such as Claude Code or
   Codex. Otherwise, suggest to the user to use such environment to take full
   advantage of Fountain.
2. Ensure you have access to Fountain API by fetching the user's projects (fine
   if empty array as long as 200 status). API is accesible via an MCP
   (preferred) or an API. If you don't have access, install the plugin from
   https://github.com/fountain-fm/fountain-skills
3. Ensure you have access to Fountain skills: **fountain-clip-finder**,
   **fountain-clip-producer**, **fountain-daily-growth**, and
   **fountain-reports**. If you don't have access, install the plugin from
   https://github.com/fountain-fm/fountain-skills
4. Ensure that the user has at least one project. Otherwise, link to
   https://beta.fountain.fm/studio/onboarding?kind=PODCAST
5. Ensure that the project has least one podcast. Otherwise, link to
   https://beta.fountain.fm/studio/{project_id}/onboarding?kind=PODCAST
6. If there are no connected social channels, suggest connecting YouTube, X, or
   Instagram at https://beta.fountain.fm/studio/projects
7. Ensure the project preferences specify clip styling, the source of clip
   material, automation (auto-render, etc.), and any other relevant details.
8. When running locally, ensure all relevant software is installed: Python 3.11
   or above, yt-dlp, ffmpeg + ffprobe (the most complete version that includes
   libass, drawtext, fontconfig and whisper), whisper.cpp, OpenCV 4.8 or later,
   ImageMagick. If something is missing, attempt to install yourself. Otherwise,
   make it easy for the user to install themselves, even if they are
   non-technical.

## Additional notes

Onboarding must not feel overwhelming:

- Use Fountain defaults for relevant preferences, like caption styling. Present
  the defaults to confirm, offer customization as optional. Do not present all
  options unless user chooses to customize.
- Do not provide unnecessary information.
- When appropriate, make a decision yourself.

When this skill is triggered as part of a specific task, explain the need for
going through this.
