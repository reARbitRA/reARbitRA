/*
 * Rasterise the generated SVGs so they can be eyeballed before shipping.
 *
 * resvg does not implement CSS @font-face, so the embedded base64 faces are
 * invisible to it. To make the preview representative we point it at the same
 * fonts converted to TTF in ~/.local/share/fonts. That means this preview
 * shows real IBM Plex Mono / Inter metrics — which is exactly what caught the
 * pill-overflow and caret-collision bugs.
 *
 * Note: resvg renders the *static* first frame of a CSS animation. That is the
 * point — it verifies the base state is legible for anyone whose renderer does
 * not animate (and for prefers-reduced-motion).
 *
 *   node tools/render/preview.js <in.svg> <out.png> [width]
 */
const { Resvg } = require("@resvg/resvg-js");
const fs = require("fs");
const os = require("os");
const path = require("path");

const [, , input, output, widthArg] = process.argv;
if (!input || !output) {
  console.error("usage: node preview.js <in.svg> <out.png> [width]");
  process.exit(1);
}

const svg = fs.readFileSync(input, "utf8");
const resvg = new Resvg(svg, {
  background: "#0a0908",
  fitTo: { mode: "width", value: parseInt(widthArg || "1200", 10) },
  font: {
    loadSystemFonts: false,
    fontDirs: [path.join(os.homedir(), ".local/share/fonts")],
    defaultFontFamily: "JetBrains Mono",
  },
});
fs.writeFileSync(output, resvg.render().asPng());
console.log("rendered", path.basename(input), "->", output);
