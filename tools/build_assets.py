#!/usr/bin/env python3
"""
KONKRED profile asset generator — FACTORY FLOOR theme.

Emits self-contained animated SVGs for the GitHub profile README.
Everything is derived from the KONKRED Factory Floor theme:

  Canvas   konk-black #0a0908 — warm near-black, never pure #000
  Signal   konk-red #d60019 / red-glow #ff1a2e — power, not danger
  Ash      a 9-step neutral ladder, #f4f1eb down to #262221
  Type     Archivo Black (display) · Special Elite (prose) · JetBrains Mono (machine)
  Texture  chalk grain, canvas smudge, scanlines, blueprint grid, hazard tape
  Hardware rivets, staples, keycaps, rubber stamps, octagonal spec shells
  Motion   fast and mechanical: .18s hover, .35-.6s entries, steps() grain

One rule: the background never glows, only foreground objects ignite.

GitHub renders README images inside <img>, which blocks scripts, external
fonts and pointer events. So: no JS, glyph outlines inlined as base64
@font-face, and every "interaction" is expressed as an autonomous looping
animation. The glow-on-hover mechanic that drives the live site becomes an
*ignition sweep* here — a red charge that walks the row and lights each
element in turn, so the theme's core gesture still reads in a static frame.

Usage:  python3 tools/build_assets.py
"""

import math
import os

import fontpack

# --------------------------------------------------------------------------
# 2. COLOUR TOKENS
# --------------------------------------------------------------------------
# 2.1 base canvas
BLACK     = "#0a0908"   # page background, warm near-black
ASH       = "#171514"   # raised surface / panel top
PANEL_BOT = "#0c0b0a"   # panel gradient bottom
SUNKEN    = "#0d0c0b"   # inputs, wells
SUNKEN2   = "#100e0d"   # nested cards

# 2.2 the red family — the only accent
RED       = "#d60019"   # deep red: fills, borders, tape, meters
RED_GLOW  = "#ff1a2e"   # hot red: ignition state + glowing text only
RED_TINT  = "#120d0c"   # red-stained surface
RED_TINT2 = "#1a1010"
RED_DIM   = "#3a201f"   # border for red-tinged elements at rest

# 2.3 the ash ladder
INK       = "#f4f1eb"   # interactive white
BODY      = "#eae7e1"   # default body text
REST      = "#b7b2a9"   # interactive at rest — everything hoverable starts here
DIM       = "#8a857d"   # secondary mono
META      = "#7a756d"   # captions
FAINT     = "#5c5852"   # ticker text, inactive labels
GHOST     = "#3d3835"   # disabled / [..] pipeline markers
LINE1     = "#2a2624"   # standard hairline
LINE2     = "#262221"   # nested / inner border
EDGE      = "#33302e"   # keycap bevel edge

# 3.1 the three faces. Values are fontpack logical keys; the CSS family and
# weight are derived from them so a run can never declare a face that is not
# embedded.
MONO   = "jb400"
MONO_M = "jb500"
MONO_B = "jb700"
MONO_X = "jb800"
TW     = "elite400"    # Special Elite — human sentences
DISP   = "archivo400"  # Archivo Black — ALL-CAPS display

FAMILY = {
    "jb400":      "'JetBrains Mono',ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace",
    "jb500":      "'JetBrains Mono',ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace",
    "jb700":      "'JetBrains Mono',ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace",
    "jb800":      "'JetBrains Mono',ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace",
    "elite400":   "'Special Elite','American Typewriter','Courier New',monospace",
    "archivo400": "'Archivo Black','Arial Black','Helvetica Neue',sans-serif",
}
WEIGHT = {"jb400": "400", "jb500": "500", "jb700": "700", "jb800": "800",
          "elite400": "400", "archivo400": "400"}

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def pt(p):
    return f"{p[0]:.2f},{p[1]:.2f}"


def poly(points):
    return " ".join(pt(p) for p in points)


def octagon(x, y, w, h, c=16):
    """9.x: the spec-shell silhouette — a rectangle with its corners cut."""
    return ("M " + " L ".join(pt(p) for p in [
        (x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c),
        (x + w - c, y + h), (x + c, y + h), (x, y + h - c), (x, y + c),
    ]) + " Z")


# --------------------------------------------------------------------------
# 4. TEXTURE SYSTEM
#
# Four independent layers. In the browser these are CSS; inside a README image
# they have to be native SVG, so the chalk grain is a real feTurbulence filter
# rather than a data-URI of one, and the blend is baked into a feColorMatrix
# instead of relying on mix-blend-mode (which several static rasterisers drop).
# --------------------------------------------------------------------------
def texture_defs(idp):
    return (
        # 4.1 global chalk grain — fine tooth, fractalNoise .85 / 4 octaves.
        # The colour matrix throws away the noise RGB and rebuilds it as warm
        # chalk dust whose *alpha* tracks the noise luminance, so the layer
        # speckles the black instead of greying it out.
        f'<filter id="{idp}grain" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" '
        f'stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" type="matrix" values="'
        f'0 0 0 0 0.957  0 0 0 0 0.945  0 0 0 0 0.921  0.34 0.34 0.34 0 -0.16"/>'
        f'</filter>'
        # 4.2 per-panel soft chalk — coarser, lower contrast
        f'<filter id="{idp}soft" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="3" '
        f'stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" type="matrix" values="'
        f'0 0 0 0 0.90  0 0 0 0 0.89  0 0 0 0 0.87  0.22 0.22 0.22 0 -0.11"/>'
        f'</filter>'
        # 4.3 canvas smudge — cold white breath top-left, red heat bottom-right
        f'<radialGradient id="{idp}breath" cx="15%" cy="10%" r="95%">'
        f'<stop offset="0%" stop-color="#ffffff" stop-opacity=".035"/>'
        f'<stop offset="55%" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="{idp}heat" cx="90%" cy="90%" r="90%">'
        f'<stop offset="0%" stop-color="{RED}" stop-opacity=".07"/>'
        f'<stop offset="60%" stop-color="{RED}" stop-opacity="0"/></radialGradient>'
        # 4.4 scanlines — 1px on, 2px off
        f'<pattern id="{idp}scan" width="3" height="3" patternUnits="userSpaceOnUse">'
        f'<rect width="3" height="1" fill="#ffffff" opacity=".015"/></pattern>'
        # 4.5 blueprint grid — 24px, red at 10%
        f'<pattern id="{idp}bp" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M 24 0 L 0 0 0 24" fill="none" stroke="{RED}" stroke-width="1" opacity=".10"/>'
        f'</pattern>'
        # 4.6 hazard tape — 45 degrees, 9px on / 9px off
        f'<pattern id="{idp}hz" width="18" height="18" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)">'
        f'<rect width="18" height="18" fill="{BLACK}"/>'
        f'<rect width="9" height="18" fill="{RED}"/></pattern>'
        # panel gradient: ash top -> near-black bottom
        f'<linearGradient id="{idp}pan" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{ASH}"/>'
        f'<stop offset="100%" stop-color="{PANEL_BOT}"/></linearGradient>'
        # rivet: machined metal dot, lit from upper-left
        f'<radialGradient id="{idp}riv" cx="35%" cy="30%" r="75%">'
        f'<stop offset="0%" stop-color="{INK}"/>'
        f'<stop offset="55%" stop-color="{DIM}"/>'
        f'<stop offset="100%" stop-color="{LINE2}"/></radialGradient>'
        # red flood: rises from the bottom of an igniting object
        f'<linearGradient id="{idp}flood" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0%" stop-color="{RED}" stop-opacity=".30"/>'
        f'<stop offset="100%" stop-color="{RED}" stop-opacity="0"/></linearGradient>'
        # beam: the diagonal light-bar that sweeps an igniting card
        f'<linearGradient id="{idp}beam" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{RED_GLOW}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{RED_GLOW}" stop-opacity=".30"/>'
        f'<stop offset="100%" stop-color="{RED_GLOW}" stop-opacity="0"/></linearGradient>'
    )


def canvas(idp, w, h, smudge=True):
    """4.3 — the floor itself. Flat black, then the two faint breaths."""
    o = [f'<rect width="{w}" height="{h}" fill="{BLACK}"/>']
    if smudge:
        o.append(f'<rect width="{w}" height="{h}" fill="url(#{idp}breath)"/>')
        o.append(f'<rect width="{w}" height="{h}" fill="url(#{idp}heat)"/>')
    return "".join(o)


def grain(idp, w, h, op=0.40):
    """4.1 — the signature layer. Drawn last so it bites into everything."""
    return (f'<g class="grain" opacity="{op}" pointer-events="none">'
            f'<rect x="-60" y="-60" width="{w+120}" height="{h+120}" '
            f'filter="url(#{idp}grain)"/></g>')


def soft_chalk(idp, x, y, w, h, op=0.35):
    """4.2 — a panel's own smudge."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" opacity="{op}" '
            f'filter="url(#{idp}soft)"/>')


def scanlines(idp, x, y, w, h):
    """4.4 — hero and full-bleed bands only, never body copy."""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{idp}scan)"/>'


def hazard(idp, x, y, w, thin=False):
    """4.6 — crime-scene tape as a UI device. 7px normal, 4px thin."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{4 if thin else 7}" '
            f'fill="url(#{idp}hz)"/>')


GRAIN_CSS = """
  .grain { animation: grainflick .9s steps(3) infinite; }
  @keyframes grainflick {
      0%   { transform: translate(0,0); }
     33%   { transform: translate(-40px,30px); }
     66%   { transform: translate(30px,-45px); }
    100%   { transform: translate(0,0); } }
"""


# --------------------------------------------------------------------------
# 6. FRAMES, PANELS & HARDWARE
# --------------------------------------------------------------------------
def rivet(idp, x, y, r=3):
    """6.2 — machined metal dot. The only round thing in the system."""
    x, y = float(x), float(y)
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="url(#{idp}riv)"/>'
            f'<circle cx="{x:.2f}" cy="{y+0.6:.2f}" r="{r}" fill="none" stroke="#000000" '
            f'stroke-width=".7" opacity=".55"/>')


def rivets(idp, x, y, w, h, inset=9, r=3):
    return "".join(rivet(idp, x + dx, y + dy, r) for dx, dy in
                   ((inset, inset), (w - inset, inset),
                    (inset, h - inset), (w - inset, h - inset)))


