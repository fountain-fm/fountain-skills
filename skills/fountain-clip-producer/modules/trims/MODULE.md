---
name: trims
description: Remove dead air and filler from a clip, after the user asks for it and sees what would go.
---

## Overview

A clip is often shorter than its span deserves.
This module finds the pauses and the filler, says what removing them would save, and cuts them when the
user agrees.
It removes time, so every module after it works on a shorter clock.
Module **captions** takes its revised word list, so the words and the picture never disagree.

## Input

- The `TranscriptWord` list of the span, and the duration of the clip.
- `clip-landscape-master.mp4` from module **media**, so a cut can land in real silence.

## Output

- A removal report, with the length and the words of each cut.
- The spans to keep, and the `TranscriptWord` list rebased onto the shorter clock.
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
7. Listen to each join, and confirm that no cut clicks and no sentence lost its sense.

## Additional notes

You MUST NOT trim unless the user asks.
Every other module changes how the clip looks, and this one changes what the speaker said.
A crop the user did not want is a disagreement about taste, and a cut they did not want is a misquotation.

Module **captions** removes filler from the text of a caption by default, and that is safe because the
audio still carries the word.
This module removes the word itself, and nothing carries it afterwards.
That difference is the whole reason the two behave differently.

You MUST NOT join two spans so that the speaker appears to say something they did not.
A removal that takes speech with it, and runs longer than the single-cut limit, is held back for that reason.
Take each one to the user on its own, with the words that would go.

Only sounds that are not words are removed by default.
"Like", "you know", and "I mean" are speech as often as they are filler, so name them yourself to remove them.
A repeated word can carry emphasis or contrast, so a repeat stays unless you ask for it.
An emphasised word is never treated as filler.

A pause is exempt from the single-cut limit, because silence holds no words and cannot invent a quotation.
It still changes the performance, so the report names each long pause it closes.
Check that the pause was not a beat before a punchline.

Give the media, because a cut on a word boundary clicks.
The script measures the real silence and moves each cut into it.

Removing a quarter of a clip is the point at which it stops being a fair excerpt, and the report says so.
