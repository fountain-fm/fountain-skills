#!/usr/bin/env python3
"""Render every caption preset onto one frame of the clip, tiled into a labelled contact sheet.

The user picks a caption style by looking at it on their own footage, and names
the label back. Each tile is a real libass burn of that preset, so the tile and
the finished clip are drawn by the same renderer.

Reads no model. Takes the word timings the skill made from the clip's audio,
in the shape build-captions.py reads: a list of {word|text, start, end}, or an
object with those under "words".
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MODULES = Path(__file__).resolve().parents[2]
CAPTIONS = MODULES / "captions"
BUILD_CAPTIONS = CAPTIONS / "scripts" / "build-captions.py"
PRESETS_DIR = CAPTIONS / "assets"
FONTS_DIR = MODULES.parent / "assets" / "fonts"
LABEL_FONT = FONTS_DIR / "montserrat-bold.ttf"

MAX_WORD_DUR = 2.0  # past this a whisper timing is debris, and a long tail is not a longer word

SHEET_BACKGROUND = "#101014"  # near-black, so a white caption and a dark one both separate from it
SHEET_FILL = "#FFFFFF"


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd):
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def load_words(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("words", [])
    words = []
    for item in data:
        text = (item.get("word") or item.get("text") or "").strip()
        if not text:
            continue
        try:
            words.append({"text": text, "start": float(item["start"]), "end": float(item["end"])})
        except (KeyError, TypeError, ValueError):
            continue
    if not words:
        fail(f"no usable words in {path}")
    return words


def sample_time(words):
    """A moment inside the longest word of the middle of the clip.

    The middle is past the opening, where a speaker is often still settling.
    The longest word is the one whose animation has finished and whose
    successor has not started, so every tile shows its style at rest rather
    than caught half-scaled mid-pop.
    """
    middle = words[len(words) // 4 : max(len(words) * 3 // 4, len(words) // 4 + 1)]
    word = max(middle, key=lambda w: min(w["end"] - w["start"], MAX_WORD_DUR))
    duration = max(word["end"] - word["start"], 0.05)
    return word["start"] + min(0.45, duration * 0.6)


def ass_path_for_filter(path):
    # The subtitles filter parses its own argument list, so the separators inside
    # a path have to survive it: backslash, colon, and the quote that wraps it.
    escaped = str(path).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")
    return f"'{escaped}'"


def presets(selected):
    found = sorted(p for p in PRESETS_DIR.glob("*.json"))
    if not found:
        fail(f"no caption presets in {PRESETS_DIR}")
    if selected:
        wanted = [s.strip() for s in selected.split(",") if s.strip()]
        by_name = {p.stem: p for p in found}
        missing = [w for w in wanted if w not in by_name]
        if missing:
            fail(f"unknown preset(s): {', '.join(missing)}")
        found = [by_name[w] for w in wanted]
    return found


def first_sentence(text):
    """The opening claim of a preset's description, for the index the agent reads out."""
    return re.split(r"(?<=[.;])\s", text.strip())[0].rstrip(".;") if text else ""


def frame_height(ffprobe, source):
    probe = run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=height",
            "-of",
            "csv=p=0",
            str(source),
        ]
    )
    try:
        return int(probe.stdout.strip().splitlines()[0])
    except (IndexError, ValueError):
        fail(f"could not read the height of {source}\n{probe.stderr.strip()}")


def extract_frame(ffmpeg, source, at, out):
    proc = run([ffmpeg, "-hide_banner", "-y", "-ss", f"{at:.3f}", "-i", str(source), "-frames:v", "1", str(out)])
    if proc.returncode != 0 or not out.exists():
        fail(f"could not take a frame at {at:.2f}s from {source}\n{proc.stderr.strip()}")


def crop_filter(mode, height):
    """Keep the caption band when the whole frame draws the words too small to judge."""
    if mode == "caption":
        # the lower half plus a little, which holds every preset's margin and the speaker's shoulders
        return f"crop=iw:{int(height * 0.55)}:0:{int(height * 0.45)},"
    return ""


def burn(ffmpeg, frame, ass, at, out, crop=""):
    """Draw one preset's caption on the still, at the clip time the still came from.

    setpts moves the still's timestamp to that clip time, so libass draws the
    event that is really on screen then, rather than the one at zero.
    """
    chain = (
        f"setpts=PTS+{at:.3f}/TB,"
        f"subtitles={ass_path_for_filter(ass)}:fontsdir={ass_path_for_filter(FONTS_DIR)},"
        f"{crop}null"
    )
    proc = run(
        [
            ffmpeg,
            "-hide_banner",
            "-y",
            "-loop",
            "1",  # hold the still, so the filter chain has a stream to time
            "-i",
            str(frame),
            "-vf",
            chain,
            "-frames:v",
            "1",
            "-an",
            str(out),
        ]
    )
    return proc.returncode == 0 and out.exists(), proc.stderr.strip()


