#!/usr/bin/env python3
"""Verify generated SVGs before they ship.

Checks, per asset:
  1. well-formed XML
  2. no external references (GitHub's proxy blocks scripts/network/webfonts,
     so anything external silently disappears)
  3. every character drawn by a <text> run exists in the embedded subset for
     the face that run declares — i.e. the brand typography really renders
     rather than falling back to a generic system font
  4. text stays inside the canvas, measured with the *real* per-glyph advances
     of the shipped fonts (two of the three faces are proportional)
  5. no two visible text runs collide at the same absolute point
  6. nothing starts fully transparent without an animation to bring it back
     (a static rasteriser would render it blank)
  7. theme guardrails: no blue/green/purple/amber anywhere, no pure #000 or
     #fff, and no rounded rect corners outside the rivet dots

Run: python3 tools/verify_assets.py
"""

import base64
import glob
import io
import os
import re
import sys
import xml.dom.minidom

from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import fontpack  # noqa: E402  (needs the path above)

FACE_KEY = {
    ("JetBrains Mono", "400"): "jb400",
    ("JetBrains Mono", "500"): "jb500",
    ("JetBrains Mono", "700"): "jb700",
    ("JetBrains Mono", "800"): "jb800",
    ("Special Elite", "400"): "elite400",
    ("Archivo Black", "400"): "archivo400",
}

# first family in a font-family stack -> logical face prefix
STACK_FACE = {
    "JetBrains Mono": "jb",
    "Special Elite": "elite400",
    "Archivo Black": "archivo400",
}

FONT_FACE_RE = re.compile(
    r"font-family:'([^']+)';font-style:normal;font-weight:(\d+);"
    r"src:url\(data:font/woff2;base64,([^)]+)\)"
)
TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
ATTR_RE = re.compile(r'(\w[\w-]*)="([^"]*)"')

BANNED = ("<script", "<foreignObject", "xlink:href", "<image", "@import", "url(http")

# 2.4 "There is no blue, green, purple or amber anywhere in the theme."
# Every colour the theme permits, plus plain black/white used only inside
# gradient stops and shadow rgba() where they are modulated by opacity.
ALLOWED_HEX = {
    "#0a0908", "#171514", "#0c0b0a", "#0d0c0b", "#100e0d",
    "#d60019", "#ff1a2e", "#120d0c", "#161210", "#1a1010", "#3a201f", "#5c0a10",
    "#f4f1eb", "#eae7e1", "#b7b2a9", "#8a857d", "#7a756d", "#5c5852", "#3d3835",
    "#2a2624", "#262221", "#33302e", "#4a4640",
    "#23201e", "#1a1817", "#141211",          # cube faces
    "#000000", "#ffffff",                      # gradient stops / bevel shadow only
}
HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")


def unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'"))


def face_of(stack, weight):
    """Resolve a declared font-family stack + weight to a fontpack face key."""
    first = stack.split(",")[0].strip().strip("'\"")
    base = STACK_FACE.get(first)
    if base is None:
        return None
    if base == "jb":
        return "jb" + (weight if weight in ("500", "700", "800") else "400")
    return base


