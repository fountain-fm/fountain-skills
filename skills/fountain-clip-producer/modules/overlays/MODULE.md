---
name: overlays
description: Composite the layers of a clip - logos, titles, lower thirds, progress bars, and audiograms.
---

## Overview

An overlay is polish, and it is requested work.
A spec lists the layers in paint order.
`build-overlays.py` compiles the layers into one ffmpeg command.
One pass therefore draws every layer.
A standing layer from module **brand**, such as the logo of the show, counts as requested.

## Input

- The export to decorate, usually `clip-vertical.mp4`, and its duration.
- The artwork of the show, for a clip whose source carries no video.
- Optional: a preset name, the text of a title, a brand kit, and per-clip overrides.

## Output

- The decorated export, and a preview thumbnail when the request asks for one.
- An overlay plan, with the resolved layer list.

## Requirements

- ffmpeg built with drawtext and fontconfig.
  On macOS that is the Homebrew `ffmpeg-full` formula.
- ImageMagick, to measure a title before it is drawn.
- Python 3.11 or later.

## Process

1. Read the standing layers of the show from module **brand**.
   Use preset `show-logo` or `sponsor-logo` when the show has no kit, and point `asset` at the real image.
   Each of these presets ships a placeholder, so that it renders from its defaults.
   An `asset` can be a file on this machine or an `http` URL.
   ffmpeg opens the URL itself.
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

   Pick a moment when the speaker is clearly visible and in the middle of an expression.
   Never pick a moment in the middle of a blink.

4. Confirm that no layer covers the face of the speaker, an active caption, or key text on screen.

## Additional notes

These are the layer types:

- `image` puts a still, a video, or a GIF on the clip, for a logo, a B-roll insert, or an animated sticker.
- `title` is the hook headline, and a box colour turns it into the solid headline bar.
- `lowerThird` is the guest name and role, or the show and the episode number.
  For a clip from a talk that no episode holds, it is the speaker and the event.
- `watermark` is small persistent text, such as a handle.
- `scrim` fades a dark gradient over the lower or the upper third, so that a caption stays legible on
  bright footage or over a graphic burned into the picture.
  A scrim is one part of a package, and not a package itself.
  Add it to the preset that needs it, as `audiogram-headline` does, because a scrim alone is not a look.
- `progressBar` sweeps a thin bar across the clip.
- `audiogram` draws a meter of the sound, for a source that carries no video.
- `blurFill` is the base for footage that is not vertical.
  It gives both the blurred fill and the card look.

The compiler validates the spec before it emits the command.
An unknown layer type, a misspelled field, and a missing asset are hard errors.
`blurFill` MUST be the first layer, because it builds the base.
Text near the caption zone and a layer in the right tenth of the frame cause a warning.
The reason is that the platform draws its own buttons in that right tenth.
The compiler wraps a title that is too long for one line.
It then makes the title smaller until the title fits the number of lines that it is allowed.
This is necessary because the writer of a hook cannot see the frame that the hook appears in.
`boxShape` says what the `boxColor` paints: the text, a `band` with square ends, or a rounded `card`.
The box of `drawtext` fits each line separately and leaves a ragged edge.
Thus a band and a card are both measured from the drawn glyphs instead.
They give one clean edge around every line, centred on the ink, and not on the typeset box.
The typeset box includes leading that the letters do not have, and that puts the backing too high on its
own words.
A band and a card both fit the text, and not the frame.
The reason is that a backing sized to the frame is far wider than a short hook needs.
`boxMargin` sets how close either one can come to the edge.
`blurFill` takes a `borderW`.
A card needs a border whenever the artwork and the background are both dark.
Without one, the cover looks like a hole in the frame, and not like a card on it.
`backgroundDim` makes the blurred artwork behind the card darker, toward black.
The reason is that a cover blurred at full strength still competes for attention with the card and the
words, which come from the same picture.
With enough blur and enough dimming, the background is no longer a picture at all.
It becomes an even area of the show's own colour, and that is the purpose of the treatment.
A card always has a rim on a background made from its own picture.
A dark cover blurred into a dark background leaves no visible edge, and the card looks like a hole in the
frame.

A source with no video needs one of the audiogram packages.
Each package is built around the show's artwork, and not around the meter.
All the shows that do this well use this design.
The artwork, the episode title and the words are the content of the clip.
The meter only shows that the picture is not frozen.
`audiogram-cover` is the default choice, because it needs only the artwork and the title.
Take `audiogram-headline` when the clip starts with a claim.
Take `audiogram-brand` when the artwork is too busy to put text on it.
Take `audiogram-minimal` when the cover alone is enough.
Every audiogram package needs `layers.0.asset` set to the artwork file.
The agent downloads that file from the show's `info.image`.

The meter looks like a meter only when it has few, wide bars.
Thus `bars` is dozens, and never hundreds.
`barGap` is what separates one bar from the next.
Speech fills only a fraction of a full-scale meter, so `gain` stretches the part that is drawn.
Raise `gain` for a quiet clip, and lower it if the bars reach the top.
`mirror` grows the bars from a centre line instead of from the floor.

The convention on a podcast clip is to keep overlays simple and few.
A simple lower third works well.
Heavy branding on the first frame looks like an advertisement, and it raises the skip rate.
Keep a title card clear of the caption zone, and take it off screen before the viewer must read both at once.

Take the font from `assets/fonts`, or from the kit of the show, rather than choose one per clip,
because a title card in the wrong typeface breaks the look, the same as a caption in the wrong typeface.

On a two-speaker clip, use the speaker labels of module **captions** rather than name the speaker in both layers.

Check the placement again whenever the crop or the caption layout changes,
because either change moves what is under the overlay.

An overlay that hides the subject is a failed export, and not a matter of taste.
