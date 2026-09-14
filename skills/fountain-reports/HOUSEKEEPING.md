## Overview

This file holds shared runtime rules for Fountain skills.
Read it one time per session, and only before a task uses the Fountain API, changes preferences,
publishes, or writes local outputs.

## Fountain API

Use the Fountain MCP when it is available.
Confirm access by listing projects before you report an authentication problem.

Use HTTP only when the MCP is unavailable.
Read https://beta.fountain.fm/docs.md before the first HTTP request of the session.
Read the key from `FOUNTAIN_API_KEY` or `.env`.
Never put a key, token, or cookie in a command, log, report, or output file.

Run skill **fountain-onboarding** only for the setup item that blocks the requested work.
Resume the requested work as soon as that item is resolved.

## Authority

Do not approve, schedule, or publish content without an explicit user instruction.
Creating or editing a draft does not approve it.

Tell the user about a change that affects meaning, cost, public state, or their next action.
When you ask for approval, include the complete content that the user will approve.
When you report a number about a show, name the sources or time window that you counted.

## Preferences

Preferences are the only store for Fountain project data that a later session needs.
Load them with the Project API only when the task needs them.
Never keep a local copy for a later session.
Record a new user preference in the same turn.

Preferences are Markdown with unordered lists under these optional `##` headings:

- Narratives.
- Editorial.
- Brand.
- Accounts.
- Reporting.
- Automation.
- Other.

Each item MUST be at most 200 characters and end with `(AGENT-YYYY-MM-DD)` or `(USER-YYYY-MM-DD)`.
An item in preferences is active, so do not mark it as proposed or pending.
Do not store data that the API or another source can derive.

The Project API replaces the complete preferences document.
Preserve every unrelated entry when you update it.
Tell the user what changed.

Use Narratives for subjects that the show returns to across episodes.
Use Editorial for tone, structure, selection rules, and lessons.
Use Brand for caption styles, fonts, colours, and assets.
Use Accounts for handles, external sources, and machine-specific locations.
Use Reporting for report presets, delivery, and recipients.
Use Automation for recurring work, clip budgets, and auto-render choices.

## Local outputs

Write Fountain files under `fountain/outputs/<show>/<asset>`.
Use `<episode-number-or-date>-<topic>` for the asset folder.
Put only finished work in the asset folder.
Put plans, reports, proofs, intermediate media, and temporary scripts in `workings` below it.

Use the show folder name from Accounts when one exists.
When you choose a new show folder name, record it in Accounts in the same turn.
Treat outputs as ephemeral work, and do not require a later session to read them.
