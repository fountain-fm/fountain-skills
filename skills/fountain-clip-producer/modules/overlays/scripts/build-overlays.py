#!/usr/bin/env python3
"""Compile an overlay spec into a complete ffmpeg command.

The overlay spec is the overlays counterpart of the caption style spec: a JSON
document listing layers (logo images, hook title cards, lower thirds, progress
bars, audiograms, blurred background fill), each with nine-point positioning,
timing windows, and fades. This script validates the spec, resolves the show's
brand kit standing layers, and prints (or runs) the single ffmpeg command that
composites everything in one pass — so overlay work is reproducible from the
recorded plan instead of improvised filtergraphs.

Precedence mirrors captions: brand kit standing layers render first (underneath),
then the spec's layers in order; --override dot paths (list indices allowed,
e.g. layers.0.opacity=0.6) apply to the spec last.

Omit --run to print the composed ffmpeg command instead of executing it, which
is the way to inspect or debug a single layer's filtergraph.
"""

import argparse
import copy
import json
import shlex
import subprocess
import sys
from pathlib import Path

LAYER_DEFAULTS = {
    "image": {
        # asset may be a still (PNG/JPG) or a video/GIF (B-roll insert, animated
        # CTA sticker — alpha-channel .mov/.webm composites transparently)
        "type": "image",
        "asset": None,
        "width": 180,
        "opacity": 1.0,
        "position": "top-right",
        "marginH": 40,
        "marginV": 40,
        "start": 0.0,
        "end": None,
        "fadeInMs": 0,
        "fadeOutMs": 0,
        "loop": False,  # video/GIF assets only; stills always persist
    },
    "title": {
        "type": "title",
        "text": None,
        "fontFile": None,
        "size": 64,
        "color": "#FFFFFF",
        "borderW": 4,
        "borderColor": "#000000",
        "boxColor": None,  # solid bar behind the text (headline-bar style)
        "boxPad": 12,
        "position": "top-center",
        "marginH": 60,
        "marginV": 300,
        "start": 0.0,
        "end": 2.5,
        "fadeInMs": 200,
        "fadeOutMs": 300,
    },
    "lowerThird": {
        "type": "lowerThird",
        "lines": None,
        "fontFile": None,
        "size": 44,
        "secondarySize": 30,
        "color": "#FFFFFF",
        "borderW": 3,
        "borderColor": "#000000",
        "boxColor": None,
        "boxPad": 10,
        "position": "bottom-left",
        "marginH": 70,
        "marginV": 560,
        "start": 2.0,
        "end": 7.0,
        "fadeInMs": 400,
        "fadeOutMs": 400,
    },
    "watermark": {
        # persistent small text (@handle) for the whole clip
        "type": "watermark",
        "text": None,
        "fontFile": None,
        "size": 30,
        "color": "#FFFFFFB3",
        "borderW": 2,
        "borderColor": "#000000",
        "position": "top-left",
        "marginH": 40,
        "marginV": 40,
    },
    "scrim": {
        # a soft dark band so bright footage cannot swallow the caption under it
        "type": "scrim",
        "height": 620,
        "color": "#000000",
        "opacity": 0.85,
        "position": "bottom",  # bottom | top
        "curve": 1.6,  # >1 keeps the middle clearer and darkens only near the edge
    },
    "progressBar": {
        "type": "progressBar",
        "height": 12,
        "color": "#FFFFFFD9",
        "position": "bottom",
    },
    "audiogram": {
        "type": "audiogram",
        "width": 900,
        "height": 140,
        "color": "#FFFFFFE6",
        "position": "bottom-center",
        "marginV": 560,
        "waveMode": "filled",  # filled | line | bars
    },
    "blurFill": {
        # base composition: foreground scaled onto a background. scale=1.0 +
        # background=blur is the classic blurred fill; scale<1 + a solid color
        # + cornerRadius is the picture-in-picture card look.
        "type": "blurFill",
        "sigma": 30,
        "scale": 1.0,
        "background": "blur",  # "blur" or a hex color
        "cornerRadius": 0,
    },
}

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".gif"}
WAVE_MODES = {"filled": ("showwaves", "cline"), "line": ("showwaves", "p2p"), "bars": ("showfreqs", "bar")}

