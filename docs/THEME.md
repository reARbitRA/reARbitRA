# KONKRED — Factory Floor

> A brutalist industrial dark theme: chalk-grained black canvas, deep-red
> glowing hardware, typewriter-white interactive text. Everything looks
> manufactured — stamped, riveted, taped, scanned.

This file is the source of truth for the look. Two surfaces implement it:

| Surface | File | Notes |
|---|---|---|
| Profile README artwork | `tools/build_assets.py` → `assets/*.svg` | No JS, no external fonts — GitHub blocks both |
| Pages site | `docs/index.html` | Full hover/cursor interaction |

Regenerate and check with:

```sh
python3 tools/build_assets.py     # writes assets/ and mirrors into docs/assets/
python3 tools/verify_assets.py    # XML, glyph coverage, overflow, palette
node    tools/render/checksite.js # DOM, wiring, theme invariants
```

---

## 1. Brand position

| | |
|---|---|
| **Tone of voice** | Industrial, terse, honest. Lowercase technical labels, ALL-CAPS display. |
| **Core metaphor** | A factory floor of benches. Each workflow is a *bench* with an intake, a rail, and a stamped output. |
| **Red meaning** | Signal / power / live state — **not** "danger" or "error". Red = the machine is awake. |
| **One rule** | The background never glows. Only foreground objects ignite. |

---

## 2. Colour tokens

### Base canvas
| Token | Hex | Use |
|---|---|---|
| `--konk-black` | `#0a0908` | Page background. Near-black with a warm brown cast (never pure `#000`). |
| `--konk-ash` | `#171514` | Raised surface / panel top |
| `--panel-bottom` | `#0c0b0a` | Panel gradient bottom |
| `--sunken` / `--sunken-2` | `#0d0c0b` · `#100e0d` | Inputs, wells, nested cards |

Pure `#000` reads as LCD void. `#0a0908` reads as chalkboard / dried concrete,
which is what the grain layer needs to bite into.

### The red family (the only accent)
| Token | Hex | Use |
|---|---|---|
| `--konk-red` | `#d60019` | Deep red — fills, borders, tape, meters |
| `--konk-red-glow` | `#ff1a2e` | Hot red — hover state + glowing text only |
| `--red-tint` … `-3` | `#120d0c` · `#161210` · `#1a1010` | Red-stained surface (subtle wash, never saturated) |
| `--red-border-dim` | `#3a201f` | Border for red-tinged elements at rest |
| `--crit-border` | `#5c0a10` | Critical severity border |

### Neutrals (a 9-step ash ladder)
| Token | Hex | Role |
|---|---|---|
| `--ink` | `#f4f1eb` | Interactive white (typewriter text) |
| `--body` | `#eae7e1` | Default body text |
| `--rest` | `#b7b2a9` | **`.konk-item` default** — everything hoverable starts here |
| `--dim` | `#8a857d` | Secondary mono text |
| `--meta` | `#7a756d` | Captions, helper copy |
| `--faint` | `#5c5852` | Ticker text, inactive labels |
| `--ghost` | `#3d3835` | Disabled / `[..]` pipeline markers |
| `--line-1` / `--line-2` | `#2a2624` · `#262221` | Hairline / nested border |
| `--edge` | `#33302e` | Keycap bevel edge |

There is **no blue, green, purple or amber** anywhere. Success is expressed as
white/ash plus a red stamp, so red never loses its signal value. Both verifiers
fail the build on an off-palette hex.

---

## 3. Typography

| Family | Weights | Job |
|---|---|---|
| **Special Elite** | 400 | The American-typewriter voice. All human-readable sentences. |
| **Archivo Black** | 400 | Display slab. ALL-CAPS headlines, workflow names, big numerals, stamps. |
| **JetBrains Mono** | 400 / 500 / 700 / 800 | Machine voice. Labels, IDs, statuses, metrics. |

All three are self-hosted in `docs/fonts/` and `tools/fonts/` — never loaded
from Google Fonts. The spec calls for no third-party requests, and GitHub's
image proxy would drop a webfont link anyway.

**Law:** mono labels are always uppercase with wide tracking (`0.25em–0.4em`).
Typewriter prose is always sentence-case with normal tracking. Never mix them
on one line.

Specialty type: `.hollow` (outline words), `.hollow-red`, `.ghost-num` (huge
outlined numerals *behind* content), `.red-glow`, `.cursor-blink`.

---

## 4. Texture system (the signature)

Four independent layers:

1. **Global chalk grain** — `feTurbulence` `baseFrequency .85` / 4 octaves,
   `opacity .14`, `mix-blend-mode: overlay`, flickering on `steps(3)` so it
   reads as film grain rather than drifting.
2. **Per-panel soft chalk** — `.6` / 3 octaves, `screen`, so each panel carries
   its own smudge.
3. **Canvas smudge** — a cold white breath top-left, faint red heat
   bottom-right. Barely visible; it is what stops the black feeling flat.
4. **Scanlines** — 1px on / 2px off, hero and full-bleed bands only, never body
   copy.

Plus **blueprint grid** (24px, red at 10%) for fig plates, and **hazard tape**
(45°, 9px stripes) capping headers and frames.

In the README SVGs these are native `feTurbulence` filters rather than CSS —
the blend is baked into a `feColorMatrix`, because several static rasterisers
drop `mix-blend-mode`.

---

## 5. The glow interaction system

