---
name: fountain-reports
description: Compose and deliver Fountain performance, clip-review, or settings reports.
---

## Overview

This skill turns caller data into a consistent report from reusable presets and components.
It owns report structure and delivery, but it does not recompute the caller's results.

## Input

- A preset name and the data required by its components.
- Optional Reporting preferences and a requested delivery surface.

## Output

- The composed report, delivered through the configured surface or returned in chat.

## Housekeeping

Read HOUSEKEEPING.md before you use the Fountain API or preferences.

## Requirements

- Fountain API for email delivery and Reporting preferences.

## Process

1. Load Reporting preferences only when the request does not name the delivery and customization directly.
2. Read the selected preset from `assets/presets`.
   Apply configured component order, omissions, subject, and delivery changes.
3. Fill its templates from `assets/components` with the caller's data.
   Build Fountain and platform links from `assets/links.md`.
   Drop a data-dependent component when its input is absent, and report the omission.
4. Deliver by email, print in chat, combine with a report later in the same run, or do not send,
   as the request or Reporting preferences specify.
   Use email as the default.
   Use skill **fountain-onboarding** only when missing report setup blocks delivery.
5. Report whether the API accepted the send.
   Do not claim that an accepted send proves inbox delivery.

The run is complete when the report is delivered as requested, or when the composed report and exact
delivery blocker are both available to the user.

## Additional notes

Available presets are:

- `performance` for a performance window.
- `review-posts-simple` for posts that wait for a decision.
- `review-posts` for review posts and performance in one report.
- `settings` for current settings and their origins.

A preset describes the state it reports, not the skill or occasion that requested it.
Numbers pass through unchanged.
Send Markdown, because the Project API renders it and strips HTML attributes.
