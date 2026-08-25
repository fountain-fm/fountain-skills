#!/usr/bin/env python3
"""Check that the two edges of a clip span land in silence, before the cut is made.

Reads the `media`, `ts_start` and `ts_end` fields of a `SocialPostMediaSource`.

A transcript segment edge is not the end of the speech: the stored `end` runs early, and two
segments that abut leave no gap to reach into. Either way the span opens or closes inside a word.
This measures the real audio around each edge and names the silence to move into.

It probes the source, and never the cut master, because a master cut at `ts_end` holds no audio
past that point and cannot show that the speech continues.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# How far to reach into a silence, and never more than half of it, so two clips cut from
# neighbouring spans can never overlap. This mirrors the reach of skill fountain-clip-finder.
BREATH_SECONDS = 0.25

SILENCE_START = re.compile(r"silence_start:\s*(-?[0-9.]+)")
SILENCE_END = re.compile(r"silence_end:\s*(-?[0-9.]+)")


def run(cmd):
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def extract_window(media, window_start, window_length, wav_path):
    """Decode one window of the source to mono 16k PCM, which is all silencedetect needs."""
    proc = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            # -ss before -i seeks the source one time, so only the window is fetched.
            "-ss",
            f"{window_start:.3f}",
            "-i",
            str(media),
            # -t takes the window alone, and never the whole episode.
            "-t",
            f"{window_length:.3f}",
            # -vn drops the picture, which says nothing about where the speech stops.
            "-vn",
            # Plain mono PCM at 16k is all that silencedetect needs to measure a level.
            "-c:a",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(wav_path),
        ]
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "unknown error"
        raise RuntimeError(f"ffmpeg could not read {media}: {detail}")


def find_silences(wav_path, noise_db, min_silence, window_start, window_end):
    """Return the silences of one window, in the clock of the source."""
    proc = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(wav_path),
            # silencedetect reports every run that stays under the threshold for long enough.
            "-af",
            f"silencedetect=n={noise_db}dB:d={min_silence}",
            # The measurement is in the log, so the decoded audio goes nowhere.
            "-f",
            "null",
            "-",
        ]
    )
    text = f"{proc.stdout}\n{proc.stderr}"

    silences = []
    pending = None
    for line in text.splitlines():
        start = SILENCE_START.search(line)
        if start:
            pending = window_start + max(float(start.group(1)), 0.0)
            continue
        end = SILENCE_END.search(line)
        if end and pending is not None:
            silences.append({"start": round(pending, 3), "end": round(window_start + float(end.group(1)), 3)})
            pending = None
    # A silence that runs past the window is closed at the rim, and reported no further than measured.
    if pending is not None:
        silences.append({"start": round(pending, 3), "end": round(window_end, 3)})
    return silences


def reach_into(silence, kind):
    """Return a time inside a silence: just past the speech for an out point, just before it for an in point."""
    span = silence["end"] - silence["start"]
    breath = min(BREATH_SECONDS, span / 2)
    return round(silence["start"] + breath if kind == "out" else silence["end"] - breath, 3)


def inspect_edge(media, edge, kind, probe, noise_db, min_silence):
    """Measure one edge, and name the silence on each side of it."""
    window_start = max(edge - probe, 0.0)
    window_end = edge + probe
    with tempfile.TemporaryDirectory() as work:
        wav_path = Path(work) / "edge.wav"
        extract_window(media, window_start, window_end - window_start, wav_path)
        silences = find_silences(wav_path, noise_db, min_silence, window_start, window_end)

    holding = next((s for s in silences if s["start"] <= edge <= s["end"]), None)
    report = {
        "edge": kind,
        "time": round(edge, 3),
        "status": "pass" if holding else "fail",
        "window": [round(window_start, 3), round(window_end, 3)],
        "silences": silences,
    }
    if holding:
        report["detail"] = "the edge is already inside silence"
        report["silence"] = holding
        return report

    before = [s for s in silences if s["end"] < edge]
    after = [s for s in silences if s["start"] > edge]
    speech_start = before[-1]["end"] if before else None
    speech_end = after[0]["start"] if after else None
    report["speechRun"] = {"start": speech_start, "end": speech_end}
    report["detail"] = "the edge is inside speech, so the clip opens or closes in the middle of a word"

    # Both candidates are offered, because only the wanted words say which way the edge should move.
    report["moveEarlier"] = reach_into(before[-1], kind) if before else None
    report["moveLater"] = reach_into(after[0], kind) if after else None
    if not before or not after:
        report["detail"] += ". No silence was found on one side inside the probe window"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", required=True, help="The `media` of the SocialPostMediaSource: a file or a URL.")
    parser.add_argument("--start", type=float, required=True, help="`ts_start`, in the clock of the source.")
    parser.add_argument("--end", type=float, required=True, help="`ts_end`, in the clock of the source.")
    parser.add_argument(
        "--probe",
        type=float,
        default=3.0,
        help="Seconds to examine on each side of an edge. A longer probe finds a silence further away.",
    )
    parser.add_argument("--noise", type=float, default=-32.0, help="Silence threshold in dB.")
    parser.add_argument(
        "--min-silence",
        type=float,
        default=0.12,
        help="Shortest run that counts as silence. Below a breath, and above the stop of a consonant.",
    )
    parser.add_argument("--report", help="Where to write the report. It goes to stdout either way.")
    args = parser.parse_args()

    report = {"status": "fail", "media": args.media, "start": args.start, "end": args.end}
    try:
        edges = [
            inspect_edge(args.media, args.start, "in", args.probe, args.noise, args.min_silence),
            inspect_edge(args.media, args.end, "out", args.probe, args.noise, args.min_silence),
        ]
        report["edges"] = edges
        report["status"] = "pass" if all(edge["status"] == "pass" for edge in edges) else "fail"
    except Exception as exc:
        report["error"] = str(exc)

    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
