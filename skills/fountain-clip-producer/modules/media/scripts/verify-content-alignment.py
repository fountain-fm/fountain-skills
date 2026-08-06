#!/usr/bin/env python3
"""Verify that a clip's target window actually contains the expected spoken
content, before trusting ts_start/ts_end against that source.

Reads the `media`, `ts_start`, `ts_end`, and `transcript` fields of a
SocialPostMediaSource, passed in as CLI arguments -- this script makes no
Fountain API request of its own.

Why this exists: a duration mismatch between an RSS-declared episode and its
matched YouTube video (commonly dynamic ad insertion) means the same
start/end seconds can land on completely different content on each timeline.
Comparing durations only tells you the timelines differ, not by how much at
any specific point (ad breaks aren't evenly distributed) -- comparing the
actual expected text against what's really being said in that window is what
catches a real mismatch.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path


def norm(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def to_seconds(timestamp):
    hours, minutes, seconds = timestamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


# YouTube's auto-generated VTT is a rolling-caption format -- consecutive cues
# often repeat overlapping words and carry inline word-level timing tags like
# "<00:00:01.500><c> word</c>". This is a best-effort extraction for fuzzy
# text comparison, not a transcript -- duplicated phrases from the rolling
# style don't meaningfully hurt a similarity score, so they're left as-is
# rather than de-duplicated.
CUE_PATTERN = re.compile(
    r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})[^\n]*\n((?:.+\n?)+?)(?=\n\n|\Z)",
    re.MULTILINE,
)
INLINE_TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_vtt(path, window_start, window_end):
    """Extract the text of every caption cue overlapping [window_start, window_end].

    YouTube's rolling-caption style means consecutive cues frequently restate
    the same line before advancing -- deduplicated here (preserving first-seen
    order) so the extracted text is roughly one pass over what was actually
    said, not the same sentence three times over."""
    content = Path(path).read_text(encoding="utf-8", errors="ignore")
    seen = {}
    for match in CUE_PATTERN.finditer(content):
        start, end = to_seconds(match.group(1)), to_seconds(match.group(2))
        if end < window_start or start > window_end:
            continue
        clean = INLINE_TAG_PATTERN.sub("", match.group(3)).strip()
        for line in clean.splitlines():
            line = line.strip()
            if line:
                seen[line] = None  # dict preserves insertion order, dedupes exact repeats
    return " ".join(seen.keys())


def fetch_auto_captions(video_url, workdir):
    proc = subprocess.run(
        [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang",
            "en",
            "--sub-format",
            "vtt",
            "--skip-download",
            "-o",
            str(workdir / "captions"),
            video_url,
        ],
        capture_output=True,
        text=True,
    )
    matches = list(workdir.glob("captions*.vtt"))
    if not matches:
        detail = proc.stderr.strip() or "no auto-caption file was produced"
        raise RuntimeError(f"could not fetch auto-captions for {video_url}: {detail}")
    return matches[0]


def similarity(expected, actual):
    """How much of the expected text shows up in the (much longer) actual
    window, not how similar the two strings are overall -- actual is a whole
    padded window's worth of captions, expected is a short quote, so a
    length-normalized ratio like SequenceMatcher.ratio() dilutes toward zero
    even on a verbatim match. Score against expected's own length instead:
    coverage (what fraction of expected's words appear anywhere in actual --
    order-independent, robust to actual being long) blended with the longest
    contiguous matching run (catches whether it's a genuine phrase match, not
    just scattered common words)."""
    norm_expected, norm_actual = norm(expected), norm(actual)
    expected_tokens = norm_expected.split()
    if not expected_tokens:
        return 0.0
    actual_token_set = set(norm_actual.split())
    coverage = sum(1 for token in expected_tokens if token in actual_token_set) / len(expected_tokens)
    matcher = SequenceMatcher(None, norm_expected, norm_actual)
    longest = matcher.find_longest_match(0, len(norm_expected), 0, len(norm_actual))
    longest_match_ratio = longest.size / len(norm_expected)
    return round((coverage * 0.6) + (longest_match_ratio * 0.4), 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-url", required=True)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument(
        "--expected-text",
        required=True,
        help="The expected spoken text: the `transcript` field of the clip's SocialPostMediaSource.",
    )
    parser.add_argument(
        "--pad",
        type=float,
        default=15.0,
        help="Seconds of padding on each side of start/end when pulling captions -- "
        "the point of this check is that the boundary itself may be off.",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.45,
        help="Below this score, treat the window as not matching the expected content.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        try:
            vtt_path = fetch_auto_captions(args.video_url, workdir)
        except RuntimeError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            sys.exit(1)
        actual_text = parse_vtt(vtt_path, args.start - args.pad, args.end + args.pad)

    score = similarity(args.expected_text, actual_text)
    result = {
        "ok": score >= args.min_similarity,
        "similarity": score,
        "threshold": args.min_similarity,
        "window": [round(args.start - args.pad, 2), round(args.end + args.pad, 2)],
        "expectedText": args.expected_text,
        "actualText": actual_text,
    }
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
