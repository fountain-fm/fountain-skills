---
name: overlays
description: Composite the layers of a clip - logos, titles, lower thirds, progress bars, and audiograms.
---

## Overview

An overlay is polish, and it is requested work.
A spec lists the layers in paint order, and `build-overlays.py` compiles them into one ffmpeg command.
One pass therefore draws every layer.
A standing layer from module **brand**, such as the logo of the show, counts as requested.

## Input

- The export to decorate, usually `clip-vertical.mp4`, and its duration.
- Optional: a preset name, the text of a title, a brand kit, and per-clip overrides.

## Output

- The decorated export, and a preview thumbnail when the request asks for one.
- An overlay plan, with the resolved layer list.

## Requirements

- ffmpeg with drawtext and fontconfig, from the Homebrew `ffmpeg-full` formula.
- Python 3.11 or later.

## Process

1. Read the standing layers of the show from module **brand**.
2. Compile the layers into the render command:

   ```bash
   scripts/build-overlays.py --spec hook-title --input clip-vertical.mp4 \
     --output clip-vertical-overlay.mp4 --duration 41.5 \
     --override "layers.0.text=the moment everything changed" \
     --emit-plan overlay-plan.json --run
   ```

   Leave out `--run` to print the command rather than run it.

3. Take a preview thumbnail when the request asks for one:

   ```bash
   # -ss seeks to the chosen moment, and -frames:v 1 writes that single frame.
   ffmpeg -hide_banner -y -ss "$T" -i clip-final.mp4 -frames:v 1 thumbnail.jpg
   ```

   Pick a moment where the speaker is clear and mid-expression, and never mid-blink.

4. Confirm that no layer covers the face of the speaker, an active caption, or key text on screen.

## Additional notes

These are the layer types:

- `image` puts a still, a video, or a GIF on the clip, for a logo, a B-roll insert, or an animated sticker.
- `title` is the hook headline, and a box colour turns it into the solid headline bar.
- `lowerThird` is the guest name and role, or the show and the episode number.
- `watermark` is small persistent text, such as a handle.
- `progressBar` sweeps a thin bar across the clip.
- `audiogram` draws a waveform, for a source that carries no video.
- `blurFill` is the base for footage that is not vertical, and it spans the blurred fill and the card look.

The compiler validates before it emits.
An unknown layer type, a misspelled field, and a missing asset are hard errors.
`blurFill` MUST be the first layer, because it builds the base.
Text near the caption zone and a layer in the right tenth of the frame raise a warning,
because the platform draws its own buttons in that rail.

The convention on a podcast clip is restraint.
A simple lower third reads well.
Heavy branding on the first frame reads as an advertisement, and it raises the skip rate.
Keep a title card clear of the caption zone, and take it off screen before the viewer must read both at once.

Take the font and the colours from the kit of the show rather than choose them per clip,
because a title card in the wrong typeface breaks the look exactly as a caption does.

On a two-speaker clip, use the speaker labels of module **captions** rather than name the speaker in both layers.

Check the placement again whenever the crop or the caption layout changes,
because either one changes what the overlay now sits on.

An overlay that hides the subject is a failed export, and not a matter of taste.
