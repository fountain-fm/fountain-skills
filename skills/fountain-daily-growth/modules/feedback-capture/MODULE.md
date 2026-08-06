---
name: feedback-capture
description: Turn the operator's review feedback into durable entries in the preferences.
---

## Overview

This module makes the loop learn without local state.
It distills why the operator approved, edited, or rejected each item, and writes the durable lessons into
the preferences.
Module **trend-discovery** reads those lessons on the next run.
It does not log posts - the posts and their metadata live in the API.

## Input

- The operator's approvals, rejections, edits, and the reasons behind them.

## Output

- Updated preferences.

## Requirements

- Skill **fountain-api**.

## Process

1. After the review session, distill the reason behind each approve, edit, and reject.
   Capture why the operator decided, not just the outcome.
2. Keep only the lessons that hold beyond today.
   Examples: a banned phrase, a preferred hook style, a rejected topic, a newly confirmed platform handle.
3. Write each lesson under the matching heading of the preferences, succinctly.
   Record a narrative the operator approved in the Narratives section.
4. When a new lesson contradicts an old entry, revise the old entry - do not append a duplicate.

## Additional notes

An outcome with no reason teaches nothing - ask the operator for the reason when it is unclear.

One-day noise MUST NOT go into the preferences.
"Reject: we already covered this topic this week" is noise.
"Reject: never use price predictions in copy" is a durable lesson.

You MUST NOT keep a local log of posts, packs, or feedback for a later session.
