// Industrial Review Board deck (MMA4002 Assignment 5).
// Build:  cd assignment-5-industrial-review-board-presentation/deck && npm install && node build_deck.js
// Output: ../MMA4002_IRB_Outdoor_Bench.pptx   (media in ./media, theme applied by ./apply_theme.js)
//
// Sources for every number on the slides: 3d-modeling-and-simulation/qa_notes.md,
// robot-cell/Next steps.md, robot-cell/cycle_times.csv, robot-cell/TM bridge plan.md,
// robot-cell/AMR delivery plan.md, tests/robot_sim/OWN_TOOL.md, index.html (BOM, profile),
// and the Assignment 1 / 3 reports.

const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("./apply_theme.js");

const MEDIA = (f) => path.join(__dirname, "media", f);
const OUT = path.join(__dirname, "..", "MMA4002_IRB_Outdoor_Bench.pptx");

// ---------------------------------------------------------------- theme
const THEME = {
  name: "Bent Bar",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1E21",  // steel, near black
    lt1: "FFFFFF",
    dk2: "39424A",  // graphite
    lt2: "F0F2F3",  // card grey
    accent1: "B5622B", // timber
    accent2: "2E7D6B", // simulation green
    accent3: "E2A93B", // guide amber
    accent4: "3B6EA8", // jig blue
    accent5: "8A939B", // bar grey
    accent6: "C8453B", // collision red
    hlink: "2E7D6B",
    folHlink: "8A939B",
  },
};
const H = THEME.colors; // hex, only where pptxgenjs needs hex

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "One bent bar, assembled by a cobot";
pres.subject = "MMA4002 Industrial Review Board: outdoor bench manufacturing demonstrator";
pres.author = "Bjørge Skjelbreid Djuve, John Isak Hammer";
pres.company = "NTNU Ålesund";
const C = pres.SchemeColor;

const W = 13.333, M = 0.6;
const FOOT = "MMA4002 Design for Automated Manufacturing · Industrial Review Board · 9 Nov 2026";

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: H.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.0, w: 7.2, h: 2.0, fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.2, w: 6.8, h: 1.2, fontSize: 18, color: C.accent5, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION_DARK",
  background: { color: H.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.1, w: 5.6, h: 2.2, fontSize: 36, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.5, w: 5.4, h: 1.6, fontSize: 18, color: C.accent5, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: H.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 0.85, fontSize: 36, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: FOOT, options: { x: M, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: H.accent5, align: "right", margin: 0 },
});
pres.defineSlideMaster({
  title: "VIDEO_DARK",
  background: { color: H.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.3, w: W - 2 * M, h: 0.7, fontSize: 28, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
});

// ---------------------------------------------------------------- helpers
async function icon(Comp, hex, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
// icon in a filled circle
function iconDot(slide, data, x, y, d, fill, name) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: name + " dot" });
  const p = d * 0.25;
  slide.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + " icon" });
}
// numbered marker
function num(slide, n, x, y, fill = C.accent1, d = 0.42) {
  slide.addText(String(n), {
    shape: pres.shapes.OVAL, x, y, w: d, h: d, fill: { color: fill }, line: { color: C.background1, width: 1.5 },
    color: C.background1, bold: true, fontSize: 14, align: "center", valign: "middle", margin: 0, isTextBox: true,
    objectName: "marker " + n,
  });
}
function card(slide, x, y, w, h, fill = C.background2, name = "card") {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" }, objectName: name });
}
function text(slide, t, o) {
  slide.addText(t, Object.assign({ isTextBox: true, margin: 0, valign: "top", fontSize: 14, color: C.text1 }, o));
}
function img(slide, file, x, y, w, h, name, cover = true) {
  const o = { path: MEDIA(file), x, y, w, h, objectName: name };
  if (cover) o.sizing = { type: "cover", w, h };
  slide.addImage(o);
}
function caption(slide, t, x, y, w, color = C.accent5) {
  text(slide, t, { x, y, w, h: 0.3, fontSize: 11, color, italic: false });
}

// the bench's side frame, traced from the CAD (index.html PROFILE / SEAT_SLOTS / BACK_SLOTS)
const PROFILE_HIGH = [[46.53,-6.63],[41.61,-2.5],[-41.61,-2.5],[-56.38,9.9],[-68.3,77.5],[-58.14,77.5],
  [-46.53,11.63],[-41.61,7.5],[41.61,7.5],[46.53,11.63],[58.15,77.5],[68.3,77.5],
  [55.54,5.1],[55.54,-0.1],[71.85,-92.65],[69.83,-95.55],[64.9,-96.41],[62.01,-94.39]];
const SEAT_SLOTS = [
  [[-17.3,5.2],[-42.7,5.2],[-42.7,-0.2],[-17.3,-0.2]],
  [[12.7,5.2],[-12.7,5.2],[-12.7,-0.2],[12.7,-0.2]],
  [[42.7,5.2],[17.3,5.2],[17.3,-0.2],[42.7,-0.2]]];
