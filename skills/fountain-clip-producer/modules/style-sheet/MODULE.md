---
name: style-sheet
description: Draw every caption preset on one frame of the clip, so the user chooses a style by looking at it.
---

## Overview

A style is a thing to look at, and not a list of names to read.
`build-style-sheet.py` takes one frame of the clip, draws each preset on a copy of that frame, and tiles
the copies into one labelled JPEG.
The user reads a label and names it back, and that name goes to module **captions**.
The tile and the finished clip come from the same renderer, so a tile cannot promise a look that the
render does not make.

## Input

- The export to sample, usually `clip-vertical.mp4`.
- The word timings of the clip, made from its own audio and rebased so the first word starts at zero.
- Optional: the moment to sample, and a shorter list of presets.

## Output

- A contact sheet JPEG, where each tile carries its number and the name of its preset.
- A style index, which gives the name, the animation and the font of each tile.
- One full-size still for each preset, in the working directory.

## Requirements

- ffmpeg and ffprobe built with libass. On macOS that is the Homebrew `ffmpeg-full` formula.
- ImageMagick, for `magick montage`.
- Python 3.11 or later.

## Process

1. Build the sheet:

   ```bash
   scripts/build-style-sheet.py --input clip-vertical.mp4 --words words.json \
     --out style-sheet.jpg --emit-index style-sheet.json
   ```

2. Look at the sheet before the user does.
   Build it again with `--at` when the frame hides the speaker behind a hand, catches a blink, or holds
   a face that no caption sits clear of.
3. Give the user the sheet and the index together, and ask them to name a tile.
4. Say which of the tiles move, because a still cannot show an animation.
5. Give the chosen name to module **captions**, and ask module **brand** to record it, so that a later
   session does not ask again.

## Additional notes

The script samples the longest word of the middle of the clip.
That word is the one whose animation has finished and whose successor has not started, so every tile
shows its style at rest rather than caught half-scaled.
A moment you choose yourself with `--at` has no such guarantee, and a pop style then draws small.

Each preset groups the words its own way, so the tiles do not all carry the same words.
That is the point: how many words a style puts on screen is most of how it reads.

Use `--crop caption` when the words are too small to judge on the sheet.
It keeps the band that the words sit in, which draws them about twice as large, and it loses the face.
The full frame is the default because it shows what the caption covers.

A preset that fails to build is left out of the sheet and named on the error stream, and the sheet still
carries the rest.

One sheet serves a whole run, and a show that already chose a style needs none.
The sheet is a working, so it goes in the working directory and not to the user's library.
