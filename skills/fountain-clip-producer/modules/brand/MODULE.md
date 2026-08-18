---
name: brand
description: Hold the colours, fonts, and assets of a show, so that every clip for it looks the same.
---

## Overview

A brand kit is what makes the clips of a show look like that show every time.
The user does not describe the style again in each session.
The kit sits between a caption preset and the per-clip overrides.
It carries the colours of the show, its fonts, its text case, and the location of its logo.
The values live in the preferences, because only the preferences survive a session.

## Input

- The show of the clip.
- Optional: one or two finished clips from the user, to copy a look that they already make elsewhere.

## Output

- A brand kit, recorded in the preferences.
- A kit file for this session, which module **captions** and module **overlays** read with `--brand-kit`.
- The location of the font files and the image assets of the show.

## Requirements

- Fountain API.

## Process

1. Load the preferences with the Project API, and read the kit of the show.
   The Brand section holds all of it: the caption style, and the assets around it.
2. Produce the clip without a kit when the show has none, because a preset and an override work alone.
3. Write the kit values into a kit file for this session, and give that file to the two scripts that read it.
   Build the file again in a later session, because the preferences are the store and the file is not.
4. Apply the kit as the default, and let a per-clip override from the user win over it.
5. Build a kit from a reference clip when the user asks to match a look that they already make:
   1. Ask for one or two finished clips, or for a full-resolution screenshot of a caption on screen.
   2. Pull stills at the caption moments, and read the style off them.
      Read the character of the font, the case, the colours from the real pixels, the border, the position,
      the number of words on screen, and the animation.
   3. Draft the kit values, and render a style proof on real footage of the show.
   4. Show the proof beside the reference, and repeat until the user confirms the match.
   5. Ask for the font files when the show uses a licensed font.
6. Record the confirmed kit with the Project API in the same turn.

## Additional notes

A kit counts as established only after the user approves a proof render.
You MUST NOT read one screenshot and then produce a batch of clips against it.

The colours and the font are usually right on the first pass.
The size and the margins usually need one correction, because a reference screenshot rarely states its resolution.

Any change to a kit calls for a new style proof before the next full render.

The preferences hold text, so they hold the style values, the names of the fonts, and where each asset is.
They cannot hold the font file or the logo file itself.
Record a URL when the show has one, because a URL survives a new machine and a session that runs elsewhere.
Record a path when it does not, and know that the path is true for that one machine.
Ask again and record the new location when a recorded one no longer resolves, and never fall through to a
system font or a silently missing layer.

Record the values themselves in the preferences, and not a description of them.
