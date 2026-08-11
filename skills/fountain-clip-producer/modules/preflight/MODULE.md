---
name: preflight
description: Confirm that the machine can render what the request asks for, before the first render starts.
---

## Overview

A render that fails halfway wastes the whole render.
This module asks the machine what it can do, and it answers before any work begins.
It names the caption renderer to use, the ffmpeg binary to burn with and the one to time words with,
and every tool that is absent.
It reports the environment, and it never looks at a rendered file.

## Input

- The kind of output that the request asks for, which decides how strict the check is.
- The font families of the resolved caption style, from module **fonts**.
- Optional: the landscape master, to probe it at the same time.

## Output

- A preflight report, which names the caption renderer, the binary to burn with, and the binary that
  carries whisper.
- A list of the missing tools, and a pass or a fail.

## Requirements

- ffmpeg and ffprobe.
- Python 3.11 or later.
- OpenCV 4.8 or later, importable from that same Python.
- ImageMagick, for a captioned render.

## Process

1. Run the check before the first render:

   ```bash
   scripts/render-preflight.py --media clip-landscape-master.mp4 \
     --require-magick --require-visual-qa --require-words --fonts "Montserrat,Anton" --json
   ```

   Drop `--require-magick` and `--fonts` for an export that carries no captions, and keep
   `--require-visual-qa`, because module **framing** needs that interpreter on every export.
   Keep `--require-words` for every tier above a rough cut, because the words of the clip come from
   whisper and three modules read them.
   Name the family alone, because a weight in the name matches nothing and reads as a missing font.

2. Stop and report to the user when the report names a missing tool.
   Say which tool is absent and how to install it, because this is a fault of the machine and not of the clip.
3. Read the caption renderer from the report, and record it in the caption plan.
   The order of preference is ASS, then drawtext, then a prepared transparent layer.
4. Burn the captions with the binary that the report names, and not always with the one on the PATH.
5. Confirm that each named font resolves to itself, and read module **fonts** when one falls back.
   A family that the skill ships passes without a system install, because libass is given that directory.
6. Cache the report, and run this module again only when the machine or the kind of output changes.

## Additional notes

A stock ffmpeg is often built without libass, so it cannot burn a styled caption.
The report therefore looks for another build on the machine, wherever the platform keeps them.
When it finds one, the ASS path stays open and the report names that binary.
A build without libass is a reason to use the other binary, and never a reason to drop to a lesser renderer.
The same search finds the build that carries whisper, and the two are usually the same binary.
There is no lesser renderer for a word timing: without whisper the clip has no words at all.

The report also names the Python interpreter that carries OpenCV, which module **framing** needs for its scripts.
An interpreter older than OpenCV 4.8 carries no `FaceDetectorYN`, and that is a missing tool rather than a warning.

A prepared transparent layer is the last choice, and it needs its own checks in module **qa**.
Reach for it only when no build on the machine can burn an ASS file.
