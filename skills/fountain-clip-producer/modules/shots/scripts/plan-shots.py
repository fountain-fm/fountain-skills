#!/usr/bin/env python3
"""Turn speaker-labelled words plus per-speaker face anchors into a cut list.

Reads a list of TranscriptWord for the clip span, each carrying a "speaker"
field that TranscriptWord itself does not define, and the anchors emitted by
module framing's extract-face-framing.py --speakers 2. Writes one segment per
held shot, with the crop geometry for that speaker.

The rules below exist to stop the result reading as one frame diced up:

  * a turn shorter than --min-utterance is a backchannel ("yeah", "mm-hm")
    and never earns a cut of its own
  * no shot is held for less than --min-dwell, so rapid exchanges do not
    ping-pong
  * every cut lands --lead-ms BEFORE the incoming speaker's first word, the
    way an editor cuts on the breath rather than on the syllable
  * each speaker's crop height is derived from their own measured face height,
    so both faces end up the same size on screen
  * the face sits off-centre, away from the direction it faces, so the
    speaker looks into the frame instead of off the edge

Crop sizes differ per speaker by design, and one ffmpeg crop filter cannot
change output size mid-stream, so the segments are rendered separately and
concatenated. --emit-commands prints that sequence.
"""

import argparse
import json
import sys

TARGET_AR = 9 / 16


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_words(path):
    with open(path) as handle:
        data = json.load(handle)
    words = data["words"] if isinstance(data, dict) else data
    if not words:
        fail("no words given")
    if not any(w.get("speaker") for w in words):
        fail(
            "no speaker labels on the words -- this module cannot place a cut without them. "
            "Fetch a diarized transcript, or frame the clip as a single shot with module framing."
        )
    return words


def to_utterances(words):
    """Collapse consecutive words by the same speaker into one turn."""
    turns = []
    for word in words:
        speaker = word.get("speaker")
        if turns and turns[-1]["speaker"] == speaker:
            turns[-1]["end"] = float(word["end"])
            turns[-1]["words"] += 1
        else:
            turns.append({"speaker": speaker, "start": float(word["start"]), "end": float(word["end"]), "words": 1})
    return turns


def absorb(turns, min_utterance, min_dwell):
    """Drop backchannels, then hold every surviving shot for at least the dwell.

    Both passes fold the offending turn into the shot before it, which is what
    keeps the cut list monotonic -- a dropped turn never leaves a hole.
    """
    kept = []
    for turn in turns:
        duration = turn["end"] - turn["start"]
        short = duration < min_utterance
        if kept and (short or kept[-1]["speaker"] == turn["speaker"]):
            kept[-1]["end"] = turn["end"]
        else:
            kept.append(dict(turn))

    # Dwell is enforced after backchannels are gone, and repeatedly, because
    # absorbing one short shot can leave its neighbour short in turn.
    changed = True
    while changed and len(kept) > 1:
        changed = False
        merged = [kept[0]]
        for turn in kept[1:]:
            previous = merged[-1]
            if previous["end"] - previous["start"] < min_dwell or previous["speaker"] == turn["speaker"]:
                previous["end"] = turn["end"]
                changed = True
            else:
                merged.append(turn)
        kept = merged
    return kept


