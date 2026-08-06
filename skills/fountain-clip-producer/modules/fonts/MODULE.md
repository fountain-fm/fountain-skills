---
name: fonts
description: Make the font that a style names available to the renderer, and substitute one safely when it is absent.
---

## Overview

A style spec names a font family, and `build-captions.py` writes that name into the ASS style block.
The skill carries its own fonts, so every preset renders the same on any machine.
A missing font does more than change the look, because it changes the rendered width of the text.
The fit measurement and the burn must therefore see the same font.

## Input

- The font families that the resolved caption spec or the overlay spec names.
- The bundled fonts in `assets`, which every preset points at.
- Optional: the font files of a show, from module **brand**.

## Output

- A pass or a fail for each named font, inside the report of module **preflight**.
- The `fontsdir` path to use for the render, when the fonts come as files.

## Requirements

- ffmpeg with libass, from the Homebrew `ffmpeg-full` formula.
- fontconfig, for `fc-match`.

## Process

1. Point libass at the bundled fonts on every caption burn:

   ```bash
   # fontsdir makes libass read that folder before it asks the machine for a font.
   ffmpeg -hide_banner -y -i clip-vertical.mp4 \
     -vf "subtitles=captions.ass:fontsdir=assets/fonts" \
     -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart \
     clip-vertical-captioned.mp4
   ```

   Point it at the fonts of the show instead when module **brand** carries some.

2. Give the font names to module **preflight** when a spec names a font that is not bundled.
3. Check one font by hand while you debug a failure, where a different family means it is absent:

   ```bash
   fc-match "Montserrat"
   ```

4. Inspect a still against the expected typeface before delivery.

## Additional notes

No font is on every machine.
The web-safe faces belong to Microsoft, so a Linux box carries none of them, and a container often
carries no font at all. The skill therefore ships the fonts it names rather than trust the machine.

Never substitute a lookalike font without a word to the user.
Ask for the files when a show uses a licensed font, and say which font you used and why.

A caption in the wrong font is a styling failure and not a small cosmetic point,
because the font is most of what makes the clip look like that show.

A font that resolves by name can still render badly for other reasons, so the still is the real check.

ImageMagick can fail a family name without an error, which changes the measured width as well as the look.
Pass it an absolute path to the bundled file, because `magick -list font` is often empty.

A font file registers a family and a style, and libass matches on the family.
The bold weight of a family is therefore the family name with `font.bold`, and never "Family Bold",
which matches nothing at all.

Title cards, lower thirds, and on-screen labels follow these same rules.
They take `fontfile=` with the drawtext filter, or they come in as a prepared image.
