#!/usr/bin/env python3
"""Read the colours of a show out of its artwork, and give each one a caption role.

Takes the image file of the show's `info.image`, which the agent downloads. This
script never calls the API.

Artwork colours are chosen to work on a square cover, not over moving video, so
a colour is never taken as it is found: the outline has to be dark, the text has
to be light, and the accent has to separate from both or it is repaired until it
does. What cannot be repaired is left to the preset and reported.

Writes a palette report, and a kit file that module captions reads with
--brand-kit.
"""

import argparse
import colorsys
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# A caption is read at arm's length over moving pictures, so these are stricter
# than a cover needs: the accent must carry against the outline it sits on, and
# still separate from the words around it.
ACCENT_ON_OUTLINE = 4.5  # the accent has to read where the body text reads
ACCENT_FROM_TEXT = 2.0  # and has to look like a different colour from the body text
ACCENT_MIN_CHROMA = 0.15  # below this the artwork has no accent, only greys and browns
TEXT_MIN_LUMINANCE = 0.70  # a body text colour the artwork supplies must be this light
TEXT_MAX_CHROMA = 0.35  # and this close to neutral, or it is a colour and not a paper
TEXT_MIN_CHROMA = 0.04  # and carry some tint, because a grey is only a dimmer white
OUTLINE_MAX_LUMINANCE = 0.25  # an outline this dark carries any text that sits on it
BOX_ALPHA = "E6"  # a box is nearly solid, because a translucent one reads as a smudge


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def channels(hex_color):
    return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))


def to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def luminance(hex_color):
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in channels(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def chroma(hex_color):
    """How much colour a swatch carries, which HLS saturation overstates for a pale one."""
    values = channels(hex_color)
    return (max(values) - min(values)) / 255


def quantise(magick, artwork, count):
    """The dominant colours of the artwork, most used first, with the share of each."""
    proc = subprocess.run(
        [
            magick,
            str(artwork),
            "-resize",
            "200x200^",
            "-colors",
            str(count),
            "-depth",
            "8",
            "-format",
            "%c",
            "histogram:info:",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"could not read {artwork}\n{proc.stderr.strip()}")
    entries = []
    for line in proc.stdout.splitlines():
        match = re.search(r"^\s*(\d+):.*?(#[0-9A-Fa-f]{6})", line)
        if match:
            entries.append((int(match.group(1)), match.group(2).upper()))
    if not entries:
        fail(f"no colours came back from {artwork}")
    total = sum(n for n, _ in entries)
    entries.sort(reverse=True)
    return [
        {
            "hex": hex_color,
            "share": round(n / total, 4),
            "luminance": round(luminance(hex_color), 3),
            "chroma": round(chroma(hex_color), 3),
        }
        for n, hex_color in entries
    ]


def repair_accent(accent, outline, text):
    """Walk a cover colour to a caption colour, keeping its hue.

    Lightness is the only thing moved, because the hue is what makes it the
    show's colour. Returns (hex, moved) or (None, False) when no lightness of
    this hue reads against the outline and still separates from the text.
    """
    r, g, b = (c / 255 for c in channels(accent))
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    candidates = [lightness] + [lightness + step / 100 for step in range(2, 70, 2)]
    candidates += [lightness - step / 100 for step in range(2, 40, 2)]
    for candidate in candidates:
        if not 0.05 <= candidate <= 0.95:
            continue
        trial = to_hex([c * 255 for c in colorsys.hls_to_rgb(hue, candidate, saturation)])
        if contrast(trial, outline) >= ACCENT_ON_OUTLINE and contrast(trial, text) >= ACCENT_FROM_TEXT:
            return trial, trial != accent
    return None, False


def assign_roles(palette):
    notes = []

    darkest = min(palette, key=lambda c: c["luminance"])
    if darkest["luminance"] <= OUTLINE_MAX_LUMINANCE:
        outline = {"hex": darkest["hex"], "from": "artwork", "share": darkest["share"]}
    else:
        outline = {"hex": "#000000", "from": "default"}
        notes.append("no colour in the artwork is dark enough to outline text, so the outline is black")

    papers = [
        c for c in palette if c["luminance"] >= TEXT_MIN_LUMINANCE and TEXT_MIN_CHROMA <= c["chroma"] <= TEXT_MAX_CHROMA
    ]
    if papers:
        lightest = max(papers, key=lambda c: c["luminance"])
        primary = {"hex": lightest["hex"], "from": "artwork", "share": lightest["share"]}
    else:
        primary = {"hex": "#FFFFFF", "from": "default"}
        notes.append("the artwork carries no light tint, so the words are white")

    used = {outline["hex"], primary["hex"]}
    accents = [c for c in palette if c["hex"] not in used and c["chroma"] >= ACCENT_MIN_CHROMA]
    highlight = None
    if not accents:
        notes.append(
            "the artwork carries no accent - every colour is near neutral - so the highlight stays "
            "whatever the preset uses"
        )
    else:
        for candidate in sorted(accents, key=lambda c: (-c["chroma"], -c["share"])):
            repaired, moved = repair_accent(candidate["hex"], outline["hex"], primary["hex"])
            if repaired:
                highlight = {
                    "hex": repaired,
                    "from": "artwork, lightened to read over video" if moved else "artwork",
                    "artworkHex": candidate["hex"],
                    "share": candidate["share"],
                }
                break
        if highlight is None:
            notes.append(
                "no accent in the artwork reads against the outline and still separates from the "
                "words, at any lightness, so the highlight stays whatever the preset uses"
            )

    roles = {
        "outline": outline,
        "primary": primary,
        "box": {"hex": outline["hex"] + BOX_ALPHA, "from": outline["from"]},
    }
    if highlight:
        roles["highlight"] = highlight
    return roles, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--artwork", required=True, help="The show's artwork file, downloaded from info.image.")
    parser.add_argument("--out", help="Write the palette report here.")
    parser.add_argument("--emit-kit", help="Write a kit file that module captions reads with --brand-kit.")
    parser.add_argument("--colors", type=int, default=8, help="How many colours to quantise the artwork to.")
    parser.add_argument("--magick", default=shutil.which("magick") or "magick")
    args = parser.parse_args()

    artwork = Path(args.artwork)
    if not artwork.is_file():
        fail(f"no such artwork file: {artwork}")

    palette = quantise(args.magick, artwork, args.colors)
    roles, notes = assign_roles(palette)

    colors = {"primary": roles["primary"]["hex"], "outline": roles["outline"]["hex"], "box": roles["box"]["hex"]}
    if "highlight" in roles:
        colors["highlight"] = roles["highlight"]["hex"]

    report = {
        "artwork": str(artwork),
        "palette": palette,
        "roles": roles,
        "notes": notes,
        "captionOverrides": {"colors": colors},
    }
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    if args.emit_kit:
        Path(args.emit_kit).write_text(json.dumps({"captionOverrides": report["captionOverrides"]}, indent=2) + "\n")

    print(f"{artwork.name}: {len(palette)} colours")
    for role, value in roles.items():
        print(f"  {role:10} {value['hex']:9} {value['from']}")
    for note in notes:
        print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
