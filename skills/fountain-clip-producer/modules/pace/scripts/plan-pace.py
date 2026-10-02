#!/usr/bin/env python3
"""Plan a faster clip: a speed for each phrase, and the word timings on the new clock.

Reads the clip's word timings, each optionally carrying an "emphasize" or a
"speaker" field. Only "word", "start" and "end" are read, and every other field
is passed through to the retimed list unchanged.

Two modes:

  * --speed plays the whole clip at one speed, e.g. 1.1.
  * --target-rate plays each phrase at the speed that brings it to that many
    syllables a second, so a slow phrase speeds up more than a fast one.

A phrase ends at a pause between two words, so a speed never changes inside a
word. A phrase grows over the next pause until it lasts --min-phrase, because
a speed that changes every second sounds like a fault rather than a style.

The speed of every phrase is held between --min-speed and --max-speed. The
default floor is 1.0, so the plan never slows a speaker down.

Each segment carries the number of frames that it lasts at its speed. Render
each segment to exactly that count, so the joined clip lasts exactly as long as
the plan says, and the word timings stay on the frames that show them.
"""

import argparse
import json
import re
import sys

VOWEL_GROUPS = re.compile(r"[aeiouy]+")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_words(path):
    with open(path) as handle:
        data = json.load(handle)
    words = data["words"] if isinstance(data, dict) else data
    if not words:
        fail("no words given")
    return words


def syllables(text):
    """Estimate syllables from vowel groups, which is close enough to compare two phrases."""
    letters = re.sub(r"[^a-z]", "", text.lower())
    count = len(VOWEL_GROUPS.findall(letters))
    if count > 1 and letters.endswith("e") and not letters.endswith(("le", "ee")):
        count -= 1
    return max(1, count)


def phrases(words, duration, min_gap, min_phrase):
    """Split the clip at pauses, so each phrase starts and ends between two words."""
    cuts = [0.0]
    for before, after in zip(words, words[1:], strict=False):
        gap_start, gap_end = float(before["end"]), float(after["start"])
        if gap_end - gap_start >= min_gap:
            cuts.append(round((gap_start + gap_end) / 2, 3))
    cuts.append(round(duration, 3))

    spans = [{"start": start, "end": end} for start, end in zip(cuts, cuts[1:], strict=False) if end > start]

    # Grow each phrase until it is long enough, then start the next one. A short last phrase joins the one before.
    joined = []
    for span in spans:
        if joined and joined[-1]["end"] - joined[-1]["start"] < min_phrase:
            joined[-1]["end"] = span["end"]
        else:
            joined.append(dict(span))
    if len(joined) > 1 and joined[-1]["end"] - joined[-1]["start"] < min_phrase:
        joined[-2]["end"] = joined[-1]["end"]
        joined.pop()
    return joined


def speech_rate(span, words):
    """Syllables a second over the speech of the phrase, from its first word to its last."""
    inside = [w for w in words if float(w["start"]) >= span["start"] and float(w["end"]) <= span["end"]]
    if not inside:
        return None
    talk = float(inside[-1]["end"]) - float(inside[0]["start"])
    if talk <= 0:
        return None
    return sum(syllables(w["word"]) for w in inside) / talk


def merge_close(segments, tolerance):
    """Join neighbours whose speeds are nearly equal, because each join is one more encode boundary."""
    merged = []
    for segment in segments:
        if merged and abs(segment["speed"] - merged[-1]["speed"]) <= tolerance:
            previous = merged[-1]
            length_a = previous["end"] - previous["start"]
            length_b = segment["end"] - segment["start"]
            previous["speed"] = round(
                (previous["speed"] * length_a + segment["speed"] * length_b) / (length_a + length_b), 3
            )
            previous["end"] = segment["end"]
        else:
            merged.append(dict(segment))
    return merged


def parse_fps(text):
    num, _, den = text.partition("/")
    return float(num) / float(den or 1)


def count_frames(segments, fps):
    """Give each segment a whole number of frames, so the render can stop on exactly that frame."""
    for segment in segments:
        segment["frames"] = max(1, round((segment["end"] - segment["start"]) / segment["speed"] * fps))
        segment["length"] = round(segment["frames"] / fps, 6)


