#!/usr/bin/env python3
"""Match podcast episodes that have no video to the videos on the show's YouTube channel.

Lists the channel one time, then scores every episode against that list on title, guest, and duration.
A show often rewrites a title for YouTube but keeps the guest name, so the guest is the stronger signal.
Reads a JSON array of ContentHit on stdin, and uses `info.title`, `info.published` and `info.duration`
of each one. Prints a JSON array of matches on stdout, and writes no files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher

STOPWORDS_PATTERN = r"\b(the|a|an|and|with|to|for|of|in|on|is|are|as|your|you|this|that|it|its)\b"
GUEST_PATTERN = r"\s+(?:with|w/|ft\.?|feat\.?)\s+(.+)$"
# A show repeats a segment title with the same guest, so the date is read for the best few candidates.
DATE_CHECK_TOP = 4
# A podcast uploads its video within days of the feed, so a wider gap is a different episode.
MAX_DATE_DELTA_DAYS = 45


@dataclass
class Episode:
    title: str
    pub_date_iso: str
    duration_seconds: int | None
    episode_number: int | None = None
    guest: str | None = None


@dataclass
class Video:
    video_id: str
    title: str
    duration_seconds: int | None
    channel: str
    upload_date_iso: str = ""
    url: str = field(default="")

    def __post_init__(self) -> None:
        self.url = f"https://www.youtube.com/watch?v={self.video_id}"


def normalize_title(value: str) -> str:
    value = value.lower()
    value = re.sub(r"^\s*#?\s*\d+\s*[:.-]\s*", "", value)
    value = value.replace("&", " and ")
    value = re.sub(r"[’'`]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(STOPWORDS_PATTERN, " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_episode_number(title: str) -> int | None:
    match = re.search(r"#\s*(\d+)|\b(?:ep|episode)\.?\s*(\d+)\b|^\s*(\d+)\s*:", title, re.IGNORECASE)
    if not match:
        return None
    return int(next(group for group in match.groups() if group))


def parse_guest(title: str) -> str | None:
    """Take the guest name out of a feed title, because a rewritten YouTube title usually keeps it."""
    match = re.search(GUEST_PATTERN, title, re.IGNORECASE)
    if not match:
        return None
    guest = re.split(r"\s*[,&|]|\s+and\s+", match.group(1))[0].strip()
    return guest if len(guest.split()) >= 2 else None


def run_yt_dlp(arguments: list[str]) -> list[dict]:
    result = subprocess.run(["yt-dlp", *arguments], check=False, text=True, capture_output=True)
    if result.returncode != 0 and not result.stdout.strip():
        last_error = (result.stderr.strip().splitlines() or ["no error output"])[-1]
        raise SystemExit(f"find-episode-video: yt-dlp failed - {last_error}")
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def listing_urls(channel: str) -> list[str]:
    """Build the channel URLs to try, because a show is named by handle, by id, or by plain name."""
    value = channel.strip()
    if value.startswith("http"):
        return [value if value.rstrip("/").endswith("/videos") else f"{value.rstrip('/')}/videos"]
    if value.startswith("UC"):
        return [f"https://www.youtube.com/channel/{value}/videos"]
    handle = value.lstrip("@")
    return [f"https://www.youtube.com/@{handle}/videos"]


def discover_channel_url(channel: str) -> str | None:
    """Find the channel id with one search, for a show named by a plain name."""
    for item in run_yt_dlp(["--dump-json", "--skip-download", f"ytsearch3:{channel}"]):
        if item.get("channel_id") and normalize_title(item.get("channel") or "") == normalize_title(channel):
            return f"https://www.youtube.com/channel/{item['channel_id']}/videos"
    return None


def list_channel(channel: str, limit: int) -> list[Video]:
    """List the channel one time. The flat listing has no upload date, which the tie-break adds later."""
    urls = listing_urls(channel)
    # A limit of 0 lists the whole channel, which stays cheap because a flat listing skips per-video work.
    bound = ["--playlist-end", str(limit)] if limit > 0 else []
    for url in urls:
        rows = run_yt_dlp(["--flat-playlist", "--dump-json", *bound, url])
        if rows:
            return [
                Video(
                    video_id=row["id"],
                    title=row.get("title") or "",
                    duration_seconds=row.get("duration"),
                    channel=row.get("channel") or row.get("uploader") or "",
                )
                for row in rows
                if row.get("id")
            ]
    discovered = discover_channel_url(channel)
    if discovered:
        return list_channel(discovered, limit)
    return []


def add_upload_dates(videos: list[Video]) -> None:
    """Read the upload date of a few videos, because only a full extraction reports it."""
    for video in videos:
        if video.upload_date_iso:
            continue
        rows = run_yt_dlp(["--dump-json", "--skip-download", video.url])
        raw = (rows[0].get("upload_date") if rows else "") or ""
        if raw:
            video.upload_date_iso = datetime.strptime(raw, "%Y%m%d").date().isoformat()


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

    guest_match = bool(episode.guest) and episode.guest.lower() in video.title.lower()
    score = (title_score * 72) + (duration_score * 16) + (date_score * 12)
    if episode.episode_number is not None and re.search(rf"\b{episode.episode_number}\b", video.title):
        score += 20
    if guest_match:
        score += 25
    details = {
        "title_similarity": round(title_score, 3),
        "guest_match": guest_match,
        "duration_delta_seconds": duration_delta,
        "date_delta_days": date_delta,
    }
    return min(score, 100.0), details


def confidence_tier(score: float, details: dict[str, object]) -> str:
    # Thresholds tuned on English-language shows; treat them as heuristics, not ground truth.
    title_similarity = float(details["title_similarity"])
    duration_delta = details["duration_delta_seconds"]
    date_delta = details["date_delta_days"]

    # A recurring segment repeats its title, its guest and its length, so only the date tells two apart.
    if date_delta is None or date_delta > MAX_DATE_DELTA_DAYS:
        return "unmatched"

    close_duration = duration_delta is not None and duration_delta <= 240
    loose_duration = duration_delta is not None and duration_delta <= 600
    close_date = date_delta <= 14
    same_week = date_delta <= 3
    wide_duration = duration_delta is not None and duration_delta <= 900
    near_duration = duration_delta is not None and duration_delta <= 300

    # A rewritten title keeps the guest, so the guest plus a close duration is as good as a title match.
    if close_date and (details["guest_match"] and close_duration):
        return "high"
    if close_date and (
        score >= 72 or (title_similarity >= 0.55 and close_duration) or (title_similarity >= 0.78 and loose_duration)
    ):
        return "high"
    if (
        score >= 58
        or (details["guest_match"] and loose_duration)
        or (title_similarity >= 0.45 and close_date)
        or (title_similarity >= 0.62 and wide_duration)
        or (title_similarity >= 0.22 and same_week and near_duration)
    ):
        return "medium"
    if score >= 48 and date_delta <= 10:
        return "low"
    return "unmatched"


def parse_episode(hit: dict) -> Episode:
    """Read the three fields of a ContentHit that the match uses, all of them on `info`."""
    info = hit.get("info") or {}
    title = info.get("title") or ""
    duration = info.get("duration")
    return Episode(
        title=title,
        pub_date_iso=str(info.get("published") or "")[:10],
        duration_seconds=int(duration) if duration else None,
        episode_number=parse_episode_number(title),
        guest=parse_guest(title),
    )


def match_episode(episode: Episode, videos: list[Video]) -> dict[str, object]:
    row: dict[str, object] = {"title": episode.title, "published": episode.pub_date_iso}
    if not videos:
        return {**row, "match_confidence": "unmatched", "note": "the channel listing is empty"}

    scored = sorted(((*score_pair(episode, video), video) for video in videos), key=lambda item: -item[0])
    # The flat listing carries no date, and a high title and guest score is exactly when a
    # recurring segment matches the wrong year, so always read the date of the best few.
    best = [video for _, _, video in scored[:DATE_CHECK_TOP]]
    add_upload_dates(best)
    scored = sorted(((*score_pair(episode, video), video) for video in best), key=lambda item: -item[0])

    best_score, best_details, best_video = scored[0]
    tier = confidence_tier(best_score, best_details)
    if tier == "unmatched":
        return {**row, "match_confidence": "unmatched", "note": "no video passed the confidence bar"}
    return {
        **row,
        "youtube_video_id": best_video.video_id,
        "youtube_url": best_video.url,
        "youtube_title": best_video.title,
        "youtube_upload_date": best_video.upload_date_iso,
        "youtube_duration_seconds": best_video.duration_seconds,
        "match_confidence": tier,
        "match_score": round(best_score, 1),
        **best_details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True, help="The show's YouTube channel URL, @handle, id, or name.")
    parser.add_argument("--listing-size", type=int, default=0, help="Videos to list. Default: 0, the whole channel.")
    args = parser.parse_args()

    episodes = json.loads(sys.stdin.read())
    if not isinstance(episodes, list) or not episodes:
        raise SystemExit("find-episode-video: stdin must hold a non-empty JSON array of ContentHit")

    videos = list_channel(args.channel, args.listing_size)
    print(f"listed {len(videos)} videos from {args.channel}", file=sys.stderr)
    rows = [match_episode(parse_episode(item), videos) for item in episodes]
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