const BACK_SLOTS = [
  [[53.93,-4.22],[48.61,-5.16],[53.02,-30.17],[58.34,-29.23]],
  [[53.82,-34.7],[58.23,-59.72],[63.55,-58.78],[59.14,-33.76]],
  [[59.03,-64.25],[63.44,-89.26],[68.76,-88.32],[64.35,-63.31]]];
const FR = { minx: -68.3, miny: -96.41, maxx: 71.85, maxy: 77.5 };

function poly(slide, pts, ox, oy, s, fill, name) {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const mx = Math.min(...xs), my = Math.min(...ys);
  const w = (Math.max(...xs) - mx) * s, h = (Math.max(...ys) - my) * s;
  const points = pts.map((p) => ({ x: (p[0] - mx) * s, y: (p[1] - my) * s }));
  points.push({ close: true });
  slide.addShape(pres.shapes.CUSTOM_GEOMETRY, {
    x: ox + (mx - FR.minx) * s, y: oy + (my - FR.miny) * s, w: Math.max(w, 0.01), h: Math.max(h, 0.01),
    points, fill: { color: fill }, line: { type: "none" }, objectName: name,
  });
}
// draws the frame with its planks; returns a mapper from CAD mm to slide inches
function frame(slide, ox, oy, height, barFill, plankFill) {
  const s = height / (FR.maxy - FR.miny);
  poly(slide, PROFILE_HIGH, ox, oy, s, barFill, "frame profile");
  SEAT_SLOTS.forEach((p, i) => poly(slide, p, ox, oy, s, plankFill, "seat plank " + (i + 1)));
  BACK_SLOTS.forEach((p, i) => poly(slide, p, ox, oy, s, plankFill, "back plank " + (i + 1)));
  return { s, at: (x, y) => [ox + (x - FR.minx) * s, oy + (y - FR.miny) * s], w: (FR.maxx - FR.minx) * s };
}

