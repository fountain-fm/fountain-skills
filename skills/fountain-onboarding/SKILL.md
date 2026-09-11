---
name: fountain-onboarding
description: Set up Fountain. Trigger on first use or when asked, when preferences are empty, when a skill is missing something.
---

## Overview

This skill ensures that the user can effectively use Fountain API and skills.

It makes sure

- Fountain API is reachable
- Fountain skills are installed
- user preferences are recorded
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

1. Ensure you are in a fully capable agent environment, such as Claude Code or
   Codex. Otherwise, suggest to the user to use such environment to take full
   advantage of Fountain.
2. Ensure you have access to Fountain API by fetching the user's projects (fine
   if empty array as long as 200 status). If you don't have access, install the
   plugin from https://github.com/fountain-fm/fountain-skills
3. Ensure you have access to Fountain skills: **fountain-clip-finder**,
   **fountain-clip-producer**, **fountain-daily-growth**, and
   **fountain-reports**. If you don't have access, install the plugin from
   https://github.com/fountain-fm/fountain-skills
4. Ensure that the user has at least one project. Otherwise, link to
   https://beta.fountain.fm/studio/onboarding?kind=PODCAST
5. Ensure that the project has least one podcast. Otherwise, link to
   https://beta.fountain.fm/studio/{project_id}/onboarding?kind=PODCAST
6. If there are no connected social channels, suggest connecting YouTube, X, or
   Instagram via the Social API
7. Ensure the project preferences specify clip styling, the source of clip
   material, automation (auto-render, etc.), email address to send the reports to, and any other relevant details.
8. When running locally, ensure all relevant software is installed: Python 3.11
   or above, yt-dlp, ffmpeg + ffprobe (the most complete version that includes
   libass, drawtext, fontconfig and whisper), whisper.cpp, OpenCV 4.8 or later,
   ImageMagick. If something is missing, attempt to install yourself. Otherwise,
   make it easy for the user to install themselves, even if they are
   non-technical.
9. Set up automatic daily growth using skill **fountain-daily-growth**.

## Additional notes

Onboarding must not feel overwhelming:

- Use Fountain defaults for relevant preferences, like caption styling. Present
  the defaults to confirm, offer customization as optional. Do not present all
  options unless user chooses to customize.
- Do not provide unnecessary information.
- When appropriate, make a decision yourself.

When this skill is triggered as part of a specific task, explain the need for
going through this.
