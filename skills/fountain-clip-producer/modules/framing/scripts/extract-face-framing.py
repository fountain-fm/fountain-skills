#!/usr/bin/env python3
"""Measure the active speaker's horizontal face center over a clip segment
and return the ffmpeg crop x-offset needed to keep that face centered.

Usage:
    extract-face-framing.py <video> [start_seconds] [end_seconds] [--crop-width N]
"""

import argparse
import json
import sys

import cv2
import numpy as np

# The Haar cascade throws false positives on bookshelves, posters, mics, and
# torsos when run unconstrained. Restricting detection to the plausible face
# region (central 20-80% horizontally, upper 8-62% vertically) filters those
# out and is what makes the median face center reliable.
MIN_X, MAX_X = 0.20, 0.80
MIN_Y, MAX_Y = 0.08, 0.62


def measure(video, t0=0.0, t1=None, step=0.4, crop_width=None):
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps
    if t1 is None:
        t1 = duration

    frontal = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    profile = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

    xs, ys = [], []
    frame_w = frame_h = None
    t = t0
    while t < t1:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_h, frame_w = gray.shape

        candidates = []
        for cascade in (frontal, profile):
            for x, y, w, h in cascade.detectMultiScale(
                gray, 1.1, 8, minSize=(int(frame_h * 0.18), int(frame_h * 0.18))
            ):
                cx, cy = x + w / 2, y + h / 2
                if MIN_X * frame_w < cx < MAX_X * frame_w and MIN_Y * frame_h < cy < MAX_Y * frame_h:
                    candidates.append((x, y, w, h))

        # Profile cascade only detects left-facing profiles; flip the frame to
        # also catch right-facing speakers, then map coordinates back.
        flipped = cv2.flip(gray, 1)
        for x, y, w, h in profile.detectMultiScale(flipped, 1.1, 8, minSize=(int(frame_h * 0.18), int(frame_h * 0.18))):
            x = frame_w - x - w
            cx, cy = x + w / 2, y + h / 2
            if MIN_X * frame_w < cx < MAX_X * frame_w and MIN_Y * frame_h < cy < MAX_Y * frame_h:
                candidates.append((x, y, w, h))

        if candidates:
            # Largest detected face wins when there are several candidates in
            # one frame (e.g. a bystander in the background).
            x, y, w, h = max(candidates, key=lambda f: f[2] * f[3])
            xs.append(x + w / 2)
            ys.append(y + h / 2)
        t += step

    cap.release()

    if not xs:
        return {"ok": False, "reason": "no faces in constrained region"}

    if crop_width is None:
        # Derive from the source's actual resolution rather than assuming
        # one -- a fixed default silently produces the wrong aspect ratio
        # for any source that isn't the resolution it was picked for (e.g.
        # 405 is only correct for a 720p source; a 1080p source needs 608).
        crop_width = round(frame_h * 9 / 16)

    face_cx = float(np.median(xs))
    face_cy = float(np.median(ys))
    return {
        "ok": True,
        "frames": len(xs),
        "face_cx": round(face_cx, 1),
        "face_cy": round(face_cy, 1),
        "frameW": frame_w,
        "frameH": frame_h,
        "cropW": crop_width,
        "crop_x": int(round(max(0, min(frame_w - crop_width, face_cx - crop_width / 2)))),
        "x_spread": round(float(np.percentile(xs, 90) - np.percentile(xs, 10)), 1),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("start", nargs="?", type=float, default=0.0)
    parser.add_argument("end", nargs="?", type=float, default=None)
    parser.add_argument(
        "--crop-width",
        type=int,
        default=None,
        help="Vertical crop width in px. Defaults to a true 9:16 crop "
        "derived from the source's actual detected height -- only "
        "override this for a non-standard target aspect ratio.",
    )
    args = parser.parse_args()

    result = measure(args.video, args.start, args.end, crop_width=args.crop_width)
    print(json.dumps(result))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
