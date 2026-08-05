#!/usr/bin/env python3
"""Measure where the speakers' faces sit in a clip segment, and return the
ffmpeg crop offsets needed to centre them.

With --speakers 1 (default) this reports the single active speaker. With
--speakers 2 it reports one anchor per speaker, left to right, which is what
a boxed side-by-side layout or a locked-off wide two-shot needs -- module
speakers turns those anchors plus the speaker-labelled words into a cut list.

Each anchor carries face_h as well as face_cx/face_cy, because matching
apparent head size between speakers is what stops two crops of one frame from
reading as two crops of one frame.

Usage:
    extract-face-framing.py <video> [start_seconds] [end_seconds]
                            [--speakers N] [--crop-width N]
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

# A boxed side-by-side layout puts each speaker nearer the frame edge than a
# single-camera shot ever does, so the horizontal guard has to open up when
# more than one speaker is expected.
MULTI_MIN_X, MULTI_MAX_X = 0.04, 0.96

# Two clusters count as genuinely separate speakers only when they are this
# far apart (as a fraction of frame width) and both are seen this often.
MIN_CLUSTER_GAP = 0.18
MIN_CLUSTER_SUPPORT = 0.15


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    overlap = (x1 - x0) * (y1 - y0)
    return overlap / float(aw * ah + bw * bh - overlap)


def suppress(faces, thresh=0.4):
    """The frontal, profile and flipped-profile passes all fire on the same
    face, so collapse overlapping boxes before anything counts them."""
    kept = []
    for face in sorted(faces, key=lambda f: f[2] * f[3], reverse=True):
        if all(iou(face, other) < thresh for other in kept):
            kept.append(face)
    return kept


def cluster_1d(values, k, iters=25):
    """Deterministic 1-D k-means. Seeded across the observed range rather than
    at random, so the same footage always returns the same anchors."""
    v = np.asarray(values, dtype=float)
    centroids = np.linspace(v.min(), v.max(), k)
    labels = np.zeros(len(v), dtype=int)
    for _ in range(iters):
        labels = np.abs(v[:, None] - centroids[None, :]).argmin(axis=1)
        moved = np.array([v[labels == j].mean() if np.any(labels == j) else centroids[j] for j in range(k)])
        if np.allclose(moved, centroids):
            break
        centroids = moved
    return centroids, labels


def detect(video, t0, t1, step, wide):
    """Sample the segment and return every surviving face as (cx, cy, h)."""
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    duration = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / fps
    if t1 is None:
        t1 = duration

    frontal = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    profile = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    lo_x, hi_x = (MULTI_MIN_X, MULTI_MAX_X) if wide else (MIN_X, MAX_X)

    found = []
    frame_w = frame_h = None
    t = t0
    while t < t1:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_h, frame_w = gray.shape
        min_side = int(frame_h * 0.18)

        raw = []
        for cascade in (frontal, profile):
            raw.extend(cascade.detectMultiScale(gray, 1.1, 8, minSize=(min_side, min_side)))
        # The profile cascade only sees left-facing heads; flip to catch the rest.
        flipped = cv2.flip(gray, 1)
        for x, y, w, h in profile.detectMultiScale(flipped, 1.1, 8, minSize=(min_side, min_side)):
            raw.append((frame_w - x - w, y, w, h))

        for x, y, w, h in suppress([tuple(f) for f in raw]):
            cx, cy = x + w / 2, y + h / 2
            if lo_x * frame_w < cx < hi_x * frame_w and MIN_Y * frame_h < cy < MAX_Y * frame_h:
                found.append((cx, cy, float(h)))
        t += step

    cap.release()
    return found, frame_w, frame_h


def build_anchor(points, frame_w, crop_width):
    cxs = [p[0] for p in points]
    return {
        "face_cx": round(float(np.median(cxs)), 1),
        "face_cy": round(float(np.median([p[1] for p in points])), 1),
        "face_h": round(float(np.median([p[2] for p in points])), 1),
        "frames": len(points),
        "crop_x": int(round(max(0, min(frame_w - crop_width, float(np.median(cxs)) - crop_width / 2)))),
        "x_spread": round(float(np.percentile(cxs, 90) - np.percentile(cxs, 10)), 1),
    }


def measure(video, t0=0.0, t1=None, step=0.4, crop_width=None, speakers=1):
    found, frame_w, frame_h = detect(video, t0, t1, step, wide=speakers > 1)
    if not found:
        return {"ok": False, "reason": "no faces in constrained region"}

    if crop_width is None:
        # Derive from the source's actual resolution rather than assuming one --
        # a fixed default silently produces the wrong aspect ratio for any
        # source that isn't the resolution it was picked for.
        crop_width = round(frame_h * 9 / 16)

    xs = [p[0] for p in found]
    # Always test for a second speaker, even when only one was asked for: the
    # median of a two-shot lands in the gap between the faces and crops empty
    # table, which used to be reported as a clean success.
    split = None
    if len(set(xs)) > 1:
        centroids, labels = cluster_1d(xs, 2)
        gap = abs(centroids[1] - centroids[0]) / frame_w
        support = min((labels == 0).sum(), (labels == 1).sum()) / len(xs)
        if gap >= MIN_CLUSTER_GAP and support >= MIN_CLUSTER_SUPPORT:
            split = (centroids, labels)

    if speakers == 1:
        if split is not None:
            centroids, _ = split
            return {
                "ok": False,
                "reason": "two separated face clusters found -- this looks like a side-by-side or "
                "wide two-shot. Re-run with --speakers 2 and plan the cut list with module speakers; "
                "a single crop here lands between the faces.",
                "cluster_cx": [round(float(c), 1) for c in sorted(centroids)],
                "frameW": frame_w,
                "frameH": frame_h,
            }
        anchor = build_anchor(found, frame_w, crop_width)
        return {"ok": True, "frameW": frame_w, "frameH": frame_h, "cropW": crop_width, **anchor}

    if split is None:
        return {
            "ok": False,
            "reason": f"asked for {speakers} speakers but only one face cluster is present",
            "frameW": frame_w,
            "frameH": frame_h,
        }

    _, labels = split
    groups = [[p for p, lab in zip(found, labels, strict=True) if lab == j] for j in (0, 1)]
    anchors = [build_anchor(g, frame_w, crop_width) for g in groups if g]
    anchors.sort(key=lambda a: a["face_cx"])
    for i, anchor in enumerate(anchors):
        anchor["position"] = "left" if i == 0 else "right"
    return {
        "ok": True,
        "frameW": frame_w,
        "frameH": frame_h,
        "cropW": crop_width,
        "speakers": len(anchors),
        "anchors": anchors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("start", nargs="?", type=float, default=0.0)
    parser.add_argument("end", nargs="?", type=float, default=None)
    parser.add_argument(
        "--speakers",
        type=int,
        default=1,
        choices=(1, 2),
        help="How many speakers share the frame. Use 2 for a boxed side-by-side layout or a locked-off wide two-shot.",
    )
    parser.add_argument(
        "--crop-width",
        type=int,
        default=None,
        help="Vertical crop width in px. Defaults to a true 9:16 crop "
        "derived from the source's actual detected height -- only "
        "override this for a non-standard target aspect ratio.",
    )
    args = parser.parse_args()

    result = measure(args.video, args.start, args.end, crop_width=args.crop_width, speakers=args.speakers)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
