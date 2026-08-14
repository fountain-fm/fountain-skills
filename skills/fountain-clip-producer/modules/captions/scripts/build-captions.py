#!/usr/bin/env python3
"""Compile a caption style spec + word-level timings into a finished .ass file.

The style spec is a small JSON document (see modules/captions/assets/ for the
named presets) describing font, colors, border, position, grouping, and
animation. Every field can be overridden per-clip with --override dot.path=value,
and a brand kit (--brand-kit) layers show-level defaults between the preset and
the CLI. Precedence: built-in defaults < preset < brand kit < --override.

The words JSON is the clip's word timings, rebased to clip
time, each optionally carrying "speaker" and "emphasize":
[{"word": "...", "start": 1.23, "end": 1.45,
"speaker": "A"?, "emphasize": true?}, ...] (or wrapped in {"words": [...]}).
Only "word", "start", and "end" are read.
Editorial text cleanup (faithful-clean) happens BEFORE this script — it renders
the words it is given and never rewrites them beyond the spec's case setting.

Animation timing units are the fiddly part this script exists to get right:
ASS karaoke tags (\\k, \\kf) take CENTISECONDS; transform tags (\\t, \\move)
take MILLISECONDS. Karaoke durations are computed word-onset to word-onset so
the highlight tracks real speech, not just each word's own span.
"""

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULTS = {
    "playResX": 1080,
    "playResY": 1920,
    # Tokens the ASR lowercases that must render in their canonical case. Conservative
    # by default - only strings that are not English words - because "us" is both a
    # pronoun and a country. A brand kit extends this with the show's own vocabulary.
    # An ambiguous token rides as a phrase ("the fed" -> "the Fed"), never bare.
    "casing": {
        "ai": "AI",
        "btc": "BTC",
        "eth": "ETH",
        "etf": "ETF",
        "gdp": "GDP",
        "cpi": "CPI",
        "kyc": "KYC",
        "atm": "ATM",
        "fbi": "FBI",
        "nsa": "NSA",
        "irs": "IRS",
        "llc": "LLC",
        "wifi": "Wi-Fi",
        "wi-fi": "Wi-Fi",
        "usb": "USB",
        "gpu": "GPU",
        "cpu": "CPU",
        "url": "URL",
    },
    "font": {
        "family": "Arial",
        "size": 72,
        "bold": True,
        "italic": False,
        "spacing": 0,
        # verbatim | upper | lower | sentence
        "case": "verbatim",
    },
    "colors": {
        "primary": "#FFFFFF",  # main/spoken text color
        "highlight": "#00FFFF",  # karaoke unsung color; emphasis words in word modes
        "outline": "#000000",
        "shadow": None,  # defaults to outline color when shadow depth > 0
        "box": None,  # background box fill; only used when border.style == "box"
        "highlightPalette": None,  # list of hex colors; emphasized words rotate through it
        "speakers": None,  # {"A": "#FFFFFF", "B": "#FFE45C"} — per-speaker text color
    },
    "border": {
        # outline -> ASS BorderStyle 1; box -> BorderStyle 3 (colors.box behind text)
        "style": "outline",
        "outline": 4,  # outline thickness, or box padding when style == "box"
        "shadow": 0,  # drop-shadow depth
        "blur": 0,  # softens the border into a glow (\blur on every event)
    },
    "emphasis": {
        # how "emphasize": true words render, on top of their highlight color
        "scalePct": 100,  # >100 renders emphasized words larger
        "bold": False,  # force bold even when the base style isn't
    },
    "position": {
        # numpad-style: bottom|middle|top - left|center|right
        "alignment": "bottom-center",
        "marginL": 60,
        "marginR": 60,
        "marginV": 240,
    },
    "grouping": {
        "maxWords": 5,  # ceiling for rhythm; fitWidth decides the real count
        "fitWidth": True,  # pack each group up to the safe width at the resolved size
        "maxGapMs": 600,  # silence gap that forces a new group
        "sentenceSplit": True,  # a sentence-final word (. ! ?) always closes its group
        "stripFullStops": True,  # drop sentence-final periods from display (? and ! stay)
        "stripTrailingCommas": True,  # a comma on a group's last word is noise; the caption ends there
        "padMs": 150,  # readability pad after a group's last word
        "maxLines": 1,  # 1 = single-line rule (default); >=2 explicitly allows wrapping
        "speakerLabels": False,  # True = prefix "SPEAKER: " from the words' speaker field;
        # or a map {"A": "NICK"} to rename labels
    },
    "animation": {
        # none | karaoke-fill | highlight-sweep | current-word | word-pop | bounce-in | typewriter
        "type": "none",
        "appearMs": 120,  # pop/bounce scale-in time
        "settleMs": 100,  # pop/bounce overshoot->rest time
        "overshootPct": 112,  # peak scale during pop/bounce
        "entryPct": 55,  # starting scale for word-pop
        "riseHeight": 130,  # bounce-in: pixels risen from below
        "msPerChar": 45,  # typewriter reveal speed
        "popPct": 0,  # current-word: group-entry pop scale (0/100 = off)
        "leadMs": 0,  # captions land this early vs the audio (50-200ms reads as
        # "synced"; exact onset reads as lagging)
        "activeScalePct": 100,  # current-word: render the active word this % larger
        "highlightMode": "color",  # current-word active-word treatment: color | box | glow
    },
}

# Spec-level keys that aren't style fields and shouldn't fail unknown-key checks.
META_KEYS = {"name", "description", "notes"}

