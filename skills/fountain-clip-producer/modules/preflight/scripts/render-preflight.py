#!/usr/bin/env python3
"""Validate that the current environment can actually render what's being
asked for, before spending time on a full render. Checks ffmpeg/ffprobe
presence, required filters, which caption renderer is available, which
ffmpeg carries the whisper filter that times the words of the clip, and
which python interpreter carries a cv2 new enough for the framing module's
face detection and visual-person-qa.py. It also downloads the fonts, the
face model and the overlay placeholders once, and checks each sha256.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REQUIRED_FILTERS = {
    "core": {"crop", "scale", "overlay", "fps", "format"},
    "subtitle": {"ass", "subtitles"},
    "text": {"drawtext"},
    "words": {"whisper"},
}


ASSETS_URL = "https://media.fountain.fm/clip-assets/skills/"

# Each file the local renderer reads, by its path in the assets folder and on the host, with its sha256.
# A new version of a file gets a new name, because a published path never changes.
ASSETS = {
    "fonts/anton-regular.ttf": "a4ba3a92350ebb031da0cb47630ac49eb265082ca1bc0450442f4a83ab947cab",
    "fonts/archivo-black-regular.ttf": "dd9a89a019b4849f66ab75455fe7bdf931311042cbb0f0f97acc061539703180",
    "fonts/bebas-neue-regular.ttf": "08e4623805102d819f58601e46e345648846075e363b2ceb23313c2d1c83ec73",
    "fonts/courier-prime-regular.ttf": "72f793376f8e2841656bf21d77a5de010f2929bd6956a22ee848ad0c7eb978af",
    "fonts/dm-serif-display-regular.ttf": "8cc3643535edf039aa5d95440a8542735e9197e4f4b8d9303e980fefbf5ab616",
    "fonts/montserrat-black.ttf": "ea67b37f8776eebea135cd1fe9adeaf6f9427683e8dc11ab8398b6be5f102c60",
    "fonts/montserrat-bold.ttf": "bc6e854971cea46b463be6f9eef4d9cd52f51cfc1fc0dd90c9d3e6483dc0ec61",
    "fonts/montserrat-regular.ttf": "3e8abe50c44c82e2242e97d1ec8c0d385c4890cdc50447bcdb8605c81a38cfb2",
    "fonts/permanent-marker-regular.ttf": "28f82c8a7943cb8e9d599f8554da1d4fc75dbcf69b9885ad6c0611d20c6946c5",
    "fonts/poppins-bold.ttf": "983676516167748b74de6f4771fb384c664fd913acb8b471122ecacf5da5ea6c",
    "models/face-detection-yunet-2023mar.onnx": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    "overlays/placeholder-logo.png": "2e35a1ad41710866323ef97da04ca647fd72c7746796028082e9ca31625679ea",
    "overlays/placeholder-sponsor.png": "bfd9a28eeffa029b5478f2f1aa986e3ea819751ce448a5d5e7aff2a8905b47cb",
    "licences/apache-permanent-marker.txt": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    "licences/mit-yunet.txt": "c83b8120c50ccbd4c4f96edf53141bdd566ebb8f8e9227e415326aa1b1aba958",
    "licences/ofl-anton.txt": "ee67e6ee22790b7929f1a3769ca2801d565c64b5a9096942c1adf5596de9c9e4",
    "licences/ofl-archivo-black.txt": "3173acd82f8c6159b5b1037b539fcbd4edff68e65c2ea8b9412b5a5ca97b08ff",
    "licences/ofl-bebas-neue.txt": "72082f6cb4d04be2ecf7cc7d9e1e7d73787f0af8a5a278a47cade70c16b78341",
    "licences/ofl-courier-prime.txt": "9a755af092b494944c99f471be6fddd19b006a448fefdc4717e4ee0aa09a97b0",
    "licences/ofl-dm-serif-display.txt": "a3e5cdd67d4571dd0a24fcc968de0efde7ae97ef752daf0906e4767619dd7231",
    "licences/ofl-montserrat.txt": "8b7141c03fa4f8d44e6345d5d4931709290f0f67875e452e95ac1fd3a027802e",
    "licences/ofl-poppins.txt": "6be04893d770899a015649c7aa3b582f871b272f8747a92b78b17c3e5c8b2573",
}


def clip_assets_dir():
    """The folder that this script downloads the fonts, the face model and the overlay placeholders into."""
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches"
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return root / "fountain-skills" / "clip-assets"


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def download(url, path):
    """Download a file with curl, which carries the system certificates that a bare python often lacks."""
    if shutil.which("curl"):
        proc = run(["curl", "-fsSL", "--retry", "2", "-o", str(path), url])
        if proc.returncode != 0:
            raise OSError(proc.stderr.strip() or f"curl exited with {proc.returncode}")
        return
    with urllib.request.urlopen(url, timeout=60) as response:
        Path(path).write_bytes(response.read())


def fetch_assets(assets_dir):
    """Download each asset that is absent or that fails its sha256, and return the ones that still fail."""
    failed = []
    for name, digest in ASSETS.items():
        path = Path(assets_dir) / name
        if path.is_file() and file_sha256(path) == digest:
            continue
        partial = path.with_name(path.name + ".part")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            download(ASSETS_URL + name, partial)
            if file_sha256(partial) != digest:
                partial.unlink()
                failed.append(f"asset:{name} (sha256 mismatch from {ASSETS_URL})")
                continue
            partial.replace(path)
        except OSError as exc:
            partial.unlink(missing_ok=True)
            failed.append(f"asset:{name} (download to {assets_dir} failed: {exc})")
    return failed


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
    """Family names of the fonts this script downloads, read from the files themselves.

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
# The first entry is where this skill asks the user to put it.
WHISPER_MODEL = (
    "~/.cache/whisper/ggml-*.bin",  # where the install hint below puts it
    "/opt/homebrew/share/whisper-cpp/ggml-*.bin",  # macOS, Apple silicon Homebrew
    "/usr/local/share/whisper-cpp/ggml-*.bin",  # macOS, Intel Homebrew
    "/opt/homebrew/share/whisper.cpp/models/ggml-*.bin",  # a source build, kept beside its models
    "/usr/local/share/whisper.cpp/models/ggml-*.bin",
    "/usr/share/whisper.cpp/models/ggml-*.bin",  # a distribution package
    "/opt/whisper.cpp/models/ggml-*.bin",  # an unpacked release build
)

