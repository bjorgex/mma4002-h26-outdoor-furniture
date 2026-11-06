// Manipulability layers for the mock's 3D cell view (sim_view.html at /sim/, sim_scene.js in /all).
//   import("/sim/manip_layers.js").then(m => m.addManipLayers({ THREE, scene, camera, joints, el, base: "/sim/", tip: 160 }))
// Data: /sim/manip_data.json, written by manipulability.py ("python tests/robot_sim/manipulability.py all").
// Every layer is switched on its own in the small "Manipulability" panel (bottom left of the 3D pane); the choice
// is kept in localStorage. Layers:
//   heat planes   horizontal planes at chosen TCP heights (cell/plate frame): mu1 with the tool's orientation held
//                 (tool pointing down, or the best of 8 tool directions), same colours as manipulability.html
//   slice         the vertical slice through the J1 axis (optionally turned with the robot's J1)
//   danger        the mu1 = 3 iso-surface (tool down) as a translucent red volume
//   live          mu1 / mu3 / joint-limit margin of the CURRENT joints every frame (gauge), TCP marker coloured
//                 green -> yellow -> red, and the live velocity ellipsoid at the TCP
//   path          the program's TCP path coloured by mu1 per target, flagged targets red with labels; hover = details
// Maths as in manipulability.py (Modern Robotics 5.4): A = J J^T, mu1 = sqrt(lmax/lmin), mu3 = sqrt(det A).
// "Held" = linear TCP velocity with the orientation held: v^T (C^T C) v <= 1, C = the v-columns of J^-1.

const KEY = "manipLayers.v2";
const DEF = { open: true, planes: true, heights: "50", slice: false, sliceFollow: true, unreach: false,
              iso: false, gauge: true, tcp: true, ell: false, ellKind: "fix", path: true, labels: true, prog: "auto",
              variant: "down", thr: 3, ellScale: 150 };
const LIMITS = [[-270, 270], [-180, 180], [-155, 155], [-180, 180], [-180, 180], [-270, 270]];
const VIRIDIS = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#fde725"];

function load() {                         // saved choice; ?manip=slice,iso,ell,-planes in the page URL turns layers on/off
  let st;
  try { st = { ...DEF, ...JSON.parse(localStorage.getItem(KEY) || "{}") }; } catch (e) { st = { ...DEF }; }
  for (const k of (new URLSearchParams(location.search).get("manip") || "").split(",").filter(Boolean))
    if (k.replace("-", "") in DEF) st[k.replace("-", "")] = !k.startsWith("-");
  return st;
}
function save(st) { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* private window */ } }

// ---- small linear algebra (plain arrays) ----------------------------------------------------------------
function solve(A, B) {                     // A (n x n) X = B (n x m), Gaussian elimination; null if singular
  const n = A.length, m = B[0].length, M = A.map((r, i) => [...r, ...B[i]]);
  const scale = Math.max(...A.flat().map(Math.abs)) || 1;
  for (let c = 0; c < n; c++) {
    let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    if (Math.abs(M[p][c]) < 1e-12 * scale) return null;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k < n + m; k++) M[r][k] -= f * M[c][k]; }
  }
  return M.map((r, i) => r.slice(n).map(v => v / M[i][i]));
}
function jacobi3(S) {                      // symmetric 3x3 -> { val: [3] ascending, vec: columns as [3][3] }
  const a = S.map(r => r.slice()), v = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let sweep = 0; sweep < 12; sweep++) {
    let off = 0; for (const [p, q] of [[0, 1], [0, 2], [1, 2]]) off += a[p][q] * a[p][q];
    if (off < 1e-30) break;
    for (const [p, q] of [[0, 1], [0, 2], [1, 2]]) {
      if (Math.abs(a[p][q]) < 1e-300) continue;
      const th = (a[q][q] - a[p][p]) / (2 * a[p][q]), t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1));
      const c = 1 / Math.sqrt(t * t + 1), s = t * c;
      for (let k = 0; k < 3; k++) { const akp = a[k][p], akq = a[k][q]; a[k][p] = c * akp - s * akq; a[k][q] = s * akp + c * akq; }
      for (let k = 0; k < 3; k++) { const apk = a[p][k], aqk = a[q][k]; a[p][k] = c * apk - s * aqk; a[q][k] = s * apk + c * aqk; }
      for (let k = 0; k < 3; k++) { const vkp = v[k][p], vkq = v[k][q]; v[k][p] = c * vkp - s * vkq; v[k][q] = s * vkp + c * vkq; }
    }
  }
  const idx = [0, 1, 2].sort((i, j) => a[i][i] - a[j][j]);
  return { val: idx.map(i => a[i][i]), vec: idx.map(i => [v[0][i], v[1][i], v[2][i]]) };
}
const mul3 = (A, B) => A.map(r => B[0].map((_, j) => r.reduce((s, x, k) => s + x * B[k][j], 0)));
const T = M => M[0].map((_, j) => M.map(r => r[j]));

