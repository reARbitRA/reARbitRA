#!/usr/bin/env python3
"""
KONKRED profile asset generator.

Emits self-contained animated SVGs for the GitHub profile README.
Everything is derived from the KONKRED Brand System v2 (2026-06-22):

  Colour   Void #0B0F14 - Clinical #D7D9DD - Signal Amber #D98A2E
  Type     IBM Plex Mono (primary) + Inter (body)
  Mark     Cube-K v3, isometric 30 degrees, K excavated through the right face
  Motion   scan 4s linear - trace 11-12s linear - glow 3.2-3.4s ease-in-out
           card reveal 0.16-0.18s ease-out - signal dot 2.4s ease-in-out
           easing: linear or ease-out only, no spring, no bounce
           respects prefers-reduced-motion

GitHub renders README images inside <img>, which blocks scripts, external
fonts and pointer events. So: no JS, system font stacks only, and every
"interaction" is expressed as an autonomous looping/staggered animation.
Real hover/parallax interaction lives on the Pages site in docs/.

Usage:  python3 tools/build_assets.py
"""

import math
import os

# --------------------------------------------------------------------------
# Brand tokens - Brand System v2, sections 03 and 07
# --------------------------------------------------------------------------
VOID      = "#0B0F14"   # ground
CARD      = "#0E1319"   # Void-2, elevated surfaces
ROW       = "#0D1218"   # tool / product rows
LINE      = "#1A212B"   # borders
LINE2     = "#222B36"   # hover / inputs
MUTED     = "#9AA0A8"   # secondary text
MID       = "#6B717A"   # meta / labels
CLINICAL  = "#D7D9DD"   # primary text
CONC_LT   = "#E8E9EC"   # cube top face
CONC_SH   = "#C4C7CC"   # cube right face
CONC_MD   = "#D7D9DD"   # cube left face
SIGNAL    = "#D98A2E"   # accent - one element per composition
WIRE      = "#7a7f88"   # interior wireframe
WIRE2     = "#8a8f97"   # icon secondary

MONO  = "ui-monospace,'IBM Plex Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace"
INTER = "Inter,'Segoe UI',system-ui,-apple-system,'Helvetica Neue',sans-serif"

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------
# Cube-K v3 geometry - isometric 30 degrees, master space 200 x 220
# --------------------------------------------------------------------------
S = 100.0
W = S * math.cos(math.radians(30))      # 86.6025
H = S * 0.5                             # 50
OX, OY = 100.0, 10.0

T  = (OX,     OY)             # top vertex
TR = (OX + W, OY + H)         # top-right
TL = (OX - W, OY + H)         # top-left
C  = (OX,     OY + 2 * H)     # centre (front-top)
BL = (OX - W, OY + H + S)     # bottom-left
BR = (OX + W, OY + H + S)     # bottom-right
B  = (OX,     OY + 2 * H + S) # bottom vertex


def rf(u, v):
    """Point on the RIGHT face. u = horizontal 0..1, v = vertical 0..1."""
    return (C[0] + u * W, C[1] - u * H + v * S)


def lf(u, v):
    """Point on the LEFT face."""
    return (TL[0] + u * W, TL[1] + u * H + v * S)


def tf(a, b):
    """Point on the TOP face, a toward TR, b toward TL."""
    return (T[0] + a * W - b * W, T[1] + a * H + b * H)


def pt(p):
    return f"{p[0]:.2f},{p[1]:.2f}"


def poly(points):
    return " ".join(pt(p) for p in points)


# K letterform in right-face (u, v) space. The K is not drawn - it is cut.
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


def small_cube(top, side, opacity=0.85):
    """3-face isometric concrete block, `top` is the apex vertex."""
    w, h = side * math.cos(math.radians(30)), side * 0.5
    x, y = top
    t  = (x, y)
    tr = (x + w, y + h)
    tl = (x - w, y + h)
    c  = (x, y + 2 * h)
    bl = (x - w, y + h + side)
    br = (x + w, y + h + side)
    b  = (x, y + 2 * h + side)
    return (
        f'<g opacity="{opacity}">'
        f'<polygon points="{poly([t,tr,c,tl])}" fill="{CONC_LT}" opacity=".55"/>'
        f'<polygon points="{poly([tl,c,b,bl])}" fill="{CONC_MD}" opacity=".38"/>'
        f'<polygon points="{poly([c,tr,br,b])}" fill="{CONC_SH}" opacity=".26"/>'
        f'</g>'
    )


