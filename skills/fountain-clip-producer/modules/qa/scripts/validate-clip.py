#!/usr/bin/env python3
"""The blocking QA gate for a produced clip. Aggregates whole-clip checks
(dimensions, fps, duration, audio presence, black-frame regression) with the
per-module reports handed up from framing (visual QA) and captions (fit
report) into a single qa_report.json. Does not redo those per-module checks —
only confirms they exist and passed.
"""

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def ffprobe(path, count_frames=False):
    cmd = ["ffprobe", "-hide_banner", "-v", "error"]
    if count_frames:
        cmd.append("-count_frames")
    cmd += [
        "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,duration,nb_read_frames,pix_fmt",
        "-of",
        "json",
        str(path),
    ]
    proc = run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe failed for {path}")
    return json.loads(proc.stdout)


def parse_fps(value):
    if not value or value == "0/0":
        return None
    if "/" in value:
        num, den = value.split("/", 1)
        den_value = float(den)
        return float(num) / den_value if den_value else None
    return float(value)


def video_stream(probe):
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    return None


def audio_streams(probe):
    return [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"]


def blackdetect(path):
    proc = run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-vf", "blackdetect=d=0.05:pix_th=0.10", "-an", "-f", "null", "-"]
    )
    text = f"{proc.stdout}\n{proc.stderr}"
    intervals = []
    pattern = re.compile(r"black_start:([0-9.]+) black_end:([0-9.]+) black_duration:([0-9.]+)")
    for match in pattern.finditer(text):
        intervals.append(
            {"start": float(match.group(1)), "end": float(match.group(2)), "duration": float(match.group(3))}
        )
    return intervals


def covered(interval, baselines, tolerance=0.04):
    return any(
        interval["start"] >= baseline["start"] - tolerance and interval["end"] <= baseline["end"] + tolerance
        for baseline in baselines
    )


