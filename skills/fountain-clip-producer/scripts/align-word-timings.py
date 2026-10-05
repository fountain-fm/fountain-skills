#!/usr/bin/env python3
"""Give each word of the transcript its time in the clip, from whisper's timings of the clip's audio.

Whisper hears the clip and knows when each word is said, but it mishears names and numbers.
The transcript has the words right and no timings. This script keeps the transcript's words and
whisper's timings: it matches the two letter by letter, so it does not matter how whisper split a word
into tokens, and a word whisper got wrong still takes the timing of the letters around it.

Inputs:
- The whisper output of the clip's audio, as SRT, with one token for each segment (`max_len=1`).
- The reference: the words the captions must show, as plain text. This is the `transcript` of the
  `SocialPostMediaSource`, corrected by hand where it is wrong.

Output: the words JSON that `build-captions.py` reads, rebased to clip time, with `anchor_ratio`, the share
of reference words that matched whisper, and `unheard`, each run of reference words that matched nothing.
A run of words packed tighter than anybody speaks is spread over the words around it, and listed in `spread`.
A low ratio means the reference does not describe this audio: check the span before you caption it.
"""

import argparse
import difflib
import json
import re
import sys

SRT_TIME = re.compile(r"^(\d+):(\d\d):(\d\d)[,.](\d{3})\s*-->\s*(\d+):(\d\d):(\d\d)[,.](\d{3})")
EDGE_SLACK = 0.3  # seconds a token can hang over the clip edge and still count
MIN_WORD = 0.06  # seconds, the shortest span a word can keep
MAX_WORD = 1.0  # seconds a word keeps before an unheard run; whisper stretches it over the words it missed
LOW_RATIO = 0.8  # below this share of matched words, the reference does not describe the audio
MAX_RATE = 8.5  # words a second over RATE_WINDOW words; under the 9.0 that build-captions.py refuses
RATE_WINDOW = 5


def seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def read_srt(path):
    """Return (start, end, text) for each cue of the SRT, in file time."""
    cues, current = [], None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            match = SRT_TIME.match(line)
            if match:
                g = match.groups()
                current = [seconds(*g[:4]), seconds(*g[4:]), []]
                cues.append(current)
            elif current is not None and line and not line.isdigit():
                current[2].append(line)
    return [(a, b, " ".join(t)) for a, b, t in cues if " ".join(t).strip()]