def staple(x, y, w=14, h=4):
    """6.2 — paper sheets and dossiers."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#4a4640"/>'
            f'<rect x="{x}" y="{y+h-1}" width="{w}" height="1" fill="#000000" opacity=".8"/>')


def frame(idp, x, y, w, h, c=16, stroke=LINE2, fill=None, sw=1.5):
    """6.1 — the specimen frame: octagon clip + four rivets."""
    body = fill or f"url(#{idp}pan)"
    return (f'<path d="{octagon(x, y, w, h, c)}" fill="{body}" stroke="{stroke}" '
            f'stroke-width="{sw}"/>' + rivets(idp, x, y, w, h))


def keycap(idp, x, y, label, size=10, ls=2.5, pad=9, h=22, color=REST, cls=""):
    """6.2 — 1.5px border with a 3.5px bottom border: a physical bevel."""
    tw_ = fontpack.width(MONO_M, label, size, ls)
    w = tw_ + pad * 2
    c = f' class="{cls}"' if cls else ""
    return (f'<g{c}>'
            f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" fill="{SUNKEN2}" '
            f'stroke="{EDGE}" stroke-width="1.5"/>'
            f'<rect x="{x}" y="{y+h-3.5}" width="{w:.1f}" height="3.5" fill="{EDGE}"/>'
            + txt(x + pad, y + h / 2 + 2.6, label, size, color, MONO_M, ls)
            + '</g>'), w


def stamp(x, y, label, size=17, color=RED, rot=-6, ls=2.0):
    """6.3 — rotated rubber stamp, 4px double border.

    SVG has no `border-style: double`, so the double rule is drawn as two
    concentric strokes with a 3px gap — which is what `4px double` resolves
    to anyway.
    """
    tw_ = fontpack.width(DISP, label.upper(), size, ls)
    padx, pady = 13, 8
    w = tw_ + padx * 2
    h = size + pady * 2
    return (f'<g transform="translate({x},{y}) rotate({rot})">'
            f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="1.6"/>'
            f'<rect x="3" y="3" width="{w-6:.1f}" height="{h-6:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="1.6"/>'
            + txt(padx, h / 2 + size * 0.36, label.upper(), size, color, DISP, ls)
            + '</g>'), w, h


def diamond(x, y, s=5, fill=RED):
    """6.4 — the red diamond that opens every panel header."""
    return (f'<polygon points="{poly([(x, y-s), (x+s, y), (x, y+s), (x-s, y)])}" '
            f'fill="{fill}"/>')


def panel_head(idp, x, y, w, label, dots=True):
    """6.4 — panel anatomy: red diamond + mono label, three dots on the right."""
    o = [diamond(x + 12, y + 15)]
    o.append(txt(x + 24, y + 19, label.upper(), 10, DIM, MONO_M, 3.0))
    if dots:
        for i in range(3):
            o.append(f'<circle cx="{x+w-16-i*11}" cy="{y+15}" r="2.6" '
                     f'fill="{RED if i == 0 else LINE1}"/>')
    o.append(f'<line x1="{x}" y1="{y+30}" x2="{x+w}" y2="{y+30}" '
             f'stroke="{LINE2}" stroke-width="1"/>')
    return "".join(o)


# --------------------------------------------------------------------------
# 3. TYPOGRAPHY helpers
# --------------------------------------------------------------------------
USED = {}


def reset_used():
    USED.clear()


def _note(face, s):
    USED.setdefault(face, set()).update(s)


def tw(face, s, size, ls=0.0):
    """Rendered width, measured against the real font metrics."""
    return fontpack.width(face, s, size, ls)


def fit(face, s, size, maxw, ls=0.0, minsize=7.0):
    """Largest size <= `size` at which `s` fits `maxw`."""
    while size > minsize and tw(face, s, size, ls) > maxw:
        size -= 0.25
    return round(size, 2)


def txt(x, y, s, size=12, fill=BODY, face=MONO, ls=None, anchor="start",
        cls="", extra=""):
    _note(face, s)
    a = f' letter-spacing="{ls}"' if ls is not None else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text{c} x="{x:.2f}" y="{y:.2f}" font-family="{FAMILY[face]}" '
            f'font-size="{size}" font-weight="{WEIGHT[face]}" fill="{fill}" '
            f'text-anchor="{anchor}"{a}{extra}>{esc(s)}</text>')


def hollow(x, y, s, size, stroke=LINE1, face=DISP, ls=0.0, sw=1.5, anchor="start",
           cls="", extra="", op="1"):
    """3.3 `.hollow` — transparent fill, ash stroke. Decorative only."""
    _note(face, s)
    c = f' class="{cls}"' if cls else ""
    return (f'<text{c} x="{x:.2f}" y="{y:.2f}" font-family="{FAMILY[face]}" '
            f'font-size="{size}" font-weight="{WEIGHT[face]}" fill="none" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{extra}>{esc(s)}</text>')


def ghost_num(x, y, n, size=96, op=".5", anchor="start", cls=""):
    """3.3 `.ghost-num` — huge outlined numerals *behind* content."""
    return hollow(x, y, n, size, stroke=LINE1, ls=-2, sw=1.5, anchor=anchor,
                  cls=cls, op=op)


def typed(x, y, s, size, fill, face=MONO, ls=0.0, start=0.0, step=0.03, cls="ty"):
    """Per-character reveal. Each glyph is its own <text> so it can carry its
    own delay — a typed look with no script. Proportional faces advance by
    their real per-glyph width rather than a fixed pitch."""
    _note(face, s)
    out = []
    cx = x
    for i, ch in enumerate(s):
        adv = fontpack.advance(face, ch) * size + ls
        if ch != " ":
            out.append(
                f'<text class="{cls}" x="{cx:.2f}" y="{y:.2f}" '
                f'font-family="{FAMILY[face]}" font-size="{size}" '
                f'font-weight="{WEIGHT[face]}" fill="{fill}" '
                f'style="animation-delay:{start + i * step:.3f}s">{esc(ch)}</text>')
        cx += adv
    return "".join(out)


TYPED_CSS = """
  .ty { animation: tyin .26s ease-out backwards; }
  @keyframes tyin { from { opacity:0 } to { opacity:1 } }
"""


def counter(x, y, final, size, fill, face=MONO_X, ls=0.0, anchor="start",
            start=0.0, cls="cnt"):
    """Odometer count-up. Intermediate frames carry opacity="0" as a
    presentation attribute so a renderer that ignores CSS shows only the final
    value instead of every frame stacked on top of each other."""
    digits = "".join(c for c in final if c.isdigit())
    if digits and len(digits) <= 4:
        end = int(digits)
        pre = final[:final.index(digits[0])]
        post = final[final.index(digits[0]) + len(digits):]
        steps = 7
        frames = [f"{pre}{int(end * (i + 1) / steps)}{post}" for i in range(steps)]
    else:
        frames = [final]
    frames = frames[:-1] + [final]
    n = len(frames)
    per = 0.08
    out = []
    for i, f in enumerate(frames):
        last = i == n - 1
        _note(face, f)
        vis = "" if last else ' opacity="0"'
        klass = f"{cls} final" if last else f"{cls} step"
        out.append(
            f'<text class="{klass}" x="{x:.2f}" y="{y:.2f}"{vis} '
            f'font-family="{FAMILY[face]}" font-size="{size}" '
            f'font-weight="{WEIGHT[face]}" fill="{fill}" text-anchor="{anchor}" '
            f'letter-spacing="{ls}" '
            f'style="animation-delay:{start + i * per:.2f}s">{esc(f)}</text>')
    return "".join(out)


COUNTER_CSS = """
  .cnt.step { animation: cntflash .08s linear both; }
  @keyframes cntflash { 0% { opacity:1 } 99% { opacity:1 } 100% { opacity:0 } }
  .cnt.final { animation: cntlast .2s ease-out backwards; }
  @keyframes cntlast { from { opacity:0; transform: translateY(3px) } to { opacity:1; transform: none } }
"""


# --------------------------------------------------------------------------
# 5. THE GLOW INTERACTION SYSTEM (autonomous form)
#
# On the live site every interactive element sits at ash #b7b2a9 and ignites
# to #ff1a2e on hover in 180ms. A README image has no pointer, so the same
# gesture is driven by a timer instead: `.ign` walks each element up to hot red
# with the two-layer drop-shadow bloom, then lets it cool back to ash. Base
# state stays ash, so a renderer with no CSS still shows the resting design.
# --------------------------------------------------------------------------
IGNITE_CSS = f"""
  .ign {{ animation: ignite 6s ease-in-out infinite; }}
  @keyframes ignite {{
      0%,  70%, 100% {{ fill: {REST}; }}
     12%,  46%       {{ fill: {RED_GLOW};
                        filter: drop-shadow(0 0 6px rgba(255,26,46,.7))
                                drop-shadow(0 0 18px rgba(214,0,25,.4)); }} }}
  .ign-s {{ animation: ignites 6s ease-in-out infinite; }}
  @keyframes ignites {{
      0%,  70%, 100% {{ stroke: {LINE1}; }}
     12%,  46%       {{ stroke: {RED};
                        filter: drop-shadow(0 0 6px rgba(255,26,46,.55)); }} }}
  .beam {{ animation: beam 6s cubic-bezier(.2,.9,.2,1) infinite; }}
  @keyframes beam {{
      0%, 8%   {{ opacity:0; transform: translateX(0); }}
     14%       {{ opacity:1; }}
     46%       {{ opacity:0; transform: translateX(var(--run,340px)); }}
    100%       {{ opacity:0; transform: translateX(var(--run,340px)); }} }}
  .flood {{ animation: flood 6s cubic-bezier(.2,.9,.2,1) infinite;
            transform-origin: bottom center; }}
  @keyframes flood {{
      0%, 8%, 70%, 100% {{ transform: scaleY(0); }}
     20%, 46%           {{ transform: scaleY(1); }} }}
  .redglow {{ animation: redglow 3.2s ease-in-out infinite; }}
  @keyframes redglow {{
      0%,100% {{ opacity:.55 }}
     50%      {{ opacity:1; filter: drop-shadow(0 0 7px rgba(255,26,46,.75)); }} }}
