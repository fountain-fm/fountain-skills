#!/usr/bin/env python3
"""Plan a faster clip: its length in frames at the new speed, and the word timings on the new clock.

Reads the clip's word timings, each optionally carrying an "emphasize" or a
"speaker" field. Only "word", "start" and "end" are read, and every other field
is passed through to the retimed list unchanged.

The speed is held between 1.0 and --max-speed, so the plan never slows a
speaker down, and never goes past the speed where a voice starts to sound wrong.

The plan gives the length of the paced clip as a whole number of frames. Render
to exactly that count, so the clip lasts exactly as long as the plan says, and
the word timings stay on the frames that show them.
"""

import argparse
import json
import sys


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


def parse_fps(text):
    num, _, den = text.partition("/")
    return float(num) / float(den or 1)


def retime(words, speed, length):
    """Move each word onto the clock of the faster clip, and drop a word that falls past its end."""
    retimed = []
    for word in words:
        start, end = float(word["start"]) / speed, float(word["end"]) / speed
        if start < length:
            moved = dict(word)
            moved["start"] = round(start, 3)
            moved["end"] = round(min(end, length), 3)
            retimed.append(moved)
    return retimed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--words", required=True, help="The clip's word timings.")
    parser.add_argument("--duration", type=float, required=True, help="Clip duration in seconds.")
    parser.add_argument("--fps", required=True, help="Frame rate of the master, as ffprobe gives it, e.g. 30000/1001.")
    parser.add_argument("--speed", type=float, required=True, help="Play the clip at this speed, e.g. 1.1.")
    parser.add_argument("--max-speed", type=float, default=1.25, help="Refuse a speed above this.")
    parser.add_argument("--out", help="Write the plan here as well as to stdout.")
    args = parser.parse_args()

    if not 1.0 <= args.speed <= args.max_speed:
        fail(f"--speed {args.speed} is outside 1.0-{args.max_speed}; raise --max-speed to allow a faster speed")

    fps = parse_fps(args.fps)
    frames = max(1, round(args.duration / args.speed * fps))
    length = frames / fps
    words = sorted(load_words(args.words), key=lambda w: float(w["start"]))
    retimed = retime(words, args.speed, length)
    dropped = len(words) - len(retimed)

    plan = {
        "ok": dropped == 0,
        "speed": args.speed,
        "fps": args.fps,
        "frames": frames,
        "duration": {
            "before": round(args.duration, 3),
            "after": round(length, 6),
            "saved": round(args.duration - length, 3),
        },
        "words": retimed,
        "warnings": [f"{dropped} word(s) start past the end of the clip, so the plan dropped them"] if dropped else [],
    }

    text = json.dumps(plan, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(text + "\n")


if __name__ == "__main__":
    main()
