---
name: captions
description: Build styled, word-timed captions from a style spec and burn them into the clip.
---

## Overview

A portrait clip is watched with the sound off, so it carries captions by default.
Any other shape is captioned when the request asks for it.
A style spec drives the look, and `build-captions.py` compiles that spec and the word timings into an ASS file.
ffmpeg then burns the ASS file in with one filter pass.
Never write animated ASS events by hand, because the per-word timing arithmetic is what the script exists to get right.

## Input

- The `TranscriptWord` list of the clip span, rebased so that the first word starts at zero.
- The export to caption, usually `clip-vertical.mp4`.
- Optional: a preset name, a brand kit from module **brand**, and per-clip overrides.

## Output

- `captions.ass`, and the captioned export.
- A caption plan, with the resolved spec, the overrides, and the renderer.
- A caption fit report, which module **qa** requires.

## Requirements

- ffmpeg with libass, from the Homebrew `ffmpeg-full` formula.
- ImageMagick, to measure text width.
- Python 3.11 or later.

## Process

1. Take the word timings from the `fountain` source of the transcript, which carries a flat `TranscriptWord` list.
   The sentence-level segments are too coarse for a caption.
   Use the rebased list of module **trims** instead, when that module cut the clip.
   Stop and report to the user when a portrait export has no word timings, rather than deliver it bare.
2. Clean the text before you set any timing, under the faithful-clean rules below.
3. Compile the spec and the words into the ASS file:

   ```bash
   scripts/build-captions.py --style word-pop --words words.json \
     --override colors.highlight=#FFD400 --override font.size=84 \
     --out captions.ass --emit-lines caption-lines.json --emit-spec resolved-style.json
   ```

4. Fill in the fit report by measuring each line the script emits, which confirms the packing rather
   than finds a surprise:

   ```bash
   # label renders the text at the real font and size, and "%w" prints the width it took.
   magick -background none -font assets/fonts/Montserrat-Bold.ttf -pointsize 72 \
     label:"the line to measure" -format "%w" info:
   ```

5. Run module **qa** for a style proof whenever the style is new or changed.
6. Burn the captions in:

   ```bash
   # The subtitles filter hands the file to libass, which reads the styles and the animation from it.
   # -c:a copy leaves the audio untouched, because this pass changes the picture alone.
   ffmpeg -hide_banner -y -i clip-vertical.mp4 \
     -vf "subtitles=captions.ass:fontsdir=assets/fonts" \
     -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart \
     clip-vertical-captioned.mp4
   ```

7. Check the render: no new black interval, captions that change through the clip, and no caption that lags the audio.

## Additional notes

The spec layers from the lowest priority to the highest: defaults, preset, brand kit, per-clip override.
A misspelled override path is a hard error, and `--check` rejects unreadable contrast or flicker on its own.

Use `bold-social` when neither the request nor the brand kit names a preset: it reads on a phone at arm's
length, and it animates nothing that can go wrong.
The presets in `assets` are starting points, each carries its own description, and `hormozi` wants 3 to 5
words marked `"emphasize": true`.

These are the text rules, and the default mode is faithful-clean:

- Remove filler and a repeated false start, when that does not change the meaning.
  This is safe by default because the audio still carries the word, which is why module **trims** is not.
- Judge "like" and "I mean" one at a time, because each is filler about half the time.
  Delete the word and read the line again, and keep it when the line now says something else.
  "Like" before a quote or a number always stays.
- Keep a repetition that carries emphasis, rhythm, or contrast.
- Keep the jokes, the strong language, and the quoted words, and never turn a sentence into a different claim.
- Drop a dangling fragment when the clip ends before the speaker finishes.

Correct the machine transcript, because it renders as it arrives: check the names, the numbers and the
currency, and spell each name the way the show notes do.

Keep `font.case` at `verbatim` when the transcript carries real capitals, and use `upper` for a loud style:
`sentence` lowercases every word first, so it destroys "I" and every name.

A caption group breaks on a speaker change, a sentence end, a silence, or the safe width, and never inside a clause.
The script measures each word in the font and case it will render in and packs until the next will not fit,
so `font.size` is the control, `grouping.maxWords` only a ceiling, and a one-word style is not packed at all.
A social caption drops the full stop and the comma that end a group, though a comma inside one stays.
A question mark and an exclamation mark stay, because they carry tone.

libass renders no colour emoji, so put an emoji in an overlay rather than ship a monochrome box.