def cube(idp, scale=1.0, tx=0.0, ty=0.0):
    """Full animated Cube-K v3 mark. `idp` namespaces the defs per file."""
    o = []
    o.append(f'<defs>')
    o.append(f'<clipPath id="{idp}kcut"><path d="{K_PATH}"/></clipPath>')
    o.append(f'<clipPath id="{idp}sil"><path d="{CUBE_SIL}"/></clipPath>')
    o.append(
        f'<linearGradient id="{idp}scan" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{SIGNAL}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{SIGNAL}" stop-opacity=".5"/>'
        f'<stop offset="100%" stop-color="{SIGNAL}" stop-opacity="0"/>'
        f'</linearGradient>'
    )
    o.append('</defs>')

    o.append(f'<g transform="translate({tx},{ty}) scale({scale})" class="cube">')

    # --- three faces ------------------------------------------------------
    o.append(f'<path d="{FACE_TOP}" fill="{CONC_LT}"/>')
    o.append(f'<path d="{FACE_LFT}" fill="{CONC_MD}"/>')
    o.append(f'<path d="{FACE_RGT}" fill="{CONC_SH}"/>')

    # --- the K excavation: void, then interior structure ------------------
    o.append(f'<path d="{K_PATH}" fill="{VOID}"/>')
    o.append(f'<g clip-path="url(#{idp}kcut)">')
    #     isometric hatch, horizontal run of the right face
    for i in range(19):
        v = i / 18.0
        a, b = rf(0.0, v), rf(1.0, v)
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{WIRE}" stroke-width=".7" opacity=".34"/>')
    #     vertical wires
    for i in range(11):
        u = i / 10.0
        a, b = rf(u, 0.0), rf(u, 1.0)
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{WIRE}" stroke-width=".55" opacity=".22"/>')
    #     K-truss cross-brace, arrow form
    br1, br2 = rf(0.16, 0.90), rf(0.86, 0.10)
    br3, br4 = rf(0.16, 0.10), rf(0.86, 0.90)
    o.append(f'<line x1="{br1[0]:.2f}" y1="{br1[1]:.2f}" x2="{br2[0]:.2f}" y2="{br2[1]:.2f}" '
             f'stroke="{WIRE2}" stroke-width="1.5" opacity=".5"/>')
    o.append(f'<line x1="{br3[0]:.2f}" y1="{br3[1]:.2f}" x2="{br4[0]:.2f}" y2="{br4[1]:.2f}" '
             f'stroke="{WIRE2}" stroke-width="1.5" opacity=".28"/>')
    #     interior concrete block, bottom-right
    o.append(small_cube(rf(0.60, 0.50), 24))
    #     scanning band inside the cut - 4s linear infinite
    o.append(f'<rect class="scanband" x="0" y="-70" width="200" height="70" fill="url(#{idp}scan)"/>')
    o.append('</g>')

    # --- K edge glow, 3.3s ease-in-out ------------------------------------
    o.append(f'<path class="kedge" d="{K_PATH}" fill="none" stroke="{SIGNAL}" '
             f'stroke-width="1.15" stroke-linejoin="miter"/>')

    # --- face edges -------------------------------------------------------
    o.append(f'<path d="{CUBE_SIL}" fill="none" stroke="{VOID}" stroke-width="1.2" opacity=".55"/>')
    for a, b in ((T, C), (TL, C), (TR, C), (C, B)):
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{VOID}" stroke-width="1" opacity=".3"/>')

    # --- crop marks on the top face, left + right -------------------------
    for a0, b0, a1, b1 in ((0.14, 0.80, 0.30, 0.80), (0.80, 0.14, 0.80, 0.30)):
        p, q = tf(a0, b0), tf(a1, b1)
        o.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
                 f'stroke="{MID}" stroke-width="1.1" opacity=".85"/>')

    # --- diagonal tick on the left face -----------------------------------
    p, q = lf(0.10, 0.10), lf(0.26, 0.18)
    o.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
             f'stroke="{MID}" stroke-width="1.1" opacity=".7"/>')

    # --- 3 floor rails on the left face -----------------------------------
    for v in (0.74, 0.82, 0.90):
        p, q = lf(0.06, v), lf(0.94, v)
        o.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
                 f'stroke="{MID}" stroke-width=".9" opacity=".4"/>')

    # --- signal circuit trace, dash drift 11.5s linear --------------------
    tr_pts = [rf(0.055, 0.955), rf(0.90, 0.955), rf(0.90, 0.06)]
    o.append(f'<polyline class="trace" points="{poly(tr_pts)}" fill="none" '
             f'stroke="{SIGNAL}" stroke-width="2.4" stroke-linecap="square" '
             f'stroke-linejoin="miter" opacity=".9"/>')
    tip = rf(0.90, 0.06)
    o.append(f'<circle class="sigdot" cx="{tip[0]:.2f}" cy="{tip[1]:.2f}" r="3.2" fill="{SIGNAL}"/>')

    # --- full-cube scan sweep --------------------------------------------
    o.append(f'<g clip-path="url(#{idp}sil)">'
             f'<rect class="scanband2" x="0" y="-90" width="200" height="90" fill="url(#{idp}scan)"/>'
             f'</g>')
    o.append('</g>')
    return "".join(o)


