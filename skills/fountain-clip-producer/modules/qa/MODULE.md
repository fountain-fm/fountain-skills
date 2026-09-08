---
name: qa
description: Prove a style on a short render, and gate every delivery on one pass or fail report.
---

## Overview

This module looks at rendered pictures, and it does that twice.
A style proof checks a new look on a few seconds, before the cost of a full render.
The delivery gate then composes the checks of the other modules with whole-clip checks into one report.
Nothing reaches the user until that gate reports a pass.

## Input

- The clean master, the final export, and the landscape master of module **media**.
- The expected width, height, frame rate, and duration.
- The crop plan and the visual QA report of module **framing**, and the contact sheet.
- The caption fit report of module **captions**, when the export carries captions.
- The removal report of module **trims**, when the clip was cut.

## Output

- A style proof, and the stills taken from it.
- A QA report, whose `status` field reads `pass` or `fail`, with the reason for each failed check.
  Read that one field for the verdict, because each check carries a status of its own.

## Requirements

- ffmpeg and ffprobe.
- Python 3.11 or later.

## Process

1. Burn a style proof whenever a style is new or changed.
   Render a few seconds that span one full caption group, with the real style on real footage.
2. Inspect a still of the proof at a word onset, at mid-animation, and at rest.
   Repeat until the look is right, because a full render with a broken style is waste.
3. Run the gate after the last render:

   ```bash
   scripts/validate-clip.py \
     --clean-master clip-vertical.mp4 --final clip-vertical-captioned.mp4 \
     --landscape-master clip-landscape-master.mp4 \
     --caption-fit-report caption-fit-report.json \
     --visual-report visual-qa-report.json --contact-sheet contact-sheet.jpg \
     --expected-width 1080 --expected-height 1920 --expected-fps 30 \
     --expected-duration "$DURATION" --report qa-report.json
   ```

   Leave out `--caption-fit-report` for an export that carries no captions.
   Keep `--visual-report`, because module **framing** asks for it on every vertical export.

4. Add `--caption-layer` only when the render used a prepared transparent layer.
   That layer is the one case with a separate file, and it needs its own frame rate and alpha checks.
5. Report the failed checks and the next repair step when the gate fails.
   You MUST NOT present the file as finished.

## Additional notes

The gate blocks every tier above a rough cut, and it asks for all of this:

- The final file exists and is not empty.
- The width, the height, the frame rate, the duration, and the audio stream match what was expected.
- The landscape master is tall enough for the export, because a container says 1080x1920 whatever it holds.
- No render pass and no caption pass introduced a black interval.
- The clip opens and closes on a whole word.
  The first caption starts near the head of the clip, and the last one ends near its tail.
  Speech with no caption at either edge is the tail of the word before, or the head of the word after,
  and the clip opens or closes in the middle of it.
  This one fails the span, and not the render, so report it to the user and name the edge.
- A contact sheet exists, and somebody looked at it.
- The crop plan records a decision for each scene cut.
- The visual QA report reports a pass, when it is present.
  A frame that module **framing** named as a graphic passes this, because the show put no person
  there, and one title card MUST NOT fail a clip that every other check passed.
- The removal report of module **trims** is present, when the clip was cut, and the user approved it.

Each production module runs its own checks as it works, and this module does not repeat them.
It adds the checks that only make sense across the whole clip.

A style is new or changed when a show uses a preset for the first time, when an override changes the look,
or when the kit of the show changes.
A repeat render of a style that the user already approved needs no new proof.

The spec validation and the fit report catch the faults that a machine can measure.
The proof catches the ones of judgment, such as a look that is valid and still wrong for the show.
