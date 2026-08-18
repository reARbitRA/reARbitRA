"""Subset + embed the brand typefaces directly into each generated SVG.

Why this exists
---------------
GitHub renders README images through a sanitising proxy in "secure static
mode": no scripts, no network fetches, no webfont downloads. A plain
`font-family="IBM Plex Mono"` therefore resolves against *the viewer's*
installed fonts. Almost nobody has Plex Mono installed, so the brand
typography silently degrades to a generic monospace and the profile stops
looking like KONKRED at all.

The fix is to inline the actual glyph outlines as a base64 @font-face inside
each SVG. To keep the payload small we subset each face down to only the
characters that specific SVG actually draws — usually a few hundred bytes to
a couple of KB per file instead of ~15KB.

Both families are SIL OFL (brand book s.10: "Commercial use permitted"),
which explicitly allows embedding.
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
    "plex400":  ("plex-400.woff2",  "IBM Plex Mono", "400"),
    "plex500":  ("plex-500.woff2",  "IBM Plex Mono", "500"),
    "plex600":  ("plex-600.woff2",  "IBM Plex Mono", "600"),
    "inter400": ("inter-400.woff2", "Inter",         "400"),
}

_cache = {}


def _load(fname):
    if fname not in _cache:
        with open(os.path.join(FONT_DIR, fname), "rb") as fh:
            _cache[fname] = fh.read()
    return _cache[fname]


def available():
    return all(os.path.exists(os.path.join(FONT_DIR, f)) for f, _, _ in FACES.values())


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