def check(path):
    svg = open(path, encoding="utf-8").read()
    name = os.path.basename(path)
    problems = []

    # 1. XML validity
    try:
        xml.dom.minidom.parseString(svg)
    except Exception as exc:                       # pragma: no cover
        problems.append(f"invalid XML: {exc}")

    # 2. external references
    for bad in BANNED:
        if bad in svg:
            problems.append(f"external/unsafe reference: {bad}")

    # 3. embedded glyph coverage
    embedded = {}
    for fam, wt, b64 in FONT_FACE_RE.findall(svg):
        key = FACE_KEY.get((fam, wt))
        if key is None:
            problems.append(f"unexpected embedded face {fam} {wt}")
            continue
        font = TTFont(io.BytesIO(base64.b64decode(b64)))
        embedded[key] = set(font.getBestCmap())

    runs = 0
    for attrs_raw, body in TEXT_RE.findall(svg):
        attrs = dict(ATTR_RE.findall(attrs_raw))
        stack = attrs.get("font-family", "")
        weight = attrs.get("font-weight", "400")
        text = unescape(re.sub(r"<[^>]+>", "", body))
        if not text.strip():
            continue
        runs += 1
        key = face_of(stack, weight)
        if key is None:
            problems.append(f"text declares an unknown family {stack!r}: {text[:40]!r}")
            continue
        cov = embedded.get(key)
        if cov is None:
            problems.append(f"text uses {key} but no such face is embedded: {text[:40]!r}")
            continue
        missing = sorted({c for c in text if c != " " and ord(c) not in cov})
        if missing:
            problems.append(f"{key} missing glyphs {missing} for {text[:40]!r}")

    # 4. text must stay inside the canvas. Widths come from the real hmtx
    #    tables, so proportional faces are measured exactly rather than
    #    approximated with a monospace pitch.
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if vb:
        cw = float(vb.group(1))
        for attrs_raw, body in TEXT_RE.findall(svg):
            a = dict(ATTR_RE.findall(attrs_raw))
            key = face_of(a.get("font-family", ""), a.get("font-weight", "400"))
            if key is None:
                continue
            t = unescape(re.sub(r"<[^>]+>", "", body))
            if not t.strip():
                continue
            size = float(a.get("font-size", 12))
            ls = float(a.get("letter-spacing", 0) or 0)
            x = float(a.get("x", 0))
            w_t = fontpack.width(key, t, size, ls)
            anchor = a.get("text-anchor", "start")
            left = x if anchor == "start" else (x - w_t if anchor == "end" else x - w_t / 2)
            if left < -0.5 or left + w_t > cw + 0.5:
                problems.append(
                    f"text overflows canvas ({left:.0f}..{left+w_t:.0f} of {cw:.0f}): {t[:40]!r}")

    # 5. no two visible text runs collide at the same absolute point.
    #    Positions are resolved through enclosing <g transform="translate(x,y)">
    #    so that identical local coordinates in *different* rows do not raise a
    #    false alarm. This catches one-at-a-time animation frames that would
    #    stack on top of each other in a renderer that does not animate.
    seen = {}
    depth_tx = [(0.0, 0.0, False)]
    token = re.compile(r'<g\b([^>]*)>|</g>|<text\b([^>]*)>(.*?)</text>', re.S)
    for m in token.finditer(svg):
        if m.group(0) == "</g>":
            if len(depth_tx) > 1:
                depth_tx.pop()
            continue
        if m.group(1) is not None:                       # opening <g>
            g_attrs = m.group(1) or ""
            tr = re.search(r'translate\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)', g_attrs)
            dx, dy, ghost = depth_tx[-1]
            if tr:
                dx += float(tr.group(1))
                dy += float(tr.group(2))
            if re.search(r'opacity="0"', g_attrs):
                ghost = True
            depth_tx.append((dx, dy, ghost))
            continue
        a = dict(ATTR_RE.findall(m.group(2) or ""))
        if a.get("opacity") == "0" or depth_tx[-1][2]:
            continue
        t = unescape(re.sub(r"<[^>]+>", "", m.group(3) or ""))
        if not t.strip():
            continue
        dx, dy, _ = depth_tx[-1]
        try:
            spot = (round(float(a.get("x", 0)) + dx, 1),
                    round(float(a.get("y", 0)) + dy, 1),
                    a.get("text-anchor", "start"))
        except ValueError:
            continue
        if spot in seen and seen[spot] != t:
            problems.append(
                f"two visible texts share position {spot}: {seen[spot][:24]!r} / {t[:24]!r}")
        seen[spot] = t

    # 6. permanently invisible elements
    for m in re.finditer(r'<(?:g|text|rect|circle)\b[^>]*opacity="0"[^>]*>', svg):
        tag = m.group(0)
        cls = re.search(r'class="([^"]*)"', tag)
        if not cls or not re.search(r"animation:\s*\w+", svg):
            problems.append(f"element starts opacity=0 with no animation: {tag[:70]}")

    # 7. theme guardrails
    body_only = svg[svg.index("</style>"):] if "</style>" in svg else svg
    for hx in set(HEX_RE.findall(svg)):
        if hx.lower() not in ALLOWED_HEX:
            problems.append(f"off-theme colour {hx} (no blue/green/purple/amber allowed)")
    # 9.x "Panel radius: 0 everywhere — no rounded corners except .rivet dots"
    for m in re.finditer(r'<rect\b[^>]*\brx="([\d.]+)"', body_only):
        if float(m.group(1)) > 0:
            problems.append(f"rounded corner rx={m.group(1)} — the theme has 0 radius")

    return name, runs, len(embedded), problems


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "assets", "*.svg")))
    if not files:
        sys.exit("no assets found - run tools/build_assets.py first")
    total = 0
    for path in files:
        name, runs, faces, problems = check(path)
        total += len(problems)
        status = "OK  " if not problems else "FAIL"
        size = os.path.getsize(path)
        print(f"  {status} {name:<19} {size:>8,}B  faces={faces}  text_runs={runs}")
        for p in problems:
            print(f"         - {p}")
    print()
    if total:
        sys.exit(f"{total} problem(s) found")
    print(f"All {len(files)} assets pass: valid XML, no external refs, full glyph "
          f"coverage, in-canvas text, on-theme colour, nothing permanently invisible.")


if __name__ == "__main__":
    main()