// ---- measures for the current pose, from the joint groups' world matrices --------------------------------
export function measuresFrom(THREE, joints, tip) {
  joints[5].updateWorldMatrix(true, false);
  const e = new THREE.Vector3(), o = new THREE.Vector3(), z = new THREE.Vector3();
  const p = new THREE.Vector3(0, 0, tip).applyMatrix4(joints[5].matrixWorld);       // TCP (robot base frame, mm)
  const J = [[], [], [], [], [], []];                                               // rows v (m/rad), w
  joints.forEach((g, i) => {
    o.setFromMatrixPosition(g.matrixWorld); z.setFromMatrixColumn(g.matrixWorld, 2).normalize();
    e.copy(z).cross(p.clone().sub(o));                                              // w x (p - o)
    J[0][i] = e.x / 1000; J[1][i] = e.y / 1000; J[2][i] = e.z / 1000; J[3][i] = z.x; J[4][i] = z.y; J[5][i] = z.z;
  });
  const Jv = J.slice(0, 3), Av = mul3(Jv, T(Jv)), ev = jacobi3(Av);
  const out = { p, Av, ev, mu1_v: Math.sqrt(Math.max(ev.val[2], 0) / Math.max(ev.val[0], 1e-30)),
                mu3_v: Math.sqrt(Math.max(ev.val[0] * ev.val[1] * ev.val[2], 0)) };
  const C = solve(J, [0, 1, 2, 3, 4, 5].map(r => [0, 1, 2].map(c => (r === c ? 1 : 0))));   // J^-1 [I; 0]
  if (C) {
    const M = mul3(T(C), C), em = jacobi3(M);                                        // M = A_fix^-1
    out.mu1 = Math.sqrt(Math.max(em.val[2], 0) / Math.max(em.val[0], 1e-30));
    out.mu3 = 1 / Math.sqrt(Math.max(em.val[0] * em.val[1] * em.val[2], 1e-30));
    out.efix = { val: em.val.map(l => 1 / Math.max(l, 1e-30)), vec: em.vec };       // A_fix = M^-1
  } else { out.mu1 = Infinity; out.mu3 = 0; out.efix = null; }
  const q = joints.map(g => g.rotation.z * 180 / Math.PI);
  let mj = 0, mm = Infinity;
  q.forEach((a, i) => { const m = Math.min(a - LIMITS[i][0], LIMITS[i][1] - a); if (m < mm) { mm = m; mj = i; } });
  out.margin = mm; out.marginJ = mj + 1; out.q = q;
  return out;
}