The single most important mechanic. Every interactive element is ash-grey at
rest and ignites to glowing red on hover, in **180ms**:

```css
.konk-item{ color:#b7b2a9; transition:color .18s ease, filter .18s ease; }
.konk-item:hover, .group:hover .konk-item{
  color:#ff1a2e;
  filter:drop-shadow(0 0 6px rgba(255,26,46,.7))
         drop-shadow(0 0 18px rgba(214,0,25,.4));
  text-shadow:0 0 8px rgba(255,26,46,.6);
}
```

Two-layer `drop-shadow` = a tight core plus a wide halo. Because the selector
includes `.group:hover`, a whole card ignites from a single `group` class.

Companion effects: `.beam` (diagonal light-bar sweep, `.65s`), `.flood` (red
gradient rises from the bottom), `.box-brutal` (border ignites, gains an offset
shadow, lifts 2px), `.lock` (corner brackets acquire the target),
`.glitch-hover`.

**A README image has no pointer.** So in the SVGs the same gesture is driven by
a timer: an ignition sweep walks each element up to hot red and lets it cool.
The base state stays ash, so a renderer with no CSS still shows the resting
design.

---

## 6. Hardware

- **`.spec-shell`** — octagonal `clip-path` with rivets punched at each corner
- **`.rivet`** — 6px machined metal dot, the only round thing in the system
- **`.staple`** — 14×4px bar for paper sheets and dossiers
- **`.keycap`** — 1.5px border with a 3.5px bottom border (a physical bevel)
- **`.stamp`** — `4px double` border, rotated ±3–6° so it never looks
  machine-perfect. `CLEARED` · `BLOCKED` · `PASS` · `FORGED` · `GRADE C`
- **Panel** — red diamond + mono label, three dots (one red) on the right

---

## 7. Motion

All timings are deliberately fast and mechanical — nothing eases in slowly.

| Animation | Timing | Purpose |
|---|---|---|
| `modin` | `.6s` `cubic-bezier(.16,.84,.24,1)` | Module entry, 36px rise |
| `probe-fade` | `.35s` | Log lines slide in from `-10px` |
| `drop-fade` | `.5s` `cubic-bezier(.2,.9,.2,1)` | Stamps drop in, rotated `-2deg` |
| `marquee` | `28s` / `34s` reverse | Tickers |
| `spin` | `9s` | Cursor reticle |
| `blink` | `1s` `steps(1)` | Terminal caret |
| `grainflick` | `.9s` `steps(3)` | Global grain |
| hover | `.18s` | Every ignition |

**Pipeline state grammar**, used in every console:

```
[..]  → ghost #3d3835   (queued)
[>>]  → pulsing         (running)
[ok]  → red glow        (complete)
```

---

## 8. Cursor

The native cursor is hidden and replaced by two `pointer-events:none`,
`mix-blend-mode:screen` layers: a **reticle** (46px, dashed circle + crosshair,
rotating on a 9s loop, following with `lerp 0.16` for physical lag) and an
**ambient glow** (300px red radial, tracking exactly).

Both are **removed from the DOM entirely** on `(hover:none)` and under
`prefers-reduced-motion`, so a touch visitor keeps their native cursor and can
never have a tap trapped.

---

## 9. Layout

Max content width `1400px` · page gutter `20px` · card gap `16–20px` · card
padding `20–28px` · section rhythm `py-20`→`py-24`.

**Panel radius is 0 everywhere** — no rounded corners except `.rivet` dots.
Border width `1.5px` standard, `2px` on CTAs, `4px double` on stamps. Both
verifiers fail the build on a stray `border-radius`.

---

## 10. Card anatomy (the friendliness layer)

```
W-01  ································ ● live     ← id + status
STACK SCAFFOLD                                    ← Archivo Black, 22px
turn one sentence into a runnable skeleton        ← Special Elite, 13.5px
in: [one-line idea] → [app skeleton]              ← mono keycaps, 10px
≈ 9s  [easy]                        [ RUN ▸ ]     ← meta + one primary action
```

- The **IN → OUT** row is mandatory — it is how a reader knows whether the
  bench is theirs without reading anything else.
- Difficulty is `easy / medium / hot`, never "advanced".
- The RUN button is always bottom-right, always the same shape.
- The ghost numeral sits *behind* the card.

---

## 11. Accessibility & guardrails

- Body text `#eae7e1` on `#0a0908` is ~15.8:1. `--meta` (`#7a756d`) is ~4.9:1
  and is reserved for non-essential captions.
- `.hollow` outline text is decorative only — never the sole carrier of meaning.
- `::selection` is red fill / black text; the scrollbar is styled to stay in-world.
- Reduced motion kills grain, marquee, spin and pulses but **keeps colour
  transitions**, so the interface still answers hover.
- All interactive elements are real `<button>` / `<a>` and keyboard reachable.

### Do / Don't
| ✅ Do | ❌ Don't |
|---|---|
| Ash at rest, red on hover | Elements that are red at rest (red loses signal) |
| `1.5px` borders, 0 radius | Rounded corners, shadows without offset |
| Mono labels uppercase + wide tracking | Uppercase typewriter prose |
| One primary RUN per bench | Competing primary buttons |
| Warm black + warm whites | Pure `#000` / pure `#fff` |
| Stamp the output | Toast notifications |
| Ghost numerals behind content | Ghost numerals in front of content |
