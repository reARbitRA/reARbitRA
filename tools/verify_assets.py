#!/usr/bin/env python3
"""Verify generated SVGs before they ship.

Checks, per asset:
  1. well-formed XML
  2. no external references (GitHub's proxy blocks scripts/network/webfonts,
     so anything external silently disappears)
  3. every character drawn by a <text> run exists in the embedded subset for
     the face that run declares - i.e. the brand typography really renders
     rather than falling back to a generic system font
  4. nothing starts fully transparent without an animation to bring it back
     (a static rasteriser would render it blank)

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

FACE_KEY = {
    ("IBM Plex Mono", "400"): "plex400",
    ("IBM Plex Mono", "500"): "plex500",
    ("IBM Plex Mono", "600"): "plex600",
    ("Inter", "400"): "inter400",
}

FONT_FACE_RE = re.compile(
    r"font-family:'([^']+)';font-style:normal;font-weight:(\d+);"
    r"src:url\(data:font/woff2;base64,([^)]+)\)"
)
TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
ATTR_RE = re.compile(r'(\w[\w-]*)="([^"]*)"')

BANNED = ("<script", "<foreignObject", "xlink:href", "<image", "@import", "url(http")


def unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'"))


def face_of(stack, weight):
    first = stack.split(",")[0].strip().strip("'\"")
    if first == "Inter":
        return "inter400"
    return "plex" + (weight if weight in ("500", "600") else "400")


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
        # getBestCmap() is keyed by codepoint int - compare with ord(c)
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
        cov = embedded.get(key)
        if cov is None:
            problems.append(f"text uses {key} but no such face is embedded: {text[:40]!r}")
            continue
        missing = sorted({c for c in text if c != " " and ord(c) not in cov})
        if missing:
            problems.append(f"{key} missing glyphs {missing} for {text[:40]!r}")

    # 4. mono text must stay inside the canvas (real Plex advance = 0.6em)
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if vb:
        cw = float(vb.group(1))
        for attrs_raw, body in TEXT_RE.findall(svg):
            a = dict(ATTR_RE.findall(attrs_raw))
            if "Inter" in a.get("font-family", "").split(",")[0]:
                continue  # proportional; not safely measurable here
            t = unescape(re.sub(r"<[^>]+>", "", body))
            if not t.strip():
                continue
            size = float(a.get("font-size", 13))
            ls = float(a.get("letter-spacing", 0) or 0)
            x = float(a.get("x", 0))
            w_t = len(t) * size * 0.6 + max(0, len(t) - 1) * ls
            anchor = a.get("text-anchor", "start")
            left = x if anchor == "start" else (x - w_t if anchor == "end" else x - w_t / 2)
            if left < -0.5 or left + w_t > cw + 0.5:
                problems.append(f"text overflows canvas ({left:.0f}..{left+w_t:.0f} of {cw:.0f}): {t[:40]!r}")

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
                dx += float(tr.group(1)); dy += float(tr.group(2))
            # a group hidden with opacity="0" hides everything inside it
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
        print(f"  {status} {name:<15} {size:>7,}B  faces={faces}  text_runs={runs}")
        for p in problems:
            print(f"         - {p}")
    print()
    if total:
        sys.exit(f"{total} problem(s) found")
    print(f"All {len(files)} assets pass: valid XML, no external refs, "
          f"full glyph coverage, nothing permanently invisible.")


if __name__ == "__main__":
    main()
