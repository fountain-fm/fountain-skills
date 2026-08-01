#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yt-dlp", "certifi"]
# ///
"""Match a show's episodes to its public YouTube videos and write a per-show match index."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from difflib import SequenceMatcher
from pathlib import Path

DEFAULT_OUT_ROOT = Path("fountain/outputs/youtube-sync")
STOPWORDS = r"\b(the|a|an|and|with|to|for|of|in|on|is|are|as|your|you|this|that|it|its)\b"
CONFIDENCE_LEVELS = ["high", "medium", "low", "unmatched"]
EMPTY_DETAILS = {"title_similarity": 0.0, "duration_delta_seconds": None, "date_delta_days": None}


@dataclass
class Episode:
    title: str
    clean_title: str
    published: date | None
    duration_seconds: int | None
    episode_number: int | None
    has_video: bool | None
    episode_id: str


@dataclass
class Video:
    video_id: str
    title: str
    uploaded: date | None
    duration_seconds: int | None
    url: str


def norm_title(value: str) -> str:
    """Lowercase the title and remove the episode number, punctuation, and common English words."""
    value = value.lower()
    value = re.sub(r"^\s*\d+\s*[:.-]\s*", "", value)
    value = value.replace("&", " and ")
    value = re.sub(r"[’'`]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(STOPWORDS, " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str | None) -> date | None:
    """Read a date from an ISO date, an ISO timestamp, or a YouTube YYYYMMDD string."""
    if not value:
        return None
    if re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value, "%Y%m%d").date()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_episode_number(title: str) -> int | None:
    match = re.match(r"\s*(\d+)\s*:", title)
    return int(match.group(1)) if match else None


def load_episodes(path: Path) -> list[Episode]:
    """Read the normalized episodes file that the agent writes from the Fountain API."""
    items = json.loads(path.read_text(encoding="utf-8"))
    episodes = []
    for item in items:
        title = item.get("title") or ""
        episodes.append(
            Episode(
                title=title,
                clean_title=re.sub(r"^\s*\d+\s*:\s*", "", title),
                published=parse_date(item.get("published")),
                duration_seconds=item.get("duration_seconds"),
                episode_number=item.get("episode_number", parse_episode_number(title)),
                has_video=item.get("has_video"),
                episode_id=item.get("id") or "",
            )
        )
    return episodes


def parse_videos(lines: list[str]) -> list[Video]:
    """Read one yt-dlp JSON object per line."""
    videos = []
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        video_id = item["id"]
        videos.append(
            Video(
                video_id=video_id,
                title=item.get("title") or "",
                uploaded=parse_date(item.get("upload_date")),
                duration_seconds=item.get("duration"),
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        )
    return videos


def fetch_videos(youtube_source: str) -> list[Video]:
    """List one YouTube channel tab or playlist with the yt-dlp module of this script's environment."""
    process = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--dump-json", "--skip-download", youtube_source],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return parse_videos(process.stdout.splitlines())


def collect_videos(youtube_sources: list[str], jsonl_paths: list[Path]) -> list[Video]:
    """Merge all sources into one list, because each source can hold videos that the others do not."""
    merged: dict[str, Video] = {}
    for jsonl_path in jsonl_paths:
        for video in parse_videos(jsonl_path.read_text(encoding="utf-8").splitlines()):
            merged.setdefault(video.video_id, video)
    for youtube_source in youtube_sources:
        for video in fetch_videos(youtube_source):
            merged.setdefault(video.video_id, video)
    return list(merged.values())


def score_pair(episode: Episode, video: Video) -> tuple[float, dict[str, object]]:
    """Score one episode against one video on title, duration, and publication date."""
    episode_norm = norm_title(episode.clean_title)
    video_norm = norm_title(video.title)
    ratio = SequenceMatcher(None, episode_norm, video_norm).ratio()
    episode_tokens = set(episode_norm.split())
    video_tokens = set(video_norm.split())
    token_score = len(episode_tokens & video_tokens) / max(1, len(episode_tokens | video_tokens))
    title_score = (ratio * 0.65) + (token_score * 0.35)

    duration_score = 0.0
    duration_delta = None
    if episode.duration_seconds and video.duration_seconds:
        duration_delta = abs(int(episode.duration_seconds) - int(video.duration_seconds))
        if duration_delta <= 90:
            duration_score = 1.0
        elif duration_delta <= 240:
            duration_score = 0.75
        elif duration_delta <= 600:
            duration_score = 0.45

    date_delta = None
    if episode.published and video.uploaded:
        date_delta = abs((video.uploaded - episode.published).days)
    date_score = 0.0
    if date_delta is not None:
        if date_delta <= 3:
            date_score = 1.0
        elif date_delta <= 10:
            date_score = 0.75
        elif date_delta <= 21:
            date_score = 0.45
        elif date_delta <= 45:
            date_score = 0.2

    score = (title_score * 72) + (duration_score * 16) + (date_score * 12)
    if episode.episode_number and re.search(rf"\b{episode.episode_number}\b", video.title):
        score += 20
    return min(score, 100.0), {
        "title_similarity": round(title_score, 3),
        "duration_delta_seconds": duration_delta,
        "date_delta_days": date_delta,
    }