HORIZONTAL = {"left", "center", "right"}
VERTICAL = {"top", "middle", "bottom"}


def is_remote(value):
    """A URL ffmpeg opens itself, rather than a file on this machine."""
    return str(value).startswith(("http://", "https://"))


def asset_suffix(value):
    """The file extension of an asset, ignoring any query a URL carries."""
    return Path(str(value).split("?", 1)[0].split("#", 1)[0]).suffix.lower()


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def ff_color(value, context):
    """#RRGGBB or #RRGGBBAA -> ffmpeg color spec (0xRRGGBB@alpha)."""
    raw = str(value).lstrip("#")
    if len(raw) == 6:
        return f"0x{raw}"
    if len(raw) == 8:
        alpha = int(raw[6:8], 16) / 255
        return f"0x{raw[:6]}@{alpha:.3f}"
    fail(f"{context}: expected #RRGGBB or #RRGGBBAA, got '{value}'")


def escape_drawtext(text):
    out = []
    for ch in str(text):
        if ch in "\\':,%":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def split_position(pos, context, allowed=None):
    try:
        v, h = pos.split("-")
    except ValueError:
        fail(f"{context}: position '{pos}' is not vertical-horizontal (e.g. top-right)")
    if v not in VERTICAL or h not in HORIZONTAL:
        fail(f"{context}: position '{pos}' is not one of {sorted(VERTICAL)} x {sorted(HORIZONTAL)}")
    return v, h


def apply_override(spec, raw):
    if "=" not in raw:
        fail(f"--override expects dot.path=value, got '{raw}'")
    dotted, value = raw.split("=", 1)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    node = spec
    keys = dotted.split(".")
    for i, key in enumerate(keys):
        last = i == len(keys) - 1
        if isinstance(node, list):
            try:
                idx = int(key)
                node[idx]  # noqa: B018 — bounds check
            except (ValueError, IndexError):
                fail(f"override '{dotted}': '{key}' is not a valid index into a {len(node)}-item list")
            if last:
                node[idx] = parsed
            else:
                node = node[idx]
        elif isinstance(node, dict):
            if key not in node:
                fail(f"override '{dotted}': unknown field '{key}'")
            if last:
                node[key] = parsed
            else:
                node = node[key]
        else:
            fail(f"override '{dotted}': '{key}' does not address into a value")


def resolve_layers(spec, kit, kit_dir):
    layers = []
    if kit:
        kit_overlays = kit.get("overlays") or {}
        kit_layers = kit_overlays.get("layers", [])
        for layer in kit_layers:
            layer = dict(layer)
            # kit asset/font paths resolve relative to the kit directory
            for field in ("asset", "fontFile"):
                if layer.get(field) and not is_remote(layer[field]) and not Path(layer[field]).is_absolute():
                    layer[field] = str(kit_dir / layer[field])
            layers.append(layer)
    layers.extend(spec.get("layers", []))
    resolved = []
    for i, layer in enumerate(layers):
        kind = layer.get("type")
        if kind not in LAYER_DEFAULTS:
            fail(f"layers[{i}]: unknown type '{kind}' (expected one of {sorted(LAYER_DEFAULTS)})")
        merged = copy.deepcopy(LAYER_DEFAULTS[kind])
        for key, value in layer.items():
            if key not in merged and key != "name":
                fail(f"layers[{i}] ({kind}): unknown field '{key}'")
            merged[key] = value
        resolved.append(merged)
    return resolved


