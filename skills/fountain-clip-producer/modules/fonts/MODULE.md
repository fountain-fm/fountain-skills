---
name: fonts
description: Make the font that a style names available to the renderer, and substitute one safely when it is absent.
---

## Overview

A style spec names a font family, and `build-captions.py` writes that name into the ASS style block.
The skill carries its own fonts, so every preset renders the same on any machine.
Each bundled file has the name of the family that it holds.
The script builds the file name from the family name, and finds the file.
So a new family needs no entry in any list.
A missing font changes the look, and it also changes the rendered width of the text.
So the fit measurement and the burn must use the same font.

## Input

- The font families that the resolved caption spec or the overlay spec names.
- The bundled fonts in `assets`, which every preset points at.
- Optional: the font files of a show, from module **brand**.

## Output

- A pass or a fail for each named font, inside the report of module **preflight**.
- The `fontsdir` path to use for the render, when the fonts come as files.

## Requirements

- ffmpeg built with libass.
  On macOS that is the Homebrew `ffmpeg-full` formula, and not the default one.
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
3. While you debug a failure, check one font by hand.
   When `fc-match` returns a different family, the font is absent:

   ```bash
   fc-match "Montserrat"
   ```

4. Inspect a still against the expected typeface before delivery.

## Additional notes

No font is on every machine.
The web-safe fonts belong to Microsoft, so a Linux machine has none of them.
A container often has no font at all.
So the skill ships the fonts that it names, and does not trust the machine.

A download at render time is not a good replacement.
Module **captions** measures the width of each word against the font file itself.
If a family changes in a new release, every measurement changes, and a line that fitted before now overflows.
The measurements were taken against the bundled file.

Never substitute a lookalike font without telling the user.
Ask for the files when a show uses a licensed font, and say which font you used and why.

A caption in the wrong font is a styling failure, and not a small cosmetic point.
The font is most of what makes the clip look like that show.

A font that resolves by name can still render badly for other reasons, so the still is the real check.

ImageMagick can fail to find a family name, and give no error.
That changes the measured width as well as the look.
Pass it an absolute path to the bundled file, because `magick -list font` is often empty.

A font file registers a family and a style.
libass finds a font by its family.
So the bold weight of a family is the family name with `font.bold`.
Never use "Family Bold", because that name matches nothing at all.

Leave `font.bold` off for a face that ships a single weight.
Most display faces ship one weight.
On one of those, `font.bold` makes libass draw a bold that the file does not have.
ImageMagick measures the file as it is.
So the caption is then wider than the width that the fit report gives.

Title cards, lower thirds, and on-screen labels follow these same rules.
They take `fontfile=` with the drawtext filter, or they come in as a prepared image.
