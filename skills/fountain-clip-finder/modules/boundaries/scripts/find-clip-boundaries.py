#!/usr/bin/env python3
"""Move a moment to clean clip in and out points, and cut the word-level slice of a final span.

Reads an episode transcript as JSON on stdin.
Without `--span` it prints the sentences around the moment and every in/out pair inside the duration range.
With `--span` it prints the words of that span on stdout, with the times rebased to clip time.
"""

from __future__ import annotations

import argparse
import json
import sys

# The Fountain transcript comes from the episode audio, so its times match the media and the search.
# The RSS transcript can be offset by minutes when the feed carries a different ad-insertion cut.
TRANSCRIPT_SOURCES = ("fountain", "rss")


def load_transcript(payload: object) -> tuple[list[dict], list[dict], str]:
    """Return the segments, the words, and the name of the source that was used."""
    if isinstance(payload, list):
        return payload, [], "stdin"

    if not isinstance(payload, dict):
        raise SystemExit("find-clip-boundaries: stdin must hold a transcript object or a list of segments")

    transcript = payload.get("transcript") if isinstance(payload.get("transcript"), dict) else payload
    for source in TRANSCRIPT_SOURCES:
        entry = transcript.get(source)
        if isinstance(entry, dict) and entry.get("segments"):
            return entry["segments"], entry.get("words") or [], source
    raise SystemExit("find-clip-boundaries: the transcript holds no segments - generate it first")


def label(segment: dict) -> str:
    speaker = segment.get("speaker")
    return f"{speaker}: {segment['text']}" if speaker else segment["text"]


def print_boundaries(segments: list[dict], args: argparse.Namespace, source: str) -> None:
    window_start = args.moment_start - args.lookback
    window_end = args.moment_end + args.lookahead
    in_window = [s for s in segments if s["end"] > window_start and s["start"] < window_end]

    # An in point is a sentence that starts at or before the moment; an out point is one that ends at or after it.
    in_candidates = [s for s in in_window if window_start <= s["start"] <= args.moment_start + 2.0]
    out_candidates = [s for s in in_window if s["end"] >= args.moment_end - 2.0]

    print(f"\nSource: {source}")
    print(f"Moment: {args.moment_start:.2f}s - {args.moment_end:.2f}s ({args.moment_end - args.moment_start:.1f}s)\n")

    print(f"=== IN POINTS (last {args.context} sentence starts before the moment) ===")
    for segment in in_candidates[-args.context :]:
        index = in_window.index(segment)
        gap = (segment["start"] - in_window[index - 1]["end"]) if index > 0 else 0.0
        marker = " <<< MOMENT" if abs(segment["start"] - args.moment_start) < 3 else ""
        print(f"  [{segment['start']:8.2f}s, gap={gap:.2f}s]  {label(segment)[:90]}{marker}")

    print(f"\n=== OUT POINTS (first {args.context} sentence ends after the moment) ===")
    for segment in out_candidates[: args.context]:
        marker = " <<< MOMENT" if abs(segment["end"] - args.moment_end) < 3 else ""
        print(f"  [ends {segment['end']:8.2f}s]  {label(segment)[:90]}{marker}")

    print(f"\n=== PAIRS ({args.min_dur:.0f}-{args.max_dur:.0f}s) ===")
    pairs = [
        (start_segment, end_segment, end_segment["end"] - start_segment["start"])
        for start_segment in in_candidates[-6:]
        for end_segment in out_candidates[:8]
        if args.min_dur <= end_segment["end"] - start_segment["start"] <= args.max_dur
    ]
    if not pairs:
        print("  (no pair is inside the duration range - widen --min-dur and --max-dur)")
        return
    for start_segment, end_segment, duration in sorted(pairs, key=lambda pair: pair[2]):
        print(
            f"  [{start_segment['start']:8.2f} - {end_segment['end']:8.2f}] = {duration:.1f}s"
            f'\n    IN:  "{start_segment["text"][:70]}"'
            f'\n    OUT: "{end_segment["text"][:70]}"\n'
        )
    print("Use the start of the in sentence and the end of the out sentence. These are episode times.")


def print_span_words(segments: list[dict], words: list[dict], start: float, end: float) -> None:
    """Print the words of the span, with each time rebased to clip time."""
    if not words:
        # Some sources carry the words on each segment instead of one flat list.
        words = [word for segment in segments for word in segment.get("words") or []]

    # The span text is always available; word timings exist only on a Fountain transcript.
    spoken = [s for s in segments if s["end"] > start and s["start"] < end]
    result: dict[str, object] = {
        "start": start,
        "end": end,
        "text": " ".join(s["text"].strip() for s in spoken).strip(),
        "words": [
            {"word": word["word"], "start": round(word["start"] - start, 3), "end": round(word["end"] - start, 3)}
            for word in words
            if word["start"] >= start and word["end"] <= end
        ],
    }
    if not result["words"]:
        print("WARN: this transcript has no word timings - captions need a Fountain transcript", file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moment-start", type=float, help="Moment start in episode seconds.")
    parser.add_argument("--moment-end", type=float, help="Moment end in episode seconds.")
    parser.add_argument("--span", nargs=2, type=float, metavar=("START", "END"), help="Print the words of this span.")
    parser.add_argument("--lookback", type=float, default=90.0, help="Seconds before the moment. Default: 90.")
    parser.add_argument("--lookahead", type=float, default=90.0, help="Seconds after the moment. Default: 90.")
    parser.add_argument("--min-dur", type=float, default=35.0, help="Shortest clip in seconds. Default: 35.")
    parser.add_argument("--max-dur", type=float, default=75.0, help="Longest clip in seconds. Default: 75.")
    parser.add_argument("--context", type=int, default=8, help="Sentences to show on each side. Default: 8.")
    args = parser.parse_args()

    segments, words, source = load_transcript(json.loads(sys.stdin.read()))

    if args.span:
        print_span_words(segments, words, args.span[0], args.span[1])
        return 0
    if args.moment_start is None or args.moment_end is None:
        parser.error("--moment-start and --moment-end are required without --span")
    print_boundaries(segments, args, source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