ALIGNMENT = {
    "bottom-left": 1,
    "bottom-center": 2,
    "bottom-right": 3,
    "middle-left": 4,
    "middle-center": 5,
    "middle-right": 6,
    "top-left": 7,
    "top-center": 8,
    "top-right": 9,
}

# The ASS V4+ style fields, in order. style_line() emits its values in exactly
# this order, so the header and the row stay in step from one definition.
STYLE_FIELDS = [
    "Name",
    "Fontname",
    "Fontsize",
    "PrimaryColour",
    "SecondaryColour",
    "OutlineColour",
    "BackColour",
    "Bold",
    "Italic",
    "Underline",
    "StrikeOut",
    "ScaleX",
    "ScaleY",
    "Spacing",
    "Angle",
    "BorderStyle",
    "Outline",
    "Shadow",
    "Alignment",
    "MarginL",
    "MarginR",
    "MarginV",
    "Encoding",
]

WORD_LEVEL_TYPES = {"word-pop", "bounce-in"}
# These show the whole group at once, so the group is what has to fit the width.
# A word-level type puts one word on screen at a time, so packing it is meaningless.
GROUP_ON_SCREEN = {"none", "karaoke-fill", "highlight-sweep", "current-word", "typewriter"}
ANIMATION_TYPES = {"none", "karaoke-fill", "highlight-sweep", "current-word", "word-pop", "bounce-in", "typewriter"}


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


OPEN_DICTS = {"casing"}  # vocabulary maps: new keys are the point, not a typo


def deep_merge(base, incoming, path=""):
    """Merge incoming onto base, rejecting keys that don't exist in base —
    a typo'd override must error, not silently style nothing. Vocabulary
    dicts (OPEN_DICTS) accept new keys freely."""
    for key, value in incoming.items():
        where = f"{path}.{key}" if path else key
        if not path and key in META_KEYS:
            continue
        if key not in base:
            if path not in OPEN_DICTS:
                fail(f"unknown style field '{where}' (check spelling against the spec schema)")
            base[key] = value
            continue
        if isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value, where)
        else:
            base[key] = value
    return base


def parse_override(raw):
    if "=" not in raw:
        fail(f"--override expects dot.path=value, got '{raw}'")
    dotted, value = raw.split("=", 1)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value  # bare strings like Montserrat Bold or #FFD400
    node = out = {}
    keys = dotted.split(".")
    for key in keys[:-1]:
        node[key] = {}
        node = node[key]
    node[keys[-1]] = parsed
    return out


def hex_to_ass(value, context):
    """#RRGGBB or #RRGGBBAA (CSS alpha, FF=opaque) -> ASS &HAABBGGRR."""
    if value is None:
        return None
    raw = value.lstrip("#")
    if len(raw) == 6:
        raw += "FF"
    if len(raw) != 8:
        fail(f"{context}: expected #RRGGBB or #RRGGBBAA, got '{value}'")
    try:
        r, g, b, a = (int(raw[i : i + 2], 16) for i in (0, 2, 4, 6))
    except ValueError:
        fail(f"{context}: invalid hex color '{value}'")
    return f"&H{255 - a:02X}{b:02X}{g:02X}{r:02X}"


def hex_to_inline(value, context):
    """Inline \\c override form: &HBBGGRR&."""
    ass = hex_to_ass(value, context)
    return f"&H{ass[4:]}&"


