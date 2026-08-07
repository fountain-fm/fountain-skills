---
name: fountain-clip-producer
description: Render a clip post into a finished, platform-ready video with framing, captions, and overlays.
---

## Overview

This skill turns the clip that a post carries into a video file.
It decides nothing about the moment or the span, because the caller settles those before it runs.
Module **media** cuts the landscape master, and every module after it works from that one file.
The rest shape the picture, put the words and the layers on it, and gate the delivery on one report.

## Input

- The `SocialPostMediaSource` of a `SocialPost`, which names the file and the span.
- The `TranscriptWord` list of that span, which the `fountain` source of the transcript carries.
  Module **shots** wants the speaker of each word too, which `TranscriptWord` does not define.
- A delivery tier, which the words of the request imply.
- Or a queue run: module **queue** reads the drafts that wait for media, and derives the inputs above.

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
- Python 3.11 or later.
- OpenCV 4.8 or later, importable from that same Python, for the face detection of module **framing**.
  Its model, and the fonts that the presets name, ship in `assets`, so no machine installs either.
- ffmpeg and ffprobe, built with libass, drawtext, and fontconfig, or no caption can be burned.
  A stock build often carries none of them, and on macOS the Homebrew `ffmpeg-full` formula is the one that does.
- ImageMagick, to measure the width of caption text.
- yt-dlp, for a source that ffmpeg cannot seek directly.

## Process

1. Load skill **fountain-api**, and read the delivery tier from the request.
   Do the least work that the tier asks for.
   Generate the `fountain` transcript with the Content API when the episode carries only `rss`, then wait for it.
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
9. Run module **qa** as the blocking gate, and deliver nothing until it reports a pass.
10. Attach the video to the post with the Uploads API and the Social API, when the user asks for that.

## Additional notes

There are three delivery tiers, each adding to the one before, and the request implies which one.
The user names the work they want, not the tier, so read it from their words:

- A rough cut is the landscape master alone, with no crop, no captions and no gate.
  Read it from words about checking a span rather than making a clip.
- A clean final is publishable, and a portrait export carries captions, because it is watched muted.
  Read it from "produce this clip", when the request names neither captions nor packaging.
- A publish final adds the overlays and the packaging, and the request names one of them.

Ask when the words fit none of the three, and you MUST NOT raise the tier on your own: polish is requested work.
Captions on a portrait export are not a raise, and a square or a landscape export still waits to be asked.

A clip needs the `fountain` transcript of its episode, and never the `rss` one alone.
The `rss` transcript is timed against the feed and its different advertisement cut, so its clock can sit
minutes away from this file: a span measured on it looks right on paper and holds the wrong words.

Generating one is metered and yours to start without asking: say the cost as soon as the job is queued.
Poll until it completes, and stop when it fails or the episode is early-access.

Always cut from the tallest rendition: a 9:16 crop keeps the whole height and about a third of the width,
so that height is the real resolution of the clip, and module **qa** fails a big upscale.

When a rendered span reads wrong, report it rather than move it here - and a letterbox is requested work too.

To change a clip this skill already made, read the manifest and the QA report first, reuse what is still
correct, and write each new output under a new name.
Touch only the output of the module that changes, and a caption change MUST NOT force a new crop.

A post does not have to be approved before this skill runs, and rendering one approves nothing: you MUST
NOT approve, schedule, or publish a post, because only the user decides that.
The auto-render setting decides which drafts a queue run picks up - module **queue** defines it.

Never put an API key, a token, or a cookie into a command, a manifest, or a report.

The purpose of this skill is a good clip, and not a full set of completed steps.
Readability, framing, and sync matter more than procedure.