def retime(words, segments):
    """Move each word onto the clock of the faster clip, whose segments last a whole number of frames."""
    retimed, offset = [], 0.0
    for segment in segments:
        for word in words:
            start, end = float(word["start"]), float(word["end"])
            if segment["start"] <= start < segment["end"]:
                moved = dict(word)
                moved["start"] = round(offset + (start - segment["start"]) / segment["speed"], 3)
                moved["end"] = round(offset + (end - segment["start"]) / segment["speed"], 3)
                retimed.append(moved)
        offset += segment["length"]
    return retimed, offset


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--words", required=True, help="The clip's word timings.")
    parser.add_argument("--duration", type=float, required=True, help="Clip duration in seconds.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--speed", type=float, help="Play the whole clip at this speed.")
    mode.add_argument("--target-rate", type=float, help="Bring each phrase to this many syllables a second.")
    parser.add_argument("--min-speed", type=float, default=1.0, help="Never play a phrase slower than this.")
    parser.add_argument("--max-speed", type=float, default=1.25, help="Never play a phrase faster than this.")
    parser.add_argument("--min-gap", type=float, default=0.15, help="A gap this long between words ends a phrase.")
    parser.add_argument(
        "--min-phrase", type=float, default=2.0, help="Join a phrase shorter than this to its neighbour."
    )
    parser.add_argument(
        "--tolerance", type=float, default=0.03, help="Join neighbours whose speeds differ by this much."
    )
    parser.add_argument("--fps", required=True, help="Frame rate of the master, as ffprobe gives it, e.g. 30000/1001.")
    parser.add_argument("--out", help="Write the plan here as well as to stdout.")
    args = parser.parse_args()

    if not 0.5 <= args.min_speed <= args.max_speed <= 2.0:
        fail("--min-speed and --max-speed must sit between 0.5 and 2.0, with the floor at or below the cap")

    words = sorted(load_words(args.words), key=lambda w: float(w["start"]))
    warnings = []

    if args.speed is not None:
        if not args.min_speed <= args.speed <= args.max_speed:
            fail(f"--speed {args.speed} is outside {args.min_speed}-{args.max_speed}; raise --max-speed to allow it")
        segments = [{"start": 0.0, "end": round(args.duration, 3), "speed": round(args.speed, 3), "rate": None}]
    else:
        segments, capped = [], 0
        spans = phrases(words, args.duration, args.min_gap, args.min_phrase)
        if len(spans) == 1 and args.duration >= 2 * args.min_phrase:
            warnings.append(
                f"the word timings show no pause of {args.min_gap}s or more, so the whole clip is one phrase "
                "-- give the timings of the recogniser, because a caption stream closes every gap"
            )
        for span in spans:
            rate = speech_rate(span, words)
            wanted = args.target_rate / rate if rate else args.min_speed
            speed = min(args.max_speed, max(args.min_speed, wanted))
            capped += wanted > args.max_speed
            segments.append({**span, "speed": round(speed, 3), "rate": round(rate, 2) if rate else None})
        if capped:
            warnings.append(
                f"{capped} phrase(s) stayed under the target rate at the {args.max_speed} cap "
                "-- the speaker is slower than the target, so listen before you raise the cap"
            )
        segments = merge_close(segments, args.tolerance)

    fps = parse_fps(args.fps)
    count_frames(segments, fps)
    retimed, after = retime(words, segments)
    if len(retimed) != len(words):
        warnings.append(f"{len(words) - len(retimed)} word(s) fell outside every segment and were dropped")

    plan = {
        "ok": len(retimed) == len(words),
        "mode": "fixed" if args.speed is not None else "dynamic",
        "fps": args.fps,
        "max_speed": max(segment["speed"] for segment in segments),
        "duration": {
            "before": round(args.duration, 3),
            "after": round(after, 3),
            "saved": round(args.duration - after, 3),
        },
        "segments": segments,
        "words": retimed,
        "warnings": warnings,
    }

    text = json.dumps(plan, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(text + "\n")


if __name__ == "__main__":
    main()