CUBE_CSS = f"""
  .scanband  {{ animation: scanY 4s linear infinite; }}
  .scanband2 {{ animation: scanY 4s linear infinite; opacity:.5; }}
  @keyframes scanY {{ from {{ transform: translateY(0); }} to {{ transform: translateY(300px); }} }}
  .kedge {{ animation: kglow 3.3s ease-in-out infinite; }}
  @keyframes kglow {{ 0%,100% {{ opacity:.30; }} 50% {{ opacity:.78; }} }}
  .trace {{ stroke-dasharray: 16 10; animation: drift 11.5s linear infinite; }}
  @keyframes drift {{ to {{ stroke-dashoffset: -260; }} }}
  .sigdot {{ animation: sig 2.4s ease-in-out infinite; }}
  @keyframes sig {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:1; }} }}
"""

def motion(css: str) -> str:
    """Wrap animation rules so they only apply when motion is welcome.

    Critical: the *base* state of every element must be fully visible. GitHub
    serves README images through a camo proxy, and some renderers (and every
    static rasteriser) apply no CSS animation at all. If the base state were
    `opacity:0` the profile would render blank. So animation is strictly an
    enhancement layered on top of a readable static composition, which also
    satisfies the brand's prefers-reduced-motion requirement for free.
    """
    return "@media (prefers-reduced-motion: no-preference){" + css + "}"


def head(w, h, title, desc, css, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" role="img" '
        f'aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f'<defs>{defs}</defs>'
        f'<style>{motion(css)}</style>'
    )


def grid(idp, w, h, size=40, op=0.022):
    return (
        f'<defs><pattern id="{idp}g" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<path d="M {size} 0 L 0 0 0 {size}" fill="none" stroke="{CLINICAL}" '
        f'stroke-width="1" opacity="{op}"/></pattern></defs>'
        f'<rect width="{w}" height="{h}" fill="url(#{idp}g)"/>'
    )


def crops(w, h, m=14, l=12, op=".55"):
    """Structural crop marks - brand rule, never remove."""
    o = []
    for (x, y, dx, dy) in ((m, m, 1, 0), (m, m, 0, 1),
                           (w - m, m, -1, 0), (w - m, m, 0, 1),
                           (m, h - m, 1, 0), (m, h - m, 0, -1),
                           (w - m, h - m, -1, 0), (w - m, h - m, 0, -1)):
        o.append(f'<line x1="{x}" y1="{y}" x2="{x+dx*l}" y2="{y+dy*l}" '
                 f'stroke="{SIGNAL}" stroke-width="1.1" opacity="{op}"/>')
    return "".join(o)


def txt(x, y, s, size=13, fill=CLINICAL, family=MONO, weight="400",
        ls=None, anchor="start", cls="", extra=""):
    a = f' letter-spacing="{ls}"' if ls is not None else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text{c} x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{a}{extra}>{esc(s)}</text>')


