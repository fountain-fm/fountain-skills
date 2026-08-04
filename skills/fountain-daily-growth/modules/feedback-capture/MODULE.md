---
name: feedback-capture
description: Turn the operator's review feedback into durable editorial preferences in fountain/PREFERENCES.md.
---

## Overview

This module makes the loop learn without local state.
It distills why the operator approved, edited, or rejected each item, and writes the durable lessons into
fountain/PREFERENCES.md.
Module trend-discovery and skill fountain-stats read those lessons on the next run.
It does not log posts - the scheduled posts and their metadata live in the API.

## Input

- The operator's approvals, rejections, edits, and the reasons behind them.

## Output

- Updated entries in fountain/PREFERENCES.md.

## Process

1. After the review session, distill the reason behind each approve, edit, and reject.
   Capture why the operator decided, not just the outcome.
2. Keep only the lessons that hold beyond today.
   Examples: a banned phrase, a preferred hook style, a rejected topic, a newly confirmed platform handle.
3. Write each lesson under the matching heading of fountain/PREFERENCES.md, succinctly.
   Record a narrative the operator approved in the narrative library.
4. When a new lesson contradicts an old entry, revise the old entry - do not append a duplicate.

## Additional notes

An outcome with no reason teaches nothing - ask the operator for the reason when it is unclear.

One-day noise MUST NOT go into fountain/PREFERENCES.md.
"Reject: we already covered this topic this week" is noise.
"Reject: never use price predictions in copy" is a durable lesson.

You MUST NOT keep a local log of posts, packs, or feedback for a later session.
