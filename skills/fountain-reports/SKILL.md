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

- Fountain API.

## Process

1. Read the report customizations from the Reporting section of the preferences.
   A customization can drop a component, reorder them, change a subject line, or change the delivery.
2. Read the preset from `assets/presets`, and apply the customization.
3. Fill each component template from `assets/components` with the caller's data.
   Drop a component whose data the caller did not give, and say so after the send.
   A component that needs no data is never missing data, so this rule never drops it.
   Only a customization can.
4. Deliver as the Reporting section asks: email via the Project API, printed in the chat, combined
   into a report sent later in the same run, or not at all.
   Email is the default, and goes to the addresses under Reporting.
   Ask for them when the section holds none, and record them in the same turn.
   Print in the chat instead when the user asked to read it there.
   Say plainly when a report was composed but not sent.
   A send that answers success is not proof of delivery, so say which one you saw.

## Additional notes

The presets:

- `performance` - the numbers for a window: headline, channels overview, yesterday's clips, learnings,
  warnings.
- `clips-waiting` - the clips that wait for a decision, rendered or not: the dashboard link first,
  then one summary line per clip. The words are read in the dashboard, where the reader approves or
  deletes, so the email says which clips exist and sends them there. Whether approving renders a clip
  or sends it is the approve note's job, and not a second preset's.
- `daily` - the whole day in one mail: the clips that wait, then the numbers. The user asks for it in
  place of the two, and the Reporting section records which of the two shapes the show wants.
- `settings` - the current settings, each with its origin, and the tour of the headings.
  Sent at first contact, or whenever the user asks what their settings are.

First contact, for a caller that finds the preferences empty:

1. Write the defaults: caption preset bold-social under Brand, each report delivered as email under
   Reporting, and auto-render on under Automation.
2. Mark each one `(default)`, and drop that mark when the user confirms or changes the value.
   The mark is what lets a later reader, and the origin of a `setting-row`, tell a default from a choice.
3. Ask the user where their emails go, and record the addresses under Reporting.
   The `settings` report is the first one, so nothing sends without them.
4. Send the `settings` report, which says what was set and what else each heading holds.
   First contact comes one time, so this is the only report that shows the headings unasked.

The defaults only make the settings visible and editable, because every skill already defaults the same
way with no entry at all.

A preset is named for the state it reports, never for the occasion or the skill that sends it,
so any head of the chain reuses it unchanged.

The printed surface serves the review in the chat: the user reads the same `clips-waiting` that
the email carries, so the two never disagree.

Combining joins reports, not machines: a report can wait only for one sent later in the same run,
because nothing holds a pending report between machines.

A component is small and single-purpose.
A new kind of email is a new preset over the same components, and a missing block is a new component -
never markdown a caller writes by hand, because two callers writing the same block drift apart.

Numbers come from the caller and go into the template unchanged.
This skill formats; it MUST NOT recompute, round away, or soften what the caller measured.

Send markdown, and never HTML.
The Project API renders the markdown itself, and strips every attribute from the result, so styling
that this skill sets does not reach the reader.
It styles the tables and keeps the column alignment that markdown asks for, so markdown carries
everything a report needs.
