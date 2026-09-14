---
name: words
description: Transcribe the clip master into verified word timings for captions and content checks.
---

## Overview

This module makes the word-level transcript of the rendered clip.
The words come from the clip audio, because the episode transcript has only sentence-level timing.
It preserves punctuation for caption grouping and checks the result against the source transcript.

## Input

- The landscape master from module **media**.
- The source transcript for wording checks.
- The ffmpeg binary and whisper model from module **preflight**.

## Output

- Word timings rebased so that the first word starts at zero.
- A transcript check with each uncertain name, number, or phrase.

## Requirements

- ffmpeg built with whisper.
- A whisper.cpp model file.

## Process

1. Transcribe the master with the binary and model from module **preflight**.
   Use `max_len=1`, and put `model=` last in the filter string.
2. Treat each token as a word unless it has no leading space and the token before it does not end a sentence.
   In that case, join the tokens.
3. Attach a punctuation-only token to the word before it.
   Do not drop punctuation, because module **captions** uses it to close groups and apply case.
4. Rebase the timings to the start of the master.
5. Compare the words with the source transcript.
   Correct a clear transcription error in wording, but keep the timing measured from the clip.
6. Give the verified word list to module **captions** and module **qa**.

## Additional notes

Do not join tokens because their times touch.
Whisper commonly puts one word's start at the end of the word before it.

Flag a name, number, or currency that the audio and source transcript do not settle.
Do not invent a speaker label, because whisper does not identify speakers.