// ---------------------------------------------------------------- slides
(async () => {
  const I = {
    users: await icon(fa.FaUsers, "FFFFFF"),
    sliders: await icon(fa.FaSlidersH, "FFFFFF"),
    globe: await icon(fa.FaGlobeEurope, "FFFFFF"),
    cut: await icon(fa.FaCut, "FFFFFF"),
    boxes: await icon(fa.FaBoxes, "FFFFFF"),
    robot: await icon(fa.FaRobot, "FFFFFF"),
    stamp: await icon(fa.FaStamp, "FFFFFF"),
    truck: await icon(fa.FaTruck, "FFFFFF"),
    check: await icon(fa.FaCheck, "FFFFFF"),
    flask: await icon(fa.FaFlask, "FFFFFF"),
    cogs: await icon(fa.FaCogs, "FFFFFF"),
    question: await icon(fa.FaQuestion, "FFFFFF"),
    lightbulb: await icon(fa.FaLightbulb, "FFFFFF"),
  };

  // ============ 1. Title
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  text(s, "MMA4002 DESIGN FOR AUTOMATED MANUFACTURING · INDUSTRIAL REVIEW BOARD", { x: M, y: 1.3, w: 7.4, h: 0.35, fontSize: 12, bold: true, color: C.accent3, charSpacing: 1 });
  s.addText("One bent bar, assembled by a cobot", { placeholder: "title" });
  s.addText("An outdoor bench whose product architecture, jig and robot cell were designed together and tested in our own simulation before the lab", { placeholder: "body" });
  text(s, "Bjørge Skjelbreid Djuve · John Isak Hammer", { x: M, y: 5.75, w: 7, h: 0.35, fontSize: 16, bold: true, color: C.background1 });
  text(s, "NTNU Ålesund · L167 · 9 November 2026", { x: M, y: 6.15, w: 7, h: 0.35, fontSize: 14, color: C.accent5 });
  frame(s, 8.35, 0.95, 5.6, H.accent5, H.accent1);
  s.addNotes(
    "Suggested speaker: both (introduce yourselves), then John Isak.\n\n" +
    "We designed an outdoor bench for public spaces and the line that builds it. The drawing on the right is the real side frame, traced from our CAD: one laser-cut flat bar, bent in a press brake, with the timber planks sitting in pockets cut into the bar.\n\n" +
    "The talk has two halves: the product and its architecture, then the manufacturing cell, where our wow factor is the simulation: we built and broke every version of the robot cell in software before touching the lab robot."
  );

  // ============ 2. Customer view
  pres.addSection({ title: "Product" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("A public bench, configured per customer", { placeholder: "title" });
  const rows2 = [
    [I.users, "Who buys it", "Municipalities, cities and larger companies. They buy the message the furniture sends, not the lowest unit price."],
    [I.sliders, "What they choose", "Backrest or not, and the mark on the top plank: a laser-cut crest or a logo shield. Everything else is standard."],
    [I.globe, "How they order", "A web configurator with live 3D, bill of material and a quote request, opened from a QR code."],
  ];
  rows2.forEach((r, i) => {
    const y = 1.6 + i * 1.75;
    iconDot(s, r[0], M, y, 0.62, C.accent1, "customer " + i);
    text(s, r[1], { x: M + 0.85, y: y - 0.02, w: 3.6, h: 0.4, fontSize: 18, bold: true });
    text(s, r[2], { x: M + 0.85, y: y + 0.42, w: 3.6, h: 1.2, fontSize: 14, color: C.text2 });
  });
  img(s, "p_allee.jpg", 5.4, 1.55, 7.33, 3.1, "bench in the street");
  const vx = 5.4, vw = (7.33 - 0.4) / 3;
  [["p_high_laser.jpg", "Backrest · laser-cut mark"], ["p_high_shield.jpg", "Backrest · logo shield"], ["p_none_laser.jpg", "Bench seat only"]].forEach((v, i) => {
    img(s, v[0], vx + i * (vw + 0.2), 4.85, vw, 1.55, "variant " + i);
    caption(s, v[1], vx + i * (vw + 0.2), 6.47, vw, C.text2);
  });
  s.addNotes(
    "Suggested speaker: John Isak.\n\n" +
    "Customer view. The paying customer is a municipality or a company, not the person who sits on the bench. From assignment 1: they care about what the furniture says about the place, and studies show people prefer traditional over modern street furniture.\n\n" +
    "We deliberately limited the choices to what matters to that customer: backrest or not, and a personal mark on the top plank. The pictures are screenshots of our configurator, which generates the bench from the same frame profile as the CAD."
  );

  // ============ 3. Architecture before -> after
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("Architecture: variety moved out of the frame", { placeholder: "title" });
  const cw = 5.55, ch = 3.55, cy = 1.55;
  card(s, M, cy, cw, ch, C.background2, "as-is card");
  card(s, W - M - cw, cy, cw, ch, C.background2, "target card");
  text(s, "ASSIGNMENT 1 · AS-IS", { x: M + 0.35, y: cy + 0.3, w: 4.8, h: 0.3, fontSize: 12, bold: true, color: C.accent5, charSpacing: 1 });
  text(s, "Cast sides carry the style", { x: M + 0.35, y: cy + 0.62, w: 4.9, h: 0.45, fontSize: 20, bold: true });
  text(s, [
    { text: "Ten traditional cast side designs, five lengths, three backrests", options: { bullet: true, breakLine: true } },
    { text: "A pattern (tooling) for every side design", options: { bullet: true, breakLine: true } },
    { text: "Boards slide in lengthwise along a machined channel", options: { bullet: true, breakLine: true } },
    { text: "Style and structure in one part: an integral side", options: { bullet: true } },
  ], { x: M + 0.35, y: cy + 1.2, w: 4.9, h: 2.2, fontSize: 15, color: C.text2, paraSpaceAfter: 6 });
  const tx = W - M - cw;
  text(s, "ASSIGNMENT 2 · TARGET, BUILT", { x: tx + 0.35, y: cy + 0.3, w: 4.8, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 1 });
  text(s, "One bar, standard planks, a mark", { x: tx + 0.35, y: cy + 0.62, w: 4.9, h: 0.45, fontSize: 20, bold: true });
  text(s, [
    { text: "One laser-cut flat bar, press-brake bent; no casting tool", options: { bullet: true, breakLine: true } },
    { text: "Two frame states: with or without the backrest arm", options: { bullet: true, breakLine: true } },
    { text: "Every plank the same 25 × 5 section, dropped straight in", options: { bullet: true, breakLine: true } },
    { text: "Customer variety only in the mark, added last", options: { bullet: true } },
  ], { x: tx + 0.35, y: cy + 1.2, w: 4.9, h: 2.2, fontSize: 15, color: C.text2, paraSpaceAfter: 6 });
  s.addShape(pres.shapes.RIGHT_ARROW, { x: W / 2 - 0.3, y: cy + ch / 2 - 0.25, w: 0.6, h: 0.5, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "arrow" });
  const stats3 = [["10 → 1", "side design (in 2 states)"], ["1", "plank section, seat and back"], ["0", "fasteners in the frame"], ["1", "assembly direction: straight down"]];
  const sw3 = (W - 2 * M - 3 * 0.3) / 4;
  stats3.forEach((st, i) => {
    const x = M + i * (sw3 + 0.3);
    text(s, st[0], { x, y: 5.35, w: sw3, h: 0.8, fontSize: 40, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
    text(s, st[1], { x, y: 6.15, w: sw3, h: 0.5, fontSize: 14, color: C.text2 });
  });
  s.addNotes(
    "Suggested speaker: John Isak.\n\n" +
    "Engineering view, before and after. In assignment 1 the style lived in cast-iron sides: ten designs, each needing its own pattern, with boards sliding in lengthwise. Style and structure were the same part, so every new look meant a new casting.\n\n" +
    "In assignment 2 we moved variety out of the frame. One flat bar, laser-cut and bent, in two states. All six planks share one section. The only customer-specific part is the mark on the top plank, and it is added last: late differentiation.\n\n" +
    "The numbers along the bottom are what the robot cares about: one frame family, one plank, no fasteners, everything goes in straight down."
  );

  // ============ 4. Modules and interfaces
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("Modules and the critical interface", { placeholder: "title" });
  card(s, M, 1.5, 5.0, 5.2, C.background2, "drawing card");
  const F = frame(s, M + 0.85, 1.8, 4.2, H.dk2, H.accent1);
  text(s, "Side frame as modelled (1:7.5 demonstrator)", { x: M + 0.25, y: 6.38, w: 4.6, h: 0.28, fontSize: 11, color: C.accent5 });
  const mk = [[-30, 2.5, -0.2, 0.45], [60, -47, 0.25, -0.2], [-63, 60, -0.2, -0.2], [66, -77, 0.25, -0.3]];
  mk.forEach((m, i) => { const [x, y] = F.at(m[0], m[1]); num(s, i + 1, x + m[2] - 0.21, y + m[3] - 0.21); });
  const rows4 = [
    ["Seat pockets", "Three 25 × 5 planks in 25.4 × 5.4 windows: 0.2 mm per side. Chamfers of 1.5 and 1 mm widen the robot's capture range from ±0.2 to ±2.7 mm."],
    ["Backrest arm", "The only frame variant: the same bar, bent further, with three more pockets for the same plank."],
    ["Legs", "The bent bar reaches the ground itself: no separate foot, no fasteners, nothing to adjust."],
    ["Top plank mark", "Laser-cut crest or logo shield. A cheap part on a standard interface carries the customer variety."],
  ];
  rows4.forEach((r, i) => {
    const y = 1.55 + i * 1.3;
    num(s, i + 1, 6.15, y);
    text(s, r[0], { x: 6.8, y: y - 0.02, w: 5.9, h: 0.38, fontSize: 18, bold: true });
    text(s, r[1], { x: 6.8, y: y + 0.38, w: 5.9, h: 0.85, fontSize: 14, color: C.text2 });
  });
  s.addNotes(
    "Suggested speaker: John Isak.\n\n" +
    "This is the frame as modelled, drawn straight from the CAD coordinates. Three modules: the frame (in two states), the planks (one part, seat and back), and the mark.\n\n" +
    "The critical interface is the plank pocket. The window is only 0.2 mm larger than the plank per side, so the plank stands straight. That is too tight for an offline-programmed robot, which is 1 to 2 mm off before teaching. So we added lead-in chamfers on window and plank end: the capture range grows to about 2.7 mm. That is a design-for-assembly decision driven by the robot."
  );

  // ============ 5. Manufacturing flow + lean
  pres.addSection({ title: "Manufacturing" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Manufacturing" });
  s.addText("Manufacturing flow: order to delivery", { placeholder: "title" });
  const steps = [
    [I.globe, "Order", "Web configurator: variant and mark"],
    [I.cut, "Cut and bend", "Laser + press brake; planks cut to length"],
    [I.boxes, "Kit", "Planks in the rack, frames in the jig"],
    [I.robot, "Cobot assembly", "Omron TM5-900 in one jig"],
    [I.stamp, "Mark and check", "Crest or shield, then QC"],
    [I.truck, "AMR delivery", "Bench set on the AMR by the cobot"],
  ];
  const stw = (W - 2 * M) / steps.length;
  steps.forEach((st, i) => {
    const x = M + i * stw, cx = x + stw / 2;
    const fill = i === 3 || i === 5 ? C.accent2 : C.accent1;
    iconDot(s, st[0], cx - 0.42, 1.65, 0.84, fill, "step " + i);
    if (i < steps.length - 1) s.addShape(pres.shapes.LINE, { x: cx + 0.55, y: 2.07, w: stw - 1.1, h: 0, line: { color: C.accent5, width: 1.5, endArrowType: "triangle" }, objectName: "flow arrow " + i });
    text(s, st[1], { x: x + 0.05, y: 2.7, w: stw - 0.1, h: 0.4, fontSize: 16, bold: true, align: "center" });
    text(s, st[2], { x: x + 0.1, y: 3.1, w: stw - 0.2, h: 0.7, fontSize: 13, color: C.text2, align: "center" });
  });
  card(s, M, 4.15, W - 2 * M, 2.55, C.background2, "lean card");
  text(s, "FROM OUR LEAN ANALYSIS (ASSIGNMENT 3, ESTIMATES)", { x: M + 0.35, y: 4.4, w: 8, h: 0.3, fontSize: 12, bold: true, color: C.accent5, charSpacing: 1 });
  const stats5 = [["3.65 h", "takt time: 1000 benches in six months"], ["≈ 18 min", "mean cycle per bench, rework included"], ["≈ 8 %", "of available time used: room to grow"], ["≈ 5.5 min", "cobot assembly in our simulation (A3 assumed 5)"]];
  const sw5 = (W - 2 * M - 0.7 - 3 * 0.3) / 4;
  stats5.forEach((st, i) => {
    const x = M + 0.35 + i * (sw5 + 0.3);
    text(s, st[0], { x, y: 4.85, w: sw5, h: 0.8, fontSize: 36, bold: true, color: i === 3 ? C.accent2 : C.accent1, fontFace: THEME.headFontFace });
    text(s, st[1], { x, y: 5.7, w: sw5, h: 0.75, fontSize: 14, color: C.text2 });
  });
  s.addNotes(
    "Suggested speaker: John Isak, handing over to Bjørge at the end.\n\n" +
    "The flow from order to delivery. The order comes from the configurator, so production knows the variant and the mark before anything is cut. Frames are laser-cut and bent with no tooling per variant. The green steps are where the robots are: the cobot assembles in one jig, and the mobile robot delivers.\n\n" +
    "From our lean analysis: with 1000 benches over six months the takt time is 3.65 hours, against roughly 18 minutes of work per bench. So one cell is far from being the bottleneck. And the simulation gave us a real number for the robot step: about five and a half minutes, close to the five we had assumed in the value stream map.\n\n" +
    "Bjørge will now show how that number came about."
  );

  // ============ 6. Divider: the wow factor
  pres.addSection({ title: "Simulation" });
  s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Simulation" });
  text(s, "OUR WOW FACTOR", { x: M, y: 1.6, w: 5, h: 0.35, fontSize: 12, bold: true, color: C.accent3, charSpacing: 1 });
  s.addText("The cell runs in software before it runs in the lab", { placeholder: "title" });
  s.addText("A digital twin of the TM5-900 cell, built by us: the same robot program and TMflow logic, with reach and collisions checked on every move", { placeholder: "body" });
  img(s, "cell_iso.jpg", 6.75, 1.0, 6.0, 5.5, "cell iso view");
  s.addNotes(
    "Suggested speaker: Bjørge.\n\n" +
    "This is the part we are proudest of. We started in RoboDK, but its licence limits and the fact that it stops at the first collision slowed us down. So we wrote our own simulator: the robot's kinematics, a collision checker, the TMflow export, and a live 3D view in the browser. Every jig version you will see was tested here first."
  );

  // ============ 7. Video
  s = pres.addSlide({ masterName: "VIDEO_DARK", sectionTitle: "Simulation" });
  s.addText("Video: one bench assembled in our simulator (2× speed)", { placeholder: "title" });
  const vh = 5.65, vwid = vh * (1280 / 688);
  const poster = require("fs").readFileSync(MEDIA("v8_assembly_sim_poster.jpg")).toString("base64");
  s.addMedia({ type: "video", path: MEDIA("v8_assembly_sim.mp4"), x: (W - vwid) / 2, y: 1.15, w: vwid, h: vh, cover: "data:image/jpeg;base64," + poster, objectName: "assembly video" });
  text(s, "Planks into frame 1 · guide halves onto base A · frame 1 and planks flipped into frame 2 · guide out", { x: M, y: 6.95, w: W - 2 * M, h: 0.35, fontSize: 13, color: C.accent5, align: "center" });
  s.addNotes(
    "Suggested speaker: Bjørge. Click the video to play (about 60 s).\n\n" +
    "What you see: the robot takes five planks from the rack and stands them in frame 1. The plank guide, in two halves, goes on top so the planks stay at the right pitch. Then the robot flips frame 1 with its planks into frame 2 on the other base. Finally the guide halves are pulled out of the finished bench, and the bench goes to the mobile robot.\n\n" +
    "Everything here is the real program: the same moves that are exported to TMflow."
  );

  // ============ 8. Digital twin
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Simulation" });
  s.addText("Our own digital twin of the cell", { placeholder: "title" });
  const dx = M, dy = 1.5, dw = 7.9, dhh = dw * 1080 / 1920;
  img(s, "dashboard_v8.jpg", dx, dy, dw, dhh, "simulator dashboard", false);
  [[0.06, 0.13], [0.37, 0.13], [0.95, 0.5], [0.88, 0.13]].forEach((p, i) => num(s, i + 1, dx + p[0] * dw - 0.21, dy + p[1] * dhh - 0.21, C.accent2));
  caption(s, "Live view during a v8 run, with the one remaining collision listed top right", dx, dy + dhh + 0.1, dw);
  const rows8 = [
    ["Mock TMflow project", "The flow that runs on the robot: Listen node, gripper nodes, error exits."],
    ["Python bridge", "Sends every move as a script over the Listen node, exactly as to the real TM."],
    ["3D cell", "Techman's link meshes, our jig, planks and AMR plate; joints streamed live."],
    ["Checks on every move", "Reach, collisions (arm, gripper and carried parts) and manipulability."],
  ];
  rows8.forEach((r, i) => {
    const y = 1.5 + i * 1.12;
    num(s, i + 1, 8.85, y, C.accent2);
    text(s, r[0], { x: 9.45, y: y - 0.02, w: 3.3, h: 0.36, fontSize: 16, bold: true });
    text(s, r[1], { x: 9.45, y: y + 0.36, w: 3.3, h: 0.72, fontSize: 13, color: C.text2 });
  });
  card(s, 8.85, 6.05, W - M - 8.85, 0.75, C.background2, "validation card");
  text(s, [
    { text: "Checked against RoboDK: ", options: { bold: true, color: C.text1 } },
    { text: "kinematics within 0.005 mm, first collision at the same move.", options: { color: C.text2 } },
  ], { x: 9.0, y: 6.12, w: W - M - 9.15, h: 0.62, fontSize: 12, valign: "middle" });
  s.addNotes(
    "Suggested speaker: Bjørge.\n\n" +
    "Four parts. One: a mock of the TMflow project, the same flow that runs on the robot, so the logic is tested too, not just the path. Two: the Python bridge that streams each move over the Listen node, exactly as it does to the real robot. Three: the 3D cell. Four: the checks on every move: reach, collisions including the parts the robot carries, and manipulability, how far each pose is from a singularity.\n\n" +
    "We trust it because we checked it against RoboDK: forward kinematics agree within 0.005 mm, and on version 7 both tools found the first collision at the same move. Unlike RoboDK, ours lists every collision, not just the first, and runs on any laptop without a licence."
  );

  // ============ 9. Simulation drove the jig design
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Simulation" });
  s.addText("The simulation broke every jig before the lab did", { placeholder: "title" });
  const tl = [
    ["v3", "One double-sided guide", "Found: the guide ends up trapped between the frames."],
    ["v4", "Guide split in two", "Each half slides out its own way; the bench goes onto the AMR."],
    ["v6", "No parking pad", "The halves go straight back onto base A: the cell ends as it starts."],
    ["v7", "Jig on the work plate", "Found: wrist hits the plank rack while carrying the guide."],
    ["v8", "Feet face the robot", "Guide out before the lift, big half parked on the AMR."],
  ];
  const tw = (W - 2 * M) / tl.length, ty = 1.95;
  s.addShape(pres.shapes.LINE, { x: M + tw / 2, y: ty, w: tw * (tl.length - 1), h: 0, line: { color: C.accent5, width: 2 }, objectName: "timeline" });
  tl.forEach((t, i) => {
    const cx = M + i * tw + tw / 2;
    s.addText(t[0], { shape: pres.shapes.OVAL, x: cx - 0.4, y: ty - 0.4, w: 0.8, h: 0.8, fill: { color: i === tl.length - 1 ? C.accent2 : C.accent1 }, line: { color: C.background1, width: 2 }, color: C.background1, bold: true, fontSize: 16, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "version " + t[0] });
    text(s, t[1], { x: cx - tw / 2 + 0.08, y: ty + 0.55, w: tw - 0.16, h: 0.4, fontSize: 15, bold: true, align: "center" });
    text(s, t[2], { x: cx - tw / 2 + 0.12, y: ty + 0.95, w: tw - 0.24, h: 0.9, fontSize: 13, color: C.text2, align: "center" });
  });
  const by = 4.1, bh = 2.65;
  card(s, M, by, 3.0, bh, C.background2, "guide card");
  img(s, "guide_split.jpg", M + 0.25, by + 0.15, 2.5, 2.05, "split guide", false);
  caption(s, "Guide split: inner half orange, outer yellow", M + 0.2, by + 2.25, 2.7, C.text2);
  card(s, M + 3.3, by, 4.6, bh, C.background2, "jig card");
  img(s, "jig_v3_3d.jpg", M + 3.75, by + 0.15, 3.7, 3.7 * 308 / 562, "jig 3d", false);
  caption(s, "Two frame jigs, guide and plank rack on T-slot profiles", M + 3.5, by + 2.25, 4.2, C.text2);
  card(s, M + 8.2, by, W - 2 * M - 8.2, bh, C.background2, "rules card");
  text(s, "RULES WE TOOK AWAY", { x: M + 8.5, y: by + 0.25, w: 3.6, h: 0.3, fontSize: 12, bold: true, color: C.accent5, charSpacing: 1 });
  text(s, [
    { text: "Risers of 120 mm: 60 and 30 mm fail at the flip", options: { bullet: true, breakLine: true } },
    { text: "3-2-1 locating, push towards one datum", options: { bullet: true, breakLine: true } },
    { text: "Lead-ins on every pocket", options: { bullet: true } },
  ], { x: M + 8.5, y: by + 0.65, w: W - 2 * M - 8.75, h: 1.9, fontSize: 14, color: C.text2, paraSpaceAfter: 6 });
  s.addNotes(
    "Suggested speaker: Bjørge.\n\n" +
    "Each circle is a version of the assembly method, and every one was found wanting in the simulation, not in the lab.\n\n" +
    "Version 3 used one double-sided guide. The simulation showed it ends up trapped between the two frames. So in version 4 we cut it in two along the plank rows: each half only touches the planks on sides it can slide away from. That is the orange and yellow drawing.\n\n" +
    "Version 7 moved the jig onto the robot's work plate, and the checker found the wrist hitting the plank rack. Version 8 turned the bases so the frame's feet face the robot, takes the guide out before the bench is lifted, and parks the big guide half on the AMR plate.\n\n" +
    "The rules on the right came out of it, for example: the risers must be 120 mm, because at 60 or 30 mm the flip does not clear."
  );

  // ============ 10. Stages + cycle time chart
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Simulation" });
  s.addText("One bench: eight stages, about 333 seconds", { placeholder: "title" });
  const fr = [["sim_planks.jpg", "1", "Five planks: rack to frame 1"], ["sim_guide.jpg", "2–3", "Guide halves onto base A"], ["sim_flip.jpg", "4", "Frame 1 and planks flipped into frame 2"], ["sim_guide_out.jpg", "5–6", "Guide halves out of the bench"]];
  const fw = 2.6, fh = fw * 0.75;
  fr.forEach((f, i) => {
    const x = M + (i % 2) * (fw + 0.25), y = 1.5 + Math.floor(i / 2) * (fh + 0.55);
    img(s, f[0], x, y, fw, fh, "stage " + f[1]);
    text(s, f[1], { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.06, x: x + 0.1, y: y + 0.1, w: 0.55, h: 0.32, fill: { color: C.accent2 }, color: C.background1, bold: true, fontSize: 12, align: "center", valign: "middle" });
    caption(s, f[2], x, y + fh + 0.06, fw + 0.2, C.text2);
  });
  text(s, "7–8: bench onto the AMR, big guide half back to base B", { x: M, y: 6.55, w: 5.5, h: 0.3, fontSize: 11, color: C.text2 });
  s.addChart(pres.charts.BAR, [{ name: "Cycle time (s)", labels: ["v3", "v4", "v6", "v7", "v8"], values: [240, 345, 330, 341, 333] }], {
    x: 6.4, y: 1.45, w: 6.33, h: 3.9, barDir: "col", barGapWidthPct: 60,
    chartColors: [H.accent1],
    showTitle: true, title: "Robot cycle time per version (s)", titleFontSize: 14, titleColor: H.dk1, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: H.dk2, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: H.dk2, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt",
    valAxisLabelColor: H.accent5, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 400, valAxisMajorUnit: 100,
    valGridLine: { color: "E3E6E8", size: 0.75 }, catGridLine: { style: "none" }, showLegend: false,
    objectName: "cycle time chart",
  });
  text(s, [
    { text: "Splitting the guide cost about 100 s but removed a trapped part and a manual step.", options: { bullet: true, breakLine: true } },
    { text: "The planks dominate: slow 20 mm/s moves near the parts.", options: { bullet: true, breakLine: true } },
    { text: "Times at programmed speeds; the real robot's time comes from the lab.", options: { bullet: true } },
  ], { x: 6.5, y: 5.45, w: 6.2, h: 1.4, fontSize: 14, color: C.text2, paraSpaceAfter: 4 });
  s.addNotes(
    "Suggested speaker: Bjørge.\n\n" +
    "The eight stages of version 8. One: five planks from the rack into frame 1. Two and three: the guide halves onto base A. Four, the hardest move: frame 1 with all its planks is flipped into frame 2. Five and six: the guide comes out of the bench. Seven and eight: the bench goes to the AMR and the guide goes back for the next bench.\n\n" +
    "The chart is the cycle time for each version, calculated from the program at its programmed speeds. Version 3 was fastest, but its guide was trapped. Splitting the guide cost about a hundred seconds and removed a manual step. Version 8 is at about 333 seconds, five and a half minutes, far below the 3.65-hour takt. The planks take most of the time, because the robot moves slowly near the parts.\n\n" +
    "Data: cycle_times.csv (v3, v4, v6, v7; v5 was only an estimate and is left out). v8 = about 333 s from our own simulator (robot-cell/Next steps.md)."
  );

  // ============ 11. Sim -> real robot + AMR
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Simulation" });
  s.addText("From simulation to the real TM5-900", { placeholder: "title" });
  text(s, "VERIFIED ON THE LAB ROBOT", { x: M, y: 1.5, w: 5.5, h: 0.3, fontSize: 12, bold: true, color: C.accent2, charSpacing: 1 });
  const ver = [
    ["Live state at 100 Hz", "Joints and flange pose over Ethernet Slave and Modbus."],
    ["Moves from Python", "Line moves over the Listen node: 20 and 50 mm, exactly."],
    ["Gripper in the loop", "Grip, release and an empty grip detected; hand-over in 6 s."],
  ];
  ver.forEach((v, i) => {
    const y = 1.95 + i * 0.95;
    iconDot(s, I.check, M, y, 0.5, C.accent2, "verified " + i);
    text(s, v[0], { x: M + 0.7, y: y - 0.04, w: 5.0, h: 0.34, fontSize: 16, bold: true });
    text(s, v[1], { x: M + 0.7, y: y + 0.3, w: 5.0, h: 0.55, fontSize: 13, color: C.text2 });
  });
  text(s, "NEXT IN THE LAB", { x: M, y: 4.85, w: 5.5, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 1 });
  const nxt = [
    ["AMR delivery over ARCL", "\"goto BenchCell\", place the bench, \"goto Delivery\"."],
    ["Vision base on the AMR plate", "A TM Landmark corrects the AMR's few-cm stop error."],
  ];
  nxt.forEach((v, i) => {
    const y = 5.3 + i * 0.8;
    iconDot(s, i === 0 ? I.truck : I.cogs, M, y, 0.5, C.accent1, "next " + i);
    text(s, v[0], { x: M + 0.7, y: y - 0.04, w: 5.0, h: 0.34, fontSize: 16, bold: true });
    text(s, v[1], { x: M + 0.7, y: y + 0.3, w: 5.0, h: 0.4, fontSize: 13, color: C.text2 });
  });
  const iw = 6.2, ih = iw * 760 / 1400;
  img(s, "tmflow_demo.jpg", W - M - iw, 1.55, iw, ih, "audience view", false);
  caption(s, "Audience view during a dry run on the lab robot: what the robot is doing, step by step", W - M - iw, 1.55 + ih + 0.08, iw);
  card(s, W - M - iw, 5.25, iw, 1.5, C.background2, "export card");
  text(s, [
    { text: "One program, two targets. ", options: { bold: true, color: C.text1 } },
    { text: "The same move list drives the simulator and exports to a TMflow project. The export round-trips byte for byte on RoboDK's files; the import into TMflow is still to be tested.", options: { color: C.text2 } },
  ], { x: W - M - iw + 0.3, y: 5.4, w: iw - 0.6, h: 1.2, fontSize: 13, valign: "middle" });
  s.addNotes(
    "Suggested speaker: Bjørge.\n\n" +
    "The simulator is not a toy: the bridge it tests is the one we use on the real robot. In the lab we verified that we can read the robot's state live, move it from Python over the Listen node with millimetre accuracy, and run the gripper in the loop, including detecting when it closes on nothing.\n\n" +
    "The screen on the right is the audience view from a dry run on the lab robot.\n\n" +
    "Next is the mobile robot. Omron's AMR takes text commands over the network, so the cell can send it to the bench and on to delivery. It only stops to within a few centimetres, so the cobot finds the plate with its wrist camera and a printed landmark.\n\n" +
    "Honest status: our own TMflow export matches RoboDK's files, but we have not yet imported it on the robot."
  );

  // ============ 12. Lessons + questions for the board
  pres.addSection({ title: "Closing" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Closing" });
  s.addText("What we learned, and what we ask you", { placeholder: "title" });
  const colw = (W - 2 * M - 0.4) / 2;
  card(s, M, 1.5, colw, 5.25, C.background2, "lessons card");
  card(s, M + colw + 0.4, 1.5, colw, 5.25, C.background2, "questions card");
  iconDot(s, I.lightbulb, M + 0.35, 1.8, 0.6, C.accent1, "lessons");
  text(s, "Lessons", { x: M + 1.15, y: 1.88, w: 4, h: 0.45, fontSize: 22, bold: true });
  const les = [
    ["Design product and cell together.", " One plank section and straight-down assembly made a one-jig cell possible."],
    ["Fail in software first.", " Trapped guide, flip clearance, arm through the bench: all found before the lab."],
    ["Own tools pay off.", " No licence cap, every collision listed, runs on any laptop in the group."],
  ];
  les.forEach((l, i) => text(s, [{ text: l[0], options: { bold: true, color: C.text1 } }, { text: l[1], options: { color: C.text2 } }],
    { x: M + 0.35, y: 2.7 + i * 1.3, w: colw - 0.7, h: 1.15, fontSize: 15 }));
  const qx = M + colw + 0.4;
  iconDot(s, I.question, qx + 0.35, 1.8, 0.6, C.accent2, "questions");
  text(s, "Your feedback", { x: qx + 1.15, y: 1.88, w: 4, h: 0.45, fontSize: 22, bold: true });
  const qs = [
    ["Guide half locked in CAD.", " With the small half out, the big half cannot slide past the planks. More clearance, or a tooth less?"],
    ["Docking the AMR.", " Vision landmark or a mechanical docking guide: which holds up in a real plant?"],
    ["Plank joint at full size.", " Slot fit works at 1:7.5. Would you press-fit, snap or screw planks in a real line?"],
  ];
  qs.forEach((q, i) => text(s, [{ text: q[0], options: { bold: true, color: C.text1 } }, { text: q[1], options: { color: C.text2 } }],
    { x: qx + 0.35, y: 2.7 + i * 1.3, w: colw - 0.7, h: 1.15, fontSize: 15 }));
  s.addNotes(
    "Suggested speaker: both. John Isak takes lessons, Bjørge the questions.\n\n" +
    "Three lessons. Designing the product and the cell together is what made it work: if the planks had different sections or went in from different directions, we would need several jigs or tool changes. Failing in software is cheap; failing in the lab costs a session. And building our own tools paid off.\n\n" +
    "Three questions for you. One: our last collision. In the CAD, the big guide half is locked between the planks once the small half is out; we want to know if you would add clearance or redesign the guide. Two: docking the AMR, vision or mechanics. Three: at full size, how would you join the planks to the frame in a real line?"
  );

  // ============ 13. Closing
  s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Closing" });
  s.addText("Thank you. Questions?", { placeholder: "title" });
  s.addText([{ text: "Configure a bench yourself:", options: { breakLine: true } }, { text: "bjorgex.github.io/mma4002-assignment1", options: { color: C.accent3 } }], { placeholder: "body" });
  text(s, "Bjørge Skjelbreid Djuve · John Isak Hammer", { x: M, y: 5.75, w: 7, h: 0.35, fontSize: 16, bold: true, color: C.background1 });
  text(s, "MMA4002 Design for Automated Manufacturing · NTNU Ålesund", { x: M, y: 6.15, w: 7.2, h: 0.35, fontSize: 14, color: C.accent5 });
  frame(s, 8.35, 0.95, 5.6, H.accent5, H.accent1);
  s.addNotes("Suggested speaker: both.\n\nOpen for questions. If time allows, show the configurator live from the link or the simulator running v8.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
