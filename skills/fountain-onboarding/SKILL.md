---
name: fountain-onboarding
description: Set up Fountain or repair a missing Fountain connection, project setting, channel, or render tool.
---

## Overview

This skill completes the part of Fountain setup that the current request needs.
A full setup request can cover every setup area.
A call from another skill must resolve only its stated blocker, then return to that skill.

## Input

- The setup goal or blocker.
- Optional project, show, channel, reporting, brand, automation, or render requirements.

## Output

- The requested setup area in a usable state.
- Updated preferences for choices that must survive the session.
- A short summary of changes, remaining blockers, and the next action.

## Housekeeping

Read HOUSEKEEPING.md before you use the Fountain API, preferences, or local outputs.

## Requirements

- Fountain API for project, show, channel, preference, reporting, brand, or automation setup.

## Process

1. Identify the setup areas required by the request:

   - Fountain access and skill installation.
   - Project or podcast creation.
   - Social channel connection.
   - Project preferences.
   - Local render tools.
   - Brand style.
   - Reporting or recurring automation.

   Do not inspect or configure unrelated areas unless the user asked for a full setup.

2. Verify the selected area with the smallest direct check.
   Confirm API access by listing projects.
3. Resolve the selected area:

   - For access, connect or install the Fountain plugin.
   - For a missing project or podcast, open the applicable Fountain onboarding page.
   - For channels, guide the user to connect the requested `SocialChannel`.
   - For preferences, record only decisions needed by the current workflow.
   - For render tools, install or explain only the tools required by the selected output.
   - For brand, derive one style proof and record confirmed choices.
   - For automation, configure the requested recurring run and record its machine and time.

4. Use a safe Fountain default when the user did not choose and the choice is reversible.
   Record it, state it, and offer customization without blocking the current work.
5. Verify that the original blocker is cleared.
   Resume the calling skill when there is one.

The run is complete when the requested setup works or when one exact external action remains for the user.

## Additional notes

For a full setup, use these defaults unless the user gives another value:

- Email delivery with separate `performance` and `review-posts-simple` reports.
- Auto-render on.
- Three clips per day.

When no user is present, complete only work that needs no user choice.
Record completed choices immediately, and report the one next action for any remaining blocker.
