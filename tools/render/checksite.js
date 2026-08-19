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

  if (errors.length) {
    console.log("\n" + errors.join("\n"));
  }
  console.log(bad || errors.length ? "\nFAILED" : "\nsite OK");
  process.exit(bad || errors.length ? 1 : 0);
}, 1500);
