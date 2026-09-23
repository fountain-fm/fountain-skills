---
name: trims
description: Remove dead air and filler from a clip, after the user asks for it and sees what would go.
---

## Overview

A clip is often longer than its content needs.
This module finds the pauses and the filler, and says how much time removing them would save.
It cuts them when the user agrees.
It removes time, so every module after it works on a shorter timeline.
Module **captions** takes the revised word list of this module, so the words always match the picture.

## Input

- The word timings of the clip, and its duration.
- `clip-landscape-master.mp4` from module **media**, so that a cut can fall in real silence.

## Output

- A removal report, with the length and the words of each cut.
- The spans to keep, and the word timings rebased onto the shorter timeline.
- The trimmed master, joined from the kept spans.

## Requirements

- ffmpeg and ffprobe.
- Python 3.11 or later.

## Process

1. Survey the clip first, and never cut at this step:

   ```bash
   scripts/plan-trims.py --words words.json --duration 50.48 --media clip-landscape-master.mp4
   ```

2. Tell the user what the survey found, in one line, and stop there.
   Give the seconds and the share of the clip, for example "9.4s of pauses and 22 filler words, 19%".
3. Plan the cut only after the user asks for it:

   ```bash
   scripts/plan-trims.py --words words.json --duration 50.48 \
     --media clip-landscape-master.mp4 --apply --out trim-report.json
   ```

4. Read every warning, and take each held-back removal to the user on its own.
5. Render each kept span of the plan, all with the same settings, then join them:

   ```bash
   # Re-encode each span, because a stream copy would move the cut to the nearest keyframe.
   ffmpeg -hide_banner -y -i clip-landscape-master.mp4 -ss "$KEEP_START" -to "$KEEP_END" \
     -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k seg-00.mp4
   
   # The concat demuxer reads one "file ..." line for each span, in play order.
   printf "file '%s'\n" seg-*.mp4 > segments.txt
   
   # -c copy is safe here, because every span was just encoded the same way.
   ffmpeg -hide_banner -y -f concat -safe 0 -i segments.txt -c copy clip-landscape-trimmed.mp4
   ```

6. Give the rebased word list to module **captions**, and the trimmed master to every module after this one.
7. Listen to each join, and confirm that no cut clicks and no sentence lost its meaning.

## Additional notes

You MUST NOT trim unless the user asks.
Every other module changes how the clip looks.
This module changes what the speaker said.
A crop that the user did not want is a disagreement about taste.
A cut that the user did not want is a misquotation.

By default, module **captions** removes filler from the text of a caption.
That is safe, because the word is still in the audio.
This module removes the word itself, so the word is gone from the audio too.
That difference is the full reason why the two modules behave differently.

You MUST NOT join two spans so that the speaker appears to say something they did not.
For that reason, a removal is held back when it takes speech with it and is longer than the single-cut limit.
Take each held-back removal to the user on its own, with the words that would go.

By default, only sounds that are not words are removed.
"Like", "you know", and "I mean" are speech as often as they are filler.
To remove them, name them yourself.
A repeated word can give emphasis or contrast, so a repeat stays unless you ask to remove it.
An emphasised word is never treated as filler.

The single-cut limit does not apply to a pause, because silence has no words and cannot create a false quotation.
Removing a pause still changes the performance, so the report names each long pause that a cut removes.
Check that the pause was not a beat before a punchline.

Give the script the media, because a cut on a word boundary clicks.
The script measures the real silence and moves each cut into it.

When a quarter of a clip is removed, the clip stops being a fair excerpt, and the report says so.