def add_check(checks, name, passed, detail):
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": detail})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-master", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--caption-layer")
    parser.add_argument("--caption-fit-report")
    parser.add_argument("--expected-width", type=int, required=True)
    parser.add_argument("--expected-height", type=int, required=True)
    parser.add_argument("--expected-fps", type=float, required=True)
    parser.add_argument("--expected-duration", type=float, required=True)
    parser.add_argument(
        "--landscape-master",
        help="clip-landscape-master.mp4 from module media. Its height is the real detail behind the export.",
    )
    parser.add_argument(
        "--max-upscale",
        type=float,
        default=2.0,
        help="Largest allowed ratio of delivered height to clean-master height. 2.0 passes a 1080p source "
        "for a 1920-tall delivery and fails a 720p one.",
    )
    parser.add_argument("--contact-sheet")
    parser.add_argument("--visual-report", help="visual_qa_report.json produced by the framing module")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    checks = []
    report = {
        "status": "fail",
        "cleanMaster": args.clean_master,
        "final": args.final,
        "captionLayer": args.caption_layer,
        "captionFitReport": args.caption_fit_report,
        "checks": checks,
    }

    try:
        clean_probe = ffprobe(args.clean_master, count_frames=True)
        final_probe = ffprobe(args.final, count_frames=True)
        clean_video = video_stream(clean_probe)
        final_video = video_stream(final_probe)
        if not clean_video or not final_video:
            raise RuntimeError("missing video stream")

        final_fps = parse_fps(final_video.get("r_frame_rate"))
        final_duration = float(final_probe.get("format", {}).get("duration", 0))
        final_frames = int(final_video.get("nb_read_frames", 0))
        expected_frames = int(round(args.expected_duration * args.expected_fps))

        add_check(
            checks,
            "final_dimensions",
            final_video.get("width") == args.expected_width and final_video.get("height") == args.expected_height,
            {
                "actual": [final_video.get("width"), final_video.get("height")],
                "expected": [args.expected_width, args.expected_height],
            },
        )
        # A vertical crop keeps the whole height of the landscape master, so
        # that height is the real detail behind the delivered one. The container
        # reports 1080x1920 either way, which is how a 720p source shipped as
        # 1080p until this check existed. The clean master is already vertical,
        # so it cannot answer this -- only the landscape one can.
        if args.landscape_master:
            landscape_video = video_stream(ffprobe(args.landscape_master)) or {}
            source_height = landscape_video.get("height") or 0
            upscale = (args.expected_height / source_height) if source_height else None
            add_check(
                checks,
                "source_resolution",
                upscale is not None and upscale <= args.max_upscale,
                {
                    "sourceHeight": source_height,
                    "finalHeight": args.expected_height,
                    "upscale": round(upscale, 2) if upscale else None,
                    "maxUpscale": args.max_upscale,
                },
            )
        add_check(
            checks,
            "final_fps",
            final_fps is not None and math.isclose(final_fps, args.expected_fps, abs_tol=0.01),
            {"actual": final_video.get("r_frame_rate"), "expected": args.expected_fps},
        )
        add_check(
            checks,
            "final_duration",
            math.isclose(final_duration, args.expected_duration, abs_tol=0.25),
            {"actual": final_duration, "expected": args.expected_duration},
        )
        add_check(
            checks,
            "final_frame_count",
            abs(final_frames - expected_frames) <= 1,
            {"actual": final_frames, "expected": expected_frames},
        )
        add_check(
            checks,
            "final_audio_present",
            bool(audio_streams(final_probe)),
            {"audioStreams": len(audio_streams(final_probe))},
        )

        if args.caption_layer:
            layer_probe = ffprobe(args.caption_layer, count_frames=True)
            layer_video = video_stream(layer_probe)
            if not layer_video:
                raise RuntimeError("caption layer missing video stream")
            layer_fps = parse_fps(layer_video.get("r_frame_rate"))
            layer_duration = float(layer_video.get("duration") or layer_probe.get("format", {}).get("duration", 0))
            layer_frames = int(layer_video.get("nb_read_frames", 0))
            add_check(
                checks,
                "caption_layer_dimensions",
                layer_video.get("width") == args.expected_width and layer_video.get("height") == args.expected_height,
                {
                    "actual": [layer_video.get("width"), layer_video.get("height")],
                    "expected": [args.expected_width, args.expected_height],
                },
            )
            add_check(
                checks,
                "caption_layer_alpha",
                layer_video.get("pix_fmt") in {"argb", "rgba", "yuva420p", "yuva444p"},
                {"actual": layer_video.get("pix_fmt")},
            )
            add_check(
                checks,
                "caption_layer_fps",
                layer_fps is not None and math.isclose(layer_fps, args.expected_fps, abs_tol=0.01),
                {"actual": layer_video.get("r_frame_rate"), "expected": args.expected_fps},
            )
            add_check(
                checks,
                "caption_layer_duration",
                math.isclose(layer_duration, args.expected_duration, abs_tol=0.05),
                {"actual": layer_duration, "expected": args.expected_duration},
            )
            add_check(
                checks,
                "caption_layer_frame_count",
                abs(layer_frames - expected_frames) <= 1,
                {"actual": layer_frames, "expected": expected_frames},
            )

        if args.caption_fit_report:
            fit_path = Path(args.caption_fit_report)
            fit_report = json.loads(fit_path.read_text()) if fit_path.exists() else []
            violations = []
            for item in fit_report:
                max_width = int(item.get("maxWidth", 0))
                line_widths = item.get("lineWidths", [])
                widest = max(line_widths) if line_widths else 0
                if widest > max_width:
                    violations.append(
                        {
                            "text": item.get("text"),
                            "plate": item.get("plate"),
                            "maxWidth": max_width,
                            "widestLine": widest,
                            "lineWidths": line_widths,
                        }
                    )
            report["captionFit"] = {"path": str(fit_path), "items": len(fit_report), "violations": violations}
            point_sizes = sorted({item.get("pointSize") for item in fit_report if item.get("pointSize")})
            add_check(
                checks,
                "caption_text_fit",
                fit_path.exists() and bool(fit_report) and not violations,
                {"path": str(fit_path), "items": len(fit_report), "violations": violations},
            )
            add_check(
                checks,
                "caption_font_size_consistency",
                len(point_sizes) == 1,
                {"path": str(fit_path), "pointSizes": point_sizes},
            )

        clean_black = blackdetect(args.clean_master)
        final_black = blackdetect(args.final)
        introduced_black = [interval for interval in final_black if not covered(interval, clean_black)]
        report["blackdetect"] = {"clean": clean_black, "final": final_black, "introduced": introduced_black}
        add_check(checks, "no_new_black_intervals", not introduced_black, {"introduced": introduced_black})

        if args.contact_sheet:
            contact_sheet = Path(args.contact_sheet)
            add_check(
                checks,
                "contact_sheet_exists",
                contact_sheet.exists() and contact_sheet.stat().st_size > 0,
                {"path": str(contact_sheet)},
            )

        if args.visual_report:
            visual_path = Path(args.visual_report)
            visual = json.loads(visual_path.read_text()) if visual_path.exists() else {"status": "missing"}
            report["visualPersonQa"] = visual
            add_check(
                checks,
                "visual_person_qa",
                visual.get("status") == "pass",
                {
                    "path": str(visual_path),
                    "status": visual.get("status"),
                    "missingCount": visual.get("missingCount"),
                    "missing": visual.get("missing", []),
                },
            )

        report["status"] = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    except Exception as exc:
        report["error"] = str(exc)

    Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
