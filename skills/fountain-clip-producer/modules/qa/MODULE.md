---
name: qa
description: Check the environment before a render, and gate every delivery on one pass or fail report.
---

## Overview

This module runs twice.
Before the first render it confirms that the machine can do what the request asks for.
After the last render it composes the checks of the other modules with whole-clip checks into one gate.
Nothing reaches the user until that gate reports a pass.

## Input

- The landscape master, and the final export.
- The expected width, height, frame rate, and duration.
- The font families of the resolved style, for the preflight.
- The crop plan and the visual QA report of module **framing**, and the fit report of module **captions**.

## Output

- A preflight report, which names the renderer to use and each missing tool.
- A QA report, with a `pass` or a `fail` status and the reason for each failed check.

## Requirements

- ffmpeg and ffprobe.
- Python 3.11 or later, with OpenCV.
- ImageMagick, for a captioned render.

## Process

1. Run the preflight before the first render:

   ```bash
   scripts/render-preflight.py --media clip-landscape-master.mp4 \
     --require-magick --require-visual-qa --fonts "Montserrat Bold" --json
   ```

   Drop the last three flags for an export that carries no captions.

2. Read the renderer that the report names, and record it in the caption plan.
3. Use the ffmpeg binary that the report names for a caption burn.
   The report searches for a build that carries libass when the one on the PATH does not.
4. Run the gate after the last render:

   ```bash
   scripts/validate-clip.py \
     --clean-master clip-vertical.mp4 --final clip-vertical-captioned.mp4 \
     --caption-fit-report caption-fit-report.json --visual-report visual-qa-report.json \
     --expected-width 1080 --expected-height 1920 --expected-fps 30 \
     --expected-duration "$DURATION" --report qa-report.json
   ```

   Leave out the last two report flags for an export that carries no captions.

5. Report the failed checks and the next repair step when the gate fails.
   You MUST NOT present the file as finished.

## Additional notes

The gate blocks every tier above a rough cut, and it asks for all of this:

- The final file exists and is not empty.
- The width, the height, the frame rate, the duration, and the audio stream match what was expected.
- No render pass and no caption pass introduced a black interval.
- A contact sheet exists, and somebody looked at it.
- The crop plan records a decision for each scene cut.
- The visual QA report reports a pass, when it is present.

Each production module runs its own checks as it works, and this module does not repeat them.
It adds the checks that only make sense across the whole clip.

Burn a style proof whenever a style is new or changed.
That means the first use of a preset on a show, an override that changes the look, or an edited kit.
Render a few seconds that span one full caption group, and inspect a still at a word onset, mid-animation, and at rest.
The proof is cheap and a full render with a broken style is not.
The spec validation and the fit report catch the measurable faults, and the proof catches the ones of judgment.
A repeat render of a style that the user already approved needs no new proof.

Cache the preflight result, and run it again only when the environment or the kind of output changes.
