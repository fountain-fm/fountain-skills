#!/usr/bin/env python3
"""Sample a vertical clip at a fixed interval and flag frames where no face or
person is detected — used as evidence for the framing QA gate, not the sole
authority (a human contact-sheet check is authoritative when the detector is
known to be unreliable for the footage).

Face detection uses the same YuNet model as extract-face-framing.py. A cascade
loses a head in profile, which is what a correctly framed two-shot speaker is
for the whole shot, so it failed the very crops the framing module had just
measured as good.
"""

import argparse
import json
import sys
from pathlib import Path

import cv2

MODEL_NAME = "face-detection-yunet-2023mar.onnx"
SCORE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3


def find_model(explicit=None):
    """Locate the bundled detector by walking up from this script."""
    if explicit:
        if not Path(explicit).is_file():
            raise RuntimeError(f"detector model not found: {explicit}")
        return str(explicit)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "assets" / "models" / MODEL_NAME
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(f"detector model {MODEL_NAME} not found in any assets/models above this script")


def detect_faces(detector, frame, min_size, min_area):
    _, faces = detector.detect(frame)
    detections = []
    for row in faces if faces is not None else []:
        x, y, w, h = (int(v) for v in row[:4])
        if w < min_size or w * h < min_area:
            continue
        detections.append(
            {"type": "face", "x": x, "y": y, "w": w, "h": h, "area": w * h, "score": round(float(row[14]), 3)}
        )
    return detections


def detect_people_hog(frame):
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    scale = 480 / frame.shape[1]
    resized = cv2.resize(frame, (480, int(frame.shape[0] * scale)))
    rects, weights = hog.detectMultiScale(resized, winStride=(8, 8), padding=(8, 8), scale=1.05)
    detections = []
    for (x, y, w, h), weight in zip(rects, weights, strict=True):
        if weight < 0.3:
            continue
        detections.append(
            {
                "type": "person_hog",
                "x": int(x / scale),
                "y": int(y / scale),
                "w": int(w / scale),
                "h": int(h / scale),
                "confidence": float(weight),
                "area": int((w / scale) * (h / scale)),
            }
        )
    return detections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float)
    parser.add_argument("--max-missing-ratio", type=float, default=0.0)
    parser.add_argument("--min-face-width-ratio", type=float, default=0.035)
    parser.add_argument("--min-face-area-ratio", type=float, default=0.01)
    parser.add_argument("--report", required=True)
    parser.add_argument("--model", default=None, help="Path to the YuNet ONNX model. Defaults to the bundled copy.")
    args = parser.parse_args()

    model = find_model(args.model)
    detector = None

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"could not open video: {args.video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if frame_count else 0
    end = args.end if args.end is not None else duration

    samples, missing = [], []
    timestamp = args.start
    while timestamp <= end + 0.001:
        frame_index = int(round(timestamp * fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        if not ok:
            break

        height, width = frame.shape[:2]
        min_face = max(32, int(width * args.min_face_width_ratio))
        min_area = int(width * height * args.min_face_area_ratio)
        if detector is None:
            detector = cv2.FaceDetectorYN.create(model, "", (width, height), SCORE_THRESHOLD, NMS_THRESHOLD)
        faces = detect_faces(detector, frame, min_face, min_area)
        # Only fall back to the (slower, coarser) full-body detector when no
        # face was found — most frames resolve on the face check alone.
        people = detect_people_hog(frame) if not faces else []

        found = bool(faces or people)
        samples.append(
            {"time": round(timestamp, 3), "frame": frame_index, "foundPerson": found, "faces": faces, "people": people}
        )
        if not found:
            missing.append({"time": round(timestamp, 3), "frame": frame_index})
        timestamp += args.interval

    cap.release()

    missing_ratio = (len(missing) / len(samples)) if samples else 1.0
    status = "pass" if samples and missing_ratio <= args.max_missing_ratio else "fail"
    report = {
        "status": status,
        "video": args.video,
        "fps": fps,
        "duration": duration,
        "interval": args.interval,
        "sampleCount": len(samples),
        "missingCount": len(missing),
        "missingRatio": missing_ratio,
        "maxMissingRatio": args.max_missing_ratio,
        "missing": missing,
        "samples": samples,
    }

    Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
