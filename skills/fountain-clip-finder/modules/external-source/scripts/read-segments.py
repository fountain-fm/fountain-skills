#!/usr/bin/env python3
"""Read a video that Fountain does not hold, as transcript segments in the clock of that video.

A talk on YouTube and an episode that is not published yet have the same problem: no Fountain
episode, so no transcript to search or to cut on. This reads the words of such a video from the
best source it has - the caption track of a watch page, a subtitle file beside a local video, or
whisper on the audio of that video - and gives back segments shaped like a TranscriptSegment:
`start`, `end` and `text`, in the clock of the video itself. It makes no Fountain API request.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
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
# The model the skills install, which the whisper filter takes the path of and hangs without.
DEFAULT_MODEL = os.path.expanduser("~/.cache/whisper/ggml-base.en.bin")
# A subtitle beside the video is read before whisper runs, in this order of preference.
SIDECAR_SUFFIXES = (".srt", ".vtt", ".en.srt", ".en.vtt")
# One cue of a subtitle file: two timestamps, and the text on the lines after them.
CUE_TIMES = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[.,](\d{1,3})")


def is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


# --- a watch page, read through its caption track ------------------------------------------------


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
    source = "captions-manual"
    if payload is None:
        payload = download_captions(video_url, "--write-auto-subs", "en,en-orig")
        source = "captions-automatic"
    if payload is None:
        raise SystemExit("read-segments: the video has no English caption track")

    words: list[tuple[str, float]] = []
    for event in payload.get("events") or []:
        # A rolling automatic track repeats the line it is building, and the repeat carries this flag.
        if event.get("aAppend"):
            continue
        words += event_words(event)

    # A caption track can hand back two tracks of one line, so keep the pairs in time order.
    words.sort(key=lambda pair: pair[1])
    if not words:
        raise SystemExit("read-segments: the caption track holds no words")
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


# --- a local file, read through a subtitle beside it or through whisper ---------------------------


def find_sidecar(video_path: str) -> str | None:
    """Find a subtitle file beside the video, which is a better reading than whisper of the same audio."""
    stem = os.path.splitext(video_path)[0]
    for suffix in SIDECAR_SUFFIXES:
        candidate = stem + suffix
        if os.path.isfile(candidate):
            return candidate
    return None


def read_sidecar(path: str) -> list[dict[str, object]]:
    """Read an SRT or a VTT file as segments. Both write one cue as times and then the lines of text."""
    with open(path, encoding="utf-8-sig", errors="replace") as handle:
        lines = handle.read().splitlines()

    segments: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        match = CUE_TIMES.search(lines[index])
        if not match:
            index += 1
            continue
        # A fraction is written with one to three digits, so pad it before it is read as milliseconds.
        raw = match.groups()
        parts = [int(value) for value in raw[:3]] + [int(raw[3].ljust(3, "0"))]
        parts += [int(value) for value in raw[4:7]] + [int(raw[7].ljust(3, "0"))]
        start = parts[0] * 3600 + parts[1] * 60 + parts[2] + parts[3] / 1000.0
        end = parts[4] * 3600 + parts[5] * 60 + parts[6] + parts[7] / 1000.0

        index += 1
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            # A VTT cue can carry inline tags, and none of them is a word of the transcript.
            text_lines.append(re.sub(r"<[^>]+>", "", lines[index]).strip())
            index += 1
        text = " ".join(part for part in text_lines if part)
        if text:
            segments.append({"start": round(start, 2), "end": round(end, 2), "text": text})

    if not segments:
        raise SystemExit(f"read-segments: {path} holds no cues")
    return segments


def find_ffmpeg(named: str | None) -> str:
    """Find an ffmpeg that carries the whisper filter, because a stock build carries none."""
    candidates = [named] if named else ["ffmpeg", "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"]
    for candidate in candidates:
        binary = shutil.which(candidate) if candidate and os.path.sep not in candidate else candidate
        if not binary or not os.path.exists(binary):
            continue
        filters = subprocess.run([binary, "-hide_banner", "-filters"], check=False, text=True, capture_output=True)
        if "whisper" in filters.stdout:
            return binary
    raise SystemExit("read-segments: no ffmpeg on this machine carries the whisper filter")


def transcribe(video_path: str, ffmpeg: str, model: str) -> list[dict[str, object]]:
    """Transcribe the audio of a local video with the whisper filter of ffmpeg."""
    if not os.path.isfile(model):
        raise SystemExit(f"read-segments: no whisper model at {model} - the filter hangs without one")

    with tempfile.TemporaryDirectory() as directory:
        out = os.path.join(directory, "whisper.json")
        result = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                video_path,
                "-vn",  # the words come from the audio, and decoding the video only costs time
                "-af",
                f"whisper=model={model}:language=en:queue=10:destination={out}:format=json",
                "-f",
                "null",
                "-",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        if not os.path.isfile(out):
            raise SystemExit(f"read-segments: whisper wrote nothing - {result.stderr.strip()[:300]}")
        with open(out, encoding="utf-8") as handle:
            payload = handle.read()

    segments: list[dict[str, object]] = []
    for line in payload.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith("{"):
            continue
        record = json.loads(line)
        text = (record.get("text") or "").strip()
        if not text:
            continue
        # The filter writes milliseconds, and every module after this one reads seconds.
        segments.append(
            {
                "start": round(float(record["start"]) / 1000.0, 2),
                "end": round(float(record["end"]) / 1000.0, 2),
                "text": text,
            }
        )
    if not segments:
        raise SystemExit("read-segments: whisper heard no speech in the file")
    return segments


def probe_duration(video_path: str) -> float | None:
    """Read the duration of a local file, so that the caller can check the segments cover it."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video_path],
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        return round(float(result.stdout.strip()), 2)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="A watch page URL, or the path of a video file on this machine.")
    parser.add_argument("--subtitles", help="A subtitle file to read instead of transcribing a local video.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="The whisper.cpp model to transcribe with.")
    parser.add_argument("--ffmpeg", help="The ffmpeg build to use, when the one on the PATH carries no whisper.")
    args = parser.parse_args()

    duration: float | None = None
    if is_url(args.source):
        words, read_from = fetch_caption_words(args.source)
        segments = build_segments(words)
        detail = f"{len(words)} words from the {read_from.split('-')[1]} caption track"
    elif not os.path.isfile(args.source):
        raise SystemExit(f"read-segments: no file at {args.source}")
    else:
        duration = probe_duration(args.source)
        sidecar = args.subtitles or find_sidecar(args.source)
        if sidecar:
            segments = read_sidecar(sidecar)
            read_from = "subtitles"
            detail = f"{len(segments)} cues from {os.path.basename(sidecar)}"
        else:
            segments = transcribe(args.source, find_ffmpeg(args.ffmpeg), args.model)
            read_from = "whisper"
            detail = f"{len(segments)} segments from whisper"

    print(f"read {detail}, in {len(segments)} segments", file=sys.stderr)
    print(
        json.dumps(
            {
                "media": args.source,
                "read_from": read_from,
                "duration": duration if duration is not None else segments[-1]["end"],
                "segments": segments,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
