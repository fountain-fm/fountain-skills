#!/usr/bin/env python3
"""Survey a clip for dead air and filler, and plan the cuts that remove them.

Reads the clip's word timings, each optionally carrying an "emphasize" or a
"speaker" field. Only "word", "start" and "end" are read.

Two modes, and the default is the cautious one:

  * without --apply it only SURVEYS -- how much dead air and filler the clip
    holds, and what removing them would save. This is what the module reports
    to the user before anything is cut.
  * with --apply it also plans the cut: the spans to keep, and the word list
    rebased onto the shortened timeline.

Cut points are snapped to real silence measured from the media, because a cut
placed mid-breath clicks. Without --media the cuts fall on word boundaries
instead and the plan says so.

Only unambiguous non-words are removed by default. "like", "you know" and
"I mean" are real speech as often as they are filler, so they stay unless
--fillers names them. Repetition is kept too, because a repeat that carries
emphasis or contrast is doing work -- pass --false-starts to drop immediate
repeats anyway.
"""

import argparse
import json
import re
import subprocess
import sys

# Non-words only. Anything that can be a real word is opt-in via --fillers.
DEFAULT_FILLERS = {"um", "uh", "uhm", "erm", "er", "mm", "hmm", "mhm", "ah"}

SILENCE_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
SILENCE_END = re.compile(r"silence_end:\s*(-?[\d.]+)")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def normalise(text):
    return re.sub(r"[^a-z]", "", text.lower())


def load_words(path):
    with open(path) as handle:
        data = json.load(handle)
    words = data["words"] if isinstance(data, dict) else data
    if not words:
        fail("no words given")
    return words


def silence_map(media, noise_db, min_silence):
    """Ask ffmpeg where the real gaps are, so cuts can land in them."""
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            media,
            "-af",
            f"silencedetect=n={noise_db}dB:d={min_silence}",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # Degrading quietly here would place every cut on a word boundary while
        # the report still claimed the cuts were snapped to real silence.
        detail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "unknown error"
        fail(f"ffmpeg could not read {media}: {detail}")
    starts = [float(m) for m in SILENCE_START.findall(proc.stderr)]
    ends = [float(m) for m in SILENCE_END.findall(proc.stderr)]
    return list(zip(starts, ends, strict=False))


def snap(edge, silences, tolerance):
    """Move a cut edge onto the nearest silence boundary within tolerance."""
    best, best_gap = edge, tolerance
    for start, end in silences:
        for boundary in (start, end):
            gap = abs(boundary - edge)
            if gap < best_gap:
                best, best_gap = boundary, gap
    return best


def find_removals(words, duration, args):
    removals = []

    # Dead air, including the head and tail of the clip. A pause is shortened
    # to the target rather than closed, so the speech keeps a beat.
    edges = [{"end": 0.0}] + list(words) + [{"start": duration}]
    for before, after in zip(edges, edges[1:], strict=False):
        gap_start, gap_end = float(before.get("end", 0.0)), float(after.get("start", duration))
        if gap_end - gap_start > args.max_pause:
            removals.append(
                {
                    "start": round(gap_start + args.pause_target, 3),
                    "end": round(gap_end, 3),
                    "reason": "dead-air",
                    "text": "",
                }
            )

    fillers = set(args.fillers.split(",")) if args.fillers else DEFAULT_FILLERS
    for i, word in enumerate(words):
        if word.get("emphasize"):
            continue  # an emphasised word is never filler, whatever it says
        token = normalise(word["word"])
        if token and token in fillers:
            removals.append(
                {"start": float(word["start"]), "end": float(word["end"]), "reason": "filler", "text": word["word"]}
            )
        elif args.false_starts and i + 1 < len(words):
            nxt = words[i + 1]
            if token and token == normalise(nxt["word"]) and float(nxt["start"]) - float(word["end"]) < 0.35:
                removals.append(
                    {
                        "start": float(word["start"]),
                        "end": float(word["end"]),
                        "reason": "false-start",
                        "text": word["word"],
                    }
                )

    return sorted(removals, key=lambda r: r["start"])


