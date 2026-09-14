---
name: fountain-clip-producer
description: Render an existing clip draft as a platform-ready video.
---

## Overview

This skill turns a settled clip source into one or more finished video files.
The root document selects the delivery tier and routes only the required production modules.
Module **qa** blocks delivery of any final that fails its checks.

## Input

- A `SocialPostMediaSource`, or the same source fields for an external video.
- Or a queue run, where module **queue** selects eligible draft posts.
- Optional target shapes, caption style, overlays, trim request, and delivery instructions.

## Output

- A landscape master and each requested export.
- A `SocialPostUpload` attached to the post, unless the user asks for files only.
- The plans and reports produced by the modules that ran.

## Housekeeping

Read HOUSEKEEPING.md before you use the Fountain API, preferences, or local outputs.

## Requirements

- Fountain API.
- Read module **preflight** for the conditional render software and versions.

## Process

1. For a queue run, read and run module **queue**.
   For a named post or source, continue with the tier that the request implies.
2. Use these delivery tiers:

   - A rough cut is the landscape master from module **media**.
   - A clean final adds the requested crop, portrait captions, and module **qa**.
   - A publish final adds the requested or established brand layers.

   Ask only when the requested outcome does not identify a tier.
   Do not add optional polish that the user did not request.

3. For a final, read and run module **preflight** before the first render.
   Reuse its report while the machine and output type stay unchanged.
4. Read and run module **media** to make the master.
   Then read and run module **words** when the tier needs captions or content verification.
5. Read module **trims** only when the user asks to remove pauses or spoken filler.
6. Read and run module **framing** for each requested non-landscape shape.
   Read module **shots** only when one shot holds multiple people and speaker labels are available.
7. Read module **brand** for a clean final or publish final.
   Use module **fonts** and module **captions** for each captioned export.
   Use the default caption style when no confirmed kit exists, and report the default without pausing the run.
8. Read module **overlays** only for a requested or established layer, or for an audio-only source.
9. Read and run module **qa** after the last render.
   Repair failures caused by this run.
   Rerun the affected modules until the gate passes or a user choice is required.
10. Attach the passed final through the Uploads API and Social API, unless the user asked for files only.
11. Present the result on the clip card from skill **fountain-clip-finder**.

The run is complete when every requested export passes its applicable gate and is attached or delivered,
and every failure that needs a user choice states the exact blocked decision.

## Additional notes

Independent clips can move through one stage concurrently.
Do not assume that concurrent ffmpeg work makes encoding faster.

Always use the tallest available rendition.
Deliver a smaller true resolution when the source cannot support the requested size.
Do not upscale a crop to claim a resolution that the source does not contain.

A render does not approve a post.
Never put an API key, token, or cookie in a command, manifest, or report.

For a later change, reuse outputs that are still correct and write changed outputs under new names.
Rebuild only the affected module outputs and the checks that depend on them.