def validate(layers, duration):
    warnings = []
    blur_count = sum(1 for layer in layers if layer["type"] == "blurFill")
    if blur_count > 1:
        fail("only one blurFill layer is allowed")
    if blur_count and layers[0]["type"] != "blurFill":
        fail("blurFill must be the first layer — it builds the base the others sit on")
    needs_duration = any(layer["type"] in {"image", "progressBar"} for layer in layers)
    if needs_duration and duration is None:
        fail(
            "--duration is required when the spec has image or progressBar layers "
            "(looping images and progress math need the clip length)"
        )
    for i, layer in enumerate(layers):
        kind = layer["type"]
        ctx = f"layers[{i}] ({kind})"
        if kind == "image":
            if not layer["asset"]:
                fail(f"{ctx}: 'asset' is required")
            if not is_remote(layer["asset"]) and not Path(layer["asset"]).exists():
                fail(f"{ctx}: asset not found: {layer['asset']}")
            if not 0 < layer["opacity"] <= 1:
                fail(f"{ctx}: opacity {layer['opacity']} outside (0, 1]")
        if kind in {"title", "watermark"} and not layer["text"]:
            fail(f"{ctx}: 'text' is required")
        if kind == "lowerThird" and not layer["lines"]:
            fail(f"{ctx}: 'lines' is required (one or two strings)")
        if kind in {"title", "lowerThird", "watermark"} and not layer["fontFile"]:
            warnings.append(
                f"{ctx}: no fontFile — drawtext falls back to the libass/fontconfig default; "
                "point it at the brand kit's font file for a branded result"
            )
        if kind == "audiogram" and layer["waveMode"] not in WAVE_MODES:
            fail(f"{ctx}: waveMode '{layer['waveMode']}' is not one of {sorted(WAVE_MODES)}")
        if kind == "scrim":
            if layer["position"] not in {"bottom", "top"}:
                fail(f"layers[{i}] (scrim): position '{layer['position']}' is not bottom or top")
            if not 0 < layer["opacity"] <= 1:
                fail(f"layers[{i}] (scrim): opacity {layer['opacity']} is not between 0 and 1")
        if kind == "blurFill":
            if not 0.3 <= layer["scale"] <= 1.0:
                fail(f"{ctx}: scale {layer['scale']} outside [0.3, 1.0]")
            if layer["cornerRadius"] < 0:
                fail(f"{ctx}: cornerRadius must be >= 0")
        if kind in {"title", "lowerThird", "image", "audiogram", "watermark"}:
            pos = layer.get("position")
            if pos:
                v, h = split_position(pos, ctx)
                if v == "bottom" and layer.get("marginV", 0) < 400:
                    warnings.append(
                        f"{ctx}: bottom position with marginV {layer.get('marginV')} may sit in "
                        "the caption zone — check against the caption spec's marginV"
                    )
                if h == "right" and layer.get("marginH", 0) < 100 and v == "middle":
                    warnings.append(
                        f"{ctx}: middle-right with marginH {layer.get('marginH')} sits in the "
                        "platform engagement rail (right ~10% of frame)"
                    )
        start, end = layer.get("start"), layer.get("end")
        if start is not None and end is not None and end <= start:
            fail(f"{ctx}: end {end} <= start {start}")
        if duration is not None and start is not None and start >= duration:
            fail(f"{ctx}: start {start} is beyond the clip duration {duration}")
    return warnings


def xy_exprs(layer, w_expr, h_expr):
    v, h = split_position(layer["position"], f"{layer['type']} position")
    mh, mv = layer.get("marginH", 0), layer.get("marginV", 0)
    x = {"left": str(mh), "center": f"(W-{w_expr})/2", "right": f"W-{w_expr}-{mh}"}[h]
    y = {"top": str(mv), "middle": f"(H-{h_expr})/2", "bottom": f"H-{h_expr}-{mv}"}[v]
    return x, y


def drawtext_xy(layer, y_offset=0):
    v, h = split_position(layer["position"], f"{layer['type']} position")
    mh, mv = layer["marginH"], layer["marginV"]
    x = {"left": str(mh), "center": "(w-tw)/2", "right": f"w-tw-{mh}"}[h]
    base_y = {"top": str(mv), "middle": "(h-th)/2", "bottom": f"h-th-{mv}"}[v]
    return x, f"{base_y}+{y_offset}" if y_offset else base_y


