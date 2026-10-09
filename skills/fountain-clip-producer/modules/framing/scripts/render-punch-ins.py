#!/usr/bin/env python3
"""Crop the landscape master to a vertical export, and snap the crop closer to the face on each punch-in.

A punch-in is one object of the punch-in list: {"start": s, "end": s, "zoom": z}, in seconds of the clip.
Each segment is the JSON that extract-face-framing.py printed for it, and reads crop_x, cropW, frameW,
frameH, face_cx and face_cy. The script refuses a list that zooms past what the master can hold, a
punch-in that runs too long, and a punch-in that sits on a scene cut, and renders nothing.

Usage:
    render-punch-ins.py clip-landscape-master.mp4 --segment 0 framing.json \
        [--segment 21.4 framing-2.json] --punch-ins punch-ins.json --out clip-vertical.mp4
"""

import argparse
import json
import subprocess
import sys

import cv2
import numpy as np

# A short zoom can be softer than the whole clip, but no more than this ratio of delivered to source height.
MAX_UPSCALE = 2.25
# A longer zoom stops reading as emphasis and becomes the framing of the clip, which the gate then judges.
MAX_PUNCH_SECONDS = 3.0
# A snap this close to a scene cut reads as two edits on top of each other.
CUT_CLEARANCE_SECONDS = 0.5


def load_segments(pairs):
    segments = []
    for start, path in pairs:
        with open(path) as handle:
            segments.append((float(start), json.load(handle)))
    return sorted(segments, key=lambda segment: segment[0])


def find_problems(punch_ins, segments, out_h):
    problems = []
    cut_times = [start for start, _ in segments[1:]]
    previous_end = 0.0
    for punch_in in sorted(punch_ins, key=lambda item: item["start"]):
        start, end, zoom = punch_in["start"], punch_in["end"], punch_in["zoom"]
        label = f"punch-in at {start:.2f}s"
        if end <= start or zoom < 1:
            problems.append(f"{label}: needs end after start and a zoom of 1 or more")
        if end - start > MAX_PUNCH_SECONDS:
            problems.append(f"{label}: lasts {end - start:.2f}s, longer than {MAX_PUNCH_SECONDS}s")
        if start < previous_end:
            problems.append(f"{label}: starts before the punch-in before it ends")
        if any(start - CUT_CLEARANCE_SECONDS < cut < end + CUT_CLEARANCE_SECONDS for cut in cut_times):
            problems.append(f"{label}: sits on a scene cut")
        frame_h = segment_at(segments, start)["frameH"]
        upscale = out_h / (frame_h / zoom)
        if upscale > MAX_UPSCALE:
            problems.append(f"{label}: zoom {zoom} upscales {upscale:.2f}x, more than {MAX_UPSCALE}x")
        previous_end = max(previous_end, end)
    return problems


def segment_at(segments, t):
    current = segments[0][1]
    for start, segment in segments:
        if t >= start:
            current = segment
    return current


def zoom_at(t, punch_ins):
    for punch_in in punch_ins:
        if punch_in["start"] <= t < punch_in["end"]:
            return punch_in["zoom"]
    return 1.0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("master")
    parser.add_argument("--segment", nargs=2, action="append", required=True, metavar=("START", "FRAMING_JSON"))
    parser.add_argument("--punch-ins", required=True)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    segments = load_segments(args.segment)
    with open(args.punch_ins) as handle:
        punch_ins = json.load(handle)
    problems = find_problems(punch_ins, segments, args.height)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}, indent=2))
        return 2

    capture = cv2.VideoCapture(args.master)
    fps = capture.get(cv2.CAP_PROP_FPS)
    ffmpeg_command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        # Raw frames from this script arrive on stdin at the frame rate of the master.
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{args.width}x{args.height}", "-r", str(fps), "-i", "-",
        # The second input gives the audio, and -map pairs it with the new picture.
        "-i", args.master, "-map", "0:v", "-map", "1:a",
        # The same encode as the plain crop, so that nothing after this step can tell the two apart.
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        # -shortest stops on the last frame, because the audio can run a few milliseconds longer.
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", args.out,
    ]  # fmt: skip
    encoder = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        t = frame_index / fps
        segment = segment_at(segments, t)
        zoom = zoom_at(t, punch_ins)
        frame_w, frame_h = segment["frameW"], segment["frameH"]
        window_w, window_h = segment["cropW"] / zoom, frame_h / zoom
        # Zoom about the face, so that the face keeps its place on the screen while the frame closes in.
        x0 = segment["face_cx"] - (segment["face_cx"] - segment["crop_x"]) / zoom
        y0 = segment["face_cy"] - segment["face_cy"] / zoom
        x0 = min(max(x0, 0), frame_w - window_w)
        y0 = min(max(y0, 0), frame_h - window_h)
        scale_x, scale_y = args.width / window_w, args.height / window_h
        matrix = np.float32([[scale_x, 0, -scale_x * x0], [0, scale_y, -scale_y * y0]])
        cropped = cv2.warpAffine(frame, matrix, (args.width, args.height), flags=cv2.INTER_LANCZOS4)
        encoder.stdin.write(cropped.tobytes())
        frame_index += 1

    encoder.stdin.close()
    encoder.wait()
    print(json.dumps({"ok": encoder.returncode == 0, "frames": frame_index, "punchIns": len(punch_ins)}))
    return encoder.returncode


if __name__ == "__main__":
    sys.exit(main())