def merge(removals):
    merged = []
    for removal in removals:
        if merged and removal["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], removal["end"])
            merged[-1]["reason"] = f"{merged[-1]['reason']}+{removal['reason']}"
        else:
            merged.append(dict(removal))
    return [r for r in merged if r["end"] - r["start"] > 0.02]


def keep_segments(removals, duration):
    segments, cursor = [], 0.0
    for removal in removals:
        if removal["start"] > cursor:
            segments.append({"start": round(cursor, 3), "end": round(removal["start"], 3)})
        cursor = max(cursor, removal["end"])
    if cursor < duration:
        segments.append({"start": round(cursor, 3), "end": round(duration, 3)})
    return segments


def rebase(words, segments):
    """Drop the words inside a removed span and shift the rest onto the new clock."""
    kept, consumed = [], 0.0
    for segment in segments:
        for word in words:
            start, end = float(word["start"]), float(word["end"])
            if start >= segment["start"] and end <= segment["end"]:
                shifted = dict(word)
                shifted["start"] = round(start - segment["start"] + consumed, 3)
                shifted["end"] = round(end - segment["start"] + consumed, 3)
                kept.append(shifted)
        consumed += segment["end"] - segment["start"]
    return kept


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--words", required=True, help="The clip's word timings.")
    parser.add_argument("--duration", type=float, required=True, help="Clip duration in seconds.")
    parser.add_argument("--media", help="Landscape master, so cuts can be snapped to real silence.")
    parser.add_argument("--apply", action="store_true", help="Plan the cut, not just survey it.")
    parser.add_argument("--max-pause", type=float, default=1.5, help="A gap longer than this is dead air.")
    parser.add_argument("--pause-target", type=float, default=0.35, help="Leave this much of the pause behind.")
    parser.add_argument("--fillers", help="Comma-separated filler tokens, replacing the cautious default set.")
    parser.add_argument("--false-starts", action="store_true", help="Also drop an immediate word repeat.")
    parser.add_argument("--max-removed-pct", type=float, default=25.0, help="Warn past this share of the clip.")
    parser.add_argument(
        "--max-single",
        type=float,
        default=2.5,
        help="A single removal longer than this is a passage, not filler. Held back for approval.",
    )
    parser.add_argument("--allow-long", action="store_true", help="Keep the held-back removals in the plan.")
    parser.add_argument(
        "--long-pause",
        type=float,
        default=2.0,
        help="Warn when a single pause this long is closed, in case it is a deliberate beat.",
    )
    parser.add_argument("--noise-db", type=float, default=-30.0, help="Silence threshold for silencedetect.")
    parser.add_argument("--min-silence", type=float, default=0.15, help="Shortest gap silencedetect reports.")
    parser.add_argument("--out", help="Write the report here as well as to stdout.")
    args = parser.parse_args()

    words = load_words(args.words)
    removals = find_removals(words, args.duration, args)

    silences = silence_map(args.media, args.noise_db, args.min_silence) if args.media else []
    if silences:
        for removal in removals:
            # Snapping can push an edge just past the clip, because silencedetect
            # reports the media's own end rather than the span we were given.
            removal["start"] = round(max(0.0, snap(removal["start"], silences, 0.25)), 3)
            removal["end"] = round(min(args.duration, snap(removal["end"], silences, 0.25)), 3)

    removals = merge([r for r in removals if r["end"] > r["start"]])

    # Hold back a long removal that takes SPEECH with it, because closing a
    # passage can put two statements together that were never adjacent. Pure
    # dead air is exempt: it removes no words, so it cannot invent a
    # juxtaposition. It only changes pacing, which the warning below surfaces.
    def takes_speech(removal):
        return removal["reason"] != "dead-air"

    held = [r for r in removals if r["end"] - r["start"] > args.max_single and takes_speech(r)]
    if held and not args.allow_long:
        removals = [r for r in removals if r not in held]

    removed = sum(r["end"] - r["start"] for r in removals)
    pct = (removed / args.duration * 100) if args.duration else 0.0

    warnings = []
    if args.media is None:
        warnings.append("no media given, so cuts fall on word boundaries and the joins may click")
    elif not silences:
        warnings.append(
            f"no silence found in {args.media} at {args.noise_db}dB, so cuts fall on word boundaries "
            "and the joins may click -- raise --noise-db if the room tone is loud"
        )
    if pct > args.max_removed_pct:
        warnings.append(f"removing {pct:.0f}% of the clip, over the {args.max_removed_pct:.0f}% cap")
    for removal in held:
        warnings.append(
            f"held back a {removal['end'] - removal['start']:.1f}s removal at {removal['start']:.1f}s "
            "-- that is a passage, not filler, and it needs a person to approve it"
        )
    for removal in removals:
        length = removal["end"] - removal["start"]
        if removal["reason"] == "dead-air" and length > args.long_pause:
            warnings.append(
                f"closing a {length:.1f}s pause at {removal['start']:.1f}s "
                "-- check it is not a beat the speaker meant to leave"
            )

    report = {
        "ok": pct <= args.max_removed_pct,
        "applied": args.apply,
        "duration": {
            "before": round(args.duration, 3),
            "after": round(args.duration - removed, 3),
            "removed": round(removed, 3),
            "removed_pct": round(pct, 1),
        },
        "counts": {
            "dead_air": sum(1 for r in removals if "dead-air" in r["reason"]),
            "filler": sum(1 for r in removals if "filler" in r["reason"]),
            "held_back": len(held),
        },
        "removals": removals,
        "warnings": warnings,
    }
    if args.apply:
        segments = keep_segments(removals, args.duration)
        report["segments"] = segments
        report["words"] = rebase(words, segments)

    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(text + "\n")


if __name__ == "__main__":
    main()