def montage(magick, tiles, out, columns, tile_height, title):
    cmd = [magick, "montage"]
    for index, (label, image) in enumerate(tiles, start=1):
        cmd += ["-label", f"{index}. {label}", str(image)]
    cmd += [
        "-font",
        str(LABEL_FONT),
        "-pointsize",
        "26",
        "-background",
        SHEET_BACKGROUND,
        "-fill",
        SHEET_FILL,
        "-tile",
        f"{columns}x",
        "-geometry",
        f"x{tile_height}+12+12",
        "-title",
        title,
        "-quality",
        "88",
        str(out),
    ]
    proc = run(cmd)
    if proc.returncode != 0 or not out.exists():
        fail(f"montage failed\n{proc.stderr.strip()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="The export to sample, usually clip-vertical.mp4.")
    parser.add_argument("--words", required=True, help="Word-timings JSON for the clip, as build-captions.py reads.")
    parser.add_argument("--out", required=True, help="Output contact sheet (.jpg).")
    parser.add_argument("--at", type=float, help="Clip time to sample, in seconds. Defaults to a third of the way in.")
    parser.add_argument("--styles", help="Comma-separated preset names. Defaults to every preset.")
    parser.add_argument(
        "--brand-kit",
        help="A kit file from module brand. Every tile is then drawn through the kit, which is how the "
        "candidates for one show are compared.",
    )
    parser.add_argument("--columns", type=int, default=4, help="Tiles per row. Default 4.")
    parser.add_argument("--tile-height", type=int, default=720, help="Tile height in pixels. Default 720.")
    parser.add_argument(
        "--crop",
        choices=("full", "caption"),
        default="full",
        help="full keeps the whole frame; caption keeps the band the words sit in, which draws them larger.",
    )
    parser.add_argument("--work", default="style-sheet-work", help="Directory for the per-preset stills.")
    parser.add_argument("--emit-index", help="Write the preset index (name, description, tile number) as JSON.")
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg")
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe") or "ffprobe")
    parser.add_argument("--magick", default=shutil.which("magick") or "magick")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.exists():
        fail(f"no such export: {source}")
    if not BUILD_CAPTIONS.exists():
        fail(f"build-captions.py is not at {BUILD_CAPTIONS}")

    words = load_words(args.words)
    at = args.at if args.at is not None else sample_time(words)

    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    frame = work / "frame.png"
    extract_frame(args.ffmpeg, source, at, frame)
    crop = crop_filter(args.crop, frame_height(args.ffprobe, source))

    tiles, index, skipped = [], [], []
    for preset in presets(args.styles):
        name = preset.stem
        ass = work / f"{name}.ass"
        build = [sys.executable, str(BUILD_CAPTIONS), "--style", name, "--words", args.words, "--out", str(ass)]
        if args.brand_kit:
            build += ["--brand-kit", args.brand_kit]
        built = run(build)
        if built.returncode != 0:
            skipped.append((name, built.stderr.strip().splitlines()[-1] if built.stderr.strip() else "build failed"))
            continue
        tile = work / f"{name}.png"
        drawn, error = burn(args.ffmpeg, frame, ass, at, tile, crop)
        if not drawn:
            skipped.append((name, error.splitlines()[-1] if error else "burn failed"))
            continue
        tiles.append((name, tile))
        spec = json.loads(preset.read_text())
        index.append(
            {
                "tile": len(tiles),
                "name": name,
                "description": first_sentence(spec.get("description", "")),
                "animation": spec.get("animation", {}).get("type", "none"),
                "font": spec.get("font", {}).get("family"),
            }
        )

    if not tiles:
        for name, why in skipped:
            print(f"  {name}: {why}", file=sys.stderr)
        fail("no preset rendered, so there is nothing to choose from")

    out = Path(args.out)
    title = f"caption styles at {at:.1f}s"
    if args.brand_kit:
        title = f"{title}, in the show's colours"
    montage(args.magick, tiles, out, args.columns, args.tile_height, title)

    if args.emit_index:
        Path(args.emit_index).write_text(json.dumps({"at": at, "styles": index}, indent=2) + "\n")

    print(f"{out}: {len(tiles)} styles on a frame at {at:.2f}s")
    for entry in index:
        print(f"  {entry['tile']}. {entry['name']} - {entry['description']}")
    for name, why in skipped:
        print(f"  skipped {name}: {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