WHISPER_MODEL_DEFAULT = "ggml-base.en.bin"
WHISPER_MODEL_INSTALL = (
    "download https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
    + WHISPER_MODEL_DEFAULT
    + " and save it as ~/.cache/whisper/"
    + WHISPER_MODEL_DEFAULT
)


def find_whisper_model(explicit):
    """Find a whisper.cpp model file, which the whisper filter cannot work without.

    A `for-tests` blob is skipped deliberately: Homebrew's whisper-cpp ships one
    beside the real model directory, and it transcribes nonsense rather than
    failing, which reads as a working machine and ruins every caption.
    """
    if explicit:
        return str(explicit) if Path(explicit).is_file() else None
    found = []
    for pattern in WHISPER_MODEL:
        found.extend(sorted(Path(pattern).expanduser().parent.glob(Path(pattern).name)))
    usable = [p for p in found if "for-tests" not in p.name and p.is_file()]
    # Prefer the model the skill names, then the largest, which is the most accurate.
    named = [p for p in usable if p.name == WHISPER_MODEL_DEFAULT]
    if named:
        return str(named[0])
    return str(max(usable, key=lambda p: p.stat().st_size)) if usable else None


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
        "--assets-dir",
        default=str(clip_assets_dir()),
        help="Folder to download the fonts, the face model and the overlay placeholders into. "
        "Give the same folder to the other scripts when you change it.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    assets_dir = Path(args.assets_dir).expanduser()
    report = {
        "assets_dir": str(assets_dir),
        "fonts_dir": str(assets_dir / "fonts"),
        "face_model": str(assets_dir / "models" / "face-detection-yunet-2023mar.onnx"),
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

    report["missing"].extend(fetch_assets(assets_dir))

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
            report["missing"].append(
                "whisper model (the whisper filter takes a model file and hangs without one) - "
                f"install it one time, about 141 MB: {WHISPER_MODEL_INSTALL}"
            )

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
            fonts_dir = Path(report["fonts_dir"])
            bundled = bundled_families(fonts_dir) if fonts_dir.is_dir() else {}
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
        print(f"assets: {report['assets_dir']}")
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
