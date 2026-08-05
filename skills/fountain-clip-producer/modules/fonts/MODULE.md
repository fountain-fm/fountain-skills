---
name: fonts
description: Make the font that a style names available to the renderer, and substitute one safely when it is absent.
---

## Overview

A style spec names a font family, and `build-captions.py` writes that name into the ASS style block.
This module makes sure that libass can find the font at render time.
A missing font does more than change the look, because it changes the rendered width of the text.
The fit measurement and the burn must therefore see the same font.

## Input

- The font families that the resolved caption spec or the overlay spec names.
- Optional: the font files of a show, from module **brand**.

## Output

- A pass or a fail for each named font, inside the report of module **preflight**.
- The `fontsdir` path to use for the render, when the fonts come as files.

## Requirements

- ffmpeg with libass and fontconfig, from the Homebrew `ffmpeg-full` formula.
- fontconfig, for `fc-match`.

## Process

1. Give the font names to module **preflight**, which fails before a render starts.
2. Check one font by hand while you debug a preflight failure:

   ```bash
   fc-match "Montserrat Bold"
   ```

   A result that names a different family means the font is absent.

3. Point libass at the font files directly when a show carries its own fonts:

   ```bash
   ffmpeg -hide_banner -y -i clip-vertical.mp4 \
     -vf "subtitles=captions.ass:fontsdir=./fonts" \  # read this folder before the system fonts
   -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart \
     clip-vertical-captioned.mp4
   ```

4. Inspect a still against the expected typeface before delivery.

## Additional notes

Never substitute a lookalike font without a word to the user.
Ask for the files when a show uses a licensed font.
When you must substitute, take a widely available equivalent, and say which font you used and why.

A caption in the wrong font is a styling failure and not a small cosmetic point,
because the font is most of what makes the clip look like that show.

A font that resolves by name can still render badly for other reasons, so the still is the real check.

Title cards, lower thirds, and on-screen labels follow these same rules.
They take `fontfile=` with the drawtext filter, or they come in as a prepared image.
