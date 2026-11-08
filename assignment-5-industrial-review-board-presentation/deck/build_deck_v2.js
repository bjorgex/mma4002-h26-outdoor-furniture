// Industrial Review Board deck, version 2: shorter and more visual (MMA4002 Assignment 5, 9 Nov 2026).
// Order (Bjørge, 2026-11-07): website (configure + order) -> CAD model + interface -> manufacturing flow with the
// lean numbers -> simulation (the wow factor) -> real robot video -> bridge + gripper + changing a step ->
// vision: an AI improving a whole factory in simulation -> what we learned / next.
// Build:  cd assignment-5-industrial-review-board-presentation/deck && node build_deck_v2.js
// Output: ../MMA4002_IRB_Outdoor_Bench_v2.pptx
// Real robot video: put it at media/real_robot.mp4 (+ optional media/real_robot_poster.jpg) and rebuild; until
// then slide 7 shows a still from the lab.

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("./apply_theme.js");

const MEDIA = (f) => path.join(__dirname, "media", f);
const OUT = path.join(__dirname, "..", "MMA4002_IRB_Outdoor_Bench_v2.pptx");
const SITE = "bjorgex.github.io/mma4002-h26-outdoor-furniture";

const THEME = {
  name: "Bent Bar",
  headFontFace: "Arial",                       // the website uses Archivo; Arial is its safe stand-in
  bodyFontFace: "Arial",
  // the website's palette (index.html :root and #cfg): ink on off-white, beige panels, one brown highlight
  colors: {
    dk1: "121413",     // --ink / --accent
    lt1: "FFFFFF",
    dk2: "5B615E",     // --ink-soft
    lt2: "EEEBE4",     // --paper (configurator panels)
    accent1: "7A4B2A", // --hl, the brown highlight
    accent2: "1B1F1D", // configurator ink: the "robot" steps and the simulation
    accent3: "CBC6BA", // --line, light beige: kickers and links on the dark slides
    accent4: "686B68", // --muted
    accent5: "9A9C98", // muted grey, readable on both dark and light
    accent6: "C8453B", // collision red
    hlink: "7A4B2A", folHlink: "686B68",
  },
};
const H = THEME.colors;
const PAGE = "F6F6F4";                           // --bg: the website's page background

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Configure it online, build it with a cobot";
pres.subject = "MMA4002 Industrial Review Board: outdoor bench manufacturing demonstrator";
pres.author = "Bjørge Skjelbreid Djuve, John Isak Hammer";
pres.company = "NTNU Ålesund";
const C = pres.SchemeColor;
const W = 13.333, M = 0.6;
const FOOT = "MMA4002 Design for Automated Manufacturing · Industrial Review Board · 9 Nov 2026";

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: H.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.0, w: 7.2, h: 2.0, fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.2, w: 6.8, h: 1.2, fontSize: 18, color: C.accent5, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION_DARK", background: { color: H.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.1, w: 5.6, h: 2.2, fontSize: 36, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.5, w: 5.4, h: 1.6, fontSize: 18, color: C.accent5, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: PAGE }, margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 0.85, fontSize: 36, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: FOOT, options: { x: M, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: H.accent5, align: "right", margin: 0 },
});
pres.defineSlideMaster({
  title: "VIDEO_DARK", background: { color: H.dk1 },
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
function iconDot(slide, data, x, y, d, fill, name) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: name + " dot" });
  const p = d * 0.25;
  slide.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + " icon" });
}
function num(slide, n, x, y, fill = C.accent1, d = 0.42) {
  slide.addText(String(n), {
    shape: pres.shapes.OVAL, x, y, w: d, h: d, fill: { color: fill }, line: { color: C.background1, width: 1.5 },
    color: C.background1, bold: true, fontSize: 14, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "marker " + n,
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
// QR code to the website on a white rounded square (scannable on the dark slides too)
function qr(slide, x, y, size) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: size, h: size, rectRadius: 0.06, fill: { color: C.background1 }, line: { type: "none" }, objectName: "qr card" });
  const p = size * 0.04;
  slide.addImage({ path: MEDIA("qr_site.png"), x: x + p, y: y + p, w: size - 2 * p, h: size - 2 * p, objectName: "QR code to the website" });
}
function caption(slide, t, x, y, w, color = C.accent5) { text(slide, t, { x, y, w, h: 0.3, fontSize: 11, color }); }
function kicker(slide, t, x, y, w, color = C.accent5) { text(slide, t, { x, y, w, h: 0.3, fontSize: 12, bold: true, color, charSpacing: 1 }); }
function stat(slide, big, small, x, y, w, color = C.accent1) {
  text(slide, big, { x, y, w, h: 0.75, fontSize: 36, bold: true, color, fontFace: THEME.headFontFace });
  text(slide, small, { x, y: y + 0.78, w, h: 0.6, fontSize: 14, color: C.text2 });
}
function arrow(slide, x, y, w, name, color = C.accent5) {
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color, width: 2, endArrowType: "triangle" }, objectName: name });
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
  slide.addShape(pres.shapes.CUSTOM_GEOMETRY, { x: ox + (mx - FR.minx) * s, y: oy + (my - FR.miny) * s, w: Math.max(w, 0.01), h: Math.max(h, 0.01), points, fill: { color: fill }, line: { type: "none" }, objectName: name });
}
function frame(slide, ox, oy, height, barFill, plankFill) {
  const s = height / (FR.maxy - FR.miny);
  poly(slide, PROFILE_HIGH, ox, oy, s, barFill, "frame profile");
  SEAT_SLOTS.forEach((p, i) => poly(slide, p, ox, oy, s, plankFill, "seat plank " + (i + 1)));
  BACK_SLOTS.forEach((p, i) => poly(slide, p, ox, oy, s, plankFill, "back plank " + (i + 1)));
  return { s, at: (x, y) => [ox + (x - FR.minx) * s, oy + (y - FR.miny) * s] };
}

