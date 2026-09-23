---
name: captions
description: Build styled, word-timed captions from a style spec and burn them into the clip.
---

## Overview

People watch a portrait clip with the sound off, so it has captions by default.
Caption any other shape when the request asks for it.
A style spec sets the look.
`build-captions.py` compiles that spec and the word timings into an ASS file.
ffmpeg then burns the ASS file in with one filter pass.
Never write animated ASS events by hand.
The script exists to get the per-word timing arithmetic right.

## Input

- The word timings of the clip, made from its own audio and rebased so the first word starts at zero.
- The export to caption, usually `clip-vertical.mp4`, and its shape.
- Optional: a preset name, a brand kit from module **brand**, and per-clip overrides.

## Output

- `captions.ass`, and the captioned export.
- A caption plan, with the resolved spec, the overrides, and the renderer.
- A caption fit report, which module **qa** requires.

## Requirements

- ffmpeg built with libass.
  On macOS that is the Homebrew `ffmpeg-full` formula, and not the default one.
- ImageMagick, to measure text width.
- fontconfig, to resolve a font the way libass does.
- Python 3.11 or later.

## Process

1. Take the word timings that the skill made from the clip's audio with whisper.
   The sentence-level segments of the episode transcript are too coarse for a caption.
   Use the rebased list of module **trims** instead, when that module cut the clip.
   Stop and report to the user when a portrait export has no word timings.
   Do not deliver it without captions.
   Make the timings again when the script refuses the list, and tell the user if it refuses them twice.
2. Clean the text before you set any timing.
   Use the faithful-clean rules below.
3. Compile the spec and the words into the ASS file:

   ```bash
   scripts/build-captions.py --style word-pop --shape portrait --words words.json \
     --override colors.highlight=#FFD400 --override font.size=84 \
     --out captions.ass --emit-lines caption-lines.json --emit-spec resolved-style.json
   ```

