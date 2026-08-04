#!/usr/bin/env python3
"""Render a daily social performance report from one normalized snapshot.

The snapshot is agent-built (see skill fountain-stats) from a fresh API fetch each run:
{
  "date": "2026-07-29", "asOf": "2026-07-29T05:58:12Z", "show": "Show Name",
  "channels": [{"platform": "x", "views_7d": 100, "engagement_7d": 10, "error": "optional reason"}],
  "posts": [{"id": "p1", "clip": "C1", "title": "...", "episode_title": "...", "platform": "x",
             "narrative": "...", "hook_style": "...", "length_s": 30, "posted_at": "ISO datetime",
             "in_24h": true, "metrics": {"views": 100, "likes": 10, "comments": 1}}],
  "failed": [{"platform": "x", "posted_at": "ISO datetime", "in_24h": true,
              "narrative": "...", "error": "..."}],
  "recommendations": ["..."]
}
"posts" holds every post of the last 7 days with its cumulative metrics as the platform reports them now.
Baselines are computed inside the snapshot: the median engagement rate of the posts older than 24 hours per platform.
Metrics may also carry impressions, replies, reposts, shares, and saves when the source exposes them.
A missing metric stays absent or null - never zero-filled.
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import date, timedelta
from pathlib import Path

PLATFORM_NAMES = {
    "x": "X",
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "threads": "Threads",
}
ENGAGEMENT_KEYS = ("likes", "replies", "reposts", "shares", "saves", "comments")
# Claims from buckets smaller than this are marked low confidence, so a fluke cannot drive choices.
MIN_BUCKET_SIZE = 3


def platform_label(platform: str) -> str:
    return PLATFORM_NAMES.get(platform, platform)


def reach(metrics: dict) -> int:
    return metrics.get("impressions") or metrics.get("views") or 0


def engagement(metrics: dict) -> int:
    return sum(metrics.get(key) or 0 for key in ENGAGEMENT_KEYS)


def engagement_rate(metrics: dict) -> float:
    total_reach = reach(metrics)
    return engagement(metrics) / total_reach if total_reach else 0.0


def pct_change(current: float, previous: float | None) -> float | None:
    if not previous:
        return None
    return (current - previous) / previous * 100.0


def trend_arrow(change: float | None) -> str:
    if change is None or change == 0:
        return "·"
    if change >= 25:
        return "▲▲"
    if change > 0:
        return "▲"
    if change > -25:
        return "▼"
    return "▼▼"


def fmt_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value):,}"


def fmt_metric(value: float | None) -> str:
    return "—" if value is None else fmt_number(value)


def fmt_pct(change: float | None) -> str:
    return "—" if change is None else f"{change:+.0f}%"


def short_episode(title: str | None) -> str:
    return (title or "—").split(" with ")[0]


def baseline_median(posts: list[dict], platform: str) -> float | None:
    # Median over the older posts on the platform, so today's cohort is judged against prior performance.
    rates = [
        engagement_rate(post["metrics"])
        for post in posts
        if post["platform"] == platform and not post.get("in_24h") and reach(post["metrics"]) > 0
    ]
    if not rates:
        return None
    return statistics.median(rates)


def compare_buckets(groups: dict[str, list[float]], labels: dict[str, str] | None = None):
    groups = {key: rates for key, rates in groups.items() if rates}
    if len(groups) < 2:
        return None
    ranked = sorted(groups.items(), key=lambda item: -statistics.mean(item[1]))
    (top_key, top_rates), (bottom_key, bottom_rates) = ranked[0], ranked[-1]
    lift = pct_change(statistics.mean(top_rates), statistics.mean(bottom_rates))
    if lift is None or abs(lift) < 5.0:
        return None
    labels = labels or {}
    top_label = labels.get(top_key, top_key)
    bottom_label = labels.get(bottom_key, bottom_key)
    claim = f"**{top_label}** beat **{bottom_label}** by {lift:+.0f}% on engagement rate"
    if min(len(top_rates), len(bottom_rates)) < MIN_BUCKET_SIZE:
        return f"{claim} — _low confidence (n={len(top_rates)} vs n={len(bottom_rates)}), directional only._", False
    return f"{claim}.", True


def bucket_rates(posts: list[dict], bucket_fn) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = {}
    for post in posts:
        groups.setdefault(bucket_fn(post), []).append(engagement_rate(post["metrics"]))
    return groups


def length_bucket(post: dict) -> str:
    length = post.get("length_s") or 0
    if length < 25:
        return "<25s clips"
    if length <= 40:
        return "25-40s clips"
    return ">40s clips"


def render_channel_overview(today: dict, report_date: date) -> list[str]:
    lines = ["## 1. Channel Overview", "", "| Platform | Views (7d) | Engagement (7d) |", "|---|--:|--:|"]
    week_ago = report_date - timedelta(days=7)
    summed_views_used = False
    for channel in today.get("channels", []):
        platform = channel["platform"]
        if channel.get("error"):
            lines.append(f"| {platform_label(platform)} | unavailable (api error) | — |")
            continue
        # Channel analytics can under-report vs a post's own cumulative views - take whichever is higher.
        channel_views = channel.get("views_7d") or 0
        post_views = sum(
            reach(post["metrics"])
            for post in today.get("posts", [])
            if post["platform"] == platform
            and post.get("posted_at")
            and date.fromisoformat(post["posted_at"][:10]) >= week_ago
        )
        views = max(channel_views, post_views)
        marker = ""
        if post_views > channel_views:
            marker = " †"
            summed_views_used = True
        views_text = f"{fmt_number(views)}{marker}" if views else "—"
        engagement_text = fmt_metric(channel.get("engagement_7d"))
        lines.append(f"| {platform_label(platform)} | {views_text} | {engagement_text} |")
    if summed_views_used:
        lines += ["", "> † Views summed from post-level data because channel analytics are unavailable."]
    lines.append("")
    return lines


def render_recent_posts(today: dict) -> list[str]:
    all_posts = today.get("posts", [])
    cohort = [post for post in all_posts if post.get("in_24h")]
    failed = [failure for failure in today.get("failed", []) if failure.get("in_24h")]
    lines = ["## 2. Recent Posts (Last 24 Hours)", ""]
    if not cohort:
        lines.append("_No posts went live in the last 24 hours._")
    else:
        by_clip: dict[str, list[dict]] = {}
        for post in cohort:
            by_clip.setdefault(post["clip"], []).append(post)
        clip_average = {
            clip: statistics.mean(engagement_rate(post["metrics"]) for post in group) for clip, group in by_clip.items()
        }
        for clip in sorted(by_clip, key=lambda key: -clip_average[key]):
            group = by_clip[clip]
            first = group[0]
            lines += [f"### Clip {clip} — “{first['title']}”", f"_{first.get('episode_title', '—')}_", ""]
            lines += ["| Channel | Posted | Reach | Likes | Comments | Eng. rate | vs baseline |"]
            lines += ["|---|---|--:|--:|--:|--:|:--|"]
            total_reach = 0
            for post in sorted(group, key=lambda item: -engagement_rate(item["metrics"])):
                metrics = post["metrics"]
                rate = engagement_rate(metrics)
                baseline = baseline_median(all_posts, post["platform"])
                change = pct_change(rate, baseline)
                verdict = f"{trend_arrow(change)} {fmt_pct(change)}" if baseline else "(no baseline yet)"
                total_reach += reach(metrics)
                lines.append(
                    f"| {platform_label(post['platform'])} | {post['posted_at'][11:16]} | {fmt_number(reach(metrics))} "
                    f"| {fmt_metric(metrics.get('likes'))} | {fmt_metric(metrics.get('comments'))} "
                    f"| {rate * 100:.1f}% | {verdict} |"
                )
            lines.append(
                f"| **Clip total** | | **{fmt_number(total_reach)}** | | | **{clip_average[clip] * 100:.1f}% avg** | |"
            )
            lines.append("")
        lines.append(
            "> **vs baseline** = engagement rate vs the median of the show's older posts on the same platform."
        )
    if failed:
        lines += ["", f"**⚠️ {len(failed)} failed publish(es) in this window - never went live:**", ""]
        for failure in failed:
            lines.append(
                f"- **{platform_label(failure['platform'])}** at {failure['posted_at'][11:16]} "
                f"({failure.get('narrative', '—')}) — {failure.get('error', 'publish failed')}"
            )
    lines.append("")
    return lines


def render_top_posts(week_posts: list[dict]) -> list[str]:
    lines = ["## 3. Top Posts (Last 7 Days)", ""]
    if not week_posts:
        lines += ["_No posts with engagement in the last 7 days yet._", ""]
        return lines
    lines += [
        "| Rank | Title | Episode | Channel | Posted | Reach | Eng | Eng. rate |",
        "|--:|---|---|---|---|--:|--:|--:|",
    ]
    for rank, post in enumerate(sorted(week_posts, key=lambda p: -engagement_rate(p["metrics"]))[:6], 1):
        metrics = post["metrics"]
        lines.append(
            f"| {rank} | {post['title'][:24]} | {short_episode(post.get('episode_title'))} "
            f"| {platform_label(post['platform'])} | {post['posted_at'][:10]} | {fmt_number(reach(metrics))} "
            f"| {fmt_number(engagement(metrics))} | {engagement_rate(metrics) * 100:.1f}% |"
        )
    clip_rates = bucket_rates(week_posts, lambda post: post["clip"])
    best_clip = max(clip_rates, key=lambda clip: statistics.mean(clip_rates[clip]))
    best_title = next(post["title"] for post in week_posts if post["clip"] == best_clip)
    average = statistics.mean(clip_rates[best_clip]) * 100
    count = len(clip_rates[best_clip])
    lines += [
        "",
        f"- **Best clip of the week:** “{best_title}” (avg {average:.1f}% engagement across {count} post(s)).",
        "",
    ]
    return lines


def render_key_learnings(week_posts: list[dict]) -> list[str]:
    lines = ["## 4. Key Learnings", "", "**This week's patterns** (last 7 days):", ""]
    claims = [
        compare_buckets(bucket_rates(week_posts, lambda post: post.get("narrative") or "unknown")),
        compare_buckets(bucket_rates(week_posts, lambda post: post["platform"]), PLATFORM_NAMES),
        compare_buckets(bucket_rates(week_posts, lambda post: f"{post.get('hook_style') or 'unknown'} hooks")),
        compare_buckets(bucket_rates(week_posts, length_bucket)),
    ]
    claims = [claim for claim in claims if claim]
    if claims:
        actionable_count = 0
        for claim, actionable in claims:
            lines.append(f"- {claim}")
            if actionable:
                actionable_count += 1
        if not actionable_count:
            hold = f"keep current defaults until ≥{MIN_BUCKET_SIZE} posts per bucket"
            lines.append(f"- _All patterns above are low-confidence - {hold}._")
    else:
        lines.append("- _Not enough volume in the last 7 days to call a pattern yet._")
    lines.append("")
    return lines


def render(today: dict, show_name: str) -> str:
    report_date = date.fromisoformat(today["date"])
    week_posts = [post for post in today.get("posts", []) if reach(post["metrics"]) > 0]
    lines = [
        f"# {show_name} Daily Performance Report - {today['date']}",
        "",
        f"_As of {today['asOf']}. Ranked by engagement rate. Metrics are cumulative as reported at fetch time._",
        "",
    ]
    lines += render_channel_overview(today, report_date)
    lines += render_recent_posts(today)
    lines += render_top_posts(week_posts)
    lines += render_key_learnings(week_posts)
    recommendations = today.get("recommendations", [])
    lines += ["## 5. Recommendations for Today", ""]
    lines += [f"- {item}" for item in recommendations] or ["- _No recommendations generated._"]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the daily performance report from a snapshot.")
    parser.add_argument("--snapshot", required=True, type=Path, help="Path to the run's normalized snapshot JSON.")
    parser.add_argument("--show-name", help="Show name for the report header. Default: the snapshot's 'show' field.")
    args = parser.parse_args()

    today = json.loads(args.snapshot.read_text(encoding="utf-8"))
    show_name = args.show_name or today.get("show") or "Show"
    print(render(today, show_name))


if __name__ == "__main__":
    main()
