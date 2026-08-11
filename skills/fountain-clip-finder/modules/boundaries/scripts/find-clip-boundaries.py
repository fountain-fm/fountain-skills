#!/usr/bin/env python3
"""Move a moment to clean clip in and out points, and cut the text of a final span.

Reads a transcript on stdin and uses `start`, `end` and `text` of each TranscriptSegment.
Accepts either the Load Transcript response, `{"segments": [...]}`, or a bare list of segments.

Without `--span` it prints the in/out pairs inside the duration range, spread across that range.
Each pair is padded into the silence around it: a segment edge already falls between words, and the
gap to the neighbouring segment is silence, so a cut placed inside that gap opens and closes cleanly.
With `--span` it prints the text of that span, for `transcript` on a SocialPostMediaSource.

The word timings that captions need are not here. They come from the clip's own audio at render time.
"""

from __future__ import annotations

import argparse
import json
import sys

# How far to reach into the silence on each side, and never more than half of it, so two clips
# cut from neighbouring segments can never overlap.
PAD_SECONDS = 0.25


def load_segments(payload: object) -> list[dict]:
    """Return the transcript segments."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        segments = payload.get("segments")
        if isinstance(segments, list) and segments:
            return segments
    raise SystemExit("find-clip-boundaries: stdin must hold {'segments': [...]} or a list of segments")


def pad_in(segments: list[dict], index: int) -> float:
    """The in point: reach back into the silence before this segment, never past its neighbour."""
    start = segments[index]["start"]
    gap = start - segments[index - 1]["end"] if index > 0 else start
    return round(start - min(PAD_SECONDS, max(gap, 0.0) / 2), 3)


def pad_out(segments: list[dict], index: int) -> float:
    """The out point: reach forward into the silence after this segment, never into the next one."""
    end = segments[index]["end"]
    gap = segments[index + 1]["start"] - end if index + 1 < len(segments) else PAD_SECONDS
    return round(end + min(PAD_SECONDS, max(gap, 0.0) / 2), 3)


def print_boundaries(segments: list[dict], args: argparse.Namespace) -> None:
    window_start = args.moment_start - args.lookback
    window_end = args.moment_end + args.lookahead
    indexed = [(i, s) for i, s in enumerate(segments) if s["end"] > window_start and s["start"] < window_end]

    # A moment runs for minutes, so a clip can start or end anywhere inside it, not only at its edges.
    in_candidates = [(i, s) for i, s in indexed if window_start <= s["start"] <= args.moment_end]
    out_candidates = [(i, s) for i, s in indexed if args.moment_start <= s["end"] <= window_end]

    print(f"\nMoment: {args.moment_start:.2f}s - {args.moment_end:.2f}s ({args.moment_end - args.moment_start:.1f}s)\n")
    print(f"in points: {len(in_candidates)}   out points: {len(out_candidates)}")

    print(f"\n=== PAIRS ({args.min_dur:.0f}-{args.max_dur:.0f}s) ===")
    pairs = []
    for i, start_segment in in_candidates:
        for j, end_segment in out_candidates:
            cut_in, cut_out = pad_in(segments, i), pad_out(segments, j)
            duration = cut_out - cut_in
            if args.min_dur <= duration <= args.max_dur:
                pairs.append((cut_in, cut_out, duration, start_segment, end_segment))
    if not pairs:
        print("  (no pair is inside the duration range - widen --min-dur and --max-dur)")
        return
    # A long moment yields hundreds of pairs, so show a spread rather than every one.
    pairs.sort(key=lambda pair: pair[2])
    if len(pairs) > args.pairs:
        step = len(pairs) / args.pairs
        pairs = [pairs[int(i * step)] for i in range(args.pairs)]
    print(f"  showing {len(pairs)} of the pairs, spread across the duration range\n")
    for cut_in, cut_out, duration, start_segment, end_segment in pairs:
        print(
            f"  [{cut_in:8.2f} - {cut_out:8.2f}] = {duration:.1f}s"
            f'\n    IN:  "{start_segment["text"][:70]}"'
            f'\n    OUT: "{end_segment["text"][:70]}"\n'
        )
    print("These are episode times, already padded into the silence at each edge.")


def print_span(segments: list[dict], start: float, end: float) -> None:
    """Print the text of the span, for `transcript` on the clip's source."""
    spoken = [s for s in segments if s["end"] > start and s["start"] < end]
    if not spoken:
        raise SystemExit("find-clip-boundaries: no segment falls inside that span")
    print(
        json.dumps(
            {
                "start": start,
                "end": end,
                "text": " ".join(s["text"].strip() for s in spoken).strip(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moment-start", type=float, help="Moment start in episode seconds.")
    parser.add_argument("--moment-end", type=float, help="Moment end in episode seconds.")
    parser.add_argument("--span", nargs=2, type=float, metavar=("START", "END"), help="Print the text of this span.")
    parser.add_argument("--lookback", type=float, default=90.0, help="Seconds before the moment. Default: 90.")
    parser.add_argument("--lookahead", type=float, default=90.0, help="Seconds after the moment. Default: 90.")
    parser.add_argument("--min-dur", type=float, default=35.0, help="Shortest clip in seconds. Default: 35.")
    parser.add_argument("--max-dur", type=float, default=75.0, help="Longest clip in seconds. Default: 75.")
    parser.add_argument("--pairs", type=int, default=8, help="In/out pairs to print. Default: 8.")
    args = parser.parse_args()

    segments = load_segments(json.loads(sys.stdin.read()))

    if args.span:
        print_span(segments, args.span[0], args.span[1])
        return 0
    if args.moment_start is None or args.moment_end is None:
        parser.error("--moment-start and --moment-end are required without --span")
    print_boundaries(segments, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
