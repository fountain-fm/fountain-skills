#!/usr/bin/env python3
"""Read the caption track of a video that Fountain does not hold, as transcript segments.

A talk on YouTube has no episode and no Fountain transcript, so nothing can be searched or cut from
it. This reads the captions of the watch page and groups them into segments shaped like a
TranscriptSegment - `start`, `end` and `text` - in the clock of that video, which is the clock the
clip is cut on. It makes no Fountain API request.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

# A pause this long ends a segment, because the speaker stopped rather than ran on.
SEGMENT_GAP_SECONDS = 0.8
# The longest a segment runs before it is broken, so that no segment is too coarse to cut on.
MAX_SEGMENT_SECONDS = 12.0
# The most words in a segment, for speech that never pauses and never punctuates.
MAX_SEGMENT_WORDS = 30
# The last word of a sentence ends a segment, which is the cut a reader expects.
SENTENCE_END = re.compile(r"[.!?]['\")\]]?$")
# An automatic track times a line and not a word, so the last word of a line needs a length.
DEFAULT_WORD_SECONDS = 0.4


def download_captions(video_url: str, mode: str, languages: str) -> dict | None:
    """Ask yt-dlp for one kind of caption track. Return the parsed track, or None when there is none."""
    with tempfile.TemporaryDirectory() as directory:
        target = os.path.join(directory, "captions")
        subprocess.run(
            [
                "yt-dlp",
                "--skip-download",  # the segments need the captions only, never the video
                mode,  # the track the channel uploaded, or the track YouTube generated
                "--sub-langs",
                languages,  # one named list, because a wildcard also pulls the translated tracks
                "--sub-format",
                "json3",  # json3 times an automatic track word by word, and the other formats do not
                "-o",
                target,
                video_url,
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        files = sorted(glob.glob(f"{target}*.json3"))
        if not files:
            return None
        with open(files[0], encoding="utf-8") as handle:
            return json.load(handle)


def event_words(event: dict) -> list[tuple[str, float]]:
    """Read one caption event as (word, start) pairs. A word with no time of its own takes the line's."""
    start = float(event.get("tStartMs", 0)) / 1000.0
    words: list[tuple[str, float]] = []
    for piece in event.get("segs") or []:
        text = (piece.get("utf8") or "").strip()
        if not text:
            continue
        offset = piece.get("tOffsetMs")
        piece_start = start + float(offset) / 1000.0 if offset is not None else start
        words += [(token, piece_start) for token in text.split()]
    return words


def fetch_caption_words(video_url: str) -> tuple[list[tuple[str, float]], str]:
    """Download the caption track of the video and return it as (word, start) pairs, in time order."""
    # A track the channel uploaded reads better than a generated one, so ask for it first and on its own.
    payload = download_captions(video_url, "--write-subs", "en,en-US,en-GB")
    source = "manual"
    if payload is None:
        payload = download_captions(video_url, "--write-auto-subs", "en,en-orig")
        source = "automatic"
    if payload is None:
        raise SystemExit("fetch-captions: the video has no English caption track")

    words: list[tuple[str, float]] = []
    for event in payload.get("events") or []:
        # A rolling automatic track repeats the line it is building, and the repeat carries this flag.
        if event.get("aAppend"):
            continue
        words += event_words(event)

    # A caption track can hand back two tracks of one line, so keep the pairs in time order.
    words.sort(key=lambda pair: pair[1])
    if not words:
        raise SystemExit("fetch-captions: the caption track holds no words")
    return words, source


def build_segments(words: list[tuple[str, float]]) -> list[dict[str, object]]:
    """Group the words into segments, breaking on a pause, a sentence end, and the limits above."""
    segments: list[dict[str, object]] = []
    tokens: list[str] = []
    segment_start = words[0][1]

    for index, (word, start) in enumerate(words):
        next_start = words[index + 1][1] if index + 1 < len(words) else start + DEFAULT_WORD_SECONDS
        if not tokens:
            segment_start = start
        tokens.append(word)

        gap = next_start - start
        too_long = next_start - segment_start >= MAX_SEGMENT_SECONDS or len(tokens) >= MAX_SEGMENT_WORDS
        if gap >= SEGMENT_GAP_SECONDS or SENTENCE_END.search(word) or too_long or index + 1 == len(words):
            # The segment ends where the words stop, and the pause after it stays outside the segment.
            end = min(next_start, start + DEFAULT_WORD_SECONDS) if gap >= SEGMENT_GAP_SECONDS else next_start
            segments.append(
                {"start": round(segment_start, 2), "end": round(max(end, segment_start), 2), "text": " ".join(tokens)}
            )
            tokens = []
    return segments


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_url", help="The watch page of the video to read the captions of.")
    args = parser.parse_args()

    words, caption_source = fetch_caption_words(args.video_url)
    segments = build_segments(words)
    print(
        f"read {len(words)} words from the {caption_source} track, in {len(segments)} segments",
        file=sys.stderr,
    )
    print(
        json.dumps(
            {
                "media": args.video_url,
                "caption_source": caption_source,
                "duration": segments[-1]["end"],
                "segments": segments,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