def geometry(anchor, frame_w, frame_h, face_height, eye_line, look_room):
    """Crop box for one speaker, sized so their head matches the other's."""
    crop_h = min(float(frame_h), anchor["face_h"] / face_height)
    crop_w = crop_h * TARGET_AR
    if crop_w > frame_w:
        crop_w = float(frame_w)
        crop_h = crop_w / TARGET_AR

    # Look room: a speaker on the left faces right, so their face sits left of
    # the crop's centre, leaving the space they are looking into.
    offset = (0.5 - look_room) if anchor["position"] == "left" else (0.5 + look_room)
    crop_x = anchor["face_cx"] - offset * crop_w
    crop_y = anchor["face_cy"] - eye_line * crop_h

    crop_x = max(0, min(frame_w - crop_w, crop_x))
    crop_y = max(0, min(frame_h - crop_h, crop_y))
    # ffmpeg's crop wants even numbers for yuv420p.
    box = [int(round(v / 2) * 2) for v in (crop_x, crop_y, crop_w, crop_h)]
    return {"crop_x": box[0], "crop_y": box[1], "crop_w": box[2], "crop_h": box[3]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchors", required=True, help="JSON from extract-face-framing.py --speakers 2.")
    parser.add_argument("--words", required=True, help="TranscriptWord list for the span, with a speaker field.")
    parser.add_argument("--duration", type=float, required=True, help="Clip duration in seconds.")
    parser.add_argument("--out-width", type=int, default=1080)
    parser.add_argument("--out-height", type=int, default=1920)
    parser.add_argument("--min-utterance", type=float, default=1.2, help="Shorter turns are backchannels.")
    parser.add_argument("--min-dwell", type=float, default=1.5, help="Shortest shot that may be held.")
    parser.add_argument("--lead-ms", type=float, default=100.0, help="Cut this far before the first word.")
    parser.add_argument("--face-height", type=float, default=0.22, help="Target face height as a fraction of the crop.")
    parser.add_argument("--eye-line", type=float, default=0.42, help="Face centre this far down the crop.")
    parser.add_argument("--look-room", type=float, default=0.06, help="Face offset from centre, away from the gaze.")
    parser.add_argument(
        "--max-switches-per-minute",
        type=float,
        default=18.0,
        help="Above this the exchange is crosstalk; fall back to one held shot rather than cutting.",
    )
    parser.add_argument("--map", help="Pin speakers to sides, e.g. A=left,B=right. Defaults to first-heard order.")
    parser.add_argument("--emit-commands", action="store_true", help="Print the per-segment render and concat.")
    parser.add_argument("--out", help="Write the plan here as well as to stdout.")
    args = parser.parse_args()

    with open(args.anchors) as handle:
        anchors_doc = json.load(handle)
    anchors = anchors_doc.get("anchors")
    if not anchors or len(anchors) < 2:
        fail("anchors file has fewer than two speakers -- run extract-face-framing.py --speakers 2")
    frame_w, frame_h = anchors_doc["frameW"], anchors_doc["frameH"]
    by_side = {a["position"]: a for a in anchors}

    raw = to_utterances(load_words(args.words))
    turns = absorb(raw, args.min_utterance, args.min_dwell)

    # Pin each speaker label to a side. First heard takes the left unless told
    # otherwise; this is a guess, so the module makes you verify it on a still.
    # Built from the raw turns, not the absorbed ones: absorption can drop a
    # speaker from the cut list entirely, and the crosstalk path below may then
    # hold the shot on exactly that speaker.
    if args.map:
        sides = dict(pair.split("=", 1) for pair in args.map.split(","))
    else:
        order = []
        for turn in raw:
            if turn["speaker"] not in order:
                order.append(turn["speaker"])
        sides = {name: ("left" if i == 0 else "right") for i, name in enumerate(order)}
    unknown = {t["speaker"] for t in raw} - set(sides)
    if unknown:
        fail(f"no side mapped for speaker(s): {', '.join(sorted(map(str, unknown)))}")

    # Measure the exchange on the RAW turns. Reading it off the absorbed list
    # hides the busiest case of all: when every turn is shorter than the
    # backchannel threshold, absorption collapses them before the rate is ever
    # computed, and a clip too rapid to cut looks like a clip nobody cut.
    rate = max(0, len(raw) - 1) / (args.duration / 60) if args.duration else 0
    collapsed = len(turns) == 1 and len(raw) > 1
    crosstalk = rate > args.max_switches_per_minute or collapsed
    if crosstalk:
        talk_time = {}
        for turn in raw:
            talk_time[turn["speaker"]] = talk_time.get(turn["speaker"], 0.0) + (turn["end"] - turn["start"])
        dominant = max(talk_time, key=talk_time.get)
        turns = [{"speaker": dominant, "start": 0.0, "end": args.duration, "words": 0}]

    segments = []
    for i, turn in enumerate(turns):
        start = 0.0 if i == 0 else max(0.0, turn["start"] - args.lead_ms / 1000)
        end = args.duration if i == len(turns) - 1 else turns[i + 1]["start"] - args.lead_ms / 1000
        anchor = by_side[sides[turn["speaker"]]]
        box = geometry(anchor, frame_w, frame_h, args.face_height, args.eye_line, args.look_room)
        face_out = anchor["face_h"] * (args.out_height / box["crop_h"])
        segments.append(
            {
                "index": i,
                "start": round(start, 3),
                "end": round(end, 3),
                "speaker": turn["speaker"],
                "side": sides[turn["speaker"]],
                **box,
                "face_height_out": round(face_out, 1),
            }
        )

    heights = [s["face_height_out"] for s in segments]
    spread = (max(heights) - min(heights)) / max(heights) if heights else 0
    warnings = []
    if spread > 0.10:
        warnings.append(f"head sizes differ by {spread:.0%} between speakers -- the cut will read as a jump")
    if crosstalk:
        warnings.append(
            f"crosstalk at {rate:.0f} turns/min -- held one shot on the dominant speaker instead of "
            "cutting. Consider a two-shot or a letterbox for this clip."
        )
    for segment in segments:
        if segment["end"] - segment["start"] < args.min_dwell:
            warnings.append(f"segment {segment['index']} is shorter than the dwell")

    plan = {
        "ok": not any("head sizes" in w for w in warnings),
        "source": {"width": frame_w, "height": frame_h},
        "output": {"width": args.out_width, "height": args.out_height},
        "switches": len(segments) - 1,
        "switches_per_minute": round(rate, 1),
        "sides": sides,
        "segments": segments,
        "warnings": warnings,
    }
    text = json.dumps(plan, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(text + "\n")

    if args.emit_commands:
        print("\n# render each shot, then concatenate -- crop sizes differ, so one pass cannot do it", file=sys.stderr)
        for segment in segments:
            print(
                f"ffmpeg -hide_banner -y -i clip-landscape-master.mp4 "
                f"-ss {segment['start']} -to {segment['end']} "
                f'-vf "crop={segment["crop_w"]}:{segment["crop_h"]}:{segment["crop_x"]}:{segment["crop_y"]},'
                f'scale={args.out_width}:{args.out_height},fps=30" '
                f"-c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k "
                f"seg-{segment['index']:02d}.mp4",
                file=sys.stderr,
            )
        print(
            "ffmpeg -hide_banner -y -f concat -safe 0 -i segments.txt -c copy clip-vertical.mp4",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
