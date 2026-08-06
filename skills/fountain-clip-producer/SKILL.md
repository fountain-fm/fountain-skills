---
name: fountain-clip-producer
description: Render an approved clip post into a finished, platform-ready video with framing, captions, and overlays.
---

## Overview

This skill turns an approved post into a video file.
It decides nothing about the moment or the span, because the caller settles those before it runs.
Module **media** cuts the landscape master, and every module after it works from that one file.
The rest shape the picture, put the words and the layers on it, and gate the delivery on one report.

## Input

- The `SocialPostMediaSource` of an approved `SocialPost`, which names the file and the span.
- The `TranscriptWord` list of that span, which the `fountain` source of the transcript carries.
  Module **shots** also needs the speaker of each word, for a shot that holds two people.
- A delivery tier, which the words of the request imply.

Optional:

- A target shape, which is vertical, square, or landscape.
- The name of a caption preset, or the text of an overlay.

## Output

- A landscape master, and one export for each shape that the request asks for.
- A `SocialPostUpload` on `content.uploads` of the post, when the user asks to attach the video.
- A clip manifest, a crop plan, a caption plan, an overlay plan, and a QA report.
- A removal report, when module **trims** cut the clip.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- Skill **fountain-api**.
- Python 3.11 or later, with OpenCV 4.8 or later for the face detection of module **framing**.
- ffmpeg and ffprobe, from the Homebrew `ffmpeg-full` formula.
  The default `ffmpeg` formula carries no libass, no drawtext, and no fontconfig, so it cannot burn a caption.
- ImageMagick, to measure the width of caption text.
  The fonts that the presets name, and the face detection model, ship in `assets`, so no machine installs one.
- yt-dlp, for a source that ffmpeg cannot seek directly.

## Process

1. Load skill **fountain-api**, and read the delivery tier from the request.
   Do the least work that the tier asks for.
   Confirm that the episode carries a `fountain` transcript, and stop when it carries only `rss`.
2. Run module **preflight** to check the machine before the first render.
3. Run module **media** to cut the landscape master from `media`, between `ts_start` and `ts_end`.
4. Run module **trims** to survey the pauses and the filler, and report what it found.
   Cut only when the user asks, because the cut moves every time after it.
5. Run module **framing** to crop the master to each shape that the request asks for.
   Run module **shots** with it when one shot holds two people and the crop must follow who speaks.
6. Run module **brand** to load the look of the show, for a clean final or a publish final.
7. Run module **captions** on every portrait export, and on another shape when the request asks for it.
   Run module **fonts** with it.
8. Run module **overlays** when the request asks for a layer.
9. Run module **qa** as the blocking gate.
   Deliver nothing until it reports a pass.
10. Attach the video to the post with the Uploads API and the Social API, when the user asks for that.

## Additional notes

There are three delivery tiers, and each one adds to the tier before it:

- A rough cut is a fast file for review, with no captions and no gate.
- A clean final is publishable, and a portrait export carries captions, because it is watched with the sound off.
  This is the tier for "produce this clip", when the request names neither captions nor packaging.
- A publish final adds the overlays, the packaging, and the full gate.

You MUST NOT raise the tier on your own, because polish is requested work.
Captions on a portrait export are not a raise, and a square or a landscape export still waits to be asked.

A clip needs the `fountain` transcript of its episode, and never the `rss` one alone.
The `rss` transcript is timed against the feed, which carries a different advertisement cut, so its clock
can sit minutes away from the file this skill opens.
A span measured on it looks right on paper and holds the wrong words, and no render finds that out.
Ask the user to generate the transcript, because the Content API meters that work and the spend is theirs.

Always cut from the tallest rendition the source offers.
A vertical crop keeps about a third of the width, so a 720p source delivers a 1080x1920 file that holds
405x720 of real picture, and module **qa** fails it.

The span is settled before this skill runs.
When the start or the end of a rendered clip reads wrong, report that to the user rather than move the span here.

Loudness is requested work: normalise when the user asks, or when the source is clearly quiet.

A letterbox is requested work as well, and black bars are never your decision.

To change a clip that this skill already made, read the manifest and the QA report first.
Reuse the master, the crop plan, and the caption assets that are still correct.
Touch only the output of the module that changes, and write it under a new name.
A caption change MUST NOT force a new crop.

Never put an API key, a token, or a cookie into a command, a manifest, or a report.

The purpose of this skill is a good clip, and not a full set of completed steps.
Readability, framing, and sync matter more than procedure.