// ---- colours ---------------------------------------------------------------------------------------------
function viridis(t) {                      // t 0..1 -> [r, g, b] 0..255
  t = Math.min(1, Math.max(0, t)) * (VIRIDIS.length - 1);
  const i = Math.min(VIRIDIS.length - 2, Math.floor(t)), f = t - i;
  const c = k => parseInt(VIRIDIS[k].slice(1), 16), a = c(i), b = c(i + 1);
  return [16, 8, 0].map(s => Math.round(((a >> s) & 255) * (1 - f) + ((b >> s) & 255) * f));
}
function muColor(lg, thr) {                // log10 mu1 -> rgb, plotly page's scale: 1 .. thr*2.24, reversed viridis
  const top = Math.log10(Math.max(thr, 1.05)) + 0.35;
  return viridis(1 - lg / top);
}
function traffic(mu, thr) {                // green (round) -> yellow -> red (>= thr): for the TCP marker and gauge
  const t = Math.min(1, Math.max(0, Math.log(mu) / Math.log(Math.max(thr, 1.05))));
  return t < 0.5 ? [Math.round(60 + 390 * t), 200, 70] : [255, Math.round(200 - 340 * (t - 0.5)), 50];
}
const css = c => `rgb(${c[0]},${c[1]},${c[2]})`;

