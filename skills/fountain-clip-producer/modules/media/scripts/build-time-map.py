#!/usr/bin/env python3
"""Map the transcript clock onto the clock of the video that the clip is cut from.

A YouTube cut of an episode carries different ads and a different open, so it runs behind the
transcript by an amount that changes at every break. `--build` reads the video captions one time
and anchors the two clocks against each other across the episode. `--span` then translates one
clip span from the saved map, with no further network work, and gives the `ts_start` and `ts_end`
of a SocialPostMediaSource whose `media` is that video.

The map of an episode does not change, so `--build` keeps it in the `--cache-dir` directory, in a
file of its own named after the episode id that `--episode` names. A miss builds the map as usual
and writes it back.

Reads a transcript on stdin - `{"segments": [...]}` or a bare list - and uses `start`, `end` and `text`
of each TranscriptSegment.
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
from difflib import SequenceMatcher

# The Fountain transcript comes from the episode audio, so its times match the audio and the search.
# One anchor every two minutes finds each ad break without reading the whole episode twice.
ANCHOR_INTERVAL_SECONDS = 120.0
# A phrase of twelve words is long enough to be unique in an episode and short enough to survive an ASR error.
ANCHOR_WORDS = 12
# The words at each edge of the clip, which give the head and the tail offset of that clip.
EDGE_WORDS = 10
# Two transcripts of the same audio disagree on wording, so an anchor is a fuzzy match and never an exact one.
MIN_ANCHOR_RATIO = 0.70
# Word timings differ by a few tenths between two transcripts, so one second of drift is still one offset.
OFFSET_TOLERANCE_SECONDS = 1.0
# A break inserts an advertisement, which never runs for a second, so a region tolerates more than an edge.
REGION_TOLERANCE_SECONDS = 3.0
# An offset holds until the next ad break, so an anchor further away than this says nothing about the clip.
MAX_ANCHOR_DISTANCE_SECONDS = 240.0
# A common phrase repeats through an episode, so it cannot start a candidate window.
MAX_NGRAM_REPEATS = 20
NGRAM_SIZE = 4
# The step between the seed phrases inside one anchor, so that a dropped word does not lose the anchor.
SEED_STEP = 2


def normalize(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def load_transcript_words(payload: object) -> list[tuple[str, float]]:
    """Return the transcript as (word, start) pairs, spread across each segment."""
    segments: list[dict] = []
    if isinstance(payload, list):
        segments = payload
    elif isinstance(payload, dict) and isinstance(payload.get("segments"), list):
        segments = payload["segments"]
    if not segments:
        raise SystemExit("build-time-map: the transcript holds no segments - generate it first")

    # A segment carries no word timings, so spread its words across it. An anchor tolerates that error.
    spread: list[tuple[str, float]] = []
    for segment in segments:
        tokens = segment["text"].split()
        if not tokens:
            continue
        step = (float(segment["end"]) - float(segment["start"])) / len(tokens)
        spread += [(token, float(segment["start"]) + index * step) for index, token in enumerate(tokens)]
    return spread


def download_captions(video_url: str, mode: str, languages: str) -> dict | None:
    """Ask yt-dlp for one kind of caption track. Return the parsed track, or None when there is none."""
    with tempfile.TemporaryDirectory() as directory:
        target = os.path.join(directory, "captions")
        subprocess.run(
            [
                "yt-dlp",
                "--skip-download",  # the map needs the captions only, never the video
                mode,  # the track the show uploaded, or the track YouTube generated
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


def interpolate(entries: list[tuple[str, float | None]], start: float, end: float) -> list[tuple[str, float]]:
    """Give a time to each word that carries none, by spreading it between the words that do."""
    count = len(entries)
    points = [(-1, start)] + [(i, t) for i, (_, t) in enumerate(entries) if t is not None] + [(count, end)]
    times = [start] * count
    for (left_index, left_time), (right_index, right_time) in zip(points, points[1:], strict=False):
        span = right_index - left_index
        for index in range(max(left_index, 0), min(right_index, count)):
            known = entries[index][1]
            times[index] = (
                known if known is not None else left_time + (right_time - left_time) * (index - left_index) / span
            )
    return [(word, time) for (word, _), time in zip(entries, times, strict=True)]


def event_words(event: dict) -> list[tuple[str, float]]:
    """Read one caption event. An automatic track times each word, and a manual one times the whole line."""
    start = float(event.get("tStartMs", 0)) / 1000.0
    end = start + float(event.get("dDurationMs", 0)) / 1000.0
    entries: list[tuple[str, float | None]] = []
    for piece in event.get("segs") or []:
        text = (piece.get("utf8") or "").strip()
        if not text:
            continue
        offset = piece.get("tOffsetMs")
        piece_start = start + float(offset) / 1000.0 if offset is not None else None
        entries += [(token, piece_start if index == 0 else None) for index, token in enumerate(text.split())]
    return interpolate(entries, start, max(end, start)) if entries else []


def fetch_caption_words(video_url: str) -> tuple[list[tuple[str, float]], str]:
    """Download the caption track of the video and return it as (word, start) pairs."""
    # A track the show uploaded reads better than a generated one, so ask for it first and on its own.
    payload = download_captions(video_url, "--write-subs", "en,en-US,en-GB")
    source = "manual"
    if payload is None:
        payload = download_captions(video_url, "--write-auto-subs", "en,en-orig")
        source = "automatic"
    if payload is None:
        raise SystemExit("build-time-map: the video has no English caption track")

    caption_words = [word for event in payload.get("events") or [] for word in event_words(event)]
    if not caption_words:
        raise SystemExit("build-time-map: the caption track holds no words")
    return caption_words, source


def build_index(tokens: list[str]) -> dict[tuple[str, ...], list[int]]:
    """Index the caption words by short phrase, so that a lookup does not scan the whole episode."""
    index: dict[tuple[str, ...], list[int]] = {}
    for position in range(len(tokens) - NGRAM_SIZE + 1):
        index.setdefault(tuple(tokens[position : position + NGRAM_SIZE]), []).append(position)
    return {gram: positions for gram, positions in index.items() if len(positions) <= MAX_NGRAM_REPEATS}


def find_phrase(
    needle: list[str],
    tokens: list[str],
    times: list[float],
    index: dict[tuple[str, ...], list[int]],
    expected: float | None = None,
) -> tuple[float, float] | None:
    """Find the phrase in the caption words and return its (start time, match ratio)."""
    if len(needle) < NGRAM_SIZE:
        return None

    # Two transcripts of one audio drop and change words, so seed the lookup at several points in the
    # phrase. A seed only proposes where to look, and the whole phrase then decides the match.
    starts: set[int] = set()
    for seed in range(0, len(needle) - NGRAM_SIZE + 1, SEED_STEP):
        for position in index.get(tuple(needle[seed : seed + NGRAM_SIZE]), []):
            starts.add(max(0, position - seed))

    best: tuple[float, float] | None = None
    joined = " ".join(needle)
    for position in sorted(starts):
        if expected is not None and abs(times[position] - expected) > MAX_ANCHOR_DISTANCE_SECONDS:
            continue
        window = tokens[position : position + len(needle)]
        ratio = SequenceMatcher(None, joined, " ".join(window)).ratio()
        if ratio >= MIN_ANCHOR_RATIO and (best is None or ratio > best[1]):
            best = (times[position], ratio)
    return best


def take_phrase(words: list[tuple[str, float]], start_index: int, count: int) -> tuple[list[str], float]:
    """Take a phrase of normalized words, and return it with the transcript time of its first word."""
    phrase: list[str] = []
    first_time = words[start_index][1]
    for word, time in words[start_index:]:
        token = normalize(word)
        if not token:
            continue
        if not phrase:
            first_time = time
        phrase.append(token)
        if len(phrase) == count:
            break
    return phrase, first_time


def build_map(transcript_words: list[tuple[str, float]], video_url: str) -> dict[str, object]:
    caption_words, caption_source = fetch_caption_words(video_url)
    tokens = [normalize(word) for word, _ in caption_words]
    times = [time for _, time in caption_words]
    keep = [position for position, token in enumerate(tokens) if token]
    tokens, times = [tokens[p] for p in keep], [times[p] for p in keep]
    index = build_index(tokens)

    anchors: list[dict[str, float]] = []
    next_anchor_time = transcript_words[0][1]
    for position, (_, time) in enumerate(transcript_words):
        if time < next_anchor_time:
            continue
        next_anchor_time = time + ANCHOR_INTERVAL_SECONDS
        phrase, phrase_time = take_phrase(transcript_words, position, ANCHOR_WORDS)
        found = find_phrase(phrase, tokens, times, index)
        if found:
            anchors.append(
                {
                    "transcript_time": round(phrase_time, 2),
                    "media_time": round(found[0], 2),
                    "offset_seconds": round(found[0] - phrase_time, 2),
                    "match_ratio": round(found[1], 3),
                }
            )

    anchors, out_of_order = drop_out_of_order(anchors)
    attempted = max(1, int((transcript_words[-1][1] - transcript_words[0][1]) / ANCHOR_INTERVAL_SECONDS) + 1)
    return {
        "media": video_url,
        "caption_source": caption_source,
        "caption_word_count": len(tokens),
        "anchors_dropped_out_of_order": out_of_order,
        "anchor_coverage": round(len(anchors) / attempted, 3),
        "offset_regions": group_regions(anchors),
        "anchors": anchors,
        # The words are kept so that a span translation needs no second download.
        "caption_words": [[token, round(time, 3)] for token, time in zip(tokens, times, strict=True)],
    }


def drop_out_of_order(anchors: list[dict[str, float]]) -> tuple[list[dict[str, float]], int]:
    """Keep the longest run of anchors that advance together, because two clocks of one recording do.

    A phrase that the show repeats can match the wrong place in the episode. Such an anchor sends the
    media clock backwards while the transcript clock goes forwards, which no true anchor ever does.
    """
    if not anchors:
        return anchors, 0
    run_length = [1] * len(anchors)
    came_from = [-1] * len(anchors)
    for index in range(len(anchors)):
        for earlier in range(index):
            in_order = anchors[earlier]["media_time"] <= anchors[index]["media_time"]
            if in_order and run_length[earlier] + 1 > run_length[index]:
                run_length[index] = run_length[earlier] + 1
                came_from[index] = earlier

    position = max(range(len(anchors)), key=lambda index: run_length[index])
    kept: list[dict[str, float]] = []
    while position != -1:
        kept.append(anchors[position])
        position = came_from[position]
    kept.reverse()
    return kept, len(anchors) - len(kept)


def group_regions(anchors: list[dict[str, float]]) -> list[dict[str, float]]:
    """Join the neighbouring anchors that agree on the offset. A new region is an ad break."""
    regions: list[dict[str, float]] = []
    for anchor in anchors:
        if regions and abs(anchor["offset_seconds"] - regions[-1]["offset_seconds"]) <= REGION_TOLERANCE_SECONDS:
            regions[-1]["transcript_end"] = anchor["transcript_time"]
            continue
        regions.append(
            {
                "transcript_start": anchor["transcript_time"],
                "transcript_end": anchor["transcript_time"],
                "offset_seconds": anchor["offset_seconds"],
            }
        )
    return regions


def nearest_offset(anchors: list[dict[str, float]], time: float) -> float | None:
    """Read the offset that holds at this transcript time, from the anchors around it."""
    candidates = [a for a in anchors if abs(a["transcript_time"] - time) <= MAX_ANCHOR_DISTANCE_SECONDS]
    if not candidates:
        return None
    nearest = min(candidates, key=lambda anchor: abs(anchor["transcript_time"] - time))["offset_seconds"]
    # A single anchor can be a second out, so take the middle of the anchors that agree with it.
    agreeing = sorted(
        a["offset_seconds"] for a in candidates if abs(a["offset_seconds"] - nearest) <= REGION_TOLERANCE_SECONDS
    )
    return agreeing[len(agreeing) // 2]


def edge_offset(
    transcript_words: list[tuple[str, float]],
    time_map: dict,
    time: float,
    from_end: bool,
) -> tuple[float, float] | None:
    """Match the words at one edge of the clip in the captions, and return its (offset, ratio)."""
    caption_words = time_map["caption_words"]
    tokens = [row[0] for row in caption_words]
    times = [row[1] for row in caption_words]
    index = build_index(tokens)

    positions = [p for p, (_, word_time) in enumerate(transcript_words) if word_time >= time]
    if not positions:
        return None
    start_index = max(0, positions[0] - EDGE_WORDS) if from_end else positions[0]
    phrase, phrase_time = take_phrase(transcript_words, start_index, EDGE_WORDS)
    expected = nearest_offset(time_map["anchors"], time)
    found = find_phrase(phrase, tokens, times, index, None if expected is None else phrase_time + expected)
    if not found:
        return None
    return found[0] - phrase_time, found[1]


def translate_span(transcript_words: list[tuple[str, float]], time_map: dict, start: float, end: float) -> dict:
    head = edge_offset(transcript_words, time_map, start, from_end=False)
    tail = edge_offset(transcript_words, time_map, end, from_end=True)
    # An edge that no caption matches falls back to the nearest anchor, which is the coarser answer.
    head_offset = head[0] if head else nearest_offset(time_map["anchors"], start)
    tail_offset = tail[0] if tail else nearest_offset(time_map["anchors"], end)

    result: dict[str, object] = {
        "media": time_map["media"],
        "span_start": start,
        "span_end": end,
        "head_offset_seconds": None if head_offset is None else round(head_offset, 2),
        "tail_offset_seconds": None if tail_offset is None else round(tail_offset, 2),
        "matched_edges": sum(1 for edge in (head, tail) if edge),
        "aligned": False,
        "note": "",
    }
    if head_offset is None or tail_offset is None:
        result["note"] = "no anchor covers this span - the clip cannot be placed in the video"
        return result
    if abs(head_offset - tail_offset) > OFFSET_TOLERANCE_SECONDS:
        result["note"] = (
            f"the two edges disagree by {abs(head_offset - tail_offset):.1f}s - a break sits inside the clip"
        )
        return result

    # These two are the `ts_start` and `ts_end` of a SocialPostMediaSource whose `media` is this video.
    result["aligned"] = True
    result["ts_start"] = round(start + head_offset, 2)
    result["ts_end"] = round(end + tail_offset, 2)
    return result


def episode_cache_path(cache_dir: str, episode_id: str) -> str:
    """Name the file that holds the map of this episode, inside the cache directory."""
    # The id comes from the API, so keep the characters a file name carries and drop the rest.
    # Nothing that names another directory survives this, so the file stays inside the cache.
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "-", episode_id)[:100] or "episode"
    return os.path.join(cache_dir, f"{safe_id}.json")


def read_cached_map(cache_dir: str, episode_id: str) -> dict | None:
    """Read the map this episode already has, or None when the cache holds none for it."""
    try:
        with open(episode_cache_path(cache_dir, episode_id), encoding="utf-8") as handle:
            time_map = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return time_map if isinstance(time_map, dict) else None


def write_cached_map(cache_dir: str, episode_id: str, time_map: dict) -> None:
    """Save the map of this episode in a file of its own, which no other episode writes."""
    os.makedirs(cache_dir, exist_ok=True)
    # Write and rename, so that a reader never opens a file that is half written.
    with tempfile.NamedTemporaryFile("w", dir=cache_dir, delete=False, encoding="utf-8") as handle:
        json.dump(time_map, handle, ensure_ascii=False)
        temporary_path = handle.name
    os.replace(temporary_path, episode_cache_path(cache_dir, episode_id))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", metavar="MEDIA", help="Build the map of this video and print it.")
    parser.add_argument("--map", metavar="FILE", help="The map that --build wrote.")
    parser.add_argument("--cache-dir", metavar="DIR", help="Read and write the map of each built episode here.")
    parser.add_argument("--episode", metavar="ID", help="The episode id that keys this map in the cache.")
    parser.add_argument(
        "--span",
        nargs=2,
        type=float,
        metavar=("START", "END"),
        help="Translate this transcript span into the `ts_start` and `ts_end` of the video.",
    )
    args = parser.parse_args()

    transcript_words = load_transcript_words(json.loads(sys.stdin.read()))

    if args.build:
        cached = read_cached_map(args.cache_dir, args.episode) if args.cache_dir and args.episode else None
        # An episode whose video changed carries a map of the old file, which places a clip nowhere.
        if cached and cached.get("media") == args.build:
            print(f"read the map of episode {args.episode} from {args.cache_dir}", file=sys.stderr)
            print(json.dumps(cached, ensure_ascii=False))
            return 0
        time_map = build_map(transcript_words, args.build)
        print(
            f"anchored {len(time_map['anchors'])} points, {len(time_map['offset_regions'])} offset regions",
            file=sys.stderr,
        )
        if args.cache_dir and args.episode:
            write_cached_map(args.cache_dir, args.episode, time_map)
        print(json.dumps(time_map, ensure_ascii=False))
        return 0

    if not args.span or not args.map:
        parser.error("--span needs --map, and --build needs neither")
    with open(args.map, encoding="utf-8") as handle:
        time_map = json.load(handle)
    print(json.dumps(translate_span(transcript_words, time_map, *args.span), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