def relative_luminance(value):
    raw = value.lstrip("#")[:6]
    channels = []
    for i in (0, 2, 4):
        c = int(raw[i : i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def validate_spec(spec):
    """Readability guardrails. Returns (failures, warnings) as message lists."""
    failures, warnings = [], []
    font, colors, border = spec["font"], spec["colors"], spec["border"]
    position, grouping, animation = spec["position"], spec["grouping"], spec["animation"]

    if animation["type"] not in ANIMATION_TYPES:
        failures.append(f"animation.type '{animation['type']}' is not one of {sorted(ANIMATION_TYPES)}")
    if font["case"] not in {"verbatim", "upper", "lower", "sentence"}:
        failures.append(f"font.case '{font['case']}' is not one of verbatim/upper/lower/sentence")
    if position["alignment"] not in ALIGNMENT:
        failures.append(f"position.alignment '{position['alignment']}' is not one of {sorted(ALIGNMENT)}")
    if border["style"] not in {"outline", "box"}:
        failures.append(f"border.style '{border['style']}' is not outline or box")

    # Text must separate from arbitrary video underneath it — an outline, a box,
    # or at minimum a drop shadow.
    if border["style"] == "outline" and border["outline"] <= 0 and border["shadow"] <= 0:
        failures.append("border.outline and border.shadow are both 0 with no box — text will be unreadable over video")
    elif border["style"] == "outline" and border["outline"] <= 0:
        warnings.append("no outline, shadow only — verify readability on bright footage in the style proof")
    backdrop = colors["box"] or colors["outline"] if border["style"] == "box" else colors["outline"]
    if backdrop:
        ratio = contrast_ratio(colors["primary"], backdrop)
        if ratio < 2.0:
            failures.append(
                f"primary/{'box' if border['style'] == 'box' else 'outline'} contrast {ratio:.1f}:1 is below 2.0"
            )
        elif ratio < 4.5:
            warnings.append(f"primary/backdrop contrast {ratio:.1f}:1 is below the 4.5:1 accessibility target")

    scale = spec["playResX"] / 1080
    if not 40 * scale <= font["size"] <= 140 * scale:
        failures.append(
            f"font.size {font['size']} outside readable range "
            f"[{int(40 * scale)}, {int(140 * scale)}] for {spec['playResX']}px width"
        )

    if position["marginV"] < 150:
        warnings.append(f"position.marginV {position['marginV']} sits inside the platform UI zone (bottom ~150px)")
    if position["marginV"] > spec["playResY"] * 0.5:
        warnings.append(f"position.marginV {position['marginV']} places captions above mid-frame")

    if grouping["maxWords"] > 6:
        warnings.append(
            f"grouping.maxWords {grouping['maxWords']} exceeds the 3-6 words-on-screen guidance for vertical video"
        )
    if grouping["maxLines"] < 1:
        failures.append(f"grouping.maxLines {grouping['maxLines']} — must be at least 1")
    elif grouping["maxLines"] > 3:
        warnings.append(f"grouping.maxLines {grouping['maxLines']} — more than 3 lines buries the footage")

    if animation["type"] in WORD_LEVEL_TYPES:
        if animation["appearMs"] < 50:
            failures.append(f"animation.appearMs {animation['appearMs']} is under 50ms — flicker, not animation")
        if animation["overshootPct"] > 160:
            failures.append(f"animation.overshootPct {animation['overshootPct']} will overflow any measured fit")
        elif animation["overshootPct"] > 130:
            warnings.append(
                f"animation.overshootPct {animation['overshootPct']} is aggressive; fit is measured at this peak scale"
            )
    if animation["type"] == "typewriter" and animation["msPerChar"] < 25:
        warnings.append(
            f"animation.msPerChar {animation['msPerChar']} reveals faster than comfortable reading (~30-80ms/char)"
        )

    if animation["highlightMode"] not in {"color", "box", "glow"}:
        failures.append(f"animation.highlightMode '{animation['highlightMode']}' is not color/box/glow")
    if not 0 <= animation["leadMs"] <= 400:
        failures.append(
            f"animation.leadMs {animation['leadMs']} outside [0, 400] — beyond that captions visibly precede speech"
        )
    elif animation["leadMs"] > 250:
        warnings.append(f"animation.leadMs {animation['leadMs']} — above ~250ms the lead starts to read as desync")
    for name, value in (
        ("animation.activeScalePct", animation["activeScalePct"]),
        ("emphasis.scalePct", spec["emphasis"]["scalePct"]),
    ):
        if not 100 <= value <= 160:
            failures.append(f"{name} {value} outside [100, 160]")
        elif value > 125:
            warnings.append(f"{name} {value} is aggressive; fit is measured at this peak scale")
    if border["blur"] < 0:
        failures.append(f"border.blur {border['blur']} — must be >= 0")
    elif border["blur"] > 10:
        warnings.append(f"border.blur {border['blur']} — heavy glow; check legibility in the style proof")
    palette = colors["highlightPalette"]
    if palette is not None and (not isinstance(palette, list) or not palette):
        failures.append("colors.highlightPalette must be a non-empty list of hex colors")
    speakers = colors["speakers"]
    if speakers is not None and not isinstance(speakers, dict):
        failures.append("colors.speakers must be a map of speaker id -> hex color")
    if grouping["speakerLabels"] and animation["type"] in {"karaoke-fill", "highlight-sweep"}:
        warnings.append("speakerLabels with karaoke timing: the label is folded into the first word's highlight window")

    return failures, warnings


def load_words(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("words", [])
    words = []
    for i, item in enumerate(data):
        text = (item.get("word") or item.get("text") or "").strip()
        if not text:
            continue
        try:
            start, end = float(item["start"]), float(item["end"])
        except (KeyError, TypeError, ValueError):
            fail(f"words[{i}] ('{text}') is missing numeric start/end")
        if end < start:
            fail(f"words[{i}] ('{text}') ends before it starts")
        words.append(
            {
                "text": text,
                "start": start,
                "end": end,
                "speaker": item.get("speaker"),
                "emphasize": bool(item.get("emphasize")),
            }
        )
    if not words:
        fail(f"no usable words in {path}")
    clamped, nudged = enforce_monotonic(words)
    if clamped:
        print(f"note: shortened {clamped} word(s) that ran longer than {MAX_WORD_DUR}s in {path}", file=sys.stderr)
    if nudged:
        print(f"note: moved {nudged} word time(s) that ran backwards in {path}", file=sys.stderr)
    return words


MAX_WORD_DUR = 2.0  # nobody says one word for longer; a longer one is ASR debris, not speech
MAX_SHIFT = 1.0  # a repair this large means the order is wrong, and no repair can know the truth


def enforce_monotonic(words, min_dur=0.04):
    """Cut impossible durations, then push each word to start no earlier than the one before it ended.

    ASR output is not always ordered: a word can start before its predecessor
    finishes. Two caption events then cover the same instant and the viewer
    sees both at once. The word order carries the sentence, so the times move
    and the words never do.

    The clamp runs first because a long word's end becomes the cursor, and one
    bad word would otherwise push every later word past it. A word that must
    still move further than MAX_SHIFT fails the build instead.
    Returns (clamped, nudged).
    """
    clamped, nudged, cursor = 0, 0, 0.0
    for i, word in enumerate(words):
        if word["end"] - word["start"] > MAX_WORD_DUR:
            word["end"] = word["start"] + MAX_WORD_DUR
            clamped += 1
        start = max(word["start"], cursor)
        if start - word["start"] > MAX_SHIFT:
            fail(
                f"words[{i}] ('{word['text']}') would move {start - word['start']:.2f}s to keep its order, "
                f"past the {MAX_SHIFT}s limit - make the word timings again from the clip's audio"
            )
        end = max(word["end"], start + min_dur)
        if start != word["start"] or end != word["end"]:
            nudged += 1
        word["start"], word["end"] = start, end
        cursor = end
    return clamped, nudged


def apply_case(text, mode, capitalize=False):
    if mode == "upper":
        return text.upper()
    if mode == "lower":
        return text.lower()
    if mode == "sentence":
        # A token carrying two or more capitals (AI, CEO, U.S.) keeps them: they are information.
        if len(re.findall(r"[A-Z]", text)) >= 2 and not re.search(r"[a-z]", text):
            return text
        lowered = re.sub(r"\bi\b", "I", text.lower())
        if capitalize:
            for j, ch in enumerate(lowered):
                if ch.isalpha():
                    return lowered[:j] + ch.upper() + lowered[j + 1 :]
        return lowered
    return text


SENTENCE_END = re.compile(r'[.!?]["\')\]]*$')
TRAILING_STOPS = re.compile(r'\.+(["\')\]]*)$')
TRAILING_COMMA = re.compile(r',(["\')\]]*)$')
FILLER_WORD = re.compile(r"^(?:u+m+|u+h+|erm+|hm+m*)[,.!?]*$", re.IGNORECASE)
DANGLING_TAIL = {"and", "but", "or", "so", "because"}
NUM_COMMA = re.compile(r"^(\d+),$")


def faithful_clean(words):
    """Default text hygiene: drop pure fillers, join a spoken number range on an
    en dash, strip token-final commas, and never end the clip on a dangling
    conjunction. The audio still carries every removed word - that is what
    makes each of these safe, and why anything more stays editorial judgment."""
    out, removed, i = [], 0, 0
    while i < len(words):
        w = words[i]
        t = w["text"]
        if FILLER_WORD.match(t):
            removed += 1
            i += 1
            continue
        m = NUM_COMMA.match(t)
        if m and i + 1 < len(words) and re.match(r"^\d", words[i + 1]["text"]):
            nxt = words[i + 1]
            w = dict(w, text=f"{m.group(1)}\u2013{nxt['text']}", end=nxt["end"])
            removed += 1
            i += 2
        else:
            stripped = TRAILING_COMMA.sub(r"\1", t)
            if stripped and stripped != t:
                w = dict(w, text=stripped)
            i += 1
        out.append(w)
    while out and out[-1]["text"].rstrip(".!?").lower() in DANGLING_TAIL:
        out.pop()
        removed += 1
    words[:] = out
    return removed


FILLER_CANDIDATES = {"like", "right"}
FILLER_BIGRAMS = {("you", "know"), ("kind", "of"), ("sort", "of"), ("i", "mean")}
RIGHT_KEEPERS = {"now", "there", "here", "away", "side", "hand", "answer", "thing", "one", "amount"}
LIKE_QUOTATIVE = {"was", "is", "it's", "i'm", "be", "being", "felt", "feels", "looks", "sounds", "seems"}


def flag_filler_candidates(words):
    """Name every filler candidate and remove none: deletion is editorial
    judgment (see the module), but a candidate nobody lists is a candidate
    nobody judges. Suppresses the obvious keeps to hold the noise down."""
    hits = []
    for i, w in enumerate(words):
        t = re.sub(r"[^a-z']", "", w["text"].lower())
        prev = re.sub(r"[^a-z']", "", words[i - 1]["text"].lower()) if i else ""
        nxt = re.sub(r"[^a-z']", "", words[i + 1]["text"].lower()) if i + 1 < len(words) else ""
        if t == "like":
            before_num = i + 1 < len(words) and re.match(r"^[\d$\"]", words[i + 1]["text"])
            if prev in LIKE_QUOTATIVE or before_num or nxt == "that" or prev == "i":
                continue
            hits.append((w["start"], "like"))
        elif t == "right":
            if nxt in RIGHT_KEEPERS or prev in {"the", "all"}:
                continue
            hits.append((w["start"], "right"))
        elif i + 1 < len(words) and (t, nxt) in FILLER_BIGRAMS:
            hits.append((w["start"], f"{t} {nxt}"))
    if hits:
        preview = ", ".join(f"'{k}' at {s:.1f}s" for s, k in hits[:8])
        more = f" (+{len(hits) - 8} more)" if len(hits) > 8 else ""
        print(
            f"filler-review: {len(hits)} candidate(s) to judge, none removed: {preview}{more}",
            file=sys.stderr,
        )
    return hits


def mark_sentence_starts(words):
    """Sentence case capitalizes at sentence starts, never at bare group starts."""
    for i, w in enumerate(words):
        w["capitalize"] = i == 0 or bool(SENTENCE_END.search(words[i - 1]["text"]))


def apply_casing(words, casing):
    """Restore canonical case the ASR lost: "ai" -> "AI", "wifi" -> "Wi-Fi",
    "the fed" -> "the Fed". A cased word is protected from the case mode, or
    sentence case would immediately lower "Fed" again. Phrase keys match on
    consecutive tokens, so an ambiguous word never matches bare."""

    def core(text):
        return re.sub(r"[^A-Za-z'-]", "", text).lower()

    singles = {k: v for k, v in casing.items() if " " not in k}
    phrases = {tuple(k.split()): v.split() for k, v in casing.items() if " " in k}
    fixed = 0
    for i, w in enumerate(words):
        c = core(w["text"])
        for key, vals in phrases.items():
            if c == key[0] and i + len(key) <= len(words):
                cores = [core(words[i + j]["text"]) for j in range(len(key))]
                if tuple(cores) == key:
                    for j, val in enumerate(vals):
                        ww = words[i + j]
                        before = ww["text"]
                        ww["text"] = re.sub(r"[A-Za-z'-]+", val, ww["text"], count=1)
                        if ww["text"] != before:
                            ww["protect_case"] = True
                    fixed += 1
        if c in singles:
            w["text"] = re.sub(r"[A-Za-z'-]+", singles[c], w["text"], count=1)
            w["protect_case"] = True
            fixed += 1
    return fixed


def peak_scale(spec):
    """The largest scale any word reaches, which is the size a group must fit at."""
    animation, emphasis, kind = spec["animation"], spec["emphasis"], spec["animation"]["type"]
    scale = 1.0
    if kind in WORD_LEVEL_TYPES:
        scale = animation["overshootPct"] / 100
    elif kind == "current-word":
        scale = max(1.0, animation["popPct"] / 100, animation["activeScalePct"] / 100)
    if kind not in WORD_LEVEL_TYPES and kind not in {"karaoke-fill", "highlight-sweep", "typewriter"}:
        scale = max(scale, emphasis["scalePct"] / 100)
    return scale


def safe_width(spec):
    return (spec["playResX"] - spec["position"]["marginL"] - spec["position"]["marginR"]) * spec["grouping"]["maxLines"]


def resolve_font_file(spec, explicit=None):
    """The file behind the spec's family, so a width can be measured."""
    if explicit:
        return Path(explicit)
    family, bold = spec["font"]["family"], spec["font"]["bold"]
    bundled = Path(__file__).resolve().parents[3] / "assets" / "fonts"
    names = {
        "Montserrat Black": "montserrat-black.ttf",
        "Anton": "anton-regular.ttf",
        "Courier Prime": "courier-prime-regular.ttf",
        "Montserrat": "montserrat-bold.ttf" if bold else "montserrat-regular.ttf",
    }
    candidate = bundled / names.get(family, "")
    return candidate if candidate.is_file() else None


def measure_widths(words, font_file, point_size, case="verbatim"):
    """Width of every distinct word, and of a space, at the rendered size.

    Grouping has to know how wide a word will be, and only the font file can
    say. Each distinct word is measured once, so a clip costs one call per
    vocabulary item rather than one per word.
    """

    def render_width(text):
        proc = subprocess.run(
            [
                "magick",
                "-background",
                "none",
                "-font",
                str(font_file),
                "-pointsize",
                str(point_size),
                f"label:{text}",
                "-format",
                "%w",
                "info:",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        return int(proc.stdout.strip())

    # Measure the text as it will RENDER: an upper-case style is much wider than
    # the words it was given, so measuring the raw token under-counts every group.
    widths = {}
    for text in sorted({w["text"] for w in words}):
        measured = render_width(apply_case(text, case, True))
        if measured is None:
            return None
        widths[text] = measured
    # ImageMagick refuses a label that is only whitespace, so take the space
    # from the difference between a spaced and an unspaced pair.
    pair, joined = render_width("n n"), render_width("nn")
    if pair is None or joined is None:
        return None
    widths[" "] = max(0, pair - joined)
    return widths


def group_words(words, grouping, widths=None, budget=None):
    """Chunk words into caption groups: split on speaker turn, sentence end,
    silence gap, or the max-words cap. Never merges across a speaker turn or
    (when sentenceSplit is on) across a sentence boundary."""
    groups, current, width = [], [], 0.0
    space = widths.get(" ", 0) if widths else 0
    for word in words:
        wide = widths.get(word["text"], 0) if widths else 0
        if current:
            gap_ms = (word["start"] - current[-1]["end"]) * 1000
            turn = word["speaker"] != current[-1]["speaker"]
            sentence = grouping["sentenceSplit"] and SENTENCE_END.search(current[-1]["text"])
            # The width test is what closes a group when fitWidth is on; maxWords
            # is only a ceiling, so a caption never grows past a comfortable read.
            too_wide = budget is not None and (width + space + wide) > budget
            if turn or sentence or too_wide or gap_ms > grouping["maxGapMs"] or len(current) >= grouping["maxWords"]:
                groups.append(current)
                current, width = [], 0.0
        width += wide if not current else space + wide
        current.append(word)
    if current:
        groups.append(current)
    if budget is not None and widths:
        lone = [w["text"] for w in words if widths.get(w["text"], 0) > budget]
        if lone:
            print(
                f"note: {len(lone)} word(s) are wider than the safe width on their own "
                f"and cannot be packed smaller: {', '.join(sorted(set(lone))[:4])}",
                file=sys.stderr,
            )

    if grouping["stripFullStops"]:
        for group in groups:
            for word in group:
                stripped = TRAILING_STOPS.sub(r"\1", word["text"])
                if stripped:
                    word["text"] = stripped
    if grouping["stripTrailingCommas"]:
        # Only the last word of a group. A comma inside the group still divides
        # a list on one line, but the caption already ends where the group does.
        for group in groups:
            stripped = TRAILING_COMMA.sub(r"\1", group[-1]["text"])
            if stripped:
                group[-1]["text"] = stripped
    return groups


def format_time(seconds):
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def onset_durations_cs(group, pad_s):
    """Per-word karaoke durations in centiseconds, onset-to-onset so the
    highlight tracks when the next word actually begins."""
    durations = []
    for i, word in enumerate(group):
        is_last = i + 1 == len(group)
        # The last word has no next onset to run to, so it takes its own span plus the pad.
        span = word["end"] - word["start"] + pad_s if is_last else group[i + 1]["start"] - word["start"]
        durations.append(max(1, round(span * 100)))
    return durations


def anchor_xy(spec):
    align, pos = spec["position"]["alignment"], spec["position"]
    horizontal = {"left": pos["marginL"], "center": spec["playResX"] / 2, "right": spec["playResX"] - pos["marginR"]}
    vertical = {"bottom": spec["playResY"] - pos["marginV"], "middle": spec["playResY"] / 2, "top": pos["marginV"]}
    v, h = align.split("-")
    return round(horizontal[h]), round(vertical[v])


def build_events(groups, spec):
    """Return (dialogue_lines, fit_lines). fit_lines describe the widest text
    simultaneously on screen per event, at the animation's PEAK scale, for the
    caption fit report."""
    animation, grouping, case_mode = spec["animation"], spec["grouping"], spec["font"]["case"]
    colors, border, emphasis = spec["colors"], spec["border"], spec["emphasis"]
    pad_s = grouping["padMs"] / 1000
    kind = animation["type"]
    karaoke_kind = kind in {"karaoke-fill", "highlight-sweep"}

    # Lead: shift everything uniformly earlier so captions land slightly before
    # the audio (preserves karaoke durations, which are onset-to-onset).
    lead_s = animation["leadMs"] / 1000
    if lead_s:
        groups = [
            [{**w, "start": max(0.0, w["start"] - lead_s), "end": max(0.0, w["end"] - lead_s)} for w in g]
            for g in groups
        ]

    # Emphasized words rotate through the highlight palette in order of appearance.
    palette = colors["highlightPalette"]
    emph_count = 0
    for g in groups:
        for w in g:
            if w["emphasize"]:
                w["_emphColor"] = palette[emph_count % len(palette)] if palette else colors["highlight"]
                emph_count += 1

    primary_inline = hex_to_inline(colors["primary"], "colors.primary")
    outline_inline = hex_to_inline(
        colors["box"] if border["style"] == "box" and colors["box"] else colors["outline"], "colors.outline"
    )
    speakers = colors["speakers"] or {}

    def speaker_inline(word):
        # Per-speaker text colors don't apply in karaoke modes, where color is
        # owned by the style's Primary/Secondary karaoke transition.
        spk = word["speaker"]
        if spk is not None and spk in speakers and not karaoke_kind:
            return hex_to_inline(speakers[spk], f"colors.speakers.{spk}")
        return primary_inline

    def label_for(group):
        sl = grouping["speakerLabels"]
        spk = group[0]["speaker"]
        if not sl or spk is None:
            return ""
        name = sl.get(spk, str(spk)) if isinstance(sl, dict) else str(spk)
        return f"{name.upper()}: "

    def emph_wrap(txt, color_hex, base):
        open_tags = f"\\c{hex_to_inline(color_hex, 'highlight color')}"
        close_tags = f"\\c{base}"
        if emphasis["scalePct"] != 100:
            open_tags += f"\\fscx{emphasis['scalePct']}\\fscy{emphasis['scalePct']}"
            close_tags += "\\fscx100\\fscy100"
        if emphasis["bold"]:
            open_tags += "\\b1"
            close_tags += "\\b0"
        return f"{{{open_tags}}}{txt}{{{close_tags}}}"

    events, fit_lines = [], []
    peak_scale = 1.0
    if kind in WORD_LEVEL_TYPES:
        peak_scale = animation["overshootPct"] / 100
    elif kind == "current-word":
        peak_scale = max(1.0, animation["popPct"] / 100, animation["activeScalePct"] / 100)
    if emph_count and kind not in WORD_LEVEL_TYPES and not karaoke_kind and kind != "typewriter":
        peak_scale = max(peak_scale, emphasis["scalePct"] / 100)

    blur_prefix = f"{{\\blur{border['blur']}}}" if border["blur"] > 0 else ""

    def dialogue(start, end, text):
        events.append(f"Dialogue: 0,{format_time(start)},{format_time(end)},Caption,,0,0,0,,{blur_prefix}{text}")

    def fit(text):
        # With maxLines >= 2 the budget is per-line width x lines (smart wrap
        # balances lines; the style proof catches word-boundary edge cases).
        per_line = spec["playResX"] - spec["position"]["marginL"] - spec["position"]["marginR"]
        fit_lines.append(
            {
                "text": text,
                "pointSize": round(spec["font"]["size"] * peak_scale),
                "maxWidth": per_line * spec["grouping"]["maxLines"],
                "maxLines": spec["grouping"]["maxLines"],
                "fontFamily": spec["font"]["family"],
            }
        )

    if kind in WORD_LEVEL_TYPES:
        appear, settle = animation["appearMs"], animation["settleMs"]
        over, entry = animation["overshootPct"], animation["entryPct"]
        if kind == "word-pop":
            effect = (
                f"{{\\fscx{entry}\\fscy{entry}"
                f"\\t(0,{appear},\\fscx{over}\\fscy{over})"
                f"\\t({appear},{appear + settle},\\fscx100\\fscy100)}}"
            )
        else:  # bounce-in
            x, y = anchor_xy(spec)
            rise = animation["riseHeight"]
            effect = (
                f"{{\\move({x},{y + rise},{x},{y},0,{appear})"
                f"\\t(0,{appear},\\fscx{over}\\fscy{over})"
                f"\\t({appear},{appear + settle},\\fscx100\\fscy100)}}"
            )
        flat = [w for g in groups for w in g]
        for i, word in enumerate(flat):
            text = (
                word["text"]
                if word.get("protect_case")
                else apply_case(word["text"], case_mode, word.get("capitalize", False))
            )
            start = word["start"]
            next_start = flat[i + 1]["start"] if i + 1 < len(flat) else None
            end = next_start if next_start is not None else word["end"] + pad_s
            end = max(end, start + 0.15)  # minimum readable display...
            if next_start is not None:  # ...but never overlap the next word (stacked captions)
                end = min(end, next_start)
            end = max(end, start + 0.05)
            base = speaker_inline(word)
            if word["emphasize"]:
                color = f"{{\\c{hex_to_inline(word['_emphColor'], 'highlight color')}}}"
            elif base != primary_inline:
                color = f"{{\\c{base}}}"
            else:
                color = ""
            dialogue(start, end, f"{effect}{color}{text}")
            fit(text)
        return events, fit_lines

    for gi, group in enumerate(groups):
        cased = [
            w["text"] if w.get("protect_case") else apply_case(w["text"], case_mode, w.get("capitalize", False))
            for w in group
        ]
        start, end = group[0]["start"], group[-1]["end"] + pad_s
        if gi + 1 < len(groups):  # the pad must never overlap the next group (stacked captions)
            end = min(end, groups[gi + 1][0]["start"])
        end = max(end, start + 0.05)
        base = speaker_inline(group[0])
        base_prefix = f"{{\\c{base}}}" if base != primary_inline else ""
        label = label_for(group)
        phrase = label + " ".join(cased)

        if kind == "none":
            parts = [
                emph_wrap(txt, group[j]["_emphColor"], base) if group[j]["emphasize"] else txt
                for j, txt in enumerate(cased)
            ]
            dialogue(start, end, base_prefix + label + " ".join(parts))
        elif kind == "current-word":
            # One event per word interval; the whole phrase stays on screen and
            # only the word being spoken (plus any emphasized word) is highlighted.
            pop = animation["popPct"]
            mode = animation["highlightMode"]
            active_scale = animation["activeScalePct"]
            pill = max(8, round(spec["font"]["size"] * 0.14))
            for i, word in enumerate(group):
                w_start = word["start"]
                w_end = group[i + 1]["start"] if i + 1 < len(group) else end
                w_end = max(w_end, w_start + 0.05)
                parts = []
                for j, txt in enumerate(cased):
                    if j == i:
                        color_hex = group[j]["_emphColor"] if group[j]["emphasize"] else colors["highlight"]
                        active_hl = hex_to_inline(color_hex, "highlight color")
                        if mode == "box":
                            open_tags = f"\\bord{pill}\\3c{active_hl}\\shad0"
                            close_tags = f"\\bord{border['outline']}\\3c{outline_inline}\\shad{border['shadow']}"
                        elif mode == "glow":
                            glow = max(5, border["blur"])
                            open_tags = f"\\bord4\\blur{glow}\\3c{active_hl}"
                            close_tags = f"\\bord{border['outline']}\\blur{border['blur']}\\3c{outline_inline}"
                        else:  # color
                            open_tags = f"\\c{active_hl}"
                            close_tags = f"\\c{base}"
                        if active_scale != 100:
                            open_tags += f"\\fscx{active_scale}\\fscy{active_scale}"
                            close_tags += "\\fscx100\\fscy100"
                        parts.append(f"{{{open_tags}}}{txt}{{{close_tags}}}")
                    elif group[j]["emphasize"]:
                        parts.append(emph_wrap(txt, group[j]["_emphColor"], base))
                    else:
                        parts.append(txt)
                prefix = base_prefix
                if i == 0 and pop > 100:
                    prefix += f"{{\\fscx{pop}\\fscy{pop}\\t(0,{animation['appearMs']},\\fscx100\\fscy100)}}"
                dialogue(w_start, w_end, prefix + label + " ".join(parts))
        elif karaoke_kind:
            tag = "kf" if kind == "karaoke-fill" else "k"
            durations = onset_durations_cs(group, pad_s)
            body = "".join(f"{{\\{tag}{d}}}{t} " for d, t in zip(durations, cased, strict=True)).strip()
            dialogue(start, end, label + body)
        elif kind == "typewriter":
            ms = animation["msPerChar"]
            total_reveal = len(phrase) * ms / 1000
            available = (end - start) * 0.7
            if total_reveal > available:
                ms = max(15, int(available * 1000 / max(1, len(phrase))))
            t = start
            for i in range(1, len(phrase)):
                step_end = min(t + ms / 1000, end)
                if step_end <= t:
                    break
                dialogue(t, step_end, base_prefix + phrase[:i])
                t = step_end
            dialogue(t, end, base_prefix + phrase)
        fit(phrase)
    return events, fit_lines


def style_line(spec):
    font, colors, border, position = spec["font"], spec["colors"], spec["border"], spec["position"]
    if border["style"] == "box":
        box = colors["box"] or colors["outline"]
        outline_color = hex_to_ass(box, "colors.box")
        back_color = outline_color  # VSFilter reads the box from BackColour, libass from OutlineColour — set both
        border_style = 3
    else:
        outline_color = hex_to_ass(colors["outline"], "colors.outline")
        back_color = hex_to_ass(colors["shadow"] or colors["outline"], "colors.shadow")
        border_style = 1
    fields = [
        "Caption",
        font["family"],
        font["size"],
        hex_to_ass(colors["primary"], "colors.primary"),
        hex_to_ass(colors["highlight"], "colors.highlight"),
        outline_color,
        back_color,
        -1 if font["bold"] else 0,
        -1 if font["italic"] else 0,
        0,
        0,
        100,
        100,
        font["spacing"],
        0,
        border_style,
        border["outline"],
        border["shadow"],
        ALIGNMENT[position["alignment"]],
        position["marginL"],
        position["marginR"],
        position["marginV"],
        1,
    ]
    return "Style: " + ",".join(str(f) for f in fields)


def build_ass(spec, events):
    # Single-line specs use WrapStyle 2 (no wrapping) on purpose: an overflowing
    # line must fail the fit report visibly, never silently wrap into a second
    # line. Specs that explicitly allow lines (grouping.maxLines >= 2) get smart
    # wrapping instead.
    wrap_style = 0 if spec["grouping"]["maxLines"] > 1 else 2
    header = f"""[Script Info]
Title: {spec.get("name", "captions")}
ScriptType: v4.00+
WrapStyle: {wrap_style}
ScaledBorderAndShadow: yes
PlayResX: {spec["playResX"]}
PlayResY: {spec["playResY"]}

[V4+ Styles]
Format: {", ".join(STYLE_FIELDS)}
{style_line(spec)}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return header + "\n".join(events) + "\n"


def resolve_style(style_arg):
    path = Path(style_arg)
    if not path.exists():
        candidate = Path(__file__).resolve().parents[1] / "assets" / f"{style_arg}.json"
        if candidate.exists():
            path = candidate
        else:
            fail(f"style '{style_arg}' is neither a file nor a preset in {candidate.parent}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--style",
        default="bold-social",
        help="Preset name (from modules/captions/assets/) or path to a style spec JSON. Defaults to bold-social.",
    )
    parser.add_argument("--words", help="Word-timings JSON for the clip span. Required unless --check.")
    parser.add_argument(
        "--brand-kit",
        help="Path to a brand kit's kit.json; its style/overrides layer "
        "between the preset and --override (see the brand module).",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="dot.path=value",
        help="Per-clip style override, e.g. colors.highlight=#FFD400 or font.size=84. Repeatable.",
    )
    parser.add_argument("--font-file", help="TTF/OTF to measure with. Defaults to the bundled file for the family.")
    parser.add_argument("--out", help="Output .ass path. Required unless --check.")
    parser.add_argument(
        "--emit-lines",
        help="Write the caption fit stub (text/pointSize/maxWidth per event at "
        "peak animation scale) for the fit-measurement step.",
    )
    parser.add_argument(
        "--emit-spec", help="Write the fully resolved style spec JSON (record this path in caption_plan.json)."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the resolved spec and exit without needing words or writing output.",
    )
    args = parser.parse_args()

    spec = copy.deepcopy(DEFAULTS)
    style_path = resolve_style(args.style)
    preset = json.loads(style_path.read_text())
    deep_merge(spec, preset)
    spec["name"] = preset.get("name", style_path.stem)

    if args.brand_kit:
        kit_path = Path(args.brand_kit)
        kit = json.loads(kit_path.read_text())
        deep_merge(spec, kit.get("captionOverrides", {}))
    for raw in args.override:
        deep_merge(spec, parse_override(raw))

    failures, warnings = validate_spec(spec)
    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)
    if failures:
        for message in failures:
            print(f"FAIL: {message}", file=sys.stderr)
        return 1

    if args.emit_spec:
        Path(args.emit_spec).write_text(json.dumps(spec, indent=2) + "\n")

    if args.check:
        print(f"style spec OK: {spec['name']} ({len(warnings)} warning(s))")
        # Check alone is check-only; check with a real job carries on and builds it,
        # or --emit-lines returns nothing and the QA gate fails on the absent file.
        if not (args.words and args.out):
            return 0

    if not args.words or not args.out:
        fail("--words and --out are required unless --check")

    words = load_words(args.words)
    removed = faithful_clean(words)
    if removed:
        print(f"note: faithful-clean dropped or joined {removed} word(s)", file=sys.stderr)
    apply_casing(words, spec["casing"])
    flag_filler_candidates(words)
    mark_sentence_starts(words)
    widths = budget = None
    if spec["grouping"]["fitWidth"] and spec["animation"]["type"] in GROUP_ON_SCREEN:
        font_file = resolve_font_file(spec, args.font_file)
        if font_file:
            widths = measure_widths(
                words, font_file, round(spec["font"]["size"] * peak_scale(spec)), spec["font"]["case"]
            )
            if widths:
                # libass advances run a few percent wider than the measure, so pack with headroom
                budget = safe_width(spec) * 0.94
            else:
                fail(
                    f"could not measure text in {font_file} - install ImageMagick, or the caption "
                    f"is packed by word count alone and wraps wherever it does not fit"
                )
        else:
            fail(
                f"no font file for '{spec['font']['family']}' - pass --font-file with the file libass "
                f"will render, because a caption packed by word count alone wraps wherever it does not fit"
            )
    groups = group_words(words, spec["grouping"], widths, budget)
    events, fit_lines = build_events(groups, spec)
    Path(args.out).write_text(build_ass(spec, events))
    if args.emit_lines:
        Path(args.emit_lines).write_text(json.dumps(fit_lines, indent=2) + "\n")

    print(
        f"{args.out}: {len(events)} events from {len(words)} words in {len(groups)} groups "
        f"({spec['name']}, {spec['animation']['type']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
