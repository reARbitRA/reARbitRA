"""Subset + embed the brand typefaces directly into each generated SVG.

Why this exists
---------------
GitHub renders README images through a sanitising proxy in "secure static
mode": no scripts, no network fetches, no webfont downloads. A plain
`font-family="JetBrains Mono"` therefore resolves against *the viewer's*
installed fonts. Almost nobody has JetBrains Mono — let alone Special Elite —
installed, so the brand typography silently degrades to a generic system font
and the profile stops looking like KONKRED at all.

The fix is to inline the actual glyph outlines as a base64 @font-face inside
each SVG. To keep the payload small we subset each face down to only the
characters that specific SVG actually draws — usually a few hundred bytes to
a couple of KB per file instead of 18-53KB.

Licences (all permit embedding):
  JetBrains Mono  OFL-1.1  (c) 2020 The JetBrains Mono Project Authors
  Archivo Black   OFL-1.1  (c) 2017 The Archivo Black Project Authors
  Special Elite   Apache-2.0 (c) 2010 Brian J. Bonislawsky DBA Astigmatic

Metrics
-------
Two of the three faces are proportional, so text width cannot be derived from
a single advance constant the way IBM Plex Mono allowed. `advance()` reads the
real `hmtx` table out of the shipped font files, which is what lets the
generator place things *next to* text (carets, rules, stamps) instead of
guessing and overflowing the canvas.
"""

import base64
import io
import os

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# logical name -> (file, css family, weight)
FACES = {
    "jb400":     ("jb-400.woff2",      "JetBrains Mono", "400"),
    "jb500":     ("jb-500.woff2",      "JetBrains Mono", "500"),
    "jb700":     ("jb-700.woff2",      "JetBrains Mono", "700"),
    "jb800":     ("jb-800.woff2",      "JetBrains Mono", "800"),
    "elite400":  ("elite-400.woff2",   "Special Elite",  "400"),
    "archivo400": ("archivo-400.woff2", "Archivo Black",  "400"),
}

_cache = {}
_metrics = {}


def _load(fname):
    if fname not in _cache:
        with open(os.path.join(FONT_DIR, fname), "rb") as fh:
            _cache[fname] = fh.read()
    return _cache[fname]


def available():
    return all(os.path.exists(os.path.join(FONT_DIR, f)) for f, _, _ in FACES.values())


def _metric_table(key):
    """{codepoint: advance in em units} for a face, read from the real font."""
    if key not in _metrics:
        fname = FACES[key][0]
        font = TTFont(io.BytesIO(_load(fname)))
        upm = font["head"].unitsPerEm
        hmtx = font["hmtx"]
        cmap = font.getBestCmap()
        table = {cp: hmtx[g][0] / upm for cp, g in cmap.items() if g in hmtx.metrics}
        default = table.get(ord(" "), 0.5)
        _metrics[key] = (table, default)
    return _metrics[key]


def advance(key, ch):
    """Width of one character in em units for `key`."""
    table, default = _metric_table(key)
    return table.get(ord(ch), default)


def width(key, s, size, ls=0.0):
    """Rendered width of `s` at `size` px with `ls` px letter-spacing."""
    if not s:
        return 0.0
    table, default = _metric_table(key)
    total = sum(table.get(ord(c), default) for c in s) * size
    return total + max(0, len(s) - 1) * ls


def _subset(raw: bytes, chars: str) -> bytes:
    """Return a woff2 containing only `chars`."""
    font = TTFont(io.BytesIO(raw))
    opts = subset.Options()
    opts.layout_features = ["kern", "liga", "calt"]
    opts.desubroutinize = True
    opts.hinting = False
    opts.notdef_outline = True
    opts.drop_tables += ["DSIG"]
    s = subset.Subsetter(options=opts)
    s.populate(text=chars)
    s.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def face_css(used: dict) -> str:
    """Build @font-face rules for the faces/characters actually used.

    `used` maps logical face name -> set of characters drawn with it.
    """
    if not available():
        return ""
    out = []
    for key, chars in sorted(used.items()):
        if not chars or key not in FACES:
            continue
        fname, family, weight = FACES[key]
        data = _subset(_load(fname), "".join(sorted(chars)))
        b64 = base64.b64encode(data).decode("ascii")
        out.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
            "src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (family, weight, b64)
        )
    return "".join(out)
