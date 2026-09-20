/*
 * Headless smoke test for docs/index.html.
 *
 * The page injects all of its content with a small inline script, so a single
 * JS error means a blank page for the visitor. A browser download is blocked
 * in this sandbox, so jsdom stands in: it runs the real script against a real
 * DOM and reports what actually got rendered.
 *
 *   node tools/render/checksite.js
 */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const file = path.join(__dirname, "../../docs/index.html");
const html = fs.readFileSync(file, "utf8");
const errors = [];

const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push("JSDOM: " + e.message));
vc.on("error", (m) => errors.push("ERROR: " + m));

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  virtualConsole: vc,
});

setTimeout(() => {
  const d = dom.window.document;
  const expect = {
    metrics: 5,
    products: 4,
    "services-list": 4,
    "domains-grid": 5,
    groups: 6,
    entries: 5,
    books: 7,
  };

  let bad = 0;
  for (const [id, want] of Object.entries(expect)) {
    const node = d.getElementById(id);
    const got = node ? node.children.length : -1;
    const ok = got === want;
    if (!ok) bad++;
    console.log(`  ${ok ? "OK  " : "FAIL"} #${id.padEnd(14)} ${got}/${want}`);
  }

  // every in-page nav target must exist
  d.querySelectorAll('a[href^="#"]').forEach((a) => {
    const href = a.getAttribute("href");
    if (href.length > 1 && !d.querySelector(href)) {
      errors.push("dead anchor " + href);
      bad++;
    }
  });

  // every local asset referenced must be on disk
  d.querySelectorAll("img[src], link[href]").forEach((n) => {
    const src = n.getAttribute("src") || n.getAttribute("href");
    if (!src || /^(https?:|mailto:|data:|#)/.test(src)) return;
    const p = path.join(path.dirname(file), src.split("#")[0]);
    if (!fs.existsSync(p)) {
      errors.push("missing file " + src);
      bad++;
    }
  });

  // expandable detail panels: 4 products + 4 services + 5 log entries
  const hosts = d.querySelectorAll("[data-exp]");
  const okExp = hosts.length === 13;
  if (!okExp) bad++;
  console.log(`  ${okExp ? "OK  " : "FAIL"} [data-exp]      ${hosts.length}/13`);

  let panelBad = 0;
  hosts.forEach((h) => {
    const id = h.getAttribute("data-exp");
    const panel = h.querySelector(".detail");
    if (!panel || panel.id !== "d-" + id) panelBad++;
    if (h.getAttribute("aria-expanded") !== "false") panelBad++;
    if (!panel || !panel.querySelector(".kv")) panelBad++;
  });
  if (panelBad) { bad++; errors.push(panelBad + " detail panel wiring problems"); }
  console.log(`  ${panelBad ? "FAIL" : "OK  "} panel wiring   ${hosts.length - panelBad}/${hosts.length}`);

  // toggling
  const first = hosts[0];
  if (first) {
    first.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    const openOK = first.getAttribute("aria-expanded") === "true" &&
                   first.querySelector(".detail").classList.contains("open");
    const other = hosts[1];
    const independent = other.getAttribute("aria-expanded") === "false";
    first.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    const closeOK = first.getAttribute("aria-expanded") === "false" &&
                    !first.querySelector(".detail").classList.contains("open");
    const kev = new dom.window.KeyboardEvent("keydown", { key: "Enter", bubbles: true });
    first.dispatchEvent(kev);
    const keyOK = first.getAttribute("aria-expanded") === "true";
    first.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    const t = openOK && closeOK && keyOK && independent;
    if (!t) bad++;
    console.log(`  ${t ? "OK  " : "FAIL"} toggle         open=${openOK} close=${closeOK} key=${keyOK} indep=${independent}`);
  }

  const role = d.getElementById("role");
  console.log(`  role typed     ${JSON.stringify(role ? role.textContent : null)}`);
  console.log(`  reveal targets ${d.querySelectorAll(".rv").length}`);

  // ---- FACTORY FLOOR theme invariants ---------------------------------
  const css = [...d.querySelectorAll("style")].map((n) => n.textContent).join("\n");

  // 2.4 there is no blue, green, purple or amber anywhere in the theme
  const palette = new Set([
    "#0a0908", "#171514", "#0c0b0a", "#0d0c0b", "#100e0d",
    "#d60019", "#ff1a2e", "#120d0c", "#161210", "#1a1010", "#3a201f", "#5c0a10",
    "#f4f1eb", "#eae7e1", "#b7b2a9", "#8a857d", "#7a756d", "#5c5852", "#3d3835",
    "#2a2624", "#262221", "#33302e", "#4a4640",
    "#23201e", "#1a1817", "#141211", "#141210", "#000", "#fff",
  ]);
  const markup = d.documentElement.outerHTML.replace(/&#\d+;/g, "");
  const offTheme = [...new Set((markup.match(/#[0-9a-fA-F]{3,6}\b/g) || [])
    .map((h) => h.toLowerCase()))].filter((h) => !palette.has(h));
  if (offTheme.length) { bad++; errors.push("off-theme colours: " + offTheme.join(" ")); }
  console.log(`  ${offTheme.length ? "FAIL" : "OK  "} palette        ${offTheme.length} off-theme`);

  // the three brand faces must all be declared and self-hosted
  const faces = ["JetBrains Mono", "Special Elite", "Archivo Black"]
    .filter((f) => css.includes(`font-family:'${f}'`));
  const facesOK = faces.length === 3 && !/fonts\.googleapis|fonts\.gstatic/.test(css);
  if (!facesOK) { bad++; errors.push("brand faces missing or loaded from a CDN"); }
  console.log(`  ${facesOK ? "OK  " : "FAIL"} typefaces      ${faces.length}/3 self-hosted`);

  // 9. panel radius is 0 everywhere; only .rivet dots are round
  const radii = (css.match(/border-radius:\s*([^;}]+)/g) || [])
    .filter((r) => !/50%|0\b/.test(r.split(":")[1]));
  if (radii.length) { bad++; errors.push("rounded corners: " + radii.join(", ")); }
  console.log(`  ${radii.length ? "FAIL" : "OK  "} radius         ${radii.length} rounded`);

  // 8. the custom cursor must be removable — a touch visitor keeps theirs
  const cursorOK = /hover:\s*none|hover:hover/.test(css) &&
                   css.includes("prefers-reduced-motion") &&
                   /removeChild\(reticle\)|reticle\.parentNode/.test(markup);
  if (!cursorOK) { bad++; errors.push("custom cursor has no touch / reduced-motion fallback"); }
  console.log(`  ${cursorOK ? "OK  " : "FAIL"} cursor guard   touch+reduced-motion fallback`);

  // 5. every bench ignites from one .group, and the IN -> OUT row is mandatory
  const benches = d.querySelectorAll(".bench");
  let benchBad = 0;
  benches.forEach((b) => {
    if (!b.classList.contains("group")) benchBad++;
    if (!b.querySelector(".io .keycap")) benchBad++;     // in -> out is required
    if (!b.querySelector(".rail")) benchBad++;
    if (!b.querySelector(".run")) benchBad++;
  });
  if (benchBad) { bad++; errors.push(benchBad + " bench anatomy problems"); }
  console.log(`  ${benchBad ? "FAIL" : "OK  "} bench anatomy  ${benches.length} benches, in/out + rail + RUN`);

  if (errors.length) {
    console.log("\n" + errors.join("\n"));
  }
  console.log(bad || errors.length ? "\nFAILED" : "\nsite OK");
  process.exit(bad || errors.length ? 1 : 0);
}, 1500);
