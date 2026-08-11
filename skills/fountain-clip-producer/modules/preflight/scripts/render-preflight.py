#!/usr/bin/env python3
"""Validate that the current environment can actually render what's being
asked for, before spending time on a full render. Checks ffmpeg/ffprobe
presence, required filters, which caption renderer is available, which
ffmpeg carries the whisper filter that times the words of the clip, and
which python interpreter carries a cv2 new enough for the framing module's
face detection and visual-person-qa.py.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_FILTERS = {
    "core": {"crop", "scale", "overlay", "fps", "format"},
    "subtitle": {"ass", "subtitles"},
    "text": {"drawtext"},
    "words": {"whisper"},
}


def run(cmd):
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def ffmpeg_filters(ffmpeg):
    proc = run([ffmpeg, "-hide_banner", "-filters"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffmpeg -filters failed")
    filters = set()
    for line in proc.stdout.splitlines():
        parts = line.split()
        for idx, part in enumerate(parts):
            if "->" in part and idx > 0:
                filters.add(parts[idx - 1])
                break
    return filters


def ffmpeg_encoders(ffmpeg):
    proc = run([ffmpeg, "-hide_banner", "-encoders"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffmpeg -encoders failed")
    return proc.stdout


def bundled_families(fonts_dir):
    """Family names of the fonts the skill ships, read from the files themselves.

    libass is handed this directory with fontsdir, so a family it holds needs
    no system install and must not be reported as missing.
    """
    families = {}
    for path in sorted(Path(fonts_dir).glob("*.[to]t[fc]")):
        try:
            proc = run(["fc-scan", "--format", "%{family}", str(path)])
        except OSError:
            return families
        if proc.returncode == 0:
            for family in proc.stdout.split(","):
                families.setdefault(family.strip().lower(), str(path))
    return families


def check_font(name, bundled=None):
    """Resolve a font family name the same way libass will at render time.

    fc-match falls back to a default family instead of erroring when a font
    isn't installed, so a resolved family name that doesn't contain the
    requested one means the render would silently use the wrong font.

    Caught locally: if fc-match itself isn't installed, subprocess.run raises
    OSError regardless of check=False (that's a process-spawn failure, not a
    return code) -- letting that propagate out of this function would abort
    the entire preflight run inside main()'s single try/except, silently
    skipping every check that comes after the font loop (e.g. --media).
    """
    if bundled and name.strip().lower() in bundled:
        return {"requested": name, "resolved": name, "matched": True, "source": bundled[name.strip().lower()]}
    try:
        proc = run(["fc-match", name])
    except OSError as exc:
        return {"requested": name, "resolved": None, "matched": False, "error": f"fc-match not runnable: {exc}"}
    if proc.returncode != 0:
        return {"requested": name, "resolved": None, "matched": False}
    match = re.search(r'"([^"]+)"', proc.stdout)
    resolved = match.group(1) if match else None
    matched = bool(resolved) and name.split()[0].lower() in resolved.lower()
    return {"requested": name, "resolved": resolved, "matched": matched}


# Where a second ffmpeg build tends to sit, per platform. A stock build is
# sometimes compiled without libass while a capable sibling is already
# installed, so finding it beats reporting the filter missing.
SIBLING_FFMPEG = (
    "/opt/homebrew/opt/ffmpeg*/bin/ffmpeg",  # macOS, Apple silicon Homebrew
    "/usr/local/opt/ffmpeg*/bin/ffmpeg",  # macOS, Intel Homebrew
    "/usr/local/bin/ffmpeg*",  # a static build dropped in by hand
    "/usr/bin/ffmpeg*",  # a distribution package
    "/snap/bin/ffmpeg*",  # Ubuntu snap
    "/var/lib/flatpak/exports/bin/ffmpeg*",  # flatpak
    "/opt/ffmpeg*/bin/ffmpeg",  # an unpacked release build
)


def find_capable_ffmpeg(group, exclude):
    """Find another ffmpeg on this machine that carries a filter of one group."""
    candidates = []
    for pattern in SIBLING_FFMPEG:
        candidates.extend(sorted(Path("/").glob(pattern.lstrip("/"))))
    for candidate in candidates:
        candidate = str(candidate)
        if candidate == exclude:
            continue
        try:
            if ffmpeg_filters(candidate).intersection(REQUIRED_FILTERS[group]):
                return candidate
        except (RuntimeError, OSError):
            continue
    return None


# Where a whisper.cpp model tends to sit. The ffmpeg whisper filter takes the
# path of one, and a build with the filter and no model transcribes nothing.
WHISPER_MODEL = (
    "opt/homebrew/share/whisper.cpp/models/ggml-*.bin",  # macOS, Apple silicon Homebrew
    "usr/local/share/whisper.cpp/models/ggml-*.bin",  # macOS, Intel Homebrew
    "usr/share/whisper.cpp/models/ggml-*.bin",  # a distribution package
    "opt/whisper.cpp/models/ggml-*.bin",  # an unpacked release build
)


def find_whisper_model(explicit):
    """Find a whisper.cpp model file, which the whisper filter cannot work without."""
    if explicit:
        return str(explicit) if Path(explicit).is_file() else None
    home = Path.home() / ".cache" / "whisper"
    candidates = [p for pattern in WHISPER_MODEL for p in sorted(Path("/").glob(pattern))]
    candidates += sorted(home.glob("ggml-*.bin")) if home.is_dir() else []
    return str(candidates[0]) if candidates else None


def probe(ffprobe, media):
    proc = run(
        [
            ffprobe,
            "-hide_banner",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(media),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe failed for {media}")
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg")
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe") or "ffprobe")
    parser.add_argument("--media", help="Optional source or clean master to probe.")
    parser.add_argument("--require-subtitles", action="store_true")
    parser.add_argument(
        "--require-words",
        action="store_true",
        help="Fail if no ffmpeg carries the whisper filter, or if no whisper model file is found.",
    )
    parser.add_argument(
        "--whisper-model",
        help="Path of the whisper.cpp model to time words with. Searched for when not given.",
    )
    parser.add_argument("--require-magick", action="store_true")
    parser.add_argument(
        "--require-visual-qa",
        action="store_true",
        help="Fail if no python with cv2 4.8+ is found for framing's face detection and visual-person-qa.py.",
    )
    parser.add_argument(
        "--fonts",
        help="Comma-separated font family names a caption preset "
        "needs (see the fonts module) — fails if any resolves to a "
        "fallback family instead of the requested one.",
    )
    parser.add_argument(
        "--fonts-dir",
        default=str(Path(__file__).resolve().parents[3] / "assets" / "fonts"),
        help="Directory of bundled fonts that libass is given with fontsdir. Defaults to the skill's own.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = {
        "ffmpeg": args.ffmpeg,
        "ffprobe": args.ffprobe,
        "ok": False,
        "caption_renderer": None,
        "ffmpeg_for_words": None,
        "visual_qa_python": None,
        "missing": [],
        "filters": {},
        "fonts": [],
        "media": None,
    }

    try:
        filters = ffmpeg_filters(args.ffmpeg)
        encoders = ffmpeg_encoders(args.ffmpeg)
        for group, names in REQUIRED_FILTERS.items():
            report["filters"][group] = sorted(filters.intersection(names))

        missing_core = sorted(REQUIRED_FILTERS["core"] - filters)
        if missing_core:
            report["missing"].extend(f"ffmpeg filter:{name}" for name in missing_core)

        has_subtitles = bool(filters.intersection(REQUIRED_FILTERS["subtitle"]))
        has_drawtext = "drawtext" in filters
        has_qtrle = "qtrle" in encoders

        alt = None
        if not has_subtitles:
            alt = find_capable_ffmpeg("subtitle", exclude=args.ffmpeg)
            report["ffmpeg_with_subtitles"] = alt
            if args.require_subtitles and not alt:
                report["missing"].append(
                    "ffmpeg filter:ass-or-subtitles (no alternate libass-capable ffmpeg found on this machine)"
                )

        # A capable sibling build keeps us on the ASS path: it is the best renderer,
        # so finding one must upgrade the recommendation, not just report the binary.
        if has_subtitles:
            report["caption_renderer"] = "ass"
            report["ffmpeg_for_captions"] = args.ffmpeg
        elif alt:
            report["caption_renderer"] = "ass"
            report["ffmpeg_for_captions"] = alt
        elif has_drawtext:
            report["caption_renderer"] = "drawtext"
            report["ffmpeg_for_captions"] = args.ffmpeg
        elif has_qtrle:
            report["caption_renderer"] = "precomposited-alpha-video"
            report["ffmpeg_for_captions"] = args.ffmpeg
        else:
            report["missing"].append("caption renderer:ass/subtitles, drawtext, or qtrle alpha video")

        # Word timings come from whisper on the clip's own audio, so a build
        # without it stops captions, trims and shots after the master is cut.
        if "whisper" in filters:
            report["ffmpeg_for_words"] = args.ffmpeg
        else:
            report["ffmpeg_for_words"] = find_capable_ffmpeg("words", exclude=args.ffmpeg)
            if args.require_words and not report["ffmpeg_for_words"]:
                report["missing"].append("ffmpeg filter:whisper (no whisper-capable ffmpeg found on this machine)")

        # The filter alone transcribes nothing: it takes a whisper.cpp model file,
        # and with none it loads its backend and then hangs rather than failing.
        report["whisper_model"] = find_whisper_model(args.whisper_model)
        if args.require_words and not report["whisper_model"]:
            report["missing"].append("whisper model (the whisper filter takes a model file and hangs without one)")

        if args.require_magick and not shutil.which("magick"):
            report["missing"].append("magick")

        # Find a python interpreter with cv2 for framing's visual-person-qa.py
        # and extract-face-framing.py. Check the current interpreter first,
        # then a project .venv if one exists nearby. FaceDetectorYN arrived in
        # OpenCV 4.8, and an older build imports cleanly but cannot detect.
        candidates = [sys.executable]
        for venv in (Path.cwd() / ".venv", Path(__file__).resolve().parents[3] / ".venv"):
            venv_python = venv / "bin" / "python"
            if venv_python.exists():
                candidates.append(str(venv_python))
        for candidate in candidates:
            proc = run([candidate, "-c", "import cv2; cv2.FaceDetectorYN"])
            if proc.returncode == 0:
                report["visual_qa_python"] = candidate
                break
        if report["visual_qa_python"] is None and args.require_visual_qa:
            report["missing"].append("python with cv2 4.8+ (for framing's face detection and visual QA)")

        if args.fonts:
            bundled = bundled_families(args.fonts_dir) if Path(args.fonts_dir).is_dir() else {}
            for name in [f.strip() for f in args.fonts.split(",") if f.strip()]:
                result = check_font(name, bundled)
                report["fonts"].append(result)
                if not result["matched"]:
                    detail = result.get("error") or f"resolved to {result['resolved'] or 'nothing'}"
                    report["missing"].append(f"font:{name} ({detail})")

        if args.media:
            report["media"] = probe(args.ffprobe, Path(args.media))

        report["ok"] = not report["missing"]
    except Exception as exc:
        report["missing"].append(str(exc))

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"render preflight: {'PASS' if report['ok'] else 'FAIL'}")
        print(f"ffmpeg: {report['ffmpeg']}")
        print(f"ffprobe: {report['ffprobe']}")
        print(f"caption renderer: {report['caption_renderer'] or 'none'}")
        if report.get("ffmpeg_for_captions") and report["ffmpeg_for_captions"] != report["ffmpeg"]:
            print(f"burn captions with: {report['ffmpeg_for_captions']}")
        for font in report["fonts"]:
            status = "OK" if font["matched"] else "FALLBACK"
            print(f"font '{font['requested']}': {status} (resolved: {font['resolved'] or 'none'})")
        if report["missing"]:
            print("missing:")
            for item in report["missing"]:
                print(f"- {item}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