4. Measure each line that the script emits, and write the results in the fit report.
   This step confirms the packing of the script, and is not a search for new faults:

   ```bash
   # label renders the text at the real font and size, and "%w" prints the width it took.
   magick -background none -font assets/fonts/montserrat-bold.ttf -pointsize 72 \
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

7. Check that the render has no new black interval, and no caption that lags the audio.
   Check that the captions change through the clip.

## Additional notes

The spec applies its layers from the lowest priority to the highest: defaults, shape, preset, brand kit,
per-clip override.

`--shape` MUST name the shape of the export that you caption.
The shape sets the coordinate space that libass draws in.
A portrait spec burned on a landscape export stretches every letter.
The shape also sets where the words sit, so nobody needs to set a margin.
A portrait post plays inside the app's own interface, and the words stay clear of that interface.
The post caption, the handle and the audio line cover the bottom of the frame.
The reaction buttons cover the right edge.
The margins of the portrait shape clear the interface of the worst of the four apps.
They also keep the face clear, because a 9:16 crop of one speaker fills the middle of the frame with that
face.
A landscape clip has no such interface, so its words sit along the bottom.
Move them with an override only for a clip that needs it, such as a shot where the speaker sits low.
The script warns when an override puts the words back under the interface.
A misspelled override path is a hard error.
`--check` rejects unreadable contrast or flicker on its own.

Use `bold-social` when neither the request nor the brand kit names a preset.
It is readable on a phone at arm's length, and it has no animation that can go wrong.
When the user has not chosen a style, send them to the clip styling page, and not to this list.
The descriptions in `assets` say what a style is for, but only the page shows the style.

Each preset has one job, and no two presets differ by only one setting:

- Nothing moves: `bold-social` is readable anywhere, `broadsheet` looks serious in a display serif,
  `wide-block` sits on a solid block and stays readable on the busiest footage, `minimal-light` draws
  little attention.
- One word at a time: `word-pop` scales in, `bounce-in` rises, `impact-loud` is loud, `marker` looks
  hand-written, and `glow-bounce` glows.
- The phrase stays and the spoken word is marked: by colour in `current-word`, by a pill in
  `pill-karaoke`, by a halo in `glow-word`, by filling in `karaoke-fill`, and across the line in `stadium`.
- `typewriter` reveals a letter at a time, and `hormozi` needs 3 to 5 words marked `"emphasize": true`.

The script colours each speaker differently and labels them, through `colors.speakers` and
`grouping.speakerLabels`.
No preset uses either, because nothing gives this skill the speaker of a word.
Set them as overrides when something supplies the speaker.

These are the text rules, and the default mode is faithful-clean.
The script applies the mechanical rules.
These rules are safe because the audio still carries every word.
The script drops "um" and "uh", strips commas, and joins a number range on an en dash.
It never lets a clip end on a dangling conjunction.
It applies the casing map (ai -> AI, wifi -> Wi-Fi).
The brand kit can extend the casing map, and an ambiguous token goes into the map as a phrase
("the fed" -> "the Fed").
Sentence case capitalizes only at sentence starts, and keeps "I" and existing capitals.
You make the judgment calls:

- Remove a false start when that does not change the meaning.
  A false start is the abandoned fragment before a restart.
- The script names each filler candidate (like, right, you know, kind of, sort of, I mean), but removes none.
  Delete a filler only when the sentence keeps its claim.
  Keep the verb, the comparison, the quotative "it's like", a fixed "like that", and anything before a
  quote or a number.
  Always delete a trailing tag "right".
- Keep a repetition that carries emphasis, and never turn a sentence into a different claim.
- Correct any remaining name, number, or currency the way the show notes spell it.

Keep `font.case` at `verbatim` when the transcript carries real capitals, and use `upper` for a loud style.
`sentence` lowercases every word first, so it destroys "I" and every name.

Whisper invents timings, so the script refuses four kinds: a word that starts before the word before it,
a word that still runs when the next one starts, a word longer than two seconds, and a run of words
packed tighter than anybody speaks.
A list that you build by hand MUST refuse them too.
The long word ruins a clip because every later word is pushed past its end.
Whisper leaves a packed run when it writes words over speech that it did not hear.
Each word of the run is short, in order and not long, so only the rate shows the fault.

Give the script a word list that still has its punctuation.
The script reads the text of each word to find a sentence end.
A sentence end closes a group, and sentence case capitalises the word after it.
The script drops a full stop and a trailing comma itself, after it has used them.
When the list arrives with no punctuation, the script puts two sentences into one caption.
The capital is then the only clue that the reader gets.

A caption group breaks on a speaker change, a sentence end, a silence, or the safe width, and never inside a clause.
The script measures each word in the font and the case that it will render in.
It packs words into a group until the next word does not fit.
Thus `font.size` is the control, and `grouping.maxWords` is only a ceiling.
A one-word style is not packed at all.
The script resolves the font the way libass does: the bundled directory first, and fontconfig after.
Thus the file that it measures is the file that libass draws.
It refuses only when neither source finds the font.
Every preset names a font, so the clip has a font when you do not choose one.
Pass `--font-file` only for a family that this skill does not bundle.
Never pass it for a file that you found on the disk.
To change the font, record `font.family` under Brand.
That is enough for a family that this skill bundles.
A family that this skill does not bundle needs its file recorded beside it.
That record is true only for the machine that holds the file.
If you name such a family alone, the render uses the substitute, and not the font.
A caption packed by the word cap alone wraps wherever it does not fit.
The fit report then confirms a layout that the render never had.
Tell the user what the build says about the font.
The build can say that a font is not installed, and that the clip is drawn in the substitute.
Or it can say that it drew the font from a file that this skill does not bundle.
A social caption drops the full stop and the comma at the end of a group.
A comma inside a group stays.
A question mark and an exclamation mark stay, because they show tone.

libass renders no colour emoji.
Put an emoji in an overlay, and do not deliver a monochrome box.
