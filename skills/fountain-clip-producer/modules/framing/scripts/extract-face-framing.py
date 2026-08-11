#!/usr/bin/env python3
"""Measure where the speakers' faces sit in a clip segment, and return the
ffmpeg crop offsets needed to centre them.

With --speakers 1 (default) this reports the single active speaker. With
--speakers 2 it reports one anchor per speaker, left to right, which is what
a boxed side-by-side layout or a locked-off wide two-shot needs -- module
shots turns those anchors plus the speaker-labelled words into a cut list.

Each anchor carries face_h as well as face_cx/face_cy, because matching
apparent head size between speakers is what stops two crops of one frame from
reading as two crops of one frame.

Detection uses the YuNet model the skill bundles, and not a Haar cascade. A
cascade misses a head that is turned, lit from one side, or far from the
camera -- exactly the head on the far side of a wide two-shot -- and it misses
it silently, which reads as a one-speaker frame.

Usage:
    extract-face-framing.py <video> [start_seconds] [end_seconds]
                            [--speakers N] [--crop-width N] [--model PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# YuNet scores every box, so the plausible-face region only has to reject the
# confident-but-irrelevant: a face on a poster, a monitor, or a wall photo.
# It is deliberately wide, because a wide two-shot puts a head near the edge
# and a guard that clips one of them hides the two-shot from the split test.
MIN_X, MAX_X = 0.04, 0.96
MIN_Y, MAX_Y = 0.04, 0.72

# A head smaller than this share of the frame is scenery rather than a speaker.
MIN_FACE_H = 0.05

# The detector's own thresholds. 0.6 keeps a head turned far enough that only
# one eye is visible, and still refuses the background.
SCORE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3

# Two clusters count as genuinely separate speakers only when they are this
# far apart (as a fraction of frame width) and both are seen this often.
MIN_CLUSTER_GAP = 0.18
MIN_CLUSTER_SUPPORT = 0.15

# A speaker angled toward the other chair needs room in front of the face, or
# they read as looking out of the frame. This is the share of the crop width
# the face sits away from centre, and it matches the default of module shots.
LOOK_ROOM = 0.06

# ...and only when the two faces are actually on screen TOGETHER this often.
# Pooling faces across time finds two clusters on any footage that cuts between
# two people, and those are one crop each rather than a shared frame to split.
MIN_COOCCURRENCE = 0.25


# A nose this far off the midpoint between the eyes, measured in eye-widths,
# means the head is turned rather than facing the camera.
TURN_RATIO = 0.15

MODEL_NAME = "face-detection-yunet-2023mar.onnx"


def find_model(explicit=None):
    """Locate the bundled detector. The skill ships it beside the fonts, so
    walk up from this script rather than depend on a working directory."""
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            sys.exit(f"detector model not found: {path}")
        return str(path)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "assets" / "models" / MODEL_NAME
        if candidate.is_file():
            return str(candidate)
    sys.exit(f"detector model {MODEL_NAME} not found in any assets/models above this script")


def facing_from_landmarks(landmarks):
    """Which way the head points, from the eyes and the nose.

    A head turned toward the right of frame carries its nose right of the
    midpoint between the eyes. Measuring the shift in eye-widths keeps the
    test the same for a near face and a far one.
    """
    right_eye, left_eye, nose = landmarks[0], landmarks[1], landmarks[2]
    eye_span = abs(left_eye[0] - right_eye[0])
    if eye_span < 1:
        return None
    ratio = (nose[0] - (right_eye[0] + left_eye[0]) / 2) / eye_span
    if ratio > TURN_RATIO:
        return "right"
    if ratio < -TURN_RATIO:
        return "left"
    return None


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


def detect(video, t0, t1, step, model):
    """Sample the segment and return every surviving face as (cx, cy, h)."""
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    duration = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / fps
    if t1 is None:
        t1 = duration

    detector = None
    found = []
    facings = []
    per_frame = []
    frame_w = frame_h = None
    t = t0
    while t < t1:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        frame_h, frame_w = frame.shape[:2]
        if detector is None:
            # The input size is fixed at build time, so the detector is built
            # once the first frame has told us what it actually is.
            detector = cv2.FaceDetectorYN.create(model, "", (frame_w, frame_h), SCORE_THRESHOLD, NMS_THRESHOLD)

        # YuNet runs its own non-maximum suppression, and returns one row per
        # face: box, then five landmarks, then the score.
        _, faces = detector.detect(frame)
        kept = []
        for row in faces if faces is not None else []:
            x, y, w, h = row[:4]
            cx, cy = x + w / 2, y + h / 2
            if not (MIN_X * frame_w < cx < MAX_X * frame_w and MIN_Y * frame_h < cy < MAX_Y * frame_h):
                continue
            if h < MIN_FACE_H * frame_h:
                continue
            found.append((float(cx), float(cy), float(h)))
            facings.append(facing_from_landmarks(row[4:14].reshape(5, 2)))
            kept.append(float(cx))
        if kept:
            per_frame.append(sorted(kept))
        t += step

    cap.release()
    return found, facings, per_frame, frame_w, frame_h


def cooccurrence(per_frame, frame_w):
    """Share of sampled frames that hold two faces at once, far enough apart to
    be two people rather than one head detected twice."""
    if not per_frame:
        return 0.0
    together = sum(1 for row in per_frame if len(row) > 1 and (row[-1] - row[0]) >= MIN_CLUSTER_GAP * frame_w)
    return together / len(per_frame)


def dominant_facing(facings):
    """Which way the head points across the segment, or None when it mostly
    faced the camera and no profile pass ever claimed it."""
    seen = [f for f in facings if f]
    if not seen:
        return None
    right = seen.count("right")
    if right * 2 == len(seen):
        return None
    return "right" if right * 2 > len(seen) else "left"


def look_offset(facing):
    if facing == "right":
        return 0.5 - LOOK_ROOM
    if facing == "left":
        return 0.5 + LOOK_ROOM
    return 0.5


def build_anchor(points, frame_w, crop_width, facing=None, look_room=True):
    cxs = [p[0] for p in points]
    face_cx = float(np.median(cxs))
    # Look room: a head pointing right needs the space on its right, so it sits
    # left of the crop centre. A head facing the camera stays centred.
    offset = look_offset(facing) if look_room else 0.5
    return {
        "face_cx": round(face_cx, 1),
        "face_cy": round(float(np.median([p[1] for p in points])), 1),
        "face_h": round(float(np.median([p[2] for p in points])), 1),
        "frames": len(points),
        "facing": facing or "camera",
        "crop_x": int(round(max(0, min(frame_w - crop_width, face_cx - offset * crop_width)))),
        "x_spread": round(float(np.percentile(cxs, 90) - np.percentile(cxs, 10)), 1),
    }


def measure(video, t0=0.0, t1=None, step=0.4, crop_width=None, speakers=1, model=None):
    found, facings, per_frame, frame_w, frame_h = detect(video, t0, t1, step, find_model(model))
    if not found:
        return {"ok": False, "reason": "no faces in the plausible face region"}
    together = cooccurrence(per_frame, frame_w)

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
        # The co-occurrence test is what separates a real two-shot from a
        # multicam edit, where each person is alone on their own camera.
        if gap >= MIN_CLUSTER_GAP and support >= MIN_CLUSTER_SUPPORT and together >= MIN_COOCCURRENCE:
            split = (centroids, labels)

    if speakers == 1:
        if split is not None:
            centroids, _ = split
            return {
                "ok": False,
                "reason": "two separated face clusters share the frame, so a single crop over this "
                "span lands between the faces. When the source cuts, measure each scene-cut segment "
                "on its own. When it never cuts, re-run with --speakers 2 and plan the cut list "
                "with module shots.",
                "cluster_cx": [round(float(c), 1) for c in sorted(centroids)],
                "cooccurrence": round(together, 3),
                "frameW": frame_w,
                "frameH": frame_h,
            }
        facing = dominant_facing(facings)
        anchor = build_anchor(found, frame_w, crop_width, facing)
        result = {
            "ok": True,
            "frameW": frame_w,
            "frameH": frame_h,
            "cropW": crop_width,
            "cooccurrence": round(together, 3),
            **anchor,
        }
        return result

    if split is None:
        return {
            "ok": False,
            "reason": f"asked for {speakers} speakers but only one face cluster is present",
            "frameW": frame_w,
            "frameH": frame_h,
        }

    _, labels = split
    pairs = list(zip(found, facings, strict=True))
    groups = [[pf for pf, lab in zip(pairs, labels, strict=True) if lab == j] for j in (0, 1)]
    # The anchor reports which way each head points, but leaves the look room to
    # module shots, which sizes its own crops and applies its own offset.
    anchors = [
        build_anchor([p for p, _ in g], frame_w, crop_width, dominant_facing([f for _, f in g]), look_room=False)
        for g in groups
        if g
    ]
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
    parser.add_argument(
        "--model",
        default=None,
        help="Path to the YuNet ONNX model. Defaults to the copy the skill bundles in assets/models.",
    )
    args = parser.parse_args()

    result = measure(
        args.video,
        args.start,
        args.end,
        crop_width=args.crop_width,
        speakers=args.speakers,
        model=args.model,
    )
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