def fade_alpha(layer):
    start, end = layer["start"], layer["end"]
    fi, fo = layer["fadeInMs"] / 1000, layer["fadeOutMs"] / 1000
    parts = []
    if fi > 0:
        parts.append(f"min(1\\,max(0\\,(t-{start})/{fi}))")
    if fo > 0 and end is not None:
        parts.append(f"min(1\\,max(0\\,({end}-t)/{fo}))")
    return "*".join(parts) if parts else None


def drawtext_filter(layer, text, size, y_offset, duration, timed=True):
    x, y = drawtext_xy(layer, y_offset)
    opts = [
        f"text='{escape_drawtext(text)}'",
        f"fontsize={size}",
        f"fontcolor={ff_color(layer['color'], 'text color')}",
        f"borderw={layer['borderW']}",
        f"bordercolor={ff_color(layer['borderColor'], 'border color')}",
        f"x={x}",
        f"y={y}",
    ]
    if layer["fontFile"]:
        opts.insert(0, f"fontfile={layer['fontFile']}")
    if layer.get("boxColor"):
        opts.append("box=1")
        opts.append(f"boxcolor={ff_color(layer['boxColor'], 'box color')}")
        opts.append(f"boxborderw={layer['boxPad']}")
    if timed:
        end = layer["end"] if layer["end"] is not None else (duration if duration is not None else 1e9)
        opts.append(f"enable='between(t,{layer['start']},{end})'")
        alpha = fade_alpha({**layer, "end": end})
        if alpha:
            opts.append(f"alpha='{alpha}'")
    return "drawtext=" + ":".join(opts)


