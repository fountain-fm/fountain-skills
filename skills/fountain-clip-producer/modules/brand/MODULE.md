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

- The show of the clip, and the artwork of its `info.image`.
- Optional: one or two finished clips from the user, to copy a look that they already make elsewhere.

## Output

- A brand kit, recorded in the preferences.
- A palette report, which says where each colour came from and what the artwork could not give.
- A kit file for this session, which module **captions** and module **overlays** read with `--brand-kit`.
- The location of the font files and the image assets of the show.

## Requirements

- Fountain API.
- ImageMagick, to quantise the artwork.
- Python 3.11 or later.
- A web search tool, and a way to read a page, to reach the clips and the profiles that a show
  publishes outside Fountain.

## Process

1. Load the preferences with the Project API, and read the kit of the show.
   The Brand section holds all of it: the caption style, and the assets around it.
2. Derive a kit from the artwork of the show when the Brand section holds none, because a show that has
   never been asked still has a look, and the preset's look is nobody's:
   1. Download the image of `info.image`, and read the colours out of it:

      ```bash
      scripts/derive-palette.py --artwork artwork.jpg --out brand-palette.json --emit-kit kit.json
      ```

   2. Look at the artwork yourself and choose the font, because no script reads a typeface out of a
      picture. Take the bundled family whose character matches the wordmark, and choose three presets
      that suit it. A serif cover suits `broadsheet`, a heavy condensed one `stadium` or `impact-loud`,
      a hand-lettered one `marker`, and a clean geometric one `bold-social` or `wide-block`.
   3. Render those three through the kit with module **style-sheet**, which draws each preset in the
      colours of the show.
   4. Give the user the sheet and ask them to name a tile.
      Name what they can change on it - the size of the captions, their case, their colours and the
      highlight, the outline, where they sit, how many words are on screen, and the font - because a
      reader who does not know the vocabulary cannot ask for a correction.
   5. Tell them which values came from their artwork and which stayed with the preset, which the notes
      of the report say.
3. Write the kit values into a kit file for this session, and give that file to the two scripts that read it.
   Build the file again in a later session, because the preferences are the store and the file is not.
4. Apply the kit as the default, and let a per-clip override from the user win over it.
5. Build a kit from a reference clip when the user asks to match a look that they already make:
   1. Ask for one or two finished clips, or for a full-resolution screenshot of a caption on screen.
      Read what the show already has when the user gives none, and stop at the first that answers:

      - A clip the show posted on one of its own channels, which the Accounts section names.
        Prefer this one: it is the only source that shows the show's captions on the show's footage.
      - The website of the show and its social profiles.

      Say which source each value came from, because a colour read from a profile is a guess at a
      caption that the show has never made.

   2. Pull stills at the caption moments, and read the style off them.
      Read the character of the font, the case, the colours from the real pixels, the border, the position,
      the number of words on screen, and the animation.
   3. Draft the kit values, and render a style proof on real footage of the show.
   4. Show the proof beside the reference, and repeat until the user confirms the match.
   5. Ask for the font files when the show uses a licensed font.
6. Record the confirmed kit with the Project API in the same turn.

## Additional notes

An artwork colour is chosen to work on a square cover, and a caption is read at arm's length over
moving pictures, so the script never takes a colour as it finds it.
The darkest colour becomes the outline, the lightest tint becomes the words, and the accent goes on the
highlight rather than on the words themselves.
The accent is then lightened, keeping its hue, until it reads against the outline and still looks like a
different colour from the words.
An accent that reaches neither at any lightness is left to the preset, and so is the highlight of a
cover that carries no colour at all.
Say so when that happens, rather than let the user believe the whole look came from their artwork.

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