def confidence(score: float, details: dict[str, object]) -> str:
    """Put the best score into a tier, with a lower bar when the duration or the date agrees closely."""
    title_similarity = float(details["title_similarity"])
    duration_delta = details["duration_delta_seconds"]
    date_delta = details["date_delta_days"]
    if (
        score >= 72
        or (title_similarity >= 0.55 and duration_delta is not None and duration_delta <= 240)
        or (title_similarity >= 0.78 and duration_delta is not None and duration_delta <= 600)
    ):
        return "high"
    if (
        score >= 58
        or (title_similarity >= 0.45 and date_delta is not None and date_delta <= 14)
        or (title_similarity >= 0.62 and duration_delta is not None and duration_delta <= 900)
        or (
            title_similarity >= 0.22
            and date_delta is not None
            and date_delta <= 3
            and duration_delta is not None
            and duration_delta <= 300
        )
    ):
        return "medium"
    if score >= 48 and date_delta is not None and date_delta <= 10:
        return "low"
    return "unmatched"


def match_episode(episode: Episode, videos: list[Video]) -> dict[str, object]:
    """Give the episode its best-scoring video, or an unmatched row when no video clears the bar."""
    scored = [(*score_pair(episode, video), video) for video in videos]
    best_score, best_details, best_video = max(scored, key=lambda item: item[0], default=(0.0, EMPTY_DETAILS, None))
    level = confidence(best_score, best_details) if best_video else "unmatched"
    matched = best_video if level != "unmatched" else None
    return {
        "episode_number": episode.episode_number,
        "episode_id": episode.episode_id,
        "episode_title": episode.title,
        "episode_published": episode.published.isoformat() if episode.published else "",
        "episode_duration_seconds": episode.duration_seconds,
        "episode_has_video": episode.has_video,
        "youtube_video_id": matched.video_id if matched else "",
        "youtube_url": matched.url if matched else "",
        "youtube_title": matched.title if matched else "",
        "youtube_uploaded": matched.uploaded.isoformat() if matched and matched.uploaded else "",
        "youtube_duration_seconds": matched.duration_seconds if matched else None,
        "match_confidence": level,
        "match_score": round(best_score, 1),
        **best_details,
    }


def latest_date(values: list[date | None]) -> str:
    known = [value for value in values if value]
    return max(known).isoformat() if known else ""


def default_slug(youtube_sources: list[str]) -> str:
    """Name the output folder after the channel handle, so two shows do not overwrite each other."""
    for youtube_source in youtube_sources:
        match = re.search(r"youtube\.com/@([\w.-]+)", youtube_source)
        if match:
            return re.sub(r"[^a-z0-9]+", "-", match.group(1).lower()).strip("-") or "default"
    return "default"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", required=True, type=Path, help="Normalized episodes JSON file.")
    parser.add_argument(
        "--youtube-source",
        dest="youtube_sources",
        action="append",
        default=[],
        metavar="URL",
        help="A YouTube channel /videos URL or playlist URL. Repeat it to merge several sources.",
    )
    parser.add_argument(
        "--youtube-jsonl",
        dest="youtube_jsonls",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help="A cached yt-dlp JSONL dump to read instead of a live source. Repeatable.",
    )
    parser.add_argument("--show-slug", help="Name of the output folder (default: the YouTube channel handle).")
    parser.add_argument("--out-dir", type=Path, help="Output directory, in full.")
    args = parser.parse_args()

    if not args.youtube_sources and not args.youtube_jsonls:
        parser.error("give at least one --youtube-source or --youtube-jsonl")

    episodes = load_episodes(args.episodes)
    videos = collect_videos(args.youtube_sources, args.youtube_jsonls)
    matches = [match_episode(episode, videos) for episode in episodes]

    slug = args.show_slug or default_slug(args.youtube_sources)
    out_dir = args.out_dir or DEFAULT_OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    matches_path = out_dir / "matches.json"
    meta = {
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "show_slug": slug,
        "youtube_sources": args.youtube_sources,
        "youtube_jsonl_caches": [str(path) for path in args.youtube_jsonls],
        "episode_count": len(episodes),
        "video_count": len(videos),
        "latest_episode_published": latest_date([episode.published for episode in episodes]),
        "latest_video_uploaded": latest_date([video.uploaded for video in videos]),
        "confidence_counts": {
            level: sum(1 for match in matches if match["match_confidence"] == level) for level in CONFIDENCE_LEVELS
        },
    }
    matches_path.write_text(
        json.dumps({"meta": meta, "matches": matches}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({**meta, "output": str(matches_path)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