def build_command(layers, args):
    duration = args.duration
    inputs = [("", args.input)]
    graph = []
    chain = "[0:v]"
    label_n = 0

    def next_label():
        nonlocal label_n
        label_n += 1
        return f"[v{label_n}]"

    if layers and layers[0]["type"] == "blurFill":
        blur = layers[0]
        out = next_label()
        fg_w = round(args.width * blur["scale"] / 2) * 2
        fg_steps = [f"scale={fg_w}:-2"]
        if blur["cornerRadius"] > 0:
            r = blur["cornerRadius"]
            corners = "+".join(
                f"({xc}*{yc}*gt((X-{cx})^2+(Y-{cy})^2,{r * r}))"
                for xc, yc, cx, cy in (
                    (f"lt(X,{r})", f"lt(Y,{r})", r, r),
                    (f"gt(X,W-{r})", f"lt(Y,{r})", f"(W-{r})", r),
                    (f"lt(X,{r})", f"gt(Y,H-{r})", r, f"(H-{r})"),
                    (f"gt(X,W-{r})", f"gt(Y,H-{r})", f"(W-{r})", f"(H-{r})"),
                )
            )
            fg_steps += ["format=rgba", f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*not({corners})'"]
        if blur["background"] == "blur":
            graph.append(
                f"[0:v]scale={args.width}:{args.height}:force_original_aspect_ratio=increase,"
                f"crop={args.width}:{args.height},gblur=sigma={blur['sigma']}[bg];"
                f"[0:v]{','.join(fg_steps)}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2{out}"
            )
        else:
            graph.append(
                f"color=c={ff_color(blur['background'], 'blurFill background')}:s={args.width}x{args.height}[bg];"
                f"[0:v]{','.join(fg_steps)}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1{out}"
            )
        chain = out
        layers = layers[1:]

    for layer in layers:
        kind = layer["type"]
        if kind == "image":
            is_video = asset_suffix(layer["asset"]) in VIDEO_EXTS
            if not is_video:
                in_flags = "-loop 1"
            elif layer["loop"]:
                in_flags = "-ignore_loop 0" if asset_suffix(layer["asset"]) == ".gif" else "-stream_loop -1"
            else:
                in_flags = ""
            inputs.append((in_flags, layer["asset"]))
            idx = len(inputs) - 1
            steps = [f"format=rgba,scale={layer['width']}:-2"]
            if is_video:
                # shift the asset's own timeline to the layer's start
                steps.insert(0, f"setpts=PTS-STARTPTS+{layer['start']}/TB")
            end = layer["end"] if layer["end"] is not None else duration
            if layer["fadeInMs"]:
                steps.append(f"fade=t=in:st={layer['start']}:d={layer['fadeInMs'] / 1000}:alpha=1")
            if layer["fadeOutMs"] and end is not None:
                steps.append(f"fade=t=out:st={end - layer['fadeOutMs'] / 1000}:d={layer['fadeOutMs'] / 1000}:alpha=1")
            if layer["opacity"] < 1:
                steps.append(f"colorchannelmixer=aa={layer['opacity']}")
            lyr = f"[l{idx}]"
            graph.append(f"[{idx}:v]{','.join(steps)}{lyr}")
            x, y = xy_exprs(layer, "w", "h")
            out = next_label()
            enable = f":enable='between(t,{layer['start']},{end})'" if (layer["start"] or end is not None) else ""
            eof = ":eof_action=pass" if is_video and not layer["loop"] else ""
            graph.append(f"{chain}{lyr}overlay=x={x}:y={y}{enable}{eof}{out}")
            chain = out
        elif kind == "title":
            out = next_label()
            graph.append(f"{chain}{drawtext_filter(layer, layer['text'], layer['size'], 0, duration)}{out}")
            chain = out
        elif kind == "watermark":
            out = next_label()
            graph.append(
                f"{chain}{drawtext_filter(layer, layer['text'], layer['size'], 0, duration, timed=False)}{out}"
            )
            chain = out
        elif kind == "lowerThird":
            lines = layer["lines"] if isinstance(layer["lines"], list) else [layer["lines"]]
            out = next_label()
            filters = [drawtext_filter(layer, lines[0], layer["size"], 0, duration)]
            if len(lines) > 1:
                filters.append(
                    drawtext_filter(layer, lines[1], layer["secondarySize"], round(layer["size"] * 1.3), duration)
                )
            graph.append(f"{chain}{','.join(filters)}{out}")
            chain = out
        elif kind == "progressBar":
            out = next_label()
            graph.append(
                f"{chain}drawbox=x=0:y=ih-{layer['height']}:w='iw*t/{duration}':"
                f"h={layer['height']}:color={ff_color(layer['color'], 'progress color')}:t=fill{out}"
            )
            chain = out
        elif kind == "scrim":
            band, out = f"[scrim{label_n}]", next_label()
            alpha = round(layer["opacity"] * 255)
            raw = str(layer["color"]).lstrip("#")
            r, g, b = (int(raw[j : j + 2], 16) for j in (0, 2, 4))
            # geq paints the alpha ramp itself; the gradients source only gives a hard band.
            ramp = "Y/H" if layer["position"] == "bottom" else "(1-Y/H)"
            graph.append(
                f"color=c=black:s={args.width}x{layer['height']}:d={duration},format=rgba,"
                rf"geq=r={r}:g={g}:b={b}:a='{alpha}*pow({ramp}\,{layer['curve']})'{band}"
            )
            y = "H-h" if layer["position"] == "bottom" else "0"
            graph.append(f"{chain}{band}overlay=0:{y}{out}")
            chain = out
        elif kind == "audiogram":
            wave = f"[wave{label_n}]"
            out = next_label()
            x, y = xy_exprs(layer, "w", "h")
            filt, mode = WAVE_MODES[layer["waveMode"]]
            color = ff_color(layer["color"], "audiogram color")
            if filt == "showwaves":
                graph.append(
                    # draw=full paints a solid wave; the default trace is a hairline that
                    # disappears over footage. sqrt lifts speech, which sits low on a
                    # linear scale and otherwise reads as a flat line.
                    f"[0:a]showwaves=s={layer['width']}x{layer['height']}:mode={mode}"
                    f":draw=full:scale=sqrt:colors={color}:rate=30{wave}"
                )
            else:
                graph.append(
                    f"[0:a]showfreqs=s={layer['width']}x{layer['height']}:mode={mode}:colors={color}:ascale=cbrt{wave}"
                )
            graph.append(f"{chain}{wave}overlay=x={x}:y={y}{out}")
            chain = out

    cmd = [args.ffmpeg, "-hide_banner", "-y"]
    for flags, path in inputs:
        if flags:
            cmd.extend(flags.split())
        cmd.extend(["-i", path])
    cmd.extend(["-filter_complex", ";".join(graph), "-map", chain.strip("[]").join(["[", "]"]), "-map", "0:a?"])
    if duration is not None:
        cmd.extend(["-t", str(duration)])
    cmd.extend(
        ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", args.output]
    )
    return cmd


def resolve_spec_path(spec_arg):
    path = Path(spec_arg)
    if not path.exists():
        candidate = Path(__file__).resolve().parents[1] / "assets" / f"{spec_arg}.json"
        if candidate.exists():
            path = candidate
        else:
            fail(f"spec '{spec_arg}' is neither a file nor a preset in {candidate.parent}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--spec",
        help="Overlay preset name (from modules/overlays/assets/) or path to an overlay spec JSON. "
        "Optional when --brand-kit names a default via overlays.preset.",
    )
    parser.add_argument("--input", required=True, help="The clip to composite onto (usually the vertical export).")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--duration", type=float, help="Clip duration in seconds. Required for image/progressBar layers."
    )
    parser.add_argument(
        "--brand-kit",
        help="kit.json whose overlays.layers render underneath the spec's "
        "layers; kit asset paths resolve relative to the kit.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="dot.path=value",
        help="Spec override; list indices allowed, e.g. layers.0.text='new hook'. Repeatable.",
    )
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--emit-plan", help="Write the fully resolved layer list (record this in the clip manifest).")
    parser.add_argument(
        "--ffmpeg",
        default="ffmpeg",
        help="ffmpeg binary to use. A stock build often lacks drawtext, so pass the one module preflight names.",
    )
    parser.add_argument("--run", action="store_true", help="Execute the ffmpeg command instead of printing it.")
    args = parser.parse_args()

    kit, kit_dir = None, None
    if args.brand_kit:
        kit_path = Path(args.brand_kit)
        kit = json.loads(kit_path.read_text())
        kit_dir = kit_path.parent

    spec_arg = args.spec or (kit or {}).get("overlays", {}).get("preset")
    if not spec_arg:
        fail("no overlay spec: pass --spec, or set overlays.preset in the brand kit")
    spec_path = resolve_spec_path(spec_arg)
    spec = json.loads(spec_path.read_text())
    for raw in args.override:
        apply_override(spec, raw)
    # A preset that ships its own asset names it beside itself, so resolve a
    # relative path against the preset rather than against the caller's cwd.
    # An override always wins, because it is applied above.
    for layer in spec.get("layers", []):
        for field in ("asset", "fontFile"):
            value = layer.get(field)
            if value and not is_remote(value) and not Path(value).is_absolute() and not Path(value).exists():
                beside = spec_path.parent / value
                if beside.is_file():
                    layer[field] = str(beside)

    layers = resolve_layers(spec, kit, kit_dir)
    if not layers:
        fail("no layers to composite (spec and kit are both empty)")
    for message in validate(layers, args.duration):
        print(f"warning: {message}", file=sys.stderr)

    if args.emit_plan:
        Path(args.emit_plan).write_text(json.dumps({"spec": str(spec_path), "layers": layers}, indent=2) + "\n")

    cmd = build_command(layers, args)
    if args.run:
        proc = subprocess.run(cmd)
        return proc.returncode
    print(" ".join(shlex.quote(c) for c in cmd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
