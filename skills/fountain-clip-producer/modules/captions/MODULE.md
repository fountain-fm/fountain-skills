---
name: captions
description: Build styled, word-timed captions from a style spec and burn them into the clip.
---

## Overview

Captions are requested work, and this module captions only the export that the request names.
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
   Stop and report to the user when the request asks for captions and no word timings arrive.
2. Clean the text before you set any timing, under the faithful-clean rules below.
3. Compile the spec and the words into the ASS file:

   ```bash
   scripts/build-captions.py --style word-pop --words words.json \
     --override colors.highlight=#FFD400 --override font.size=84 \
     --out captions.ass --emit-lines caption-lines.json --emit-spec resolved-style.json
   ```

4. Measure the width of each line that the script emits, and fill in the fit report:

   ```bash
   # label renders the text at the real font and size, and "%w" prints the width it took.
   magick -background none -font "/path/to/Font-Bold.otf" -pointsize 72 \
     label:"the line to measure" -format "%w" info:
   ```

   A width over the safe width is an overflow, and you MUST fix it before the render.

5. Run module **qa** for a style proof whenever the style is new or changed.
6. Burn the captions in:

   ```bash
   # The subtitles filter hands the file to libass, which reads the styles and the animation from it.
   # -c:a copy leaves the audio untouched, because this pass changes the picture alone.
   ffmpeg -hide_banner -y -i clip-vertical.mp4 \
     -vf "subtitles=captions.ass" \
     -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart \
     clip-vertical-captioned.mp4
   ```

7. Check the render: no new black interval, captions that change through the clip, and no caption that lags the audio.

## Additional notes

The spec layers from the lowest priority to the highest: defaults, preset, brand kit, per-clip override.
A misspelled override path is a hard error and never a silent no-op.
The script validates the resolved spec, and unreadable contrast, flicker, and impossible overshoot are hard
failures. `--check` runs that validation alone, with no words.

The presets in `assets` are starting points and not cages.
`clean-editorial` and `bold-social` are static, `tiktok-style` and `karaoke-fill` sweep across each word,
and `current-word` lights the spoken word alone, which is the common talking-head look.
`word-pop`, `bounce-in`, `glow-bounce`, and `typewriter` animate one word at a time.
`impact-loud` and `hormozi` are the loud uppercase styles, and `hormozi` needs 3 to 5 emphasised words.
`pill-karaoke` puts the active word on a coloured pill, `speaker-duo` gives each speaker a colour and a label,
and `minimal-light` is small text on a soft box.

These are the text rules, and the default mode is faithful-clean:

- Remove filler and a repeated false start, when that does not change the meaning.
  This is safe by default because the audio still carries the word, which is why module **trims** is not.
- Keep a repetition that carries emphasis, rhythm, or contrast.
- Keep the jokes, the strong language, and the quoted words, and never turn a sentence into a different claim.
- Drop a dangling fragment when the clip ends before the speaker finishes.

Correct the errors of the machine transcript, because they render exactly as they arrive.
Check the names of people and places, the numbers and the currency, and the names of companies and guests.
Spell a name the way the show notes spell it, because that is what the audience searches for.

Keep `font.case` at `verbatim` when the transcript carries real capitals, and use `upper` for a loud style.
`sentence` lowercases every word first, so it destroys "I", an acronym, and every name,
and it then capitalises whatever word a group happens to start on, which is rarely a sentence.
Reach for it only when the transcript arrives with no capitals at all.

A caption group breaks on a speaker change, a sentence end, a silence, or the word cap, and never inside a clause.
A social caption carries no full stop, though a question mark and an exclamation mark stay, because they carry tone.

A vertical clip holds one line by default, and an unintended wrap is a blocking failure: shorten the phrase.

libass renders no colour emoji, so an emoji style cannot go through the ASS path.
Put the emoji in an overlay instead of shipping a monochrome box.