# ==========================================================================
# 1. HEADER
# ==========================================================================
def build_header():
    w, h = 1200, 340
    roles = [
        "AI architect  ·  research & development lead",
        "LLM security  ·  red teaming & guardrail validation",
        "App builder  ·  agents, bots, micro-tools",
        "AI economics  ·  infrastructure & cost engineering",
    ]
    css = CUBE_CSS + f"""
  .rise {{ animation: rise .5s ease-out backwards; }}
  @keyframes rise {{ from {{ opacity:0; transform: translateY(7px); }}
                     to   {{ opacity:1; transform: translateY(0); }} }}
  .cube {{ animation: rise .7s ease-out .05s backwards; }}
  .r0 {{ animation-delay:.10s }} .r1 {{ animation-delay:.22s }}
  .r2 {{ animation-delay:.34s }} .r3 {{ animation-delay:.46s }}
  .r4 {{ animation-delay:.58s }} .r5 {{ animation-delay:.70s }}
  .rot {{ animation: rot 15s linear infinite; }}
  @keyframes rot {{
     0%   {{ opacity:0; transform: translateY(6px); }}
     2.5% {{ opacity:1; transform: translateY(0); }}
    22.5% {{ opacity:1; transform: translateY(0); }}
    25%   {{ opacity:0; transform: translateY(-6px); }}
   100%   {{ opacity:0; transform: translateY(-6px); }} }}
  .k0 {{ animation-delay:.9s }} .k1 {{ animation-delay:4.65s }}
  .k2 {{ animation-delay:8.4s }} .k3 {{ animation-delay:12.15s }}
  .rail {{ stroke-dasharray: 200 900; animation: railrun 9s linear infinite; }}
  @keyframes railrun {{ to {{ stroke-dashoffset: -1100; }} }}
  .live {{ animation: sig 2.4s ease-in-out infinite; }}
  .caret {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes blink {{ 0%,49% {{ opacity:1 }} 50%,100% {{ opacity:0 }} }}
"""
    o = [head(w, h, "Ari Miyanji - AI research and development",
              "Animated KONKRED-branded profile header with the Cube-K mark.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')
    o.append(grid("h", w, h))
    o.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="{LINE}" stroke-width="1"/>')
    o.append(crops(w, h))

    o.append(cube("h", scale=0.80, tx=52, ty=58))

    x = 282
    o.append(f'<g class="rise r0">')
    o.append(txt(x, 92, "AI RESEARCH  ·  DEVELOPMENT  ·  SECURITY", 11, MID, MONO, "400", "3.6"))
    o.append('</g>')

    o.append(f'<g class="rise r1">')
    o.append(txt(x, 152, "ARI MIYANJI", 50, CONC_LT, MONO, "600", "11"))
    o.append('</g>')

    o.append(f'<g class="rise r2">')
    o.append(f'<line x1="{x}" y1="174" x2="742" y2="174" stroke="{LINE2}" stroke-width="1"/>')
    o.append(f'<line class="rail" x1="{x}" y1="174" x2="742" y2="174" stroke="{SIGNAL}" stroke-width="1.6"/>')
    o.append('</g>')

    # rotating role line - appears and disappears
    for i, r in enumerate(roles):
        o.append(f'<g class="rot k{i}" opacity="{1 if i == 0 else 0}">'
                 f'{txt(x, 208, r, 16, CLINICAL, MONO, "500", "0.4")}</g>')

    o.append(f'<g class="rise r4">')
    o.append(txt(x, 246, "Concrete tools for abstract problems.", 15, MUTED, INTER, "400"))
    o.append('</g>')

    # availability pill
    o.append(f'<g class="rise r5">')
    o.append(f'<rect x="{x}" y="266" width="352" height="30" fill="{ROW}" stroke="{LINE2}" stroke-width="1" rx="2"/>')
    o.append(f'<circle class="live" cx="{x+16}" cy="281" r="3.6" fill="{SIGNAL}"/>')
    o.append(txt(x + 30, 285, "OPEN TO REMOTE ENGAGEMENTS  —  WORLDWIDE", 10.5, MUTED, MONO, "400", "1.5"))
    o.append('</g>')

    # right meta column
    o.append(f'<g class="rise r3">')
    o.append(txt(w - 40, 92, "BRAND SYSTEM v2", 10, MID, MONO, "400", "2.4", "end"))
    o.append(txt(w - 40, 110, "konkred.xyz", 10, SIGNAL, MONO, "400", "1.6", "end"))
    o.append(f'<line x1="{w-40}" y1="126" x2="{w-160}" y2="126" stroke="{LINE2}" stroke-width="1"/>')
    for i, s in enumerate(["AUDIT", "ENTERPRISE", "REDEYE", "ARBITRA"]):
        o.append(txt(w - 40, 150 + i * 19, s, 10, MID, MONO, "400", "2.0", "end"))
    o.append('</g>')

    # terminal caret line
    o.append(f'<g class="rise r5">')
    o.append(txt(x, 320, "$ status --remote --stack ai", 10.5, MID, MONO, "400", "1.2"))
    o.append(f'<rect class="caret" x="{x+178}" y="311" width="6" height="11" fill="{SIGNAL}"/>')
    o.append('</g>')

    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 2. PRODUCTS
# ==========================================================================
ICONS = {
    "verify": ['M12 2 L20 5.6 V11.2 C20 16.4 16.6 20.2 12 22 C7.4 20.2 4 16.4 4 11.2 V5.6 Z',
               'M8.3 11.9 L11 14.6 L15.9 9.3'],
    "market": ['M3 8.2 L5.2 3.6 H18.8 L21 8.2 M3 8.2 H21 M4.8 8.2 V20.4 H19.2 V8.2 M9.2 20.4 V13.4 H14.8 V20.4'],
    "secure": ['M12 2 L20 5.6 V11.2 C20 16.4 16.6 20.2 12 22 C7.4 20.2 4 16.4 4 11.2 V5.6 Z',
               'M12 9.4 A2 2 0 1 1 12 13.4 A2 2 0 1 1 12 9.4 M12 13.4 V16.6'],
    "docs":   ['M6 2.6 H14.2 L18.6 7 V21.4 H6 Z', 'M14.2 2.6 V7 H18.6',
               'M9 12.2 H15.6 M9 15.2 H15.6 M9 18.2 H13.2'],
}


def icon(name, x, y, scale=1.0, color=CLINICAL):
    paths = "".join(f'<path d="{p}" />' for p in ICONS[name])
    return (f'<g transform="translate({x},{y}) scale({scale})" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linecap="square" stroke-linejoin="miter">{paths}</g>')


def build_products():
    cards = [
        ("verify", "PROMPT CERTIFICATION", "KONKRED Audit",
         ["Audit prompts. Value them. Certify them. Structured",
          "evaluation, quality scoring, compliance trail — proof",
          "an AI asset works before it ships."],
         "audit · valuation · certification"),
        ("market", "MICRO-TOOL SUITE", "KONKRED Enterprise",
         ["Micro-tools built from enterprise-grade prompt systems",
          "across legal, finance, engineering and heavy industry.",
          "One input, concrete output. No configuration theatre."],
         "micro-tools · enterprise prompts · multi-domain"),
        ("secure", "AI SECURITY", "KONKRED Redeye",
         ["Red teaming and AI security. Adversarial prompt testing,",
          "jailbreak surface mapping, guardrail validation.",
          "367 techniques catalogued and typed."],
         "red team · adversarial · guardrails"),
        ("docs", "DOCUMENTATION", "KONKRED Arbitra",
         ["Build documentation from code, from prompts, from systems",
          "that never had any. API references, runbooks, architecture",
          "notes — generated, verified, versioned."],
         "docs · api refs · runbooks"),
    ]
    cw, ch, gap = 588, 214, 24
    w, h = cw * 2 + gap, ch * 2 + gap
    css = f"""
  .card {{ animation: cardin .55s ease-out backwards; }}
  @keyframes cardin {{ from {{ opacity:0; transform: translateY(9px); }}
                       to   {{ opacity:1; transform: translateY(0); }} }}
  .c0 {{ animation-delay:.05s }} .c1 {{ animation-delay:.19s }}
  .c2 {{ animation-delay:.33s }} .c3 {{ animation-delay:.47s }}
  .corner {{ animation: cpulse 5.2s ease-in-out infinite; }}
  @keyframes cpulse {{ 0%,100% {{ opacity:.22 }} 50% {{ opacity:.95 }} }}
  .p0 .corner {{ animation-delay:0s }} .p1 .corner {{ animation-delay:1.3s }}
  .p2 .corner {{ animation-delay:2.6s }} .p3 .corner {{ animation-delay:3.9s }}
  .live {{ animation: sig 2.4s ease-in-out infinite; }}
  @keyframes sig {{ 0%,100% {{ opacity:.35 }} 50% {{ opacity:1 }} }}
  .p1 .live {{ animation-delay:.6s }} .p2 .live {{ animation-delay:1.2s }} .p3 .live {{ animation-delay:1.8s }}
  .edge {{ stroke-dasharray: 90 700; animation: edgerun 7s linear infinite; }}
  @keyframes edgerun {{ to {{ stroke-dashoffset: -790; }} }}
  .p1 .edge {{ animation-delay:1.75s }} .p2 .edge {{ animation-delay:3.5s }} .p3 .edge {{ animation-delay:5.25s }}
"""
    o = [head(w, h, "KONKRED product suite",
              "Four product cards: Audit, Enterprise, Redeye, Arbitra.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')

    for i, (ic, tag, title, body, meta) in enumerate(cards):
        cx = (i % 2) * (cw + gap)
        cy = (i // 2) * (ch + gap)
        o.append(f'<g class="card c{i} p{i}" transform="translate({cx},{cy})">')
        o.append(f'<rect x="0" y="0" width="{cw}" height="{ch}" fill="{CARD}" stroke="{LINE}" stroke-width="1" rx="3"/>')
        # running edge highlight
        o.append(f'<rect class="edge" x=".5" y=".5" width="{cw-1}" height="{ch-1}" fill="none" '
                 f'stroke="{SIGNAL}" stroke-width="1.4" rx="3" opacity=".75"/>')
        # signal corner
        o.append(f'<path class="corner" d="M {cw-22} 1 L {cw-1} 1 L {cw-1} 22" fill="none" '
                 f'stroke="{SIGNAL}" stroke-width="2"/>')
        o.append(icon(ic, 24, 22, 1.15, CLINICAL))
        o.append(txt(66, 36, tag, 10, MID, MONO, "400", "2.4"))
        o.append(txt(66, 58, title, 24, CONC_LT, MONO, "600", "-0.2"))
        o.append(f'<line x1="24" y1="86" x2="{cw-24}" y2="86" stroke="{LINE}" stroke-width="1"/>')
        for j, ln in enumerate(body):
            o.append(txt(24, 114 + j * 24, ln, 14, MUTED, INTER, "400"))
        o.append(f'<rect x="24" y="{ch-44}" width="{cw-48}" height="1" fill="{LINE}"/>')
        o.append(f'<circle class="live" cx="29" cy="{ch-23}" r="3.4" fill="{SIGNAL}"/>')
        o.append(txt(42, ch - 19, meta, 10.5, MID, MONO, "400", "1.1"))
        o.append(txt(cw - 24, ch - 19, "LIVE", 10.5, SIGNAL, MONO, "500", "2.2", "end"))
        o.append('</g>')

    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 3. STACK
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
    pad, ph, pgap = 11, 26, 7
    lab_h, grp_gap = 34, 26

    # layout pass
    laid, heights = [], []
    for name, items in groups:
        rows, cur, curw = [], [], 0
        for it in items:
            iw = int(len(it) * 6.15) + pad * 2
            if curw + iw > colw and cur:
                rows.append(cur); cur, curw = [], 0
            cur.append((it, iw)); curw += iw + pgap
        if cur:
            rows.append(cur)
        laid.append((name, rows))
        heights.append(lab_h + len(rows) * (ph + pgap))

    r0 = max(heights[0], heights[1], heights[2])
    r1 = max(heights[3], heights[4], heights[5])
    h = r0 + grp_gap + r1

    css = """
  .pill { animation: pin .42s ease-out backwards; }
  @keyframes pin { from { opacity:0; transform: translateY(6px); }
                   to   { opacity:1; transform: translateY(0); } }
  .glab { animation: pin .45s ease-out backwards; }
  .tick { animation: tk 4.4s ease-in-out infinite; }
  @keyframes tk { 0%,100% { opacity:.25 } 50% { opacity:1 } }
"""
    o = [head(w, h, "Technical stack",
              "Six capability groups rendered as animated tokens.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')

    n = 0
    for gi, (name, rows) in enumerate(laid):
        cx = (gi % 3) * (colw + gap)
        cy = 0 if gi < 3 else r0 + grp_gap
        o.append(f'<g transform="translate({cx},{cy})">')
        o.append(f'<g class="glab" style="animation-delay:{gi*0.09:.2f}s">')
        o.append(f'<rect class="tick" x="0" y="4" width="3" height="13" fill="{SIGNAL}" '
                 f'style="animation-delay:{gi*0.5:.1f}s"/>')
        o.append(txt(13, 15, name, 11, CLINICAL, MONO, "600", "2.6"))
        o.append(f'<line x1="0" y1="26" x2="{colw}" y2="26" stroke="{LINE}" stroke-width="1"/>')
        o.append('</g>')
        for ri, row in enumerate(rows):
            px = 0
            for label, iw in row:
                d = 0.20 + n * 0.028
                o.append(f'<g class="pill" style="animation-delay:{d:.2f}s">')
                o.append(f'<rect x="{px}" y="{lab_h + ri*(ph+pgap)}" width="{iw}" height="{ph}" '
                         f'fill="{ROW}" stroke="{LINE2}" stroke-width="1" rx="2"/>')
                o.append(txt(px + pad, lab_h + ri * (ph + pgap) + 17, label, 11, MUTED, MONO, "400", "0.3"))
                o.append('</g>')
                px += iw + pgap
                n += 1
        o.append('</g>')

    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 4. METRICS
# ==========================================================================
def build_metrics():
    stats = [
        ("500+", "ENTERPRISE PROMPTS", "engineered, licensed, documented"),
        ("367", "RED-TEAM TECHNIQUES", "catalogued and typed"),
        ("70%", "COST REDUCTION", "$20k to $6k infrastructure"),
        ("20+", "MANUSCRIPTS", "AI, security, quantum"),
        ("04", "PRODUCTS SHIPPED", "audit · suite · redeye · arbitra"),
    ]
    gap = 16
    n = len(stats)
    w = 1200
    cw = (w - gap * (n - 1)) // n
    h = 156
    css = """
  .st { animation: stin .5s ease-out backwards; }
  @keyframes stin { from { opacity:0; transform: translateY(8px); }
                    to   { opacity:1; transform: translateY(0); } }
  .bar { transform-origin: left center; animation: grow 1.1s ease-out backwards; }
  @keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
  .sw { animation: sweep 5.5s linear infinite; }
  @keyframes sweep { 0% { opacity:0 } 8% { opacity:.9 } 40% { opacity:0 } 100% { opacity:0 } }
"""
    o = [head(w, h, "Signals", "Five headline metrics with animated reveal.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')

    for i, (val, lab, sub) in enumerate(stats):
        x = i * (cw + gap)
        d = 0.06 + i * 0.11
        o.append(f'<g class="st" style="animation-delay:{d:.2f}s" transform="translate({x},0)">')
        o.append(f'<rect x="0" y="0" width="{cw}" height="{h}" fill="{CARD}" stroke="{LINE}" stroke-width="1" rx="3"/>')
        o.append(f'<rect class="sw" x="0" y="0" width="{cw}" height="2" fill="{SIGNAL}" '
                 f'style="animation-delay:{i*0.55:.2f}s"/>')
        o.append(txt(20, 30, f"0{i+1}", 10, MID, MONO, "400", "2.0"))
        o.append(txt(20, 78, val, 40, CONC_LT, MONO, "600", "-0.5"))
        o.append(f'<rect class="bar" x="20" y="92" width="{cw-40}" height="2" fill="{SIGNAL}" '
                 f'style="animation-delay:{d+0.25:.2f}s" opacity=".8"/>')
        o.append(txt(20, 116, lab, 10.5, CLINICAL, MONO, "500", "1.6"))
        o.append(txt(20, 134, sub, 10, MID, MONO, "400", "0.4"))
        o.append('</g>')

    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 5. TIMELINE
# ==========================================================================
def build_timeline():
    rows = [
        ("KONKRED Audit", "Prompt certification engine. Seven mathematical and logical formulas for valuation, accuracy scoring and certification of AI intellectual property.", "LIVE"),
        ("KONKRED Enterprise", "Micro-tool marketplace. 500+ industrial-grade prompts across 10+ strategic domains, converted into autonomous agents via the Genesis Engine architecture.", "LIVE"),
        ("KONKRED Redeye", "LLM red-team platform in TypeScript and React. 367 adversarial techniques catalogued; defensive layers against prompt injection and data leakage.", "LIVE"),
        ("KONKRED Arbitra", "Documentation engine. API references, runbooks and architecture notes generated from code and prompts, then verified and versioned.", "LIVE"),
        ("AI economics restructure", "Reverse-engineered COGS for large-scale Gemini deployments. Context management and caching strategy cut spend from $20,000 to $6,000.", "SHIPPED"),
        ("Brand system v2", "Full identity, motion spec and static production site. No framework, sub-12KB JS, first paint under 1.2s.", "SHIPPED"),
    ]
    w = 1200
    rh, gp = 88, 12
    h = len(rows) * (rh + gp) - gp + 1
    css = """
  .row { animation: rin .5s ease-out backwards; }
  @keyframes rin { from { opacity:0; transform: translateX(-8px); }
                   to   { opacity:1; transform: translateX(0); } }
  .node { animation: np 3.6s ease-in-out infinite; }
  @keyframes np { 0%,100% { opacity:.3 } 50% { opacity:1 } }
  .rail { stroke-dasharray: 60 480; animation: rr 8s linear infinite; }
  @keyframes rr { to { stroke-dashoffset: -540; } }
"""
    o = [head(w, h, "Build log", "Timeline of shipped systems.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')
    o.append(f'<line x1="26" y1="0" x2="26" y2="{h}" stroke="{LINE}" stroke-width="1"/>')
    o.append(f'<line class="rail" x1="26" y1="0" x2="26" y2="{h}" stroke="{SIGNAL}" stroke-width="1.6"/>')

    for i, (title, body, state) in enumerate(rows):
        y = i * (rh + gp)
        d = 0.05 + i * 0.1
        o.append(f'<g class="row" style="animation-delay:{d:.2f}s" transform="translate(0,{y})">')
        o.append(f'<rect x="20" y="{rh/2-6}" width="12" height="12" fill="{VOID}" stroke="{LINE2}" stroke-width="1"/>')
        o.append(f'<rect class="node" x="23" y="{rh/2-3}" width="6" height="6" fill="{SIGNAL}" '
                 f'style="animation-delay:{i*0.45:.2f}s"/>')
        o.append(f'<rect x="56.5" y="0.5" width="{w-57}" height="{rh-1}" fill="{ROW}" stroke="{LINE}" stroke-width="1" rx="3"/>')
        o.append(txt(78, 34, title, 16.5, CONC_LT, MONO, "500", "-0.1"))
        o.append(txt(78, 62, body, 13.5, MUTED, INTER, "400"))
        col = SIGNAL if state == "LIVE" else MID
        o.append(txt(w - 26, 34, state, 10, col, MONO, "500", "2.2", "end"))
        o.append('</g>')

    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 6. DIVIDER
# ==========================================================================
def build_divider():
    w, h = 1200, 26
    css = """
  .seg { stroke-dasharray: 120 1080; animation: run 6s linear infinite; }
  @keyframes run { to { stroke-dashoffset: -1200; } }
  .dot { animation: dp 2.4s ease-in-out infinite; }
  @keyframes dp { 0%,100% { opacity:.3 } 50% { opacity:1 } }
"""
    o = [head(w, h, "Divider", "Animated signal divider.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')
    o.append(f'<line x1="0" y1="13" x2="{w}" y2="13" stroke="{LINE}" stroke-width="1"/>')
    o.append(f'<line class="seg" x1="0" y1="13" x2="{w}" y2="13" stroke="{SIGNAL}" stroke-width="1.6"/>')
    for i in range(13):
        x = 24 + i * 96
        o.append(f'<rect x="{x}" y="10" width="2" height="6" fill="{MID}" opacity=".5"/>')
    o.append(f'<circle class="dot" cx="{w/2}" cy="13" r="3" fill="{SIGNAL}"/>')
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 7. FOOTER
# ==========================================================================
def build_footer():
    w, h = 1200, 170
    css = CUBE_CSS + """
  .fin { animation: fi .55s ease-out backwards; }
  @keyframes fi { from { opacity:0; transform: translateY(7px); }
                  to   { opacity:1; transform: translateY(0); } }
  .f0 { animation-delay:.06s } .f1 { animation-delay:.18s }
  .f2 { animation-delay:.30s } .f3 { animation-delay:.42s }
  .cube { animation: fi .6s ease-out .04s backwards; }
  .cyc { animation: cyc 16s linear infinite; }
  @keyframes cyc {
     0%   { opacity:0; transform: translateY(5px); }
     3%   { opacity:1; transform: translateY(0); }
    22%   { opacity:1; transform: translateY(0); }
    25%   { opacity:0; transform: translateY(-5px); }
   100%   { opacity:0; transform: translateY(-5px); } }
  .y0 { animation-delay:.6s } .y1 { animation-delay:4.6s }
  .y2 { animation-delay:8.6s } .y3 { animation-delay:12.6s }
"""
    lines = [
        "Ship or don't ship.",
        "No pitch decks. No vapor.",
        "It works. That's not the same as being good.",
        "If in doubt: colder, sharper, quieter.",
    ]
    o = [head(w, h, "Contact", "Footer with contact channels and brand voice.", css)]
    o.append(f'<rect width="{w}" height="{h}" fill="{VOID}"/>')
    o.append(grid("f", w, h, 40, 0.02))
    o.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="{LINE}" stroke-width="1"/>')
    o.append(crops(w, h, 12, 10, ".45"))
    o.append(cube("f", scale=0.42, tx=36, ty=38))

    x = 152
    o.append(f'<g class="fin f0">{txt(x, 52, "AVAILABLE FOR REMOTE WORK", 11, MID, MONO, "400", "3.2")}</g>')
    o.append(f'<g class="fin f1">{txt(x, 88, "Contract  ·  fractional  ·  advisory", 21, CONC_LT, MONO, "500", "0.2")}</g>')
    for i, ln in enumerate(lines):
        o.append(f'<g class="cyc y{i}" opacity="{1 if i == 0 else 0}">'
                 f'{txt(x, 120, ln, 13.5, MUTED, INTER, "400")}</g>')

    # channels
    o.append(f'<g class="fin f2">')
    o.append(txt(w - 40, 52, "ari@konkred.xyz", 13, CLINICAL, MONO, "500", "0.4", "end"))
    o.append(txt(w - 40, 76, "konkred.xyz", 13, SIGNAL, MONO, "400", "0.4", "end"))
    o.append(f'<line x1="{w-40}" y1="92" x2="{w-230}" y2="92" stroke="{LINE2}" stroke-width="1"/>')
    o.append(txt(w - 40, 114, "TIMEZONE FLEXIBLE  ·  ASYNC-FIRST", 10, MID, MONO, "400", "1.8", "end"))
    o.append('</g>')

    o.append(f'<g class="fin f3">')
    o.append(f'<line x1="36" y1="{h-30}" x2="{w-36}" y2="{h-30}" stroke="{LINE}" stroke-width="1"/>')
    o.append(txt(36, h - 12, "KONKRED — BRAND SYSTEM v2", 9.5, MID, MONO, "400", "2.0"))
    o.append(txt(w - 36, h - 12, "VOID #0B0F14  ·  CLINICAL #D7D9DD  ·  SIGNAL #D98A2E", 9.5, MID, MONO, "400", "1.4", "end"))
    o.append('</g>')

    o.append('</svg>')
    return "".join(o)


# ==========================================================================
# 8. STANDALONE MARK
# ==========================================================================
def build_mark():
    css = CUBE_CSS + """
  .cube { animation: mi .7s ease-out .05s backwards; }
  @keyframes mi { from { opacity:0; transform: translateY(8px) } to { opacity:1; transform: translateY(0) } }
"""
    o = [head(220, 260, "Cube-K mark", "Animated KONKRED Cube-K v3 mark.", css)]
    o.append(f'<rect width="220" height="260" fill="{VOID}"/>')
    o.append(cube("m", scale=1.0, tx=10, ty=6))
    o.append(txt(110, 250, "K O N K R E D", 12, CLINICAL, MONO, "500", "5.2", "middle"))
    o.append('</svg>')
    return "".join(o)


# ==========================================================================
def main():
    os.makedirs(OUT, exist_ok=True)
    files = {
        "header.svg":   build_header(),
        "products.svg": build_products(),
        "stack.svg":    build_stack(),
        "metrics.svg":  build_metrics(),
        "timeline.svg": build_timeline(),
        "divider.svg":  build_divider(),
        "footer.svg":   build_footer(),
        "cube-k.svg":   build_mark(),
    }
    for name, body in files.items():
        p = os.path.join(OUT, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"  {name:<15} {len(body):>7,} bytes")
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