"""

# 7. MOTION SYSTEM — every timing in one place, fast and mechanical.
MOTION_CSS = """
  .modin { animation: modin .6s cubic-bezier(.16,.84,.24,1) backwards; }
  @keyframes modin { from { opacity:0; transform: translateY(36px) scale(.985) }
                     to   { opacity:1; transform: none } }
  .probe { animation: probe .35s ease backwards; }
  @keyframes probe { from { opacity:0; transform: translateX(-10px) }
                     to   { opacity:1; transform: none } }
  .drop { animation: drop .5s cubic-bezier(.2,.9,.2,1) backwards; }
  @keyframes drop { from { opacity:0; transform: translateY(-14px) rotate(-2deg) }
                    to   { opacity:1; transform: none } }
  .blink { animation: blink 1s steps(1) infinite; }
  @keyframes blink { 0%,49% { opacity:1 } 50%,100% { opacity:0 } }
  .dashflow { animation: dashflow .7s linear infinite; }
  @keyframes dashflow { to { stroke-dashoffset: -24 } }
  .steprun { animation: steprun .6s ease-in-out infinite alternate; }
  @keyframes steprun { from { opacity:.45 } to { opacity:1 } }
"""


# --------------------------------------------------------------------------
# Document scaffold
# --------------------------------------------------------------------------
def motion(css: str) -> str:
    """Wrap animation rules so they only apply when motion is welcome.

    Critical: the *base* state of every element must be fully visible. GitHub
    serves README images through a camo proxy, and some renderers (and every
    static rasteriser) apply no CSS animation at all. If the base state were
    `opacity:0` the profile would render blank. So animation is strictly an
    enhancement layered on a readable static composition, which also satisfies
    the theme's reduced-motion requirement for free.
    """
    return "@media (prefers-reduced-motion: no-preference){" + css + "}"


def head(w, h, title, desc, css, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f'<defs>{defs}</defs>'
        f'<style>@@FONTS@@{motion(css)}</style>'
    )


def render(fn):
    """Run a builder and inline @font-face for only the glyphs it drew."""
    reset_used()
    svg = fn()
    return svg.replace("@@FONTS@@", fontpack.face_css(USED))


def arrow(x, y, length=18, color=DIM, sw=1.4):
    """The IN -> OUT connector. Drawn, not typed: none of the three brand
    faces carry U+2192, and a font fallback here would break the row."""
    return (f'<g stroke="{color}" stroke-width="{sw}" fill="none" '
            f'stroke-linecap="square">'
            f'<line x1="{x}" y1="{y}" x2="{x+length}" y2="{y}"/>'
            f'<polyline points="{x+length-5},{y-4} {x+length},{y} {x+length-5},{y+4}"/>'
            f'</g>')


def play(x, y, s=5, color=BLACK):
    """The RUN triangle."""
    return f'<polygon points="{poly([(x, y-s), (x+s*1.5, y), (x, y+s)])}" fill="{color}"/>'


# ==========================================================================
# THE CUBE-K MARK — retooled for the factory floor
#
# The mark stays: an isometric block with the K excavated through the right
# face. What changes is the material. It was clinical concrete under a cold
# grey light; here it is ash under a red work-lamp, with the K cut glowing at
# the edges and a hazard tape stripe running through the excavation.
# ==========================================================================
S = 100.0
W = S * math.cos(math.radians(30))
H = S * 0.5
OX, OY = 100.0, 10.0

T  = (OX,     OY)
TR = (OX + W, OY + H)
TL = (OX - W, OY + H)
C  = (OX,     OY + 2 * H)
BL = (OX - W, OY + H + S)
BR = (OX + W, OY + H + S)
B  = (OX,     OY + 2 * H + S)

FACE_LT = "#23201e"   # top face — catches the most light
FACE_MD = "#1a1817"   # left face
FACE_SH = "#141211"   # right face — deepest


def rf(u, v):
    return (C[0] + u * W, C[1] - u * H + v * S)


def lf(u, v):
    return (TL[0] + u * W, TL[1] + u * H + v * S)


def tf(a, b):
    return (T[0] + a * W - b * W, T[1] + a * H + b * H)


K_UV = [
    (0.185, 0.150), (0.345, 0.150), (0.345, 0.420), (0.600, 0.150),
    (0.805, 0.150), (0.500, 0.500), (0.825, 0.850), (0.612, 0.850),
    (0.345, 0.565), (0.345, 0.850), (0.185, 0.850),
]
K_PATH = "M " + " L ".join(pt(rf(u, v)) for u, v in K_UV) + " Z"
CUBE_SIL = "M " + " L ".join(pt(p) for p in (T, TR, BR, B, BL, TL)) + " Z"
FACE_TOP = "M " + " L ".join(pt(p) for p in (T, TR, C, TL)) + " Z"
FACE_LFT = "M " + " L ".join(pt(p) for p in (TL, C, B, BL)) + " Z"
FACE_RGT = "M " + " L ".join(pt(p) for p in (C, TR, BR, B)) + " Z"


def cube(idp, scale=1.0, tx=0.0, ty=0.0):
    o = [f'<defs>'
         f'<clipPath id="{idp}kcut"><path d="{K_PATH}"/></clipPath>'
         f'<clipPath id="{idp}sil"><path d="{CUBE_SIL}"/></clipPath>'
         f'<linearGradient id="{idp}kscan" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{RED_GLOW}" stop-opacity="0"/>'
         f'<stop offset="50%" stop-color="{RED_GLOW}" stop-opacity=".45"/>'
         f'<stop offset="100%" stop-color="{RED_GLOW}" stop-opacity="0"/>'
         f'</linearGradient></defs>']
    o.append(f'<g transform="translate({tx},{ty}) scale({scale})" class="cube">')

    # three cast faces
    o.append(f'<path d="{FACE_TOP}" fill="{FACE_LT}"/>')
    o.append(f'<path d="{FACE_LFT}" fill="{FACE_MD}"/>')
    o.append(f'<path d="{FACE_RGT}" fill="{FACE_SH}"/>')

    # the K is not drawn, it is cut: void first, then interior structure
    o.append(f'<path d="{K_PATH}" fill="{BLACK}"/>')
    o.append(f'<g clip-path="url(#{idp}kcut)">')
    o.append(f'<path d="{K_PATH}" fill="url(#{idp}hz)" opacity=".18"/>')
    for i in range(19):
        v = i / 18.0
        a, b = rf(0.0, v), rf(1.0, v)
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{FAINT}" stroke-width=".7" opacity=".30"/>')
    for i in range(11):
        u = i / 10.0
        a, b = rf(u, 0.0), rf(u, 1.0)
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{FAINT}" stroke-width=".55" opacity=".2"/>')
    br1, br2 = rf(0.16, 0.90), rf(0.86, 0.10)
    br3, br4 = rf(0.16, 0.10), rf(0.86, 0.90)
    o.append(f'<line x1="{br1[0]:.2f}" y1="{br1[1]:.2f}" x2="{br2[0]:.2f}" y2="{br2[1]:.2f}" '
             f'stroke="{DIM}" stroke-width="1.5" opacity=".45"/>')
    o.append(f'<line x1="{br3[0]:.2f}" y1="{br3[1]:.2f}" x2="{br4[0]:.2f}" y2="{br4[1]:.2f}" '
             f'stroke="{DIM}" stroke-width="1.5" opacity=".25"/>')
    o.append(f'<rect class="kscan" x="0" y="-70" width="200" height="70" '
             f'fill="url(#{idp}kscan)"/>')
    o.append('</g>')

    # the cut edge is the only thing allowed to glow
    o.append(f'<path class="kedge" d="{K_PATH}" fill="none" stroke="{RED}" '
             f'stroke-width="1.6" stroke-linejoin="miter"/>')

    # face edges and machined detail
    o.append(f'<path d="{CUBE_SIL}" fill="none" stroke="{LINE1}" stroke-width="1.3"/>')
    for a, b in ((T, C), (TL, C), (TR, C), (C, B)):
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{BLACK}" stroke-width="1" opacity=".5"/>')
    for a0, b0, a1, b1 in ((0.14, 0.80, 0.30, 0.80), (0.80, 0.14, 0.80, 0.30)):
        p, q = tf(a0, b0), tf(a1, b1)
        o.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
                 f'stroke="{FAINT}" stroke-width="1.1"/>')
    p, q = lf(0.10, 0.10), lf(0.26, 0.18)
    o.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
             f'stroke="{FAINT}" stroke-width="1.1" opacity=".8"/>')
    for v in (0.74, 0.82, 0.90):
        p, q = lf(0.06, v), lf(0.94, v)
        o.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
                 f'stroke="{FAINT}" stroke-width=".9" opacity=".4"/>')

    # the live power trace
    tr_pts = [rf(0.055, 0.955), rf(0.90, 0.955), rf(0.90, 0.06)]
    o.append(f'<polyline class="trace" points="{poly(tr_pts)}" fill="none" '
             f'stroke="{RED}" stroke-width="2.4" stroke-linecap="square" '
             f'stroke-linejoin="miter"/>')
    tip = rf(0.90, 0.06)
    o.append(f'<circle class="sigdot" cx="{tip[0]:.2f}" cy="{tip[1]:.2f}" r="3.2" fill="{RED_GLOW}"/>')

    # rivets on the top face
    for a, b in ((0.22, 0.22), (0.78, 0.22), (0.22, 0.78)):
        p = tf(a, b)
        o.append(rivet(idp, p[0], p[1], 3.2))

    o.append(f'<g clip-path="url(#{idp}sil)">'
             f'<rect class="kscan2" x="0" y="-90" width="200" height="90" '
             f'fill="url(#{idp}kscan)"/></g>')
    o.append('</g>')
    return "".join(o)


CUBE_CSS = f"""
  .kscan  {{ animation: kscanY 4s linear infinite; }}
  .kscan2 {{ animation: kscanY 4s linear infinite; opacity:.45; }}
  @keyframes kscanY {{ from {{ transform: translateY(0) }} to {{ transform: translateY(300px) }} }}
  .kedge {{ animation: kglow 3.2s ease-in-out infinite; }}
  @keyframes kglow {{
      0%,100% {{ stroke: {RED}; opacity:.55 }}
     50%      {{ stroke: {RED_GLOW}; opacity:1;
                 filter: drop-shadow(0 0 8px rgba(255,26,46,.7)) }} }}
  .trace {{ stroke-dasharray: 16 10; animation: kdrift 11.5s linear infinite; }}
  @keyframes kdrift {{ to {{ stroke-dashoffset: -260 }} }}
  .sigdot {{ animation: ksig 2.4s ease-in-out infinite; }}
  @keyframes ksig {{ 0%,100% {{ opacity:.35 }} 50% {{ opacity:1 }} }}
