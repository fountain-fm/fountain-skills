---
name: fountain-reports
description: Build the reports the user reads - compose components into a preset, then email or print it.
---

## Overview

This skill owns how a report looks, so no caller invents its own format.
A report is a preset: an ordered list of components, where each component is a markdown template that
data fills.
The caller names the preset and gives the data; this skill composes the report and delivers it the
way the Reporting section asks - email, printed, combined with a later report, or not at all.
The user customizes a preset once, in the preferences, and every later report honours it.

## Input

- The preset name.
- The data that the preset's components need, from the caller.
- Optional: the surface, when the user is present and asks to read the report here.
- Report customizations from the Reporting section of the preferences, when the show has any.

## Output

- The report, delivered as the Reporting section asks - email is the default.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the report customizations from the Reporting section of the
   preferences.
   A customization can drop a component, reorder them, change a subject line, or change the delivery.
2. Read the preset from `assets/presets`, and apply the customization.
3. Fill each component template from `assets/components` with the caller's data.
   Drop a component whose data the caller did not give, and say so after the send.
4. Deliver as the Reporting section asks: email via the Project API, printed in the chat, combined
   into a report sent later in the same run, or not at all.
   Email is the default, and a user who is present and asked to read it here wins over the section.
   Say plainly when a report was composed but not sent.

## Additional notes

The presets:

- `performance` - the numbers for a window: headline, stats table, winners and losers, warnings.
- `draft-posts` - drafts before any render: the words, one card per draft, the dashboard link.
- `rendered-posts` - the rendered posts: headline, one card per post, the dashboard link.
- `settings` - the current settings, each with its origin, and the tour of the headings.
  Sent at first contact, or whenever the user asks what their settings are.

First contact, for a caller that finds the preferences empty:

1. Write the defaults: caption preset bold-social under Brand, each report delivered as email under
   Reporting, and auto-render off under Automation.
2. Mark each one `(default)`, and drop that mark when the user confirms or changes the value.
   The mark is what lets a later reader, and the origin of a `setting-row`, tell a default from a choice.
3. Send the `settings` report, which says what was set and what else each heading holds.

The defaults only make the settings visible and editable, because every skill already defaults the same
way with no entry at all.

A preset is named for the state it reports, never for the occasion or the skill that sends it,
so any head of the chain reuses it unchanged.

The printed surface serves the review in the chat: the user reads the same `rendered-posts` that
the email carries, so the two never disagree.

Combining joins reports, not machines: a report can wait only for one sent later in the same run,
because nothing holds a pending report between machines.

A component is small and single-purpose.
A new kind of email is a new preset over the same components, and a missing block is a new component -
never markdown a caller writes by hand, because two callers writing the same block drift apart.

Numbers come from the caller and go into the template unchanged.
This skill formats; it MUST NOT recompute, round away, or soften what the caller measured.