// the bench in side view, rendered from the CAD (benchV1_parts frame.stl + plank_body.stl in the assembly, see
// media/bench_cad_side_*.png): the picture spans exactly x -75..79, up (-z) -80..101 mm. Returns a mapper from the
// frame's (x, z) mm to slide inches, for markers.
// V3 (bench-cad/benchesV3/BenchV3LongWBackrest.STEP, 2 back planks): the picture spans x' -99..45 (x' = -x, backrest
// on the right), z -3..178 mm; at(x', z) maps those to slide inches.
function cadBench(slide, x, y, h, tag) {
  const w = h * 144 / 181;
  slide.addImage({ path: MEDIA(`bench_cad_side_${tag}.png`), x, y, w, h, objectName: "bench side view (CAD V3)" });
  return { at: (px, pz) => [x + (px + 99) / 144 * w, y + (178 - pz) / 181 * h] };
}

// ---------------------------------------------------------------- slides
(async () => {
  const I = {};
  for (const [k, comp] of Object.entries({ globe: fa.FaGlobeEurope, sliders: fa.FaSlidersH, cart: fa.FaShoppingCart,
    cut: fa.FaCut, boxes: fa.FaBoxes, robot: fa.FaRobot, stamp: fa.FaStamp, truck: fa.FaTruck, code: fa.FaCode,
    plug: fa.FaPlug, hand: fa.FaHandPaper, edit: fa.FaEdit, cube: fa.FaCube, bullseye: fa.FaBullseye, brain: fa.FaBrain,
    check: fa.FaCheckCircle, lightbulb: fa.FaLightbulb, forward: fa.FaForward, exchange: fa.FaExchangeAlt }))
    I[k] = await icon(comp, "FFFFFF");

  // ============ 1. Title
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  kicker(s, "MMA4002 DESIGN FOR AUTOMATED MANUFACTURING", M, 1.3, 7.6, C.accent3);
  s.addText("Configure it online, build it with a cobot", { placeholder: "title" });
  text(s, "Bjørge Skjelbreid Djuve · John Isak Hammer", { x: M, y: 5.75, w: 7, h: 0.35, fontSize: 16, bold: true, color: C.background1 });
  text(s, "NTNU Ålesund · L167 · 9 November 2026", { x: M, y: 6.15, w: 4.6, h: 0.35, fontSize: 14, color: C.accent5 });
  text(s, [{ text: SITE, options: { color: C.accent3, bold: true } }],
    { x: M, y: 6.55, w: 5.2, h: 0.35, fontSize: 13 });
  qr(s, 5.85, 5.0, 1.65);
  cadBench(s, 8.15, 0.95, 5.6, "dark");
  s.addNotes("Suggested speaker: both introduce themselves, then John Isak.\n\n" +
    "We made an outdoor bench for public spaces and the robot cell that builds it. We start where the customer starts, on the website, then the product, the factory flow, and then the part we are proudest of: the simulation and the real robot.");

  // ============ 2. Website
  pres.addSection({ title: "Customer" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Customer" });
  s.addText("The customer configures and orders online", { placeholder: "title" });
  // no configurator renders (Bjørge: the website's 3D models don't show well): a big QR code to try it live
  card(s, M, 1.5, 5.4, 5.2, C.background1, "qr card");
  s.addImage({ path: MEDIA("qr_site.png"), x: M + 0.7, y: 1.75, w: 4.0, h: 4.0, objectName: "QR code to the website" });
  text(s, "Scan and configure your own bench", { x: M + 0.3, y: 5.85, w: 4.8, h: 0.35, fontSize: 16, bold: true, align: "center" });
  text(s, SITE, { x: M + 0.3, y: 6.2, w: 4.8, h: 0.35, fontSize: 14, color: C.accent1, align: "center" });
  const rx = 6.75, rw = W - M - rx;
  [[I.sliders, "Choose", "Backrest or not, and the customer's mark on the top plank: a laser-cut crest or a logo shield."],
   [I.cube, "See it in 3D", "The bench is drawn live from the same frame profile as our CAD."],
   [I.cart, "Order", "A quote request straight from the page. Production knows the variant before anything is cut."]].forEach((r, i) => {
    const y = 1.6 + i * 1.7;
    iconDot(s, r[0], rx, y, 0.7, i === 2 ? C.accent1 : C.accent2, "web " + i);
    text(s, r[1], { x: rx + 0.95, y: y + 0.12, w: rw - 0.95, h: 0.45, fontSize: 22, bold: true });
  });
  s.addNotes("Suggested speaker: John Isak. Invite the board to scan the QR code and try it while you talk.\n\n" +
    "The paying customer is a municipality or a company. On our website they choose backrest or not and the mark on the top plank, see the bench in 3D, and send an order. The order tells production exactly which variant to build before anything is cut.");

  // ============ 3. CAD + interface
  pres.addSection({ title: "Product" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("One bent bar, one plank, one interface", { placeholder: "title" });
  // three CAD pictures in a row (Bjørge 2026-11-08: the 2D side view + the real CAD in 3D, whole bench and interface),
  // all from bench-cad/benchesV3/BenchV3LongWBackrest.STEP; the three points below
  const gap3 = 0.25, cw3 = (W - 2 * M - 2 * gap3) / 3, cy3 = 1.4, ch3 = 3.75, ih3 = 3.0;
  const cx3 = (i) => M + i * (cw3 + gap3);
  [0, 1, 2].forEach(i => card(s, cx3(i), cy3, cw3, ch3, C.background2, "cad card " + (i + 1)));
  const w2d = ih3 * 144 / 181;
  const F = cadBench(s, cx3(0) + (cw3 - w2d) / 2, cy3 + 0.2, ih3, "light");
  [[-57, 70, 0, 0.16], [36, 170, 0.26, 0], [-88, 40, -0.18, 0]].forEach((m, i) => { const [x, y] = F.at(m[0], m[1]); num(s, i + 1, x + m[2] - 0.18, y + m[3] - 0.18, C.accent1, 0.36); });
  // interface_cad_3d.png: the plank's interface clip (the small solid at each plank end), pulled 14 mm off the plank end
  [["bench_cad_3d.png", 835 / 904, "The whole bench in 3D (CAD)"], ["interface_cad_3d.png", 829 / 589, "The interface clip on the plank end (CAD)"]].forEach(([f, a, t], k) => {
    const i = k + 1, iw = Math.min(ih3 * a, cw3 - 0.4), h = iw / a;
    s.addImage({ path: MEDIA(f), x: cx3(i) + (cw3 - iw) / 2, y: cy3 + 0.2 + (ih3 - h) / 2, w: iw, h, objectName: t });
  });
  caption(s, "Side view, CAD V3 (1:7.5 demonstrator)", cx3(0) + 0.25, cy3 + ch3 - 0.42, cw3 - 0.5);
  caption(s, "The whole bench in 3D, CAD V3", cx3(1) + 0.25, cy3 + ch3 - 0.42, cw3 - 0.5);
  caption(s, "The interface: the clip on each plank end", cx3(2) + 0.25, cy3 + ch3 - 0.42, cw3 - 0.5);
  [["Plank pockets", "Same 25 × 5 section for every plank. 0.2 mm play, chamfers: the robot hits within ±2.7 mm."],
   ["Backrest arm", "The only variant in the frame: the same bar, bent further."],
   ["No fasteners", "The bent bar is also the leg. Nothing to screw or adjust."]].forEach((r, i) => {
    const x = cx3(i), y = 5.55;
    num(s, i + 1, x, y);
    text(s, r[0], { x: x + 0.6, y: y + 0.0, w: cw3 - 0.6, h: 0.42, fontSize: 19, bold: true });
  });
  s.addNotes("Suggested speaker: John Isak.\n\n" +
    "The product is one laser-cut flat bar, bent in a press brake, in two states: with or without the backrest arm. All planks share one section. The critical interface is the plank pocket: tight enough that the plank stands straight, but with chamfers so an offline-programmed robot still gets it in. The design was made for the robot, and the robot cell for the design.");

  // ============ 4. Manufacturing flow + lean
  pres.addSection({ title: "Manufacturing" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Manufacturing" });
  s.addText("From order to delivery", { placeholder: "title" });
  const steps = [[I.globe, "Order", "Web configurator"], [I.cut, "Cut and bend", "Laser + press brake"], [I.boxes, "Kit", "Planks and frames to the cell"],
    [I.robot, "Cobot assembly", "TM5-900 in one jig"], [I.stamp, "Mark and check", "Crest or shield, QC"], [I.truck, "AMR delivery", "Bench set on the AMR"]];
  const stw = (W - 2 * M) / steps.length;
  steps.forEach((st, i) => {
    const x = M + i * stw, cx = x + stw / 2;
    iconDot(s, st[0], cx - 0.42, 1.6, 0.84, i === 3 || i === 5 ? C.accent2 : C.accent1, "step " + i);
    if (i < steps.length - 1) arrow(s, cx + 0.55, 2.02, stw - 1.1, "flow arrow " + i);
    text(s, st[1], { x: x + 0.05, y: 2.62, w: stw - 0.1, h: 0.4, fontSize: 16, bold: true, align: "center" });
  });
  card(s, M, 3.9, W - 2 * M, 2.45, C.background2, "lean card");
  kicker(s, "FROM OUR LEAN ASSIGNMENT · ESTIMATES", M + 0.35, 4.15, 8);
  const sw = (W - 2 * M - 0.7 - 3 * 0.3) / 4;
  [["3.65 h", "takt time"], ["≈ 18 min", "work per bench"],
   ["≈ 8 %", "of the time used"], ["≈ 6.5 min", "cobot assembly (sim)"]].forEach((st, i) =>
    stat(s, st[0], st[1], M + 0.35 + i * (sw + 0.3), 4.65, sw, i === 3 ? C.accent2 : C.accent1));
  s.addNotes("Suggested speaker: John Isak, then hand over to Bjørge.\n\n" +
    "The flow from order to delivery. The green steps are robots: the cobot assembles, the mobile robot delivers. From our lean assignment, as estimates: 1000 benches in six months gives a takt of 3.65 hours, against about 18 minutes of work per bench, so one cell has plenty of capacity. Our simulation estimates the cobot assembly at about six and a half minutes; the real-robot time we measure now.");

  pres.addSection({ title: "Simulation" });

  // ============ 6a. Before the video: the whole program at a glance (Bjørge's screenshot of the sim page if saved as
  // media/sim_overview.png, else the video's intro frame), time to explain the path, the map and the timeline
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Simulation" });
  s.addText("One loop from the simulator to the robot", { placeholder: "title" });
  {
    const dim = require("image-size")(MEDIA("tmflow_mock.png"));
    const bw = 8.2, iw = bw, ih = bw * dim.height / dim.width;
    img(s, "tmflow_mock.png", M, 1.4, iw, ih, "TMflow mock and the 3D cell", false);
    const qx = M + bw + 0.45, qw = W - M - qx;
    kicker(s, "THE LOOP", qx, 1.45, qw);
    [[I.cube, "Simulator page", "3D cell, timeline, Run"], [I.code, "Python bridge", "one script, sim or robot"],
     [I.plug, "TMflow Listen node", "moves arrive as scripts"], [I.robot, "TM5-900 + Hand-E", "gripper as TMflow nodes"]].forEach((r, i) => {
      const y = 1.85 + i * 1.1;
      iconDot(s, r[0], qx, y, 0.55, i === 3 ? C.accent1 : C.accent2, "loop " + i);
      text(s, r[1], { x: qx + 0.72, y: y + 0.08, w: qw - 0.72, h: 0.4, fontSize: 16, bold: true });
      if (i < 3) s.addShape(pres.shapes.LINE, { x: qx + 0.275, y: y + 0.62, w: 0, h: 0.4, line: { color: C.accent5, width: 1.5, endArrowType: "triangle" }, objectName: "loop arrow " + i });
    });
  }
  s.addNotes("Suggested speaker: Bjørge.\n\n" +
    "Our own simulator page. On the left is the TMflow project that runs on the robot: start, home, initialise the Hand-E, then the Listen node called Bridge, where our Python script takes over and sends every move. A gateway reads which gripper command comes next: grip, release, home or stop, and every branch comes back to the Bridge. We mocked that whole flow, so the robot's own logic is tested together with the motion, not only the path. On the right is the 3D cell.\n\n" +
    "The loop: the page drives our Python bridge, the bridge sends each move as a script to TMflow's Listen node, and the gripper runs as TMflow nodes. The same script runs against the mock or the real TM5. A step changed and saved on the page rebuilds the robot program.");

  // ============ 6b. Before the video: the whole program at a glance (Bjørge's screenshot), to explain path and map
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Simulation" });
  s.addText("Before it runs: the whole program at a glance", { placeholder: "title" });
  {
    const dim = require("image-size")(MEDIA("sim_overview.png"));
    const bw = 8.3, iw = bw, ih = bw * dim.height / dim.width;
    img(s, "sim_overview.png", M, 1.4, iw, ih, "simulator page: path and manipulability", false);
    const qx = M + bw + 0.45, qw = W - M - qx;
    [[I.robot, "Gripper path", "Every target the robot moves to, coloured by how free the arm is there. Red = stiff or near a joint limit."],
     [I.bullseye, "Manipulability", "Where the arm works well (green) and where it gets close to a singularity or out of reach (red)."],
     [I.check, "Checked before the lab", "Reach, collisions and every grip and release, on the timeline above the 3D view."]].forEach((r, i) => {
      const y = 1.5 + i * 1.7;
      iconDot(s, r[0], qx, y, 0.55, i === 1 ? C.accent1 : C.accent2, "overview point " + i);
      text(s, r[1], { x: qx + 0.75, y: y + 0.06, w: qw - 0.75, h: 0.42, fontSize: 19, bold: true });
    });
  }
  s.addNotes("Suggested speaker: Bjørge.\n\n" +
    "Before we press play: the whole v9 program at once. The line is the gripper path; every point is a target the robot moves to, coloured by how free the arm is there. Red points are stiff or close to a joint limit, green rings are where the gripper closes and opens. " +
    "The red and green volume is the manipulability: green is where the arm works well, red is close to a singularity or out of reach. The timeline at the top shows every stage, grip, release and any collision; this version is collision-free.");

  // ============ 6. Simulation video
  s = pres.addSlide({ masterName: "VIDEO_DARK", sectionTitle: "Simulation" });
  s.addText("One bench assembled in our simulator", { placeholder: "title" });
  // v9, exported with the sim page's "Export video" button (4x real time, 1884 x 668): intro with the gripper path and
  // the manipulability map, then the clean assembly
  const vwid = W - 2 * M, vh = vwid * 668 / 1884;
  const poster = fs.readFileSync(MEDIA("v9_full_sim_poster.jpg")).toString("base64");
  s.addMedia({ type: "video", path: MEDIA("v9_full_sim.mp4"), x: M, y: 1.15 + (5.65 - vh) / 2, w: vwid, h: vh, cover: "data:image/jpeg;base64," + poster, objectName: "simulation video" });
  text(s, "4× real time", { x: M, y: 6.95, w: W - 2 * M, h: 0.35, fontSize: 13, color: C.accent5, align: "center" });
  s.addNotes("Suggested speaker: Bjørge. Click the video to play (about 38 s, 4x real time).\n\n" +
    "The assembly: five planks from the rack into frame 1, the plank guide on, frame 1 with the planks flipped into frame 2, the guide halves slide out of the finished bench, and the bench is turned onto its feet on the mobile robot. These are the exact moves we send to the real robot.");

  // ============ 10. Learned / next
  pres.addSection({ title: "Closing" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Closing" });
  s.addText("What we learned, and what comes next", { placeholder: "title" });
  const colw = (W - 2 * M - 0.4) / 2;
  card(s, M, 1.5, colw, 5.25, C.background2, "learned card");
  card(s, M + colw + 0.4, 1.5, colw, 5.25, C.background2, "next card");
  iconDot(s, I.lightbulb, M + 0.35, 1.8, 0.6, C.accent1, "learned");
  text(s, "Learned", { x: M + 1.15, y: 1.88, w: 4, h: 0.45, fontSize: 22, bold: true });
  [["Design the product and the cell together.", " One plank and straight-down assembly made a one-jig cell possible."],
   ["Fail in software first.", " Trapped guide, flip clearance, arm through the bench: all found before the lab."],
   ["Simulation and real robot from one program.", " What we tune on the robot goes straight back into the model."]].forEach((l, i) =>
    text(s, l[0].replace(/\.$/, ""), { x: M + 0.35, y: 2.7 + i * 1.1, w: colw - 0.7, h: 0.8, fontSize: 19, bold: true, color: C.text1 }));
  const nx = M + colw + 0.4;
  iconDot(s, I.forward, nx + 0.35, 1.8, 0.6, C.accent2, "next");
  text(s, "Next", { x: nx + 1.15, y: 1.88, w: 4, h: 0.45, fontSize: 22, bold: true });
  [["Full cycle on the real robot,", " with the measured assembly time."],
   ["New guide split,", " so the guide slides out of the finished bench without force."],
   ["Two benches stacked on the AMR", " for compact delivery, and AMR docking."]].forEach((l, i) =>
    text(s, l[0].replace(/,$/, ""), { x: nx + 0.35, y: 2.7 + i * 1.1, w: colw - 0.7, h: 0.8, fontSize: 19, bold: true, color: C.text1 }));
  s.addNotes("Suggested speaker: both. John Isak takes 'learned', Bjørge 'next'.\n\n" +
    "Three lessons: design product and cell together; fail in software first, it is cheap; and keep the simulation and the robot on one program so tuning on the robot flows back into the model. Next: the full cycle on the real robot with a measured time, the new guide split so the guide comes out without force, and stacking two benches on the AMR.");

  // ============ 11. Thank you
  s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Closing" });
  s.addText("Thank you. Questions?", { placeholder: "title" });
  s.addText([{ text: "Configure a bench yourself:", options: { breakLine: true } }, { text: SITE, options: { color: C.accent3 } }], { placeholder: "body" });
  text(s, "Bjørge Skjelbreid Djuve · John Isak Hammer", { x: M, y: 5.75, w: 7, h: 0.35, fontSize: 16, bold: true, color: C.background1 });
  text(s, "MMA4002 · NTNU Ålesund", { x: M, y: 6.15, w: 4.6, h: 0.35, fontSize: 14, color: C.accent5 });
  qr(s, 5.85, 5.0, 1.65);
  cadBench(s, 8.15, 0.95, 5.6, "dark");
  s.addNotes("Suggested speaker: both.\n\nOpen for questions. If there is time: the configurator live, or the simulator running a full bench.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