"""


# ==========================================================================
# 1. HEADER — the hero bench
# ==========================================================================
def build_header():
    w, h = 1200, 400
    idp = "h"
    roles = [
        "r&d  ·  applied ai research and development",
        "ai architect  ·  rag, agents, llm systems",
        "llm security  ·  red teaming and adversarial testing",
        "enterprise licensing  ·  500+ engineered prompts",
        "app and bot builder  ·  full-stack ai tooling",
    ]
    css = CUBE_CSS + GRAIN_CSS + IGNITE_CSS + MOTION_CSS + TYPED_CSS + f"""
  .rise {{ animation: rise .5s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes rise {{ from {{ opacity:0; transform: translateY(9px) }}
                     to   {{ opacity:1; transform: none }} }}
  .cube {{ animation: rise .7s cubic-bezier(.16,.84,.24,1) .05s backwards; }}
  .r0 {{ animation-delay:.08s }} .r1 {{ animation-delay:.20s }}
  .r2 {{ animation-delay:.32s }} .r3 {{ animation-delay:.44s }}
  .r4 {{ animation-delay:.56s }} .r5 {{ animation-delay:.68s }}
  .rot {{ animation: rot 19s linear infinite; }}
  @keyframes rot {{
      0%  {{ opacity:0; transform: translateY(6px) }}
      2%  {{ opacity:1; transform: none }}
     18%  {{ opacity:1; transform: none }}
     20%  {{ opacity:0; transform: translateY(-6px) }}
    100%  {{ opacity:0; transform: translateY(-6px) }} }}
  .k0 {{ animation-delay:.9s }} .k1 {{ animation-delay:4.7s }}
  .k2 {{ animation-delay:8.5s }} .k3 {{ animation-delay:12.3s }}
  .k4 {{ animation-delay:16.1s }}
  .rail {{ stroke-dasharray: 220 980; animation: railrun 9s linear infinite; }}
  @keyframes railrun {{ to {{ stroke-dashoffset: -1200 }} }}
  .live {{ animation: livep 2.4s ease-in-out infinite; }}
  @keyframes livep {{ 0%,100% {{ opacity:.35 }}
                      50% {{ opacity:1; filter: drop-shadow(0 0 7px rgba(255,26,46,.8)) }} }}
  .i1 {{ animation-delay:0s }} .i2 {{ animation-delay:1.5s }}
  .i3 {{ animation-delay:3s }}  .i4 {{ animation-delay:4.5s }}
"""
    o = [head(w, h, "Ari Miyanji — R&D, AI architect, LLM security",
              "KONKRED factory-floor profile header: hazard tape, the Cube-K mark, "
              "stamped display type and a live status rail.", css,
              defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))
    o.append(scanlines(idp, 0, 0, w, h))

    # hazard tape caps the header, top and bottom
    o.append(hazard(idp, 0, 0, w))
    o.append(hazard(idp, 0, h - 4, w, thin=True))

    # Ghost numeral: bottom-right, the one quadrant with no content, so it
    # stays *behind* the composition instead of tangling with the zone list.
    o.append(ghost_num(w - 26, 340, "01", 160, op=".45", anchor="end"))

    # --- status bar -------------------------------------------------------
    o.append('<g class="rise r0">')
    o.append(f'<line x1="0" y1="44" x2="{w}" y2="44" stroke="{LINE1}" stroke-width="1"/>')
    o.append(diamond(26, 26))
    o.append(txt(40, 30, "KONKRED / FACTORY FLOOR", 10, DIM, MONO_M, 3.4))
    o.append(txt(268, 30, "MK III", 10, FAINT, MONO, 2.0))
    live_w = tw(MONO_M, "SYSTEM LIVE", 10, 3.0)
    o.append(f'<circle class="live" cx="{w-38-live_w:.1f}" cy="26" r="3.6" fill="{RED_GLOW}"/>')
    o.append(txt(w - 26, 30, "SYSTEM LIVE", 10, REST, MONO_M, 3.0, "end"))
    o.append('</g>')

    # --- the mark, in its specimen frame ----------------------------------
    o.append('<g class="rise r1">')
    o.append(frame(idp, 30, 68, 214, 250, c=16))
    o.append(soft_chalk(idp, 30, 68, 214, 250))
    o.append('</g>')
    o.append(cube(idp, scale=0.74, tx=64, ty=88))
    o.append('<g class="rise r2">')
    o.append(txt(137, 306, "CUBE-K  ·  MK III", 9, FAINT, MONO, 2.6, "middle"))
    o.append('</g>')

    # --- display block ----------------------------------------------------
    x = 282
    o.append('<g class="rise r1">')
    o.append(txt(x, 94, "AI RESEARCH  ·  DEVELOPMENT  ·  SECURITY", 10, META, MONO_M, 4.0))
    o.append('</g>')

    name = "ARI MIYANJI"
    nsize = fit(DISP, name, 74, w - x - 60, -2.6)
    o.append(typed(x, 160, name, nsize, INK, DISP, -2.6, start=0.22, step=0.045))

    # the rail under the name: a static hairline with a red charge running it
    o.append('<g class="rise r2">')
    rail_end = w - 132   # stops clear of the zone column on the right
    o.append(f'<line x1="{x}" y1="180" x2="{rail_end}" y2="180" stroke="{LINE1}" stroke-width="1.5"/>')
    o.append(f'<line class="rail" x1="{x}" y1="180" x2="{rail_end}" y2="180" '
             f'stroke="{RED}" stroke-width="1.8"/>')
    o.append('</g>')

    # rotating machine-voice role line
    for i, r in enumerate(roles):
        o.append(f'<g class="rot k{i}" opacity="{1 if i == 0 else 0}">'
                 f'{txt(x, 212, r, 13.5, REST, MONO_M, 0.6)}</g>')

    # typewriter prose — sentence case, normal tracking, never mixed with mono
    o.append('<g class="rise r4">')
    o.append(txt(x, 250, "Concrete tools for abstract problems.", 19, BODY, TW, 0))
    o.append(txt(x, 276, "I design AI systems, break them on purpose, and hand them over documented.",
                 14.5, META, TW, 0))
    o.append('</g>')

    # --- intake -> output row, the mandatory bench signature --------------
    o.append('<g class="rise r5">')
    o.append(txt(x, 312, "in:", 10, FAINT, MONO, 2.0))
    ix = x + 26
    inw, _ = keycap(idp, ix, 298, "A HARD AI PROBLEM", 9.5, 2.2)
    o.append(inw)
    aw = tw(MONO_M, "A HARD AI PROBLEM", 9.5, 2.2) + 18
    o.append(arrow(ix + aw + 12, 309, 18, DIM))
    o.append(keycap(idp, ix + aw + 44, 298, "A SHIPPED SYSTEM", 9.5, 2.2, color=REST)[0])
    o.append('</g>')

    # --- run strip --------------------------------------------------------
    # The button is sized from the measured label rather than a guessed box,
    # so the play triangle can never overrun the text.
    o.append('<g class="rise r5">')
    blab = "OPEN TO HIRE"
    bpad, bh, by = 20, 34, 340
    lw_ = tw(MONO_X, blab, 11, 2.4)
    bw = lw_ + bpad * 2 + 22
    o.append(f'<rect x="{x}" y="{by}" width="{bw:.1f}" height="{bh}" fill="{RED}"/>')
    o.append(f'<rect x="{x}" y="{by}" width="{bw:.1f}" height="{bh}" fill="none" '
             f'stroke="{RED_GLOW}" stroke-width="1.5" class="redglow"/>')
    o.append(txt(x + bpad, by + 22, blab, 11, BLACK, MONO_X, 2.4))
    o.append(play(x + bpad + lw_ + 8, by + bh / 2, 5, BLACK))
    o.append(txt(x + bw + 22, by + 22, "remote · contract · fractional · advisory",
                 13, META, TW, 0))
    o.append('</g>')

    # --- right meta column: the four zones, each ignites in turn ----------
    o.append('<g class="rise r3">')
    o.append(txt(w - 26, 96, "ZONES", 9, FAINT, MONO, 3.0, "end"))
    o.append(f'<line x1="{w-92}" y1="106" x2="{w-26}" y2="106" '
             f'stroke="{LINE1}" stroke-width="1"/>')
    for i, s in enumerate(["I  BUILD", "II  AUDIT", "III  SECURE", "IV  DOCUMENT"]):
        o.append(txt(w - 26, 128 + i * 21, s, 10, REST, MONO, 2.4, "end",
                     cls=f"ign i{i+1}"))
    o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 2. PRODUCTS — four benches, full card anatomy (spec s.11)
# ==========================================================================
def build_products():
    cards = [
        ("W-01", "PROMPT CERTIFICATION", "KONKRED AUDIT",
         "audit a prompt, price it, and stamp it certified before it ships",
         "an engineered prompt", "a certified asset", "~ 12s", "medium", "CLEARED"),
        ("W-02", "MICRO-TOOL SUITE", "KONKRED ENTERPRISE",
         "turn a licensed prompt into a standalone tool with its own interface",
         "a licensed prompt", "a running micro-tool", "~ 30s", "medium", "FORGED"),
        ("W-03", "AI SECURITY", "KONKRED REDEYE",
         "throw 367 catalogued attacks at a model and grade what gets through",
         "a live endpoint", "a breach report", "~ 45s", "hot", "GRADE C"),
        ("W-04", "ENTERPRISE LICENSING", "KONKRED ARBITRA",
         "license the library, then orchestrate it into autonomous agents",
         "a business workflow", "an agent fleet", "~ 20s", "easy", "PASS"),
    ]
    cw, ch, gap = 588, 268, 24
    w, h = cw * 2 + gap, ch * 2 + gap
    idp = "p"
    css = GRAIN_CSS + IGNITE_CSS + MOTION_CSS + TYPED_CSS + f"""
  .card {{ animation: modin .6s cubic-bezier(.16,.84,.24,1) backwards; }}
  .c0 {{ animation-delay:.05s }} .c1 {{ animation-delay:.19s }}
  .c2 {{ animation-delay:.33s }} .c3 {{ animation-delay:.47s }}
  .p0 .ign, .p0 .ign-s, .p0 .beam, .p0 .flood {{ animation-delay:0s }}
  .p1 .ign, .p1 .ign-s, .p1 .beam, .p1 .flood {{ animation-delay:1.5s }}
  .p2 .ign, .p2 .ign-s, .p2 .beam, .p2 .flood {{ animation-delay:3s }}
  .p3 .ign, .p3 .ign-s, .p3 .beam, .p3 .flood {{ animation-delay:4.5s }}
  .live {{ animation: livep 2.4s ease-in-out infinite; }}
  @keyframes livep {{ 0%,100% {{ opacity:.35 }}
                      50% {{ opacity:1; filter: drop-shadow(0 0 7px rgba(255,26,46,.8)) }} }}
  .p1 .live {{ animation-delay:.6s }} .p2 .live {{ animation-delay:1.2s }}
  .p3 .live {{ animation-delay:1.8s }}
"""
    o = [head(w, h, "KONKRED product suite",
              "Four workflow benches: Audit, Enterprise, Redeye and Arbitra. Each card "
              "shows its id, name, what goes in, what comes out, run time and difficulty.",
              css, defs=texture_defs(idp))]
    clips = "".join(
        f'<clipPath id="{idp}clip{i}"><path d="{octagon(0, 0, cw, ch, 16)}"/></clipPath>'
        for i in range(len(cards)))
    o.append(f'<defs>{clips}</defs>')
    o.append(canvas(idp, w, h))

    for i, (wid, tag, title, desc, ins, outs, time, level, stamp_txt) in enumerate(cards):
        cx = (i % 2) * (cw + gap)
        cy = (i // 2) * (ch + gap)
        d = 0.05 + i * 0.14
        o.append(f'<g class="card c{i} p{i}" transform="translate({cx},{cy})">')
        o.append(f'<path d="{octagon(0, 0, cw, ch, 16)}" fill="url(#{idp}pan)" '
                 f'stroke="{LINE2}" stroke-width="1.5" class="ign-s"/>')
        o.append(f'<g clip-path="url(#{idp}clip{i})">')
        o.append(soft_chalk(idp, 0, 0, cw, ch, 0.3))
        # ghost numeral behind the content, opacity .7 per the card rules
        o.append(ghost_num(cw - 150, ch - 26, wid[-2:], 132, op=".45"))
        # flood rises from the bottom when the bench ignites
        o.append(f'<rect class="flood" x="0" y="{ch-90}" width="{cw}" height="90" '
                 f'fill="url(#{idp}flood)"/>')
        # beam sweeps left to right, skewed
        o.append(f'<g class="beam" style="--run:{cw+120}px">'
                 f'<rect x="-120" y="-40" width="90" height="{ch+80}" '
                 f'fill="url(#{idp}beam)" transform="skewX(-14)"/></g>')
        o.append('</g>')
        o.append(rivets(idp, 0, 0, cw, ch))

        # id row + live dot
        o.append(txt(26, 38, wid, 11, RED, MONO_X, 2.4))
        o.append(f'<line x1="78" y1="34" x2="{cw-92}" y2="34" stroke="{LINE1}" '
                 f'stroke-width="1" stroke-dasharray="2 4"/>')
        o.append(f'<circle class="live" cx="{cw-80}" cy="34" r="3.4" fill="{RED_GLOW}"/>')
        o.append(txt(cw - 68, 38, "LIVE", 10, REST, MONO_M, 2.6))
        o.append(txt(26, 58, tag, 9.5, META, MONO, 3.0))

        # display name
        tsize = fit(DISP, title, 27, cw - 52, -0.6)
        o.append(typed(26, 96, title, tsize, INK, DISP, -0.6, start=d + 0.2, step=0.022))

        # typewriter description
        o.append(txt(26, 126, desc, 14, BODY, TW, 0))

        # IN -> OUT row: mandatory, it is how a reader knows if this bench is theirs
        o.append(txt(26, 160, "in:", 10, FAINT, MONO, 2.0))
        kx = 52
        kw1 = tw(MONO_M, ins.upper(), 9.5, 2.2) + 18
        o.append(keycap(idp, kx, 148, ins.upper(), 9.5, 2.2)[0])
        o.append(arrow(kx + kw1 + 10, 159, 16, DIM))
        o.append(keycap(idp, kx + kw1 + 38, 148, outs.upper(), 9.5, 2.2)[0])

        # pipeline rail: [..] queued, [>>] running, [ok] complete
        rail = [("[ok]", RED, "redglow"), ("[ok]", RED, "redglow"),
                ("[>>]", REST, "steprun"), ("[..]", GHOST, "")]
        rx = 26
        for lab, col, kls in rail:
            o.append(txt(rx, 194, lab, 11, col, MONO_B, 1.0, cls=kls))
            rx += tw(MONO_B, lab, 11, 1.0) + 12
        o.append(f'<line x1="{rx}" y1="190" x2="{cw-150}" y2="190" stroke="{LINE2}" '
                 f'stroke-width="1"/>')

        # footer: meta left, one primary RUN bottom-right
        o.append(f'<line x1="26" y1="{ch-56}" x2="{cw-26}" y2="{ch-56}" '
                 f'stroke="{LINE2}" stroke-width="1"/>')
        o.append(txt(26, ch - 30, time, 11, META, MONO, 1.2))
        lw, _ = keycap(idp, 80, ch - 44, level.upper(), 9.5, 2.2,
                       color=RED if level == "hot" else REST)
        o.append(lw)

        st, sw_, sh_ = stamp(cw - 250, ch - 52, stamp_txt, 14,
                             RED if i % 2 == 0 else REST, -4 if i % 2 == 0 else 3)
        o.append(f'<g class="drop" style="animation-delay:{d+0.45:.2f}s">{st}</g>')

        bw, bh = 96, 30
        bx, by = cw - 26 - bw, ch - 44
        o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{RED}"/>')
        o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" '
                 f'stroke="{RED_GLOW}" stroke-width="1.5" class="redglow"/>')
        o.append(txt(bx + 18, by + 20, "RUN", 11, BLACK, MONO_X, 2.6))
        o.append(play(bx + bw - 26, by + bh / 2, 5, BLACK))
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 3. STACK — keycap tokens on a blueprint deck
# ==========================================================================
def build_stack():
    groups = [
        ("LLM ENGINEERING", ["Prompt architecture", "RAG", "Agents", "Tool use",
                             "Evals", "Hallucination control", "Multi-modal",
                             "Chain-of-thought", "ReAct", "Context engineering"]),
        ("AI SECURITY", ["Red teaming", "Jailbreak taxonomy", "Prompt injection defence",
                         "Guardrail validation", "Data-leak surface", "Adversarial testing",
                         "Threat modelling"]),
        ("BUILD", ["Python", "FastAPI", "Flask", "TypeScript", "React", "Node",
                   "Tailwind", "HTML5", "CSS3", "Static-first web"]),
        ("AI ECONOMICS", ["COGS modelling", "Context caching", "Token budgeting",
                          "Model routing", "Gemini / AI Studio", "Throughput tuning",
                          "Observability"]),
        ("GOVERNANCE", ["ISO/IEC 42001", "EU AI Act", "AI asset valuation",
                        "Certification trails", "PRD / SDP authoring", "Runbooks"]),
        ("ADVANCED", ["Qiskit", "Quantum algorithms", "Applied research",
                      "Technical authoring", "Bot systems", "Automation pipelines"]),
    ]
    colw, gap = 380, 30
    w = colw * 3 + gap * 2
    pad, ph, pgap = 10, 26, 8
    lab_h, grp_gap = 38, 30
    idp = "s"

    laid, heights = [], []
    for name, items in groups:
        rows, cur, curw = [], [], 0
        for it in items:
            iw = round(tw(MONO_M, it.upper(), 9.5, 1.6) + pad * 2, 1)
            if curw + iw > colw and cur:
                rows.append(cur)
                cur, curw = [], 0
            cur.append((it, iw))
            curw += iw + pgap
        if cur:
            rows.append(cur)
        laid.append((name, rows))
        heights.append(lab_h + len(rows) * (ph + pgap))

    r0 = max(heights[0], heights[1], heights[2])
    r1 = max(heights[3], heights[4], heights[5])
    h = int(r0 + grp_gap + r1)

    css = GRAIN_CSS + IGNITE_CSS + MOTION_CSS + """
  .key { animation: keyin .4s cubic-bezier(.16,.84,.24,1) backwards; }
  @keyframes keyin { from { opacity:0; transform: translateY(6px) }
                     to   { opacity:1; transform: none } }
  .glab { animation: keyin .45s cubic-bezier(.16,.84,.24,1) backwards; }
  .gline { transform-origin:left center; animation: gl .6s ease-out backwards; }
  @keyframes gl { from { transform: scaleX(0) } to { transform: scaleX(1) } }
  .tick { animation: tk 4.4s ease-in-out infinite; }
  @keyframes tk { 0%,100% { opacity:.3 } 50% { opacity:1 } }
"""
    o = [head(w, h, "Technical stack",
              "Six capability groups rendered as beveled keycaps on a blueprint deck.",
              css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))
    o.append(f'<rect width="{w}" height="{h}" fill="url(#{idp}bp)" opacity=".5"/>')

    n = 0
    for gi, (name, rows) in enumerate(laid):
        cx = (gi % 3) * (colw + gap)
        cy = 0 if gi < 3 else r0 + grp_gap
        o.append(f'<g transform="translate({cx},{cy})">')
        o.append(f'<g class="glab" style="animation-delay:{gi*0.09:.2f}s">')
        o.append(f'<rect class="tick" x="0" y="4" width="4" height="14" fill="{RED}" '
                 f'style="animation-delay:{gi*0.5:.1f}s"/>')
        o.append(txt(15, 16, name, 11, REST, MONO_B, 3.0))
        o.append(f'<line x1="0" y1="28" x2="{colw}" y2="28" stroke="{LINE1}" stroke-width="1"/>')
        o.append(f'<line class="gline" x1="0" y1="28" x2="{colw}" y2="28" stroke="{RED}" '
                 f'stroke-width="1.5" opacity=".6" style="animation-delay:{gi*0.09+0.25:.2f}s"/>')
        o.append('</g>')
        for ri, row in enumerate(rows):
            px = 0.0
            for label, iw in row:
                d = 0.20 + n * 0.026
                ky = lab_h + ri * (ph + pgap)
                o.append(f'<g class="key" style="animation-delay:{d:.2f}s">')
                o.append(f'<rect x="{px:.1f}" y="{ky}" width="{iw}" height="{ph}" '
                         f'fill="{SUNKEN2}" stroke="{EDGE}" stroke-width="1.5"/>')
                o.append(f'<rect x="{px:.1f}" y="{ky+ph-3.5}" width="{iw}" height="3.5" '
                         f'fill="{EDGE}"/>')
                o.append(txt(px + pad, ky + 15.5, label.upper(), 9.5, REST, MONO_M, 1.6,
                             cls="ign", extra=f' style="animation-delay:{(n%11)*0.55:.2f}s"'))
                o.append('</g>')
                px += iw + pgap
                n += 1
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 4. METRICS — the telemetry strip
# ==========================================================================
def build_metrics():
    stats = [
        ("500+", "ENTERPRISE PROMPTS", "engineered and licensed"),
        ("367", "RED-TEAM TECHNIQUES", "catalogued and typed"),
        ("70%", "COST REDUCTION", "$20k down to $6k"),
        ("20+", "MANUSCRIPTS", "ai, security, quantum"),
        ("10+", "STRATEGIC DOMAINS", "legal to heavy industry"),
    ]
    gap = 16
    n = len(stats)
    w = 1200
    cw = (w - gap * (n - 1)) // n
    h = 172
    idp = "m"
    css = GRAIN_CSS + IGNITE_CSS + COUNTER_CSS + f"""
  .cell {{ animation: cellin .5s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes cellin {{ from {{ opacity:0; transform: translateY(10px) }}
                       to   {{ opacity:1; transform: none }} }}
  .meter {{ transform-origin: left center; animation: meter 1.1s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes meter {{ from {{ transform: scaleX(0) }} to {{ transform: scaleX(1) }} }}
  .heat {{ animation: heat 5.5s ease-in-out infinite; }}
  @keyframes heat {{ 0%,72%,100% {{ opacity:.25 }}
                     12%,40% {{ opacity:1; filter: drop-shadow(0 0 14px rgba(255,26,46,.75)) }} }}
"""
    o = [head(w, h, "Signals",
              "Five headline metrics: 500+ enterprise prompts, 367 red-team techniques, "
              "70% cost reduction, 20+ manuscripts, 10+ strategic domains.",
              css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))

    for i, (val, lab, sub) in enumerate(stats):
        x = i * (cw + gap)
        d = 0.06 + i * 0.1
        o.append(f'<g class="cell" style="animation-delay:{d:.2f}s" transform="translate({x},0)">')
        o.append(f'<path d="{octagon(0, 0, cw, h, 12)}" fill="url(#{idp}pan)" '
                 f'stroke="{LINE2}" stroke-width="1.5"/>')
        o.append(rivets(idp, 0, 0, cw, h, 8, 2.6))
        o.append(hazard(idp, 18, 0, cw - 36, thin=True))
        o.append(ghost_num(cw - 18, h - 16, f"0{i+1}", 74, op=".4", anchor="end"))
        o.append(txt(18, 36, f"0{i+1}", 9.5, FAINT, MONO, 2.4))
        o.append(f'<circle class="heat" cx="{cw-20}" cy="32" r="3.4" fill="{RED_GLOW}" '
                 f'style="animation-delay:{i*0.55:.2f}s"/>')
        o.append(counter(18, 88, val, 42, INK, DISP, -1.6, start=d + 0.15))
        # the meter: a red bar that fills, the machine reporting a level
        o.append(f'<rect x="18" y="100" width="{cw-36}" height="3" fill="{LINE2}"/>')
        o.append(f'<rect class="meter" x="18" y="100" width="{cw-36}" height="3" '
                 f'fill="{RED}" style="animation-delay:{d+0.25:.2f}s"/>')
        o.append(txt(18, 126, lab, fit(MONO_M, lab, 10, cw - 36, 1.8), REST, MONO_M, 1.8))
        o.append(txt(18, 148, sub, fit(TW, sub, 12, cw - 36), META, TW, 0))
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 5. TIMELINE — the build log, as a pipeline board
# ==========================================================================
def build_timeline():
    rows = [
        ("KONKRED AUDIT",
         "Prompt certification engine. Seven mathematical and logical formulas for valuation, accuracy scoring and certification of AI intellectual property.",
         "ok"),
        ("KONKRED ENTERPRISE",
         "Micro-tool marketplace. 500+ industrial-grade prompts across 10+ strategic domains, converted into autonomous agents via the Genesis Engine architecture.",
         "ok"),
        ("KONKRED REDEYE",
         "LLM red-team platform in TypeScript and React. 367 adversarial techniques catalogued; defensive layers against prompt injection and data leakage.",
         "ok"),
        ("KONKRED ARBITRA",
         "Documentation and licensing engine. API references, runbooks and architecture notes generated from code and prompts, then verified and versioned.",
         "ok"),
        ("AI ECONOMICS RESTRUCTURE",
         "Reverse-engineered COGS for large-scale Gemini deployments. Context management and caching strategy cut spend from $20,000 to $6,000.",
         "run"),
    ]
    w = 1200
    rh, gp = 100, 14
    h = len(rows) * (rh + gp) - gp
    idp = "t"
    css = GRAIN_CSS + IGNITE_CSS + MOTION_CSS + TYPED_CSS + """
  .row { animation: probe .45s ease backwards; }
  .node { animation: node 3.6s ease-in-out infinite; }
  @keyframes node { 0%,100% { opacity:.3 }
                    50% { opacity:1; filter: drop-shadow(0 0 8px rgba(255,26,46,.7)) } }
  .spine { stroke-dasharray: 70 500; animation: spine 8s linear infinite; }
  @keyframes spine { to { stroke-dashoffset: -570 } }
  .t0 .ign, .t0 .ign-s { animation-delay:0s }
  .t1 .ign, .t1 .ign-s { animation-delay:1.2s }
  .t2 .ign, .t2 .ign-s { animation-delay:2.4s }
  .t3 .ign, .t3 .ign-s { animation-delay:3.6s }
  .t4 .ign, .t4 .ign-s { animation-delay:4.8s }
"""
    o = [head(w, h, "Build log",
              "Pipeline board of shipped systems, with each entry marked complete or running.",
              css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))

    # the spine: a rail with a packet running down it
    o.append(f'<line x1="28" y1="0" x2="28" y2="{h}" stroke="{LINE1}" stroke-width="1.5"/>')
    o.append(f'<line class="spine" x1="28" y1="0" x2="28" y2="{h}" stroke="{RED}" stroke-width="2"/>')

    for i, (title, body, state) in enumerate(rows):
        y = i * (rh + gp)
        d = 0.05 + i * 0.1
        o.append(f'<g class="row t{i}" style="animation-delay:{d:.2f}s" '
                 f'transform="translate(0,{y})">')
        # node on the spine
        o.append(f'<rect x="21" y="{rh/2-7}" width="14" height="14" fill="{BLACK}" '
                 f'stroke="{LINE1}" stroke-width="1.5"/>')
        o.append(f'<rect class="node" x="24.5" y="{rh/2-3.5}" width="7" height="7" '
                 f'fill="{RED_GLOW}" style="animation-delay:{i*0.45:.2f}s"/>')
        # the bench
        bx = 62
        bwid = w - bx
        o.append(f'<path d="{octagon(bx, 0, bwid, rh, 14)}" fill="url(#{idp}pan)" '
                 f'stroke="{LINE2}" stroke-width="1.5" class="ign-s"/>')
        o.append(rivets(idp, bx, 0, bwid, rh, 9, 2.8))
        o.append(ghost_num(w - 26, rh - 20, f"0{i+1}", 70, op=".4", anchor="end"))
        o.append(txt(bx + 26, 30, f"W-0{i+1}", 10, RED, MONO_X, 2.4))
        o.append(typed(bx + 26, 56, title, 20, INK, DISP, -0.4,
                       start=d + 0.15, step=0.018))
        o.append(txt(bx + 26, 82, body, fit(TW, body, 13.5, bwid - 200), META, TW, 0))
        # pipeline state grammar
        lab = "[ok]" if state == "ok" else "[>>]"
        col = RED if state == "ok" else REST
        kls = "redglow" if state == "ok" else "steprun"
        o.append(txt(w - 26, 32, lab, 13, col, MONO_B, 1.2, "end", cls=kls))
        o.append(txt(w - 26, 52, "COMPLETE" if state == "ok" else "RUNNING",
                     9, FAINT, MONO, 2.4, "end"))
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 6. DIVIDER — hazard-thin tape with a running charge
# ==========================================================================
def build_divider():
    w, h = 1200, 22
    idp = "d"
    css = GRAIN_CSS + """
  .charge { animation: charge 5s linear infinite; }
  @keyframes charge { 0% { opacity:0; transform: translateX(0) }
                      8% { opacity:1 } 88% { opacity:1 }
                      100% { opacity:0; transform: translateX(1150px) } }
  .dtick { animation: dtick 3.2s ease-in-out infinite; }
  @keyframes dtick { 0%,100% { opacity:.3 } 50% { opacity:.9 } }
"""
    o = [head(w, h, "Divider", "Hazard tape divider with a running red charge.", css,
              defs=texture_defs(idp))]
    o.append(canvas(idp, w, h, smudge=False))
    o.append(hazard(idp, 0, 9, w, thin=True))
    for i in range(13):
        x = 24 + i * 96
        o.append(f'<rect class="dtick" x="{x}" y="4" width="1.5" height="5" fill="{FAINT}" '
                 f'style="animation-delay:{i*0.16:.2f}s"/>')
        o.append(f'<rect class="dtick" x="{x}" y="13" width="1.5" height="5" fill="{FAINT}" '
                 f'style="animation-delay:{i*0.16:.2f}s"/>')
    o.append(f'<rect class="charge" x="0" y="9" width="54" height="4" fill="{RED_GLOW}"/>')
    o.append(grain(idp, w, h, 0.3))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 7. FOOTER — giant hollow display + contact
# ==========================================================================
def build_footer():
    w, h = 1200, 210
    idp = "f"
    css = CUBE_CSS + GRAIN_CSS + IGNITE_CSS + f"""
  .fin {{ animation: fin .55s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes fin {{ from {{ opacity:0; transform: translateY(8px) }}
                    to   {{ opacity:1; transform: none }} }}
  .f0 {{ animation-delay:.06s }} .f1 {{ animation-delay:.18s }}
  .f2 {{ animation-delay:.30s }} .f3 {{ animation-delay:.42s }}
  .cube {{ animation: fin .6s cubic-bezier(.16,.84,.24,1) .04s backwards; }}
  .cyc {{ animation: cyc 16s linear infinite; }}
  @keyframes cyc {{
      0%  {{ opacity:0; transform: translateY(5px) }}
      3%  {{ opacity:1; transform: none }}
     22%  {{ opacity:1; transform: none }}
     25%  {{ opacity:0; transform: translateY(-5px) }}
    100%  {{ opacity:0; transform: translateY(-5px) }} }}
  .y0 {{ animation-delay:.6s }} .y1 {{ animation-delay:4.6s }}
  .y2 {{ animation-delay:8.6s }} .y3 {{ animation-delay:12.6s }}
  .caret {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 0%,49% {{ opacity:1 }} 50%,100% {{ opacity:0 }} }}
"""
    lines = [
        "Ship or don't ship.",
        "No pitch decks. No vapour.",
        "It works. That's not the same as being good.",
        "If in doubt: colder, sharper, quieter.",
    ]
    o = [head(w, h, "Contact",
              "Footer: available for remote work, contract, fractional or advisory. "
              "ari@konkred.xyz",
              css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))
    o.append(scanlines(idp, 0, 0, w, h))
    o.append(hazard(idp, 0, 0, w))

    # the giant hollow word behind everything
    o.append(hollow(w / 2, 150, "KONKRED", 118, stroke=LINE1, ls=2, sw=1.5,
                    anchor="middle", op=".7"))

    o.append(cube(idp, scale=0.36, tx=34, ty=46))

    x = 168
    o.append(f'<g class="fin f0">{txt(x, 62, "AVAILABLE FOR REMOTE WORK", 10, META, MONO_M, 3.6)}</g>')
    o.append(f'<g class="fin f1">{txt(x, 100, "CONTRACT · FRACTIONAL · ADVISORY", 25, INK, DISP, -0.6)}</g>')
    for i, ln in enumerate(lines):
        o.append(f'<g class="cyc y{i}" opacity="{1 if i == 0 else 0}">'
                 f'{txt(x, 132, ln, 14, BODY, TW, 0)}</g>')

    o.append('<g class="fin f2">')
    o.append(txt(w - 30, 62, "ari@konkred.xyz", 13, REST, MONO_M, 0.4, "end", cls="ign"))
    o.append(txt(w - 30, 86, "konkred.xyz", 13, RED, MONO_M, 0.4, "end", cls="redglow"))
    o.append(f'<line x1="{w-30}" y1="102" x2="{w-230}" y2="102" stroke="{LINE1}" stroke-width="1"/>')
    o.append(txt(w - 30, 124, "TIMEZONE FLEXIBLE · ASYNC-FIRST", 9.5, FAINT, MONO, 2.0, "end"))
    o.append('</g>')

    # terminal line
    o.append('<g class="fin f3">')
    cmd = "$ konkred status --remote --stack ai"
    o.append(txt(x, 170, cmd, 11, FAINT, MONO, 1.0))
    o.append(f'<rect class="caret" x="{x + tw(MONO, cmd, 11, 1.0) + 5:.1f}" y="160" '
             f'width="7" height="12" fill="{RED}"/>')
    o.append(f'<line x1="30" y1="186" x2="{w-30}" y2="186" stroke="{LINE1}" stroke-width="1"/>')
    o.append(txt(30, 202, "KONKRED — FACTORY FLOOR", 9, FAINT, MONO, 2.0))
    o.append(txt(w - 30, 202, "BLACK #0A0908 · RED #D60019 · INK #F4F1EB", 9, FAINT, MONO, 1.4, "end"))
    o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 8. STANDALONE MARK
# ==========================================================================
def build_mark():
    w, h = 220, 268
    idp = "k"
    css = CUBE_CSS + GRAIN_CSS + """
  .cube { animation: mi .7s cubic-bezier(.16,.84,.24,1) .05s backwards; }
  @keyframes mi { from { opacity:0; transform: translateY(9px) } to { opacity:1; transform: none } }
"""
    o = [head(w, h, "Cube-K mark", "The KONKRED Cube-K mark, ash block with the K cut through.",
              css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))
    o.append(cube(idp, scale=1.0, tx=10, ty=8))
    o.append(txt(110, 250, "KONKRED", 13, REST, MONO_X, 6.0, "middle"))
    o.append(hazard(idp, 40, 260, 140, thin=True))
    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 9. LINK BADGES — keycaps, not shields
# ==========================================================================
def build_badge(label, accent=False):
    """Brand-styled link badges.

    Replaces shields.io: a third-party image renders in its own typeface and
    palette, breaking the theme, and adds an external dependency to a README
    that otherwise has none. These are keycaps — 1.5px border with a 3.5px
    bevel on the bottom edge, exactly as spec s.6.2 defines them.
    """
    size, ls, padx, h = 10.5, 2.2, 14, 32
    lab = label.upper()
    text_w = tw(MONO_M, lab, size, ls)
    w = int(round(text_w + padx * 2 + (16 if accent else 0)))
    idp = "b"

    css = f"""
  .b {{ animation: bin .45s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes bin {{ from {{ opacity:0; transform: translateY(5px) }}
                    to   {{ opacity:1; transform: none }} }}
  .bdot {{ animation: bsig 2.4s ease-in-out infinite; }}
  @keyframes bsig {{ 0%,100% {{ opacity:.35 }}
                     50% {{ opacity:1; filter: drop-shadow(0 0 6px rgba(255,26,46,.8)) }} }}
  .blab {{ animation: blab 5s ease-in-out infinite; }}
  @keyframes blab {{ 0%,72%,100% {{ fill: {REST} }}
                     14%,44% {{ fill: {RED_GLOW};
                                filter: drop-shadow(0 0 6px rgba(255,26,46,.6)) }} }}
"""
    o = [head(w, h, label, f"Link badge: {label}", css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h, smudge=False))
    o.append('<g class="b">')
    o.append(f'<rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5-3.5}" '
             f'fill="{SUNKEN2}" stroke="{RED if accent else EDGE}" stroke-width="1.5"/>')
    o.append(f'<rect x="0.75" y="{h-4.25}" width="{w-1.5}" height="3.5" '
             f'fill="{RED if accent else EDGE}"/>')
    if accent:
        o.append(f'<circle class="bdot" cx="14" cy="{(h-3.5)/2}" r="3.2" fill="{RED_GLOW}"/>')
    o.append(txt(padx + (16 if accent else 0), (h - 3.5) / 2 + 3.6, lab, size,
                 RED if accent else REST, MONO_M, ls, cls="" if accent else "blab"))
    o.append('</g>')
    o.append(grain(idp, w, h, 0.3))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 10. SERVICES — what can actually be engaged
# ==========================================================================
def build_services():
    rows = [
        ("R&D / AI ARCHITECTURE", "applied research turned into deployable llm systems",
         ["RAG architecture", "Hallucination mitigation", "Multi-modal",
          "Chain-of-Thought / ReAct", "Agent orchestration"]),
        ("LLM SECURITY / RED TEAMING", "adversarial testing and defensive layers for production models",
         ["Jailbreak taxonomy", "Filter-bypass typing", "Prompt injection defence",
          "Data-leak mitigation", "Chatbot hardening"]),
        ("ENTERPRISE PROMPT LICENSING", "500+ industrial-grade prompts, licensed and converted into tooling",
         ["Arbitra Enterprise Library", "Genesis Engine conversion", "PRD / SDP authoring",
          "Autonomous agents", "Micro-tools"]),
        ("APP AND BOT BUILDING", "full-stack delivery of ai tools with custom interfaces",
         ["Python / FastAPI / Flask", "React / TypeScript", "Custom GUIs", "Marketplace deployment"]),
    ]
    w = 1200
    rh, gap = 146, 16
    h = len(rows) * (rh + gap) - gap
    idp = "v"

    css = GRAIN_CSS + IGNITE_CSS + MOTION_CSS + TYPED_CSS + f"""
  .srow {{ animation: probe .5s ease backwards; }}
  .key {{ animation: keyin .4s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes keyin {{ from {{ opacity:0; transform: translateY(5px) }}
                      to   {{ opacity:1; transform: none }} }}
  .v0 .ign, .v0 .ign-s, .v0 .beam, .v0 .flood {{ animation-delay:0s }}
  .v1 .ign, .v1 .ign-s, .v1 .beam, .v1 .flood {{ animation-delay:1.5s }}
  .v2 .ign, .v2 .ign-s, .v2 .beam, .v2 .flood {{ animation-delay:3s }}
  .v3 .ign, .v3 .ign-s, .v3 .beam, .v3 .flood {{ animation-delay:4.5s }}
"""
    o = [head(w, h, "Services",
              "What can be engaged: AI architecture, LLM security and red teaming, "
              "enterprise prompt licensing, app and bot building.",
              css, defs=texture_defs(idp))]
    clips = "".join(
        f'<clipPath id="{idp}clip{i}"><path d="{octagon(0, 0, w, rh, 14)}"/></clipPath>'
        for i in range(len(rows)))
    o.append(f'<defs>{clips}</defs>')
    o.append(canvas(idp, w, h))

    for i, (title, sub, chips) in enumerate(rows):
        y = i * (rh + gap)
        d = 0.06 + i * 0.12
        o.append(f'<g class="srow v{i}" style="animation-delay:{d:.2f}s" '
                 f'transform="translate(0,{y})">')
        o.append(f'<path d="{octagon(0, 0, w, rh, 14)}" fill="url(#{idp}pan)" '
                 f'stroke="{LINE2}" stroke-width="1.5" class="ign-s"/>')
        o.append(f'<g clip-path="url(#{idp}clip{i})">')
        o.append(soft_chalk(idp, 0, 0, w, rh, 0.28))
        o.append(f'<rect class="flood" x="0" y="{rh-60}" width="{w}" height="60" '
                 f'fill="url(#{idp}flood)"/>')
        o.append(f'<g class="beam" style="--run:{w+140}px">'
                 f'<rect x="-140" y="-30" width="110" height="{rh+60}" '
                 f'fill="url(#{idp}beam)" transform="skewX(-14)"/></g>')
        o.append(f'<rect x="0" y="0" width="5" height="{rh}" fill="{RED}"/>')
        o.append('</g>')
        o.append(rivets(idp, 0, 0, w, rh, 10, 2.8))
        o.append(ghost_num(w - 24, rh - 22, f"0{i+1}", 96, op=".45", anchor="end"))

        o.append(txt(30, 34, f"ZONE {['I', 'II', 'III', 'IV'][i]}", 9.5, RED, MONO_X, 3.0))
        tsize = fit(DISP, title, 23, w - 260, -0.5)
        o.append(typed(30, 66, title, tsize, INK, DISP, -0.5, start=d + 0.18, step=0.016))
        o.append(txt(30, 92, sub, 14, META, TW, 0))

        cx = 30.0
        for j, c in enumerate(chips):
            cwid = round(tw(MONO_M, c.upper(), 9.5, 1.6) + 20, 1)
            ky = rh - 44
            o.append(f'<g class="key" style="animation-delay:{d+0.4+j*0.06:.2f}s">')
            o.append(f'<rect x="{cx:.1f}" y="{ky}" width="{cwid}" height="26" '
                     f'fill="{SUNKEN2}" stroke="{EDGE}" stroke-width="1.5"/>')
            o.append(f'<rect x="{cx:.1f}" y="{ky+22.5}" width="{cwid}" height="3.5" fill="{EDGE}"/>')
            o.append(txt(cx + 10, ky + 15.5, c.upper(), 9.5, REST, MONO_M, 1.6))
            o.append('</g>')
            cx += cwid + 8
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 11. DOMAINS — fig plates on a blueprint
# ==========================================================================
def build_domains():
    doms = [
        ("LEGAL", "contracts, compliance, discovery"),
        ("FINANCE", "modelling, risk, reporting"),
        ("ENGINEERING", "specs, review, diagnostics"),
        ("HEALTHCARE", "triage, documentation, coding"),
        ("HEAVY INDUSTRY", "maintenance, safety, ops"),
    ]
    w = 1200
    cols, cwid, chh, gap = 5, 232, 118, 10
    h = chh
    idp = "n"

    css = GRAIN_CSS + IGNITE_CSS + f"""
  .dom {{ animation: domin .5s cubic-bezier(.16,.84,.24,1) backwards; }}
  @keyframes domin {{ from {{ opacity:0; transform: scale(.965) }}
                      to   {{ opacity:1; transform: none }} }}
  .lock {{ animation: lock 6s ease-in-out infinite; }}
  @keyframes lock {{ 0%,72%,100% {{ stroke: {LINE1} }}
                     14%,44% {{ stroke: {RED_GLOW};
                                filter: drop-shadow(0 0 6px rgba(255,26,46,.6)) }} }}
  .n0 .ign, .n0 .lock {{ animation-delay:0s }}
  .n1 .ign, .n1 .lock {{ animation-delay:1.2s }}
  .n2 .ign, .n2 .lock {{ animation-delay:2.4s }}
  .n3 .ign, .n3 .lock {{ animation-delay:3.6s }}
  .n4 .ign, .n4 .lock {{ animation-delay:4.8s }}
"""
    o = [head(w, h, "Domains",
              "Strategic domains where the prompt library has shipped: legal, finance, "
              "engineering, healthcare, heavy industry.", css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))

    for i, (name, sub) in enumerate(doms):
        cx = i * (cwid + gap)
        d = 0.04 + i * 0.055
        o.append(f'<g class="dom n{i}" style="animation-delay:{d:.2f}s" '
                 f'transform="translate({cx},0)">')
        o.append(f'<path d="{octagon(0, 0, cwid, chh, 12)}" fill="url(#{idp}pan)" '
                 f'stroke="{LINE2}" stroke-width="1.5"/>')
        o.append(f'<rect x="14" y="40" width="{cwid-28}" height="{chh-58}" '
                 f'fill="url(#{idp}bp)" opacity=".8"/>')
        o.append(rivets(idp, 0, 0, cwid, chh, 8, 2.6))
        # .lock — two corner brackets that acquire the target
        o.append(f'<g fill="none" stroke="{LINE1}" stroke-width="1.6" class="lock">'
                 f'<polyline points="10,26 10,14 22,14"/>'
                 f'<polyline points="{cwid-22},{chh-14} {cwid-10},{chh-14} {cwid-10},{chh-26}"/>'
                 f'</g>')
        o.append(txt(16, 28, f"FIG.{i+1}", 9, FAINT, MONO, 2.2))
        nsize = fit(DISP, name, 15, cwid - 34, 0.4)
        o.append(txt(16, 66, name, nsize, REST, DISP, 0.4, cls="ign"))
        o.append(f'<line x1="16" y1="80" x2="{cwid-16}" y2="80" stroke="{LINE2}" stroke-width="1"/>')
        o.append(txt(16, 100, sub, fit(TW, sub, 12, cwid - 32), META, TW, 0))
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 12. WRITING — stapled paper sheets
# ==========================================================================
def build_writing():
    books = [
        ("Tame the Machine", "Enterprise AI governance and deployment", "1,000pp"),
        ("Google AI Studio Goldmine", "Economics and profitability of the Gemini era", "19 CH"),
        ("The Genesis Engine", "Generative architecture for heavy industry", "ARBITRA"),
        ("Prompting the Beast", "Hallucination control and output steering", "MANUAL"),
        ("Quantum Engineering Reality", "Quantum algorithms in practice with Qiskit", "QISKIT"),
        ("From Prompt to Power", "Workflow patterns for conversational systems", "PATTERNS"),
        ("Revolutionizing SEO", "Machine learning for digital strategy", "APPLIED"),
    ]
    w = 1200
    rh, gap = 62, 9
    h = len(books) * (rh + gap) - gap
    idp = "wr"

    css = GRAIN_CSS + IGNITE_CSS + """
  .sheet { animation: sheet .45s ease backwards; }
  @keyframes sheet { from { opacity:0; transform: translateX(-8px) }
                     to   { opacity:1; transform: none } }
  .w0 .ign { animation-delay:0s }   .w1 .ign { animation-delay:.85s }
  .w2 .ign { animation-delay:1.7s } .w3 .ign { animation-delay:2.55s }
  .w4 .ign { animation-delay:3.4s } .w5 .ign { animation-delay:4.25s }
  .w6 .ign { animation-delay:5.1s }
"""
    o = [head(w, h, "Writing",
              "Selected manuscripts on AI governance, economics, security and quantum computing.",
              css, defs=texture_defs(idp))]
    o.append(canvas(idp, w, h))

    for i, (title, sub, tag) in enumerate(books):
        y = i * (rh + gap)
        d = 0.04 + i * 0.07
        o.append(f'<g class="sheet w{i}" style="animation-delay:{d:.2f}s" '
                 f'transform="translate(0,{y})">')
        # a paper sheet: sunken surface, hairline, stapled at the top-left
        o.append(f'<rect x="0.75" y="0.75" width="{w-1.5}" height="{rh-1.5}" '
                 f'fill="{SUNKEN}" stroke="{LINE2}" stroke-width="1.5"/>')
        o.append(f'<rect x="0" y="0" width="4" height="{rh}" fill="{RED}"/>')
        o.append(staple(22, 12))
        o.append(staple(22, rh - 16))
        o.append(txt(52, 26, f"MS-{i+1:02d}", 9, FAINT, MONO, 2.2))
        o.append(txt(52, 47, title, 16.5, REST, TW, 0, cls="ign"))
        o.append(txt(430, 40, sub, 13.5, META, TW, 0))
        o.append(txt(w - 24, 40, tag, 10, RED, MONO_X, 2.2, "end"))
        o.append('</g>')

    o.append(grain(idp, w, h))
    o.append('</svg>')
    return "".join(o)


def main():
    os.makedirs(OUT, exist_ok=True)
    if not fontpack.available():
        raise SystemExit(
            "Brand fonts missing from tools/fonts/. Without them GitHub falls back "
            "to a generic system font and the theme's typography is lost."
        )
    files = {
        "header.svg":   render(build_header),
        "products.svg": render(build_products),
        "stack.svg":    render(build_stack),
        "metrics.svg":  render(build_metrics),
        "timeline.svg": render(build_timeline),
        "divider.svg":  render(build_divider),
        "footer.svg":   render(build_footer),
        "cube-k.svg":   render(build_mark),
        "services.svg": render(build_services),
        "domains.svg":  render(build_domains),
        "writing.svg":  render(build_writing),
        "badge-site.svg":    render(lambda: build_badge("konkred.xyz", True)),
        "badge-email.svg":   render(lambda: build_badge("ari@konkred.xyz")),
        "badge-remote.svg":  render(lambda: build_badge("OPEN TO REMOTE")),
        "badge-profile.svg": render(lambda: build_badge("INTERACTIVE PROFILE")),
    }
    for name, body in files.items():
        p = os.path.join(OUT, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"  {name:<19} {len(body):>8,} bytes")
    print(f"\n{len(files)} assets written to {OUT}")

    # Mirror into docs/ so the GitHub Pages site is self-contained regardless of
    # whether Pages is configured to serve the repo root or the /docs folder.
    import shutil
    docs_assets = os.path.join(os.path.dirname(OUT), "docs", "assets")
    os.makedirs(docs_assets, exist_ok=True)
    for name in files:
        shutil.copyfile(os.path.join(OUT, name), os.path.join(docs_assets, name))
    print(f"{len(files)} assets mirrored to {docs_assets}")


if __name__ == "__main__":
    main()
