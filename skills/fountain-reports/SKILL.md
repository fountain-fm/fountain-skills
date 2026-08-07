---
name: fountain-reports
description: Build the reports the operator reads - compose components into a preset, then email or print it.
---

## Overview

This skill owns how a report looks, so no caller invents its own format.
A report is a preset: an ordered list of components, where each component is a markdown template that
data fills.
The caller names the preset and gives the data; this skill composes the report, then emails it via the
Project API or prints it in the chat when the operator is reading there.
The operator customizes a preset once, in the preferences, and every later report honours it.

## Input

- The preset name, and the surface: email or printed.
- The data that the preset's components need, from the caller.
- Report customizations from the Reporting section of the preferences, when the show has any.

## Output

- A sent email via the Project API, or the same report printed in the chat.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the report customizations from the Reporting section of the
   preferences.
   A customization can drop a component, reorder them, or change the subject line of a preset.
2. Read the preset from `assets/presets`, and apply the customization.
3. Fill each component template from `assets/components` with the caller's data.
   Drop a component whose data the caller did not give, and say so after the send.
4. Email the composed markdown via the Project API, or print it when the surface is the chat.

## Additional notes

The presets:

- `performance` - the numbers for a window: headline, stats table, winners and losers, warnings.
- `draft-posts` - drafts before any render: the words, one card per draft, the dashboard link.
- `rendered-posts` - the rendered posts: headline, one card per post, the dashboard link.

A preset is named for the state it reports, never for the occasion or the skill that sends it,
so any head of the chain reuses it unchanged.

The printed surface serves the review in the chat: the operator reads the same `rendered-posts` that
the email carries, so the two never disagree.

A component is small and single-purpose.
A new kind of email is a new preset over the same components, and a missing block is a new component -
never markdown a caller writes by hand, because two callers writing the same block drift apart.

Numbers come from the caller and go into the template unchanged.
This skill formats; it MUST NOT recompute, round away, or soften what the caller measured.