def letters(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def spread(words, clip_end):
    """Give each unmatched word an even share of the gap between its matched neighbours."""
    i = 0
    while i < len(words):
        if words[i] is not None:
            i += 1
            continue
        j = i
        while j < len(words) and words[j] is None:
            j += 1
        left = 0.0
        if i > 0:
            left = words[i - 1][1] = min(words[i - 1][1], words[i - 1][0] + MAX_WORD)
        right = words[j][0] if j < len(words) else clip_end
        step = max(MIN_WORD, right - left) / (j - i)
        for k in range(i, j):
            words[k] = [left + step * (k - i), left + step * (k - i + 1)]
        i = j
    return words


def unpack(words):
    """Spread each run of words that whisper packed tighter than anybody speaks over the words around it."""
    spread_runs = []
    for _ in range(len(words)):
        packed = next(
            (
                i
                for i in range(len(words) - RATE_WINDOW + 1)
                if words[i + RATE_WINDOW - 1]["end"] - words[i]["start"] < RATE_WINDOW / MAX_RATE
            ),
            None,
        )
        if packed is None:
            break
        lo, hi = packed, packed + RATE_WINDOW
        while words[hi - 1]["end"] - words[lo]["start"] < (hi - lo) / MAX_RATE and (lo > 0 or hi < len(words)):
            lo, hi = max(0, lo - 1), min(len(words), hi + 1)
        start, step = words[lo]["start"], (words[hi - 1]["end"] - words[lo]["start"]) / (hi - lo)
        for k in range(lo, hi):
            words[k]["start"] = round(start + step * (k - lo), 3)
            words[k]["end"] = round(start + step * (k - lo + 1), 3)
        if spread_runs and lo <= spread_runs[-1][1] and hi >= spread_runs[-1][0]:
            lo, hi = min(lo, spread_runs[-1][0]), max(hi, spread_runs[-1][1])
            spread_runs.pop()
        spread_runs.append((lo, hi))
    return [f"{words[lo]['start']:.1f}s: {' '.join(w['word'] for w in words[lo:hi])}" for lo, hi in spread_runs]


def align(cues, reference, offset, duration):
    tokens = []
    for a, b, text in cues:
        a, b = a - offset, b - offset
        if letters(text) and b >= -EDGE_SLACK and a <= duration + EDGE_SLACK:
            tokens.append((max(0.0, a), min(duration, b), letters(text)))
    # Whisper hears the audio in chunks that overlap, so a token can still run when the next one starts.
    for k in range(len(tokens) - 1):
        a, b, text = tokens[k]
        tokens[k] = (a, max(a, min(b, tokens[k + 1][0])), text)
    ref_words = [w for w in reference.split() if letters(w)]
    if not ref_words:
        sys.exit("align-word-timings: the reference holds no words")

    # Match letter by letter, and remember which word or token each letter came from.
    ref_owner = [i for i, w in enumerate(ref_words) for _ in letters(w)]
    tok_owner = [i for i, t in enumerate(tokens) for _ in t[2]]
    matcher = difflib.SequenceMatcher(
        None, "".join(letters(w) for w in ref_words), "".join(t[2] for t in tokens), autojunk=False
    )
    spans = {}
    for i, j, n in matcher.get_matching_blocks():
        for k in range(n):
            word, token = ref_owner[i + k], tokens[tok_owner[j + k]]
            a, b = spans.get(word, (token[0], token[1]))
            spans[word] = (min(a, token[0]), max(b, token[1]))

    timed = spread([list(spans[i]) if i in spans else None for i in range(len(ref_words))], duration)
    out, past_end, cursor = [], [], 0.0
    for word, (a, b) in zip(ref_words, timed, strict=True):
        a = max(a, cursor)
        # A reference that runs past the clip describes speech this file does not hold: say so, and drop it.
        if a >= duration - MIN_WORD:
            past_end.append(word)
            continue
        b = min(max(b, a + MIN_WORD), duration)
        out.append({"word": word, "start": round(a, 3), "end": round(b, 3)})
        cursor = out[-1]["end"]
    if not out:
        sys.exit("align-word-timings: no reference word falls inside the clip - check the offset and the duration")
    spread_runs = unpack(out)

    unheard, run = [], []
    for i, word in enumerate(ref_words):
        if i in spans:
            if run:
                unheard.append(" ".join(run))
            run = []
        else:
            run.append(word)
    if run:
        unheard.append(" ".join(run))
    return {
        "anchor_ratio": round(len(spans) / len(ref_words), 3),
        "duration": duration,
        "unheard": unheard,
        "past_end": past_end,
        "spread": spread_runs,
        "words": out,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--srt", required=True, help="Whisper output of the clip's audio, one token per cue.")
    parser.add_argument("--reference", required=True, help="Text file of the words the captions must show.")
    parser.add_argument(
        "--offset", type=float, default=0.0, help="Where the clip starts in the SRT's time. Default: 0."
    )
    parser.add_argument("--duration", type=float, required=True, help="Length of the clip in seconds.")
    parser.add_argument("--out", required=True, help="Where to write the words JSON.")
    args = parser.parse_args()

    try:
        with open(args.reference, encoding="utf-8") as handle:
            reference = handle.read()
        cues = read_srt(args.srt)
    except OSError as error:
        sys.exit(f"align-word-timings: {error}")
    if not cues:
        sys.exit(f"align-word-timings: {args.srt} holds no cues - is it the whisper SRT of the clip?")
    result = align(cues, reference, args.offset, args.duration)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1, ensure_ascii=False)

    print(f"{args.out}: {len(result['words'])} words, anchor_ratio {result['anchor_ratio']}")
    for run in result["unheard"]:
        print(f"  unheard: {run}")
    for run in result["spread"]:
        print(f"  packed by whisper, spread out: {run}")
    if result["past_end"]:
        print(f"  past the end of the clip, dropped: {' '.join(result['past_end'])}")
    if result["anchor_ratio"] < LOW_RATIO:
        print(f"  WARNING: under {LOW_RATIO:.0%} of the reference matched - it may not describe this audio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
