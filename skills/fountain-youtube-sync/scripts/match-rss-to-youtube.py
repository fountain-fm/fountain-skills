#!/usr/bin/env python3
"""Match podcast RSS feed episodes to a show's public YouTube videos."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
STOPWORDS_PATTERN = r"\b(the|a|an|and|with|to|for|of|in|on|is|are|as|your|you|this|that|it|its)\b"
CONFIDENCE_TIERS = ["high", "medium", "low", "unmatched"]
DEFAULT_OUT_ROOT = Path("fountain") / "outputs" / "youtube-sync"


@dataclass
class Episode:
    episode_number: int | None
    title: str
    pub_date_iso: str
    duration_seconds: int | None
    guid: str
    link: str


@dataclass
class Video:
    video_id: str
    title: str
    upload_date_iso: str
    duration_seconds: int | None
    url: str


def normalize_title(value: str) -> str:
    value = value.lower()
    value = re.sub(r"^\s*\d+\s*[:.-]\s*", "", value)
    value = value.replace("&", " and ")
    value = re.sub(r"[’'`]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(STOPWORDS_PATTERN, " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return int(value)
    parts = value.split(":")
    if not all(part.isdigit() for part in parts):
        return None
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + int(part)
    return seconds


def parse_episode_number(title: str) -> int | None:
    match = re.match(r"\s*(\d+)\s*:", title)
    return int(match.group(1)) if match else None


def fetch_rss(rss_url: str) -> list[Episode]:
    data = urllib.request.urlopen(rss_url, timeout=60).read()
    channel = ET.fromstring(data).find("channel")
    if channel is None:
        raise SystemExit(f"match: no <channel> element in feed {rss_url}")
    episodes: list[Episode] = []
    for item in channel.findall("item"):
        title = item.findtext("title") or ""
        pub_dt = parsedate_to_datetime(item.findtext("pubDate") or "")
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=UTC)
        episodes.append(
            Episode(
                episode_number=parse_episode_number(title),
                title=title,
                pub_date_iso=pub_dt.date().isoformat(),
                duration_seconds=parse_duration(item.findtext(f"{ITUNES_NS}duration")),
                guid=item.findtext("guid") or "",
                link=item.findtext("link") or "",
            )
        )
    return episodes


def parse_video_lines(lines: list[str]) -> list[Video]:
    videos: list[Video] = []
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        upload_date = item.get("upload_date") or ""
        upload_iso = datetime.strptime(upload_date, "%Y%m%d").date().isoformat() if upload_date else ""
        video_id = item["id"]
        videos.append(
            Video(
                video_id=video_id,
                title=item.get("title") or "",
                upload_date_iso=upload_iso,
                duration_seconds=item.get("duration"),
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        )
    return videos


def load_videos(youtube_sources: list[str], cache_paths: list[Path]) -> list[Video]:
    # Merge every source and drop duplicate video ids, because channel tabs and playlists overlap only partly.
    merged: dict[str, Video] = {}
    for cache_path in cache_paths:
        for video in parse_video_lines(cache_path.read_text(encoding="utf-8").splitlines()):
            merged.setdefault(video.video_id, video)
    for youtube_source in youtube_sources:
        listing = subprocess.run(
            ["yt-dlp", "--dump-json", "--skip-download", youtube_source],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        for video in parse_video_lines(listing.stdout.splitlines()):
            merged.setdefault(video.video_id, video)
    return list(merged.values())


def score_pair(episode: Episode, video: Video) -> tuple[float, dict[str, object]]:
    episode_norm = normalize_title(episode.title)
    video_norm = normalize_title(video.title)
    ratio = SequenceMatcher(None, episode_norm, video_norm).ratio()
    episode_tokens = set(episode_norm.split())
    video_tokens = set(video_norm.split())
    token_score = len(episode_tokens & video_tokens) / max(1, len(episode_tokens | video_tokens))
    title_score = (ratio * 0.65) + (token_score * 0.35)

    duration_delta = None
    duration_score = 0.0
    if episode.duration_seconds and video.duration_seconds:
        duration_delta = abs(episode.duration_seconds - int(video.duration_seconds))
        if duration_delta <= 90:
            duration_score = 1.0
        elif duration_delta <= 240:
            duration_score = 0.75
        elif duration_delta <= 600:
            duration_score = 0.45

    date_delta = None
    date_score = 0.0
    if episode.pub_date_iso and video.upload_date_iso:
        episode_date = datetime.fromisoformat(episode.pub_date_iso).date()
        video_date = datetime.fromisoformat(video.upload_date_iso).date()
        date_delta = abs((video_date - episode_date).days)
        if date_delta <= 3:
            date_score = 1.0
        elif date_delta <= 10:
            date_score = 0.75
        elif date_delta <= 21:
            date_score = 0.45
        elif date_delta <= 45:
            date_score = 0.2

    score = (title_score * 72) + (duration_score * 16) + (date_score * 12)
    if episode.episode_number is not None and re.search(rf"\b{episode.episode_number}\b", video.title):
        score += 20
    details = {
        "title_similarity": round(title_score, 3),
        "duration_delta_seconds": duration_delta,
        "date_delta_days": date_delta,
    }
    return min(score, 100.0), details


def confidence_tier(score: float, details: dict[str, object]) -> str:
    # Thresholds tuned on English-language shows; treat them as heuristics, not ground truth.
    title_similarity = float(details["title_similarity"])
    duration_delta = details["duration_delta_seconds"]
    date_delta = details["date_delta_days"]
    close_duration = duration_delta is not None and duration_delta <= 240
    loose_duration = duration_delta is not None and duration_delta <= 600
    if score >= 72 or (title_similarity >= 0.55 and close_duration) or (title_similarity >= 0.78 and loose_duration):
        return "high"
    close_date = date_delta is not None and date_delta <= 14
    same_week = date_delta is not None and date_delta <= 3
    wide_duration = duration_delta is not None and duration_delta <= 900
    near_duration = duration_delta is not None and duration_delta <= 300
    if (
        score >= 58
        or (title_similarity >= 0.45 and close_date)
        or (title_similarity >= 0.62 and wide_duration)
        or (title_similarity >= 0.22 and same_week and near_duration)
    ):
        return "medium"
    if score >= 48 and date_delta is not None and date_delta <= 10:
        return "low"
    return "unmatched"


def default_out_dir(rss_url: str, youtube_sources: list[str]) -> Path:
    # Derive a per-show slug so two shows in one project do not overwrite each other's index.
    for youtube_source in youtube_sources:
        handle_match = re.search(r"youtube\.com/@([\w.-]+)", youtube_source)
        if handle_match:
            slug = re.sub(r"[^a-z0-9]+", "-", handle_match.group(1).lower()).strip("-")
            return DEFAULT_OUT_ROOT / (slug or "default")
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(rss_url).netloc.lower()).strip("-")
    return DEFAULT_OUT_ROOT / (slug or "default")


def build_rows(episodes: list[Episode], videos: list[Video]) -> list[dict[str, object]]:
    rows = []
    for episode in episodes:
        scored = [(*score_pair(episode, video), video) for video in videos]
        best_score, best_details, best_video = max(scored, key=lambda item: item[0])
        tier = confidence_tier(best_score, best_details)
        matched = tier != "unmatched"
        rows.append(
            {
                "episode_number": episode.episode_number,
                "rss_title": episode.title,
                "rss_pub_date": episode.pub_date_iso,
                "rss_duration_seconds": episode.duration_seconds,
                "youtube_video_id": best_video.video_id if matched else "",
                "youtube_url": best_video.url if matched else "",
                "youtube_title": best_video.title if matched else "",
                "youtube_upload_date": best_video.upload_date_iso if matched else "",
                "youtube_duration_seconds": best_video.duration_seconds if matched else "",
                "match_confidence": tier,
                "match_score": round(best_score, 1),
                **best_details,
                "rss_guid": episode.guid,
                "rss_link": episode.link,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rss-url", required=True, help="Podcast RSS feed URL.")
    parser.add_argument(
        "--youtube-source",
        dest="youtube_sources",
        action="append",
        default=[],
        help="YouTube channel /videos URL or playlist URL. Repeat to merge several sources.",
    )
    parser.add_argument(
        "--youtube-jsonl",
        dest="youtube_jsonls",
        action="append",
        type=Path,
        default=[],
        help="Cached yt-dlp JSONL dump to replay instead of a live fetch. Repeatable.",
    )
    parser.add_argument("--out-dir", type=Path, help="Output directory. Default: a per-show folder.")
    args = parser.parse_args()

    if not args.youtube_sources and not args.youtube_jsonls:
        parser.error("at least one --youtube-source or --youtube-jsonl is required")

    episodes = fetch_rss(args.rss_url)
    videos = load_videos(args.youtube_sources, args.youtube_jsonls)
    if not episodes:
        raise SystemExit("match: the RSS feed has no episodes")
    if not videos:
        raise SystemExit("match: the YouTube sources have no videos")

    rows = build_rows(episodes, videos)
    out_dir = args.out_dir or default_out_dir(args.rss_url, args.youtube_sources)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "rss-youtube-matches.csv"
    json_path = out_dir / "rss-youtube-matches.json"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "rss_url": args.rss_url,
        "youtube_sources": args.youtube_sources,
        "youtube_jsonl_caches": [str(path) for path in args.youtube_jsonls],
        "rss_episode_count": len(episodes),
        "youtube_video_count": len(videos),
        "confidence_counts": {
            tier: sum(1 for row in rows if row["match_confidence"] == tier) for tier in CONFIDENCE_TIERS
        },
        "outputs": [str(csv_path), str(json_path)],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