// ---- the layers ------------------------------------------------------------------------------------------
export async function addManipLayers({ THREE, scene, camera = null, joints, el, base = "/sim/", tip = 160, log = () => {} }) {
  let r = await fetch(base + "manip_data.json", { cache: "no-cache" });         // /sim/ (sim_http.FILES)
  if (!r.ok) r = await fetch(base + "manipulability/manip_data.json", { cache: "no-cache" });   // a plain file server
  if (!r.ok) throw new Error("manip_data.json: HTTP " + r.status + " (run manipulability.py all)");
  const D = await r.json();
  const st = load();
  const S = D.slice.s, Z = D.slice.z, NS = S.length, NZ = Z.length, STEP = D.step;
  const G = new THREE.Matrix4().set(...D.G.flat());                 // cell (plate) frame -> robot base frame
  const g = D.G, cellToRobot = ([x, y, h]) => [0, 1, 2].map(i => g[i][0] * x + g[i][1] * y + g[i][2] * h + g[i][3]);
  const root = new THREE.Group(); root.name = "manipulability"; scene.add(root);
  const cellG = new THREE.Group(); cellG.matrixAutoUpdate = false; cellG.matrix.copy(G); root.add(cellG);

  // heat planes
  const planes = new THREE.Group(); cellG.add(planes);
  const B = D.base, XS = [], YS = [];
  for (let x = Math.floor(B[0] - 1000); x <= B[0] + 1000; x += STEP) XS.push(x);
  for (let y = Math.floor(B[1] - 1000); y <= B[1] + 1000; y += STEP) YS.push(y);
  const mu1Key = "mu1_vfix";
  function pix(sl, c, img, k) {             // one texel: colour by mu1 held, red above thr, grey/clear unreachable
    const s = c < 0 ? 0 : sl.status[c], v = s === 1 ? sl[mu1Key][c] : null;
    if (v === null || v === undefined) {
      const grey = st.unreach && s !== 1;
      img[k] = img[k + 1] = img[k + 2] = s === 2 ? 200 : 140; img[k + 3] = grey ? 110 : 0; return;
    }
    let col = muColor(v, st.thr);
    if (Math.pow(10, v) > st.thr) col = [255, 40, 40];
    img[k] = col[0]; img[k + 1] = col[1]; img[k + 2] = col[2]; img[k + 3] = 140;
  }
  function texFrom(w, h, fill) {
    const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    const ctx = cv.getContext("2d"), im = ctx.createImageData(w, h);
    fill(im.data); ctx.putImageData(im, 0, 0);
    const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.minFilter = THREE.LinearFilter;
    t.colorSpace = THREE.SRGBColorSpace; return t;
  }
  const matFor = tex => new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide, depthWrite: false });
  function buildPlanes() {
    planes.children.slice().forEach(m => { m.removeFromParent(); m.geometry.dispose(); m.material.map.dispose(); m.material.dispose(); });
    if (!st.planes) return;
    const sl = D.slice.data[st.variant] || D.slice.data.down;
    for (const h of st.heights.split(",").map(Number).filter(v => isFinite(v))) {
      const tex = texFrom(XS.length, YS.length, img => {
        YS.forEach((y, r) => XS.forEach((x, cI) => {
          const p = cellToRobot([x, y, h]);
          const j = Math.round((Math.hypot(p[0], p[1]) - S[0]) / STEP), i = Math.round((p[2] - Z[0]) / STEP);
          const c = j < 0 || j >= NS || i < 0 || i >= NZ ? -1 : i * NS + j;
          pix(sl, c, img, ((YS.length - 1 - r) * XS.length + cI) * 4);
        }));
      });
      const w = XS[XS.length - 1] - XS[0] + STEP, hh = YS[YS.length - 1] - YS[0] + STEP;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, hh), matFor(tex));
      m.position.set((XS[0] + XS[XS.length - 1]) / 2, (YS[0] + YS[YS.length - 1]) / 2, h);
      m.renderOrder = 2; m.name = "mu1 plane z" + h; planes.add(m);
    }
  }

  // vertical slice (robot base frame, turned about J1)
  const sliceG = new THREE.Group(); root.add(sliceG);
  function buildSlice() {
    sliceG.children.slice().forEach(m => { m.removeFromParent(); m.geometry.dispose(); m.material.map.dispose(); m.material.dispose(); });
    if (!st.slice) return;
    const sl = D.slice.data[st.variant] || D.slice.data.down;
    const tex = texFrom(NS, NZ, img => { for (let i = 0; i < NZ; i++) for (let j = 0; j < NS; j++) pix(sl, i * NS + j, img, ((NZ - 1 - i) * NS + j) * 4); });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(S[NS - 1] - S[0] + STEP, Z[NZ - 1] - Z[0] + STEP), matFor(tex));
    m.rotation.x = Math.PI / 2; m.position.set((S[0] + S[NS - 1]) / 2, 0, (Z[0] + Z[NZ - 1]) / 2); m.renderOrder = 2;
    sliceG.add(m);
    sliceG.rotation.z = D.slice_az * Math.PI / 180;
  }

  // danger volume: mu1 (held) = thr iso-surface, tool down (cell frame, from manip_data.json = iso_*.glb)
  let iso = null;
  if (D.iso.v.length) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(D.iso.v, 3));
    geo.setIndex(D.iso.f); geo.computeVertexNormals();
    iso = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0xe02020, transparent: true, opacity: 0.16,
      side: THREE.DoubleSide, depthWrite: false, roughness: 0.8 }));
    iso.renderOrder = 3; iso.name = `${D.iso_key} = ${D.thr} (tool down)`; cellG.add(iso);
  }

  // live: TCP marker + ellipsoid
  const tcpMat = new THREE.MeshBasicMaterial({ color: 0x33cc55 });
  const tcp = new THREE.Mesh(new THREE.SphereGeometry(13, 20, 14), tcpMat);
  tcp.position.set(0, 0, tip); joints[5].add(tcp);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(60, 5, 8, 40), tcpMat); ring.position.set(0, 0, 60); joints[5].add(ring);
  const ell = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 18), new THREE.MeshBasicMaterial({ color: 0x2f6fde, wireframe: true,
    transparent: true, opacity: 0.55 }));
  ell.matrixAutoUpdate = false; root.add(ell);

  // path of the program
  const pathG = new THREE.Group(); cellG.add(pathG);
  const pickables = [];
  function label(text, color) {
    const cv = document.createElement("canvas"), ctx = cv.getContext("2d"), f = 26;
    ctx.font = `600 ${f}px system-ui, sans-serif`;
    cv.width = Math.ceil(ctx.measureText(text).width) + 16; cv.height = f + 14;
    ctx.font = `600 ${f}px system-ui, sans-serif`;
    ctx.fillStyle = "rgba(255,255,255,0.88)"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = color; ctx.fillText(text, 8, f + 2);
    const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true }));
    s.scale.set(cv.width * 0.42, cv.height * 0.42, 1); s.renderOrder = 10; return s;
  }
  let curProg = null, cellName = null;
  const progFor = cell => {
    const want = { cell: "v4", cell_v5: "v5", cell_v6: "v6", cell_v8: "v8" }[cell || "cell"] || "";
    const ks = Object.keys(D.programs);
    return ks.find(k => k.endsWith(" " + want)) || ks[ks.length - 1];
  };
  function buildPath() {
    pathG.children.slice().forEach(o => { o.removeFromParent(); o.traverse(c => { c.geometry?.dispose(); c.material?.map?.dispose(); c.material?.dispose(); }); });
    pickables.length = 0;
    curProg = st.prog === "auto" ? progFor(cellName) : st.prog;
    const P = D.programs[curProg];
    if (!st.path || !P || !P.length) return;
    const pos = [], col = [];
    P.forEach(t => { pos.push(...t.p); const c = muColor(Math.log10(Math.max(t.mu1_vfix, 1)), st.thr); col.push(...c.map(v => v / 255)); });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    pathG.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ vertexColors: true, depthTest: false, transparent: true })));
    const dotGeo = new THREE.SphereGeometry(7, 10, 8), seen = new Set();
    P.forEach(t => {
      const bad = t.mu1_vfix > st.thr || t.mu1_full > D.full_thr || t.margin < D.limit_warn;
      const m = new THREE.Mesh(dotGeo, new THREE.MeshBasicMaterial({ color: bad ? 0xff2020 : 0x2f6fde, depthTest: false, transparent: true }));
      m.position.set(...t.p); m.scale.setScalar(bad ? 1.6 : 0.8); m.renderOrder = 9; m.userData.t = t; pathG.add(m); pickables.push(m);
      const key = t.p.map(v => Math.round(v / 40)).join(",");           // one label per ~40 mm spot
      if (bad && st.labels && !seen.has(key)) {
        seen.add(key);
        const s = label(`#${t.i} ${t.name}  μ1 ${t.mu1_vfix}`, "#c01010");
        s.position.set(t.p[0], t.p[1], t.p[2] + 25); s.center.set(0, 0); pathG.add(s);
      }
    });
  }

  // ---- panel ---------------------------------------------------------------------------------------------
  if (getComputedStyle(el).position === "static") el.style.position = "relative";
  const box = document.createElement("div");
  box.style.cssText = "position:absolute;left:10px;bottom:10px;z-index:5;width:265px;max-height:calc(100% - 20px);overflow:auto;" +
    "background:#ffffffeb;color:#222;border:1px solid #ccc;border-radius:8px;padding:8px 10px;font:12px/1.35 system-ui,sans-serif;";
  const progOpts = ["auto", ...Object.keys(D.programs)].map(k => `<option value="${k}">${k === "auto" ? "auto (the cell shown)" : k}</option>`).join("");
  box.className = "manip-panel";
  box.innerHTML = `<style>.manip-panel label{display:block;margin:1px 0}.manip-panel input{vertical-align:middle}</style>
    <div style="display:flex;justify-content:space-between;align-items:center;cursor:pointer" data-k="toggle">
      <b>Manipulability</b><span data-k="arrow">▾</span></div>
    <div data-k="gaugebox" style="margin:6px 0 2px">
      <div style="position:relative;height:12px;border-radius:6px;background:linear-gradient(90deg,#3cc846,#ffd23a 45%,#ff3232 66.7%,#900000)">
        <div data-k="needle" style="position:absolute;top:-3px;width:3px;height:18px;background:#111;left:0"></div></div>
      <div data-k="readout" style="font:11px ui-monospace,Consolas,monospace;margin-top:3px">–</div></div>
    <div data-k="body">
      <label><input type="checkbox" data-s="gauge"> live gauge (current joints)</label>
      <label><input type="checkbox" data-s="tcp"> colour the TCP marker</label>
      <label><input type="checkbox" data-s="ell"> live velocity ellipsoid</label>
      <div style="margin-left:18px"><label><input type="radio" name="mlEll" value="fix"> orientation held</label>
        <label><input type="radio" name="mlEll" value="v"> J<sub>v</sub></label>
        <label>scale <input type="range" data-s="ellScale" min="40" max="400" step="10" style="width:90px"></label></div>
      <hr style="border:0;border-top:1px solid #ddd">
      <label><input type="checkbox" data-s="planes"> heat planes at z (plate) <input type="text" data-s="heights" style="width:95px;font:inherit"></label>
      <label><input type="checkbox" data-s="slice"> vertical slice through the base</label>
      <label style="margin-left:18px"><input type="checkbox" data-s="sliceFollow"> turns with J1</label>
      <label><input type="checkbox" data-s="unreach"> show unreachable (grey)</label>
      <label>tool <select data-s="variant"><option value="down">pointing down</option><option value="best">best of 8 directions</option></select></label>
      <label><input type="checkbox" data-s="iso"> danger volume (μ1 = ${D.thr}, tool down)</label>
      <hr style="border:0;border-top:1px solid #ddd">
      <label><input type="checkbox" data-s="path"> program path, coloured by μ1</label>
      <label style="margin-left:18px"><input type="checkbox" data-s="labels"> labels on flagged targets</label>
      <select data-s="prog" style="width:100%;font:inherit">${progOpts}</select>
      <label>μ1 threshold <b data-k="thrv"></b><input type="range" data-s="thr" min="1.5" max="10" step="0.1" style="width:100%"></label>
      <div style="color:#666;font-size:11px">μ1 = √(λmax/λmin) of A = J J<sup>T</sup> with the tool's orientation held (1 = round, ∞ = singular);
        colours: yellow good → purple poor, red above the threshold. Planes and slice: grid ${STEP} mm, cell ${D.cell} frame.</div>
    </div>
    <div data-k="tip" style="display:none;position:fixed;z-index:20;background:#fff;border:1px solid #999;border-radius:5px;padding:4px 6px;font:11px ui-monospace,Consolas,monospace;pointer-events:none;white-space:pre"></div>`;
  el.appendChild(box);
  const q = k => box.querySelector(`[data-k="${k}"]`);
  box.querySelectorAll("[data-s]").forEach(inp => {
    const k = inp.dataset.s;
    if (inp.type === "checkbox") inp.checked = !!st[k]; else inp.value = st[k];
    inp.addEventListener(inp.type === "text" ? "change" : "input", () => {
      st[k] = inp.type === "checkbox" ? inp.checked : inp.type === "range" ? +inp.value : inp.value; save(st); apply(k);
    });
  });
  box.querySelectorAll('input[name="mlEll"]').forEach(r => { r.checked = r.value === st.ellKind;
    r.onchange = () => { st.ellKind = r.value; save(st); }; });
  q("toggle").onclick = () => { st.open = !st.open; save(st); apply("open"); };
  // stop orbit controls from reacting to the panel
  ["pointerdown", "wheel"].forEach(t => box.addEventListener(t, e => e.stopPropagation()));

  function apply(k) {
    q("body").style.display = st.open ? "" : "none"; q("arrow").textContent = st.open ? "▾" : "▸";
    q("thrv").textContent = st.thr.toFixed(1);
    if (["planes", "heights", "variant", "thr", "unreach", undefined].includes(k)) buildPlanes();
    if (["slice", "variant", "thr", "unreach", undefined].includes(k)) buildSlice();
    if (["path", "labels", "prog", "thr", undefined].includes(k)) buildPath();
    if (iso) iso.visible = st.iso;
    q("gaugebox").style.display = st.gauge ? "" : "none";
    tcp.visible = ring.visible = st.tcp; ell.visible = st.ell;
  }
  apply();

  // hover / click on the path's targets
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2(), tipEl = q("tip");
  function pick(ev, sticky) {
    if (!camera || !pickables.length || !st.path) return;
    const cv = el.querySelector("canvas"), r = cv.getBoundingClientRect();
    mouse.set((ev.clientX - r.left) / r.width * 2 - 1, -(ev.clientY - r.top) / r.height * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(pickables, false)[0];
    if (!hit) { if (!sticky) tipEl.style.display = "none"; return; }
    const t = hit.object.userData.t;
    tipEl.textContent = `${curProg}  #${t.i} ${t.name} (stage ${t.stage})\nμ1 held ${t.mu1_vfix}   μ1 J_v ${t.mu1_v}   μ1 6x6 ${t.mu1_full}\n` +
      `μ3 J_v ${t.mu3_v} (m/s)³   joint margin ${t.margin}°${t.flag ? "   FLAGGED" : ""}`;
    tipEl.style.left = ev.clientX + 14 + "px"; tipEl.style.top = ev.clientY + 10 + "px"; tipEl.style.display = "block";
  }
  el.addEventListener("pointermove", e => pick(e, false));
  el.addEventListener("click", e => pick(e, true));

  // per-frame: live measures (cheap: one 6x6 solve, two 3x3 eigen)
  const basis = new THREE.Matrix4(), az = new THREE.Vector3();
  let last = null, tLog = 0;
  function frame() {
    requestAnimationFrame(frame);
    if (!st.gauge && !st.tcp && !st.ell && !(st.slice && st.sliceFollow)) return;
    const m = measuresFrom(THREE, joints, tip); last = m;
    if (st.tcp) { const c = traffic(m.mu1, st.thr); tcpMat.color.setRGB(c[0] / 255, c[1] / 255, c[2] / 255, THREE.SRGBColorSpace); }
    if (st.gauge) {
      const t = Math.min(1, Math.max(0, Math.log(Math.max(m.mu1, 1)) / (1.5 * Math.log(Math.max(st.thr, 1.05)))));   // thr at 2/3
      q("needle").style.left = `calc(${(t * 100).toFixed(1)}% - 1px)`;
      const warn = m.margin < D.limit_warn ? "  ⚠" : "";
      q("readout").innerHTML = `μ1 held <b style="color:${css(traffic(m.mu1, st.thr))};text-shadow:0 0 1px #000">${isFinite(m.mu1) ? m.mu1.toFixed(2) : "∞"}</b>` +
        `  μ1 J<sub>v</sub> ${m.mu1_v.toFixed(2)}<br>μ3 held ${m.mu3.toFixed(4)} (m/s)³<br>` +
        `limit margin ${m.margin.toFixed(1)}° (J${m.marginJ})${warn}`;
    }
    if (st.ell) {
      const E = st.ellKind === "fix" && m.efix ? m.efix : m.ev, sc = st.ellScale;   // mm drawn per 1 m/s
      const ax = E.vec.map((v, k) => new THREE.Vector3(...v).multiplyScalar(Math.sqrt(Math.max(E.val[k], 0)) * sc));
      basis.makeBasis(ax[0], ax[1], ax[2]).setPosition(m.p); ell.matrix.copy(basis);
      ell.material.color.set(st.ellKind === "fix" ? 0xd04a1a : 0x2f6fde);
    }
    if (st.slice && st.sliceFollow) {               // turn the slice with J1: face the TCP's azimuth
      az.copy(m.p); if (Math.hypot(az.x, az.y) > 1) sliceG.rotation.z = Math.atan2(az.y, az.x);
    } else sliceG.rotation.z = D.slice_az * Math.PI / 180;
    if (!isFinite(m.mu1) && performance.now() - tLog > 5000) { tLog = performance.now(); log("err", "manipulability: singular pose (μ1 = ∞)"); }
  }
  frame();

  return {
    setCell(cell) { cellName = cell || "cell"; if (st.prog === "auto") buildPath(); },
    get live() { return last; }, state: st, data: D,
  };
}
