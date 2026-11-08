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
const DEF = { open: true, more: false, planes: true, heights: "50", slice: false, sliceFollow: true, unreach: false,
              iso: false, gauge: true, tcp: true, ell: false, ellKind: "fix", path: true, labels: true, prog: "auto",
              variant: "down", thr: 3, ellScale: 150 };
const LIMITS = [[-270, 270], [-180, 180], [-155, 155], [-180, 180], [-180, 180], [-270, 270]];
const VIRIDIS = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#fde725"];

// fixed (2026-11-07, panel simplified): orientation held, the program of the chosen preset, tool pointing down,
// map at 50 mm, no vertical slice, unreachable = transparent. Not in the panel any more; old saved values are ignored.
const FIXED = { ellKind: "fix", prog: "auto", variant: "down", heights: "50", slice: false, sliceFollow: true, unreach: false };
function load() {                         // saved choice; ?manip=slice,iso,ell,-planes in the page URL turns layers on/off
  let st;
  try { st = { ...DEF, ...JSON.parse(localStorage.getItem(KEY) || "{}"), ...FIXED }; } catch (e) { st = { ...DEF, ...FIXED }; }
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
export async function addManipLayers({ THREE, scene, camera = null, joints, el, base = "/sim/", tip = 160, log = () => {},
                                        setPreview = null, previewApi = null }) {
  let r = await fetch(base + "manip_data.json", { cache: "no-cache" });         // /sim/ (sim_http.FILES)
  if (!r.ok) r = await fetch(base + "manipulability/manip_data.json", { cache: "no-cache" });   // a plain file server
  if (!r.ok) throw new Error("manip_data.json: HTTP " + r.status + " (run manipulability.py all)");
  let D = await r.json();                          // let: reloaded after an Adjust-step Save
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
    const want = { cell: "v4", cell_v5: "v5", cell_v6: "v6", cell_v8: "v8", cell_v8x2: "v8x2", cell_v9: "v9", cell_v9x2: "v9x2" }[cell || "cell"] || "";
    const ks = Object.keys(D.programs);
    return ks.find(k => k.endsWith(" " + want)) || ks[ks.length - 1];
  };
  function buildPath() {
    pathG.children.slice().forEach(o => { o.removeFromParent(); o.traverse(c => { c.geometry?.dispose(); c.material?.map?.dispose(); c.material?.dispose(); }); });
    pickables.length = 0; pathP = []; pathItems = [];
    curProg = st.prog === "auto" ? progFor(cellName) : st.prog;
    const P = D.programs[curProg];
    progP = P || [];                              // the program's points, for "Move robot" / the timeline (any layer)
    const mr = mq("moveR"); mr.max = Math.max(0, progP.length - 1);
    if (+mr.value > progP.length - 1) mr.value = 0;
    buildTimeline();
    if (previewOn) moveTo(+mr.value);
    if (!st.path || !P || !P.length) return;
    const pos = [], col = [];
    P.forEach(t => { pos.push(...t.p); const c = muColor(Math.log10(Math.max(t.mu1_vfix, 1)), st.thr); col.push(...c.map(v => v / 255)); });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    pathLine = new THREE.Line(geo, new THREE.LineBasicMaterial({ vertexColors: true, depthTest: false, transparent: true }));
    pathG.add(pathLine);
    const dotGeo = new THREE.SphereGeometry(7, 10, 8), seen = new Set();
    const gripGeo = new THREE.SphereGeometry(11, 14, 10), ringGeo = new THREE.TorusGeometry(12, 3.5, 8, 24);
    pathItems = P.map(() => []);                  // per point: its meshes/labels, for the step slider
    P.forEach((t, n) => {
      const bad = t.mu1_vfix > st.thr || t.mu1_full > D.full_thr || t.margin < D.limit_warn;
      const m = new THREE.Mesh(dotGeo, new THREE.MeshBasicMaterial({ color: bad ? 0xff2020 : 0x2f6fde, depthTest: false, transparent: true }));
      m.position.set(...t.p); m.scale.setScalar(bad ? 1.6 : 0.8); m.renderOrder = 9; m.userData.t = t; pathG.add(m); pickables.push(m);
      pathItems[n].push(m);
      if (t.grip) {                               // where the gripper closes (solid) / opens (ring)
        const g = new THREE.Mesh(t.grip === "grip" ? gripGeo : ringGeo,
          new THREE.MeshBasicMaterial({ color: t.grip === "grip" ? 0x0f9d3a : 0x5fd67a, depthTest: false, transparent: true }));
        g.position.set(t.p[0], t.p[1], t.p[2] + 16); g.renderOrder = 10; g.userData.t = t; pathG.add(g); pickables.push(g);
        pathItems[n].push(g);
      }
      const key = t.p.map(v => Math.round(v / 40)).join(",");           // one label per ~40 mm spot
      if (bad && st.labels && !seen.has(key)) {
        seen.add(key);
        const s = label(`#${t.i} ${t.name}  μ1 ${t.mu1_vfix}`, "#c01010");
        s.position.set(t.p[0], t.p[1], t.p[2] + 25); s.center.set(0, 0); pathG.add(s);
        pathItems[n].push(s);
      }
    });
    curMark = new THREE.Mesh(new THREE.TorusGeometry(18, 3, 8, 32),
      new THREE.MeshBasicMaterial({ color: 0x111111, depthTest: false, transparent: true }));
    curMark.renderOrder = 11; pathG.add(curMark);
    pathP = P;
    const r = q("stepR");
    r.max = P.length - 1;
    if (stepAt === null || stepAt > P.length - 1) stepAt = P.length - 1;
    r.value = stepAt; showUpTo(stepAt);
  }
  // "move the robot": the 3D arm to point s of the path (fractional = joint-interpolated between two points),
  // gripper closed between a GRIP and the next RELEASE. Only the 3D view: nothing is sent to any robot.
  let previewOn = false;
  function moveTo(s) {
    if (!progP.length || !progP[0].q) return;
    const k = Math.min(Math.floor(s), progP.length - 1), f = s - k, a = progP[k], b = progP[Math.min(k + 1, progP.length - 1)];
    let info;
    if (previewApi) info = previewApi.path(progP, s);                 // arm + parts (GRIP/RELEASE replayed)
    if (!info) {                                                      // older 3D view: the arm only
      if (!setPreview) return;
      let closed = false;
      for (let n = 0; n <= k; n++) if (progP[n].grip) closed = progP[n].grip === "grip";
      setPreview(a.q.map((v, j) => v + (b.q[j] - v) * f), closed); info = { closed, carrying: [] };
    }
    previewOn = true;
    mq("liveB").style.display = ""; mq("liveB").style.visibility = "visible";
    mq("moveV").textContent = `${k + 1}${f > 0.01 ? "→" + Math.min(k + 2, progP.length) : ""} / ${progP.length}`;
    const gr = a.grip ? ` - ${a.grip === "grip" ? "GRIP" : "RELEASE"}` : "";
    mq("moveName").textContent = `#${a.i} ${a.name}${gr}${f > 0.01 ? "  →  " + b.name : ""}  (gripper ` +
      (info.closed ? `closed${info.carrying.length ? ", carrying " + info.carrying.join(", ") : ""}` : "open") + ")" +
      (info.missing && info.missing.length ? `  !! not in the 3D cell (${info.cell}): ${info.missing.join(", ")}` : "");
    mq("moveName").title = mq("moveName").textContent;
  }
  function backToLive() {
    playing = false;
    if (previewApi) previewApi.end(); else if (setPreview) setPreview(null);
    previewOn = false; moveTarget = moveCur = null; showCatchUp(); setTimeout(notify);
    mq("liveB").style.visibility = "hidden"; mq("moveV").textContent = ""; mq("moveName").textContent = "";
  }
  // a running program: the slider follows it (move n = path point n - 1) while you are not dragging it yourself
  previewApi?.onMove(n => {
    if (previewOn || !progP.length) return;
    const k = Math.max(0, Math.min(n - 1, progP.length - 1));
    mq("moveR").value = k;
    mq("moveV").textContent = `${k + 1} / ${progP.length}`;
    mq("moveName").textContent = `running: #${progP[k].i} ${progP[k].name}`;
    if (mq("tl")) tlDraw();
  });
  let pathLine = null, pathItems = [], pathP = [], progP = [], curMark = null, stepAt = null;
  function showUpTo(k) {                          // the step slider: path, points and labels up to point k
    if (!pathP.length) return;
    stepAt = k;
    pathLine.geometry.setDrawRange(0, k + 1);
    pathItems.forEach((items, n) => items.forEach(o => { o.visible = n <= k; }));
    const t = pathP[k], all = k === pathP.length - 1;
    curMark.visible = !all; curMark.position.set(...t.p);
    const gr = t.grip ? ` - ${t.grip === "grip" ? "GRIP" : "RELEASE"} ${(t.grip_parts || []).join(", ")}` : "";
    q("stepv").textContent = all ? `all ${pathP.length}` : `${k + 1} / ${pathP.length}`;
    q("stepName").textContent = `#${t.i} ${t.name}${gr} (stage ${t.stage})`;
  }

  // ---- panel ---------------------------------------------------------------------------------------------
  if (getComputedStyle(el).position === "static") el.style.position = "relative";
  const box = document.createElement("div");
  box.style.cssText = "position:absolute;left:10px;top:10px;z-index:5;width:265px;max-height:calc(100% - 20px);overflow:auto;" +
    "background:#ffffffeb;color:#222;border:1px solid #ccc;border-radius:8px;padding:8px 10px;font:12px/1.35 system-ui,sans-serif;";
  box.className = "manip-panel";
  box.innerHTML = `<style>.manip-panel label{display:block;margin:1px 0}.manip-panel input{vertical-align:middle}
      .manip-panel .mi{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border-radius:50%;
        border:1.5px solid #3a6fd8;color:#3a6fd8;font:700 11px/1 Georgia,serif;font-style:italic;cursor:pointer;margin-left:6px;user-select:none}
      .manip-panel .mi:hover{background:#3a6fd8;color:#fff}
      .manip-panel .mhelp{display:none;margin:6px 0;padding:7px 8px;background:#f3f6fc;border:1px solid #d5dff2;border-radius:6px;font-size:11.5px;line-height:1.4}
      .manip-panel .mhelp p{margin:0 0 5px}.manip-panel .mhelp p:last-child{margin:0}
      .manip-panel .mmore{cursor:pointer;color:#3a6fd8;margin:6px 0 2px;user-select:none}</style>
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span><b style="cursor:pointer" data-k="toggle">Manipulability</b><span class="mi" data-k="info" title="What is this?">i</span></span>
      <span data-k="arrow" style="cursor:pointer">▾</span></div>
    <div class="mhelp" data-k="help">
      <p><b>What it shows:</b> how freely the arm can move the gripper in every direction from where it is.</p>
      <p><b>Arm freedom</b> (μ1): <b>1</b> = it moves equally easily in all directions. The bigger the number, the more one
        direction is hard or slow; near a <b>singular pose</b> (∞) the arm cannot move that way at all and joints spin fast.</p>
      <p><b>Colours:</b> green/yellow = good, orange = getting stiff, <b style="color:#d01010">red</b> = above the
        threshold (<span data-k="thrHelp"></span>) - avoid that spot or approach it differently.</p>
      <p><b>Joint limits:</b> degrees left before the closest joint hits its stop.</p>
      <p><b>Layers</b> (each has its own <b>i</b>): <i>Gripper path</i>, <i>Manipulability map</i> (a plane at a height above
        the plate), <i>Near-singular zone</i>. More settings: the velocity ellipsoid (how fast the gripper can move
        in each direction), labels, threshold.</p>
      <p style="color:#666">μ1 = √(λmax/λmin) of A = J J<sup>T</sup> with the tool's orientation held; grid ${STEP} mm,
        cell ${D.cell} frame (Modern Robotics 5.4).</p></div>
    <div data-k="gaugebox" style="margin:6px 0 2px">
      <div style="position:relative;height:12px;border-radius:6px;background:linear-gradient(90deg,#3cc846,#ffd23a 45%,#ff3232 66.7%,#900000)">
        <div data-k="needle" style="position:absolute;top:-3px;width:3px;height:18px;background:#111;left:0"></div></div>
      <div data-k="readout" style="margin-top:4px">–</div></div>
    <div data-k="body">
      <label><input type="checkbox" data-s="path"> Gripper path <span style="color:#777">(μ1 per point)</span><span class="mi" data-h="route">i</span></label>
      <div class="mhelp" data-hb="route">The path the program moves the gripper along, one point per move. The line's colour is
        how freely the arm can move there (μ1 at that pose). Green points: the gripper closes / opens. Use the slider to
        follow it step by step.</div>
      <div data-k="legend" style="margin:2px 0 4px 18px;font-size:11px;line-height:1.5;color:#333">
        <div><span style="display:inline-block;width:34px;height:6px;border-radius:3px;vertical-align:middle;
          background:linear-gradient(90deg,#fde725,#35b779,#31688e,#440154)"></span> line: arm freedom, good → stiff</div>
        <div><span style="color:#2f6fde">●</span> a target the robot moves to</div>
        <div><span style="color:#ff2020;font-size:13px">●</span> flagged: stiff or near a joint limit</div>
        <div><span style="color:#0f9d3a;font-size:13px">●</span> gripper closes (GRIP)
          &nbsp;<span style="color:#5fd67a;font-size:13px">○</span> opens (RELEASE)</div>
        <div style="color:#777">hover a point for details</div>
        <div style="margin-top:4px">step through the path: <b data-k="stepv"></b>
          <input type="range" data-k="stepR" min="0" max="0" step="1" style="width:100%">
          <div data-k="stepName" style="font-size:11px;color:#222;min-height:14px"></div></div></div>
      <label><input type="checkbox" data-s="planes"> Manipulability map μ1
        <span style="color:#777">(z = <span data-k="mapH"></span>, tool down)</span><span class="mi" data-h="map">i</span></label>
      <div class="mhelp" data-hb="map">A see-through sheet at that height. Each square: if the fingertips were here,
        gripper pointing down, how freely could the arm move? <b>Yellow/green</b> good, <b>blue → purple</b> stiffer,
        <b style="color:#d01010">red</b> too stiff (above the threshold), <b>clear</b> = can't reach. Use it to see where a
        jig should sit. It is a slice through the near-singular zone: green = inside its big ball and outside the
        saddle by the base, red = in the saddle or out by the reach limit. Method: μ1 = √(λmax/λmin) of A = J J<sup>T</sup> (velocity ellipsoid, orientation held), on a
        ${STEP} mm grid, 50 mm above the plate.</div>
      <label><input type="checkbox" data-s="iso"> Near-singular zone <span style="color:#777">(μ1 &gt; ${D.thr}, tool down)</span><span class="mi" data-h="iso">i</span></label>
      <div class="mhelp" data-hb="iso">A red see-through volume: everywhere the fingertips would be too stiff (μ1 above
        ${D.thr}) with the gripper pointing down - near the base, at full stretch, and near singular poses. Keep grips and
        places outside it. Three parts: the saddle by the base (gripper near the J1 axis: shoulder singularity), the
        smooth ball (arm stretching: elbow singularity on its way), the outer jagged ball (the reach limit, stepped by the
        ${STEP} mm grid). Work between the saddle and the smooth ball.</div>
      <div class="mmore" data-k="moreT">More settings ▸</div>
      <div data-k="more" style="display:none">
        <label><input type="checkbox" data-s="gauge"> live bar (current joints)</label>
        <label><input type="checkbox" data-s="tcp"> colour the gripper marker</label>
        <label><input type="checkbox" data-s="ell"> velocity ellipsoid <span style="color:#777">(long = fast that way)</span></label>
        <div style="margin-left:18px"><label>scale <input type="range" data-s="ellScale" min="40" max="400" step="10" style="width:90px"></label></div>
        <label><input type="checkbox" data-s="labels"> labels on flagged path points</label>
        <label>threshold μ1 <b data-k="thrv"></b><input type="range" data-s="thr" min="1.5" max="10" step="0.1" style="width:100%"></label>
      </div>
    </div>
    <div data-k="tip" style="display:none;position:fixed;z-index:20;background:#fff;border:1px solid #999;border-radius:5px;padding:4px 6px;font:11px ui-monospace,Consolas,monospace;pointer-events:none;white-space:pre"></div>`;
  el.appendChild(box);
  // "move the robot" slider: in the page header next to Run / Stop when the page has a #move-slot, else in this panel
  const slot = document.getElementById("move-slot");
  const moveBox = document.createElement("div");
  moveBox.className = "move-robot";
  moveBox.innerHTML = slot
    ? `<style>
         .move-robot { display: flex; flex-direction: column; gap: 2px; width: 100%; font: 12.5px var(--tm-font, system-ui); }
         .move-robot .tlhead { display: flex; gap: 10px; align-items: center; min-height: 22px; }
         .move-robot .tl { position: relative; height: 34px; border-radius: 4px; background: #ffffff14; cursor: grab;
           user-select: none; touch-action: none; outline: none; }
         .move-robot .tl:active { cursor: grabbing; } .move-robot .tl:focus-visible { box-shadow: 0 0 0 2px #ffd23a; }
         .move-robot .band { position: absolute; top: 0; height: 13px; border-radius: 2px; color: #fff; font-size: 10.5px;
           line-height: 13px; padding-left: 3px; overflow: hidden; white-space: nowrap; pointer-events: none; opacity: .9; }
         .move-robot .mk { position: absolute; width: 4px; margin-left: -2px; border-radius: 2px; pointer-events: none; }
         .move-robot .mk.g { top: 15px; height: 9px; background: #19c24a; } .move-robot .mk.r { top: 15px; height: 9px; background: #8ff0a8; }
         .move-robot .mk.f { top: 25px; height: 7px; background: #ff9a3a; } .move-robot .mk.c { top: 25px; height: 7px; background: #ff2b2b; width: 5px; }
         .move-robot .thumb { position: absolute; top: -2px; bottom: -2px; width: 4px; margin-left: -2px; background: #fff;
           border-radius: 2px; box-shadow: 0 0 4px #000a; pointer-events: none; }
         .move-robot .mghost { position: absolute; top: -3px; bottom: -3px; width: 3px; margin-left: -1.5px; border-radius: 2px;
           background: #ffd23a; box-shadow: 0 0 6px #ffd23a; pointer-events: none; display: none; }
         .move-robot.catching .thumb { animation: mpulse .7s ease-in-out infinite alternate; }
         @keyframes mpulse { from { box-shadow: 0 0 2px #ffd23a; } to { box-shadow: 0 0 10px 3px #ffd23a; } }
         .move-robot .hov { position: absolute; bottom: 38px; transform: translateX(-50%); background: #111d; color: #fff;
           padding: 1px 6px; border-radius: 3px; font-size: 11px; white-space: nowrap; pointer-events: none; display: none; z-index: 30; }
         .move-robot .key { opacity: .8; font-size: 11px; white-space: nowrap; }
         .move-robot .key i { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin: 0 3px 0 8px; vertical-align: middle; }
       </style>
       <div class="tlhead">
         <span class="slab" title="Moves the 3D robot (and the parts it grips) along the program, at most as fast as Robot speed allows. 3D only - nothing is sent to a robot.">Move robot</span>
         <button class="btn" data-k="prevB" title="One step back (at Robot speed)">◀ Step</button>
         <button class="btn" data-k="nextB" title="One step forward (at Robot speed)">Step ▶</button>
         <b data-k="moveV" style="width:70px;display:inline-block;white-space:nowrap"></b>
         <button class="btn" data-k="liveB" style="visibility:hidden;white-space:nowrap">● back to live</button>
         <span data-k="moveName" style="flex:1;min-width:0;opacity:.9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>
         <span class="key"><i style="background:#19c24a"></i>grip<i style="background:#8ff0a8"></i>release<i style="background:#ff9a3a"></i>stiff (μ1)<i style="background:#ff2b2b"></i>collision</span>
         <span data-k="tlTime" class="key"></span></div>
       <div class="tl" data-k="tl" tabindex="0" title="Click or drag to move the robot; arrow keys step; Home/End">
         <div data-k="tlMarks"></div><span class="mghost" data-k="ghost"></span><span class="thumb" data-k="thumb"></span>
         <span class="hov" data-k="hov"></span></div>
       <input type="range" data-k="moveR" min="0" max="0" step="0.02" hidden>`
    : `<div style="margin-top:6px;padding-top:5px;border-top:1px solid #ddd">move the robot <span style="color:#777">(3D preview only)</span>
         <b data-k="moveV"></b> <button data-k="liveB" style="font:inherit;font-size:11px;padding:0 6px;display:none">● back to live</button>
         <input type="range" data-k="moveR" min="0" max="0" step="0.02" style="width:100%">
         <div data-k="moveName" style="font-size:11px;color:#222;min-height:14px"></div></div>`;
  if (slot) { slot.appendChild(moveBox); slot.hidden = false; }
  const mq = k => moveBox.querySelector(`[data-k="${k}"]`);
  // ---- "Adjust step": nudge the step the preview is paused on (x y z mm, rx ry rz deg about the fingertips), the
  // 3D robot shows it, Save stores it as that step's taught pose (teach_api.py: the same as step_run.py's save) ----
  const adj = document.createElement("div");
  adj.className = "adj-step";
  adj.style.cssText = "position:absolute;right:10px;bottom:10px;z-index:6;width:262px;display:none;background:#ffffffef;" +
    "color:#222;border:1px solid #bbb;border-radius:8px;padding:8px 10px;font:12px/1.35 system-ui,sans-serif;box-shadow:0 2px 8px #0002";
  const AX = [["x", "mm"], ["y", "mm"], ["z", "mm"], ["rx", "deg"], ["ry", "deg"], ["rz", "deg"]];
  adj.innerHTML = `<style>.adj-step button{font:inherit;cursor:pointer}
      .adj-step .seg{display:flex;gap:0;margin:2px 0 4px}
      .adj-step .seg label{flex:1;text-align:center;border:1px solid #bbb;padding:2px 0;cursor:pointer;font-weight:600;font-size:11.5px}
      .adj-step .seg label:first-child{border-radius:4px 0 0 4px} .adj-step .seg label:last-child{border-radius:0 4px 4px 0}
      .adj-step .seg input{display:none} .adj-step .seg input:checked+span{color:#fff}
      .adj-step .seg label:has(input:checked){background:#2f6fde;border-color:#2f6fde;color:#fff}
      .adj-step .jog{display:flex;gap:6px;align-items:center;margin:4px 0}
      .adj-step .jog button{width:52px;height:30px;font-size:17px;font-weight:700}
      .adj-step .big{padding:3px 10px;font-weight:600}</style>
    <div style="display:flex;justify-content:space-between;align-items:center"><b>Adjust step</b>
      <span style="color:#777;font-size:11px">3D only until you save</span></div>
    <div data-a="name" style="margin:2px 0 4px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"></div>
    <div class="seg" title="Base: the cell's axes (+Y left, -X towards you, Z up). Tool: the gripper's axes (Z along the gripper, X the fingers' closing direction)">
      <label><input type="radio" name="adjFr" value="base" checked><span>Base</span></label>
      <label><input type="radio" name="adjFr" value="tool"><span>Tool</span></label></div>
    <div class="seg">${["x", "y", "z", "rx", "ry", "rz"].map((a, i) =>
      `<label><input type="radio" name="adjAx" value="${a}"${i === 0 ? " checked" : ""}><span>${a.toUpperCase()}</span></label>`).join("")}</div>
    <div class="jog"><button data-a="minus">−</button><button data-a="plus">+</button>
      <span style="color:#555">step <select data-a="size"></select> <span data-a="unit">mm</span></span></div>
    <div data-a="sum" style="font:11.5px ui-monospace,Consolas,monospace;min-height:15px;color:#222"></div>
    <select data-a="hist" style="width:100%;font:inherit;margin-top:3px" title="Every position you jogged to for this step (newest first) - pick one to go back there"></select>
    <div data-a="msg" style="min-height:15px;margin:3px 0;font-size:11px;color:#555"></div>
    <div style="display:flex;gap:6px"><button class="big" data-a="save">💾 Save</button><button class="big" data-a="undo">↺ Undo</button></div>
    <div style="color:#777;font-size:10.5px;margin-top:3px">Base: +Y = left, -X = towards you, Z up. Tool: Z along the gripper,
      X = closing direction. Turns are about the fingertips.</div>`;
  el.appendChild(adj);
  ["pointerdown", "wheel"].forEach(t => adj.addEventListener(t, e => e.stopPropagation()));
  const aq = k => adj.querySelector(`[data-a="${k}"]`);
  let adjK = null, adjOps = [], adjSeq = 0, adjStart = null, adjStartLabel = "";
  // history per step: absolute flange poses (so it survives a Save, which changes the program's own pose)
  const histKey = () => `adjHist:${VERSION()}:${progP[adjK] ? progP[adjK].name : ""}`;
  const histLoad = () => { try { return JSON.parse(localStorage.getItem(histKey()) || "[]"); } catch (e) { return []; } };
  const histSave = h => { try { localStorage.setItem(histKey(), JSON.stringify(h.slice(-30))); } catch (e) { /* private */ } };
  function histAdd(flange, label, saved = false) {
    const h = histLoad(), last = h[h.length - 1];
    if (last && !saved && last.flange.every((v, i) => Math.abs(v - flange[i]) < 1e-3)) return;   // same pose again
    h.push({ t: new Date().toTimeString().slice(0, 5), label, flange, saved }); histSave(h); histShow();
  }
  function histShow() {
    const h = histLoad(), sel = aq("hist");
    sel.innerHTML = `<option value="">History (${h.length}) ▾</option><option value="prog">program (now) - no offset</option>` +
      h.map((e, i) => [e, i]).reverse().map(([e, i]) => `<option value="${i}">${e.t}  ${e.label}${e.saved ? "  ✓ saved" : ""}</option>`).join("");
  }
  const adjSizes = { mm: [0.5, 1, 2, 5, 10], deg: [0.5, 1, 2, 5] };
  const adjAxis = () => adj.querySelector('input[name="adjAx"]:checked').value;
  const adjFrame = () => adj.querySelector('input[name="adjFr"]:checked').value;
  function adjSizeList() {                           // mm for x y z, degrees for rx ry rz
    const deg = adjAxis().startsWith("r"), sel = aq("size"), keep = sel.value;
    sel.innerHTML = (deg ? adjSizes.deg : adjSizes.mm).map(v => `<option${v === 1 ? " selected" : ""}>${v}</option>`).join("");
    if ([...sel.options].some(o => o.value === keep)) sel.value = keep;
    aq("unit").textContent = deg ? "deg" : "mm";
  }
  const VERSION = () => ({ cell: "v4", cell_v5: "v5", cell_v6: "v6", cell_v8: "v8" }[cellName] || "v8");
  async function adjCall(path) {
    const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version: VERSION(), move: progP[adjK].name, ops: adjOps, flange: adjStart }) });
    return r.json().catch(() => ({ ok: false, msg: `HTTP ${r.status}` }));
  }
  function adjShow() {                             // the summary: totals per frame + axis, in the order first used
    const tot = new Map();
    adjOps.forEach(o => { const k = `${o.frame} ${o.axis}`; tot.set(k, +((tot.get(k) || 0) + o.v).toFixed(3)); });
    const parts = [...tot].filter(([, v]) => v !== 0).map(([k, v]) => `${k} ${v > 0 ? "+" : ""}${v}${k.endsWith(" x") || k.endsWith(" y") || k.endsWith(" z") ? "" : "°"}`);
    aq("sum").textContent = (adjStart ? `[${adjStartLabel}]` + (parts.length ? " + " : "") : "") +
      (parts.length ? parts.join(", ") : adjStart ? "" : "no offset");
    const any = parts.length > 0 || !!adjStart;
    aq("save").disabled = !any; aq("undo").disabled = !any;
  }
  async function adjApply() {                       // the 3D robot at the step + offset (parts as at that step)
    const seq = ++adjSeq, k = adjK;
    if (!adjOps.length && !adjStart) { moveTo(k); aq("msg").textContent = ""; return; }
    aq("msg").textContent = "…";
    const j = await adjCall("/teach/preview");
    if (seq !== adjSeq || k !== adjK) return;       // a newer nudge / another step meanwhile
    if (!j.ok) { aq("msg").innerHTML = `<span style="color:#c01010">${j.msg}</span>`; return; }
    const info = previewApi ? previewApi.path(progP, k) : null;
    setPreview && setPreview(j.joints, info ? info.closed : null);
    aq("msg").textContent = `flange x ${j.flange[0].toFixed(1)} y ${j.flange[1].toFixed(1)} z ${j.flange[2].toFixed(1)}, rz ${j.flange[5].toFixed(1)}°`;
    adjLast = j.flange;
    if (adjOps.length) histAdd(j.flange, aq("sum").textContent);
  }
  const jog = sign => { adjOps.push({ frame: adjFrame(), axis: adjAxis(), v: sign * +aq("size").value }); adjShow(); adjApply(); };
  aq("minus").onclick = () => jog(-1); aq("plus").onclick = () => jog(1);
  adj.querySelectorAll('input[name="adjAx"]').forEach(r => r.onchange = adjSizeList);
  adjSizeList();
  aq("undo").onclick = () => { adjOps = []; adjStart = null; adjShow(); adjApply(); };
  let adjLast = null;
  aq("hist").onchange = () => {                    // go back to a position from the history (absolute pose)
    const v = aq("hist").value; aq("hist").value = "";
    if (v === "") return;
    adjOps = [];
    if (v === "prog") { adjStart = null; adjStartLabel = ""; }
    else { const e = histLoad()[+v]; if (!e) return; adjStart = e.flange; adjStartLabel = `${e.t} ${e.label}`; }
    adjShow(); adjApply();
  };
  aq("save").onclick = async () => {
    aq("save").disabled = true; aq("msg").textContent = "saving + rebuilding the program (about 15 s) …";
    const j = await adjCall("/teach/save");
    if (!j.ok) { aq("msg").innerHTML = `<span style="color:#c01010">${j.msg}</span>`; adjShow(); return; }
    aq("msg").innerHTML = `<span style="color:#0a7a2a">✓ ${j.msg}</span>`;
    if (adjLast) histAdd(adjLast, aq("sum").textContent, true);
    const k = adjK; adjOps = []; adjStart = null; adjShow();
    await reloadData(); jumpTo(k);
  };
  function adjUpdate(st) {                          // shown while the preview is paused on a step
    const show = st && (st.mode === "paused" || st.mode === "end") && progP.length;
    adj.style.display = show ? "block" : "none";
    if (!show) return;
    const k = Math.round(moveCur ?? +mq("moveR").value);
    if (k !== adjK) { adjK = k; adjOps = []; adjStart = null; adjSeq++; aq("msg").textContent = ""; histShow(); }
    const p = progP[adjK];
    aq("name").textContent = `#${adjK + 1} ${p.name}${p.grip ? " (" + p.grip.toUpperCase() + ")" : ""}`;
    aq("name").title = aq("name").textContent;
    adjShow();
  }
  async function reloadData() {                     // after a Save: the rebuilt program's joints / grips / durations
    try {
      let r2 = await fetch(base + "manip_data.json", { cache: "no-cache" });
      if (!r2.ok) r2 = await fetch(base + "manipulability/manip_data.json", { cache: "no-cache" });
      if (r2.ok) { D = await r2.json(); buildPath(); }
    } catch (e) { log("err", "path data not reloaded: " + e.message); }
  }
  // pinned top left, right under the status box (.hud: "node · gripper ..."), whatever size the 3D pane gets
  const hudEl = el.querySelector(".hud");
  function pin() {
    const top = hudEl && !hudEl.hidden && hudEl.offsetHeight ? hudEl.offsetTop + hudEl.offsetHeight + 8 : 10;
    box.style.top = top + "px"; box.style.maxHeight = `calc(100% - ${top + 10}px)`;
  }
  pin();
  if (hudEl) {
    new ResizeObserver(pin).observe(hudEl);
    new MutationObserver(pin).observe(hudEl, { attributes: true, attributeFilter: ["hidden"] });
  }
  window.addEventListener("resize", pin);
  const q = k => box.querySelector(`[data-k="${k}"]`);
  box.querySelectorAll("[data-s]").forEach(inp => {
    const k = inp.dataset.s;
    if (inp.type === "checkbox") inp.checked = !!st[k]; else inp.value = st[k];
    inp.addEventListener(inp.type === "text" ? "change" : "input", () => {
      st[k] = inp.type === "checkbox" ? inp.checked : inp.type === "range" ? +inp.value : inp.value; save(st); apply(k);
    });
  });
  q("toggle").onclick = q("arrow").onclick = () => { st.open = !st.open; save(st); apply("open"); };
  q("info").onclick = () => { const h = q("help"); h.style.display = h.style.display === "block" ? "none" : "block"; };
  q("moreT").onclick = () => { st.more = !st.more; save(st); apply("more"); };
  box.querySelectorAll("[data-h]").forEach(b => b.addEventListener("click", e => {   // the small (i): its help text
    e.preventDefault(); e.stopPropagation();                                          // (not the checkbox)
    const h = box.querySelector(`[data-hb="${b.dataset.h}"]`);
    h.style.display = h.style.display === "block" ? "none" : "block";
  }));
  q("stepR").addEventListener("input", e => showUpTo(+e.target.value));
  // the robot follows the handle, forwards and backwards, but never faster than the real robot would move times the
  // page's Speed (x real time): each move takes its programmed time (manip_data "dur": line = distance / speed,
  // joint move = largest joint turn / 50 deg/s), a GRIP / RELEASE GRIP_S. Slower drags: it follows your hand directly.
  const GRIP_S = 1.0;
  let moveTarget = null, moveCur = null, moveT = 0, moveRunning = false;
  const segSecs = k => {                           // seconds from point k to point k + 1 at x1
    const n = progP[k + 1];
    return Math.max(0.05, (n ? n.dur || 0 : 0) + (progP[k] && progP[k].grip ? GRIP_S : 0));
  };
  function showCatchUp() {                         // yellow marker = where you pull to; the handle pulses while the
    const g = mq("ghost"), r = mq("moveR");          // robot (the handle) is still on its way there
    const behind = moveTarget !== null && moveCur !== null && Math.abs(moveTarget - moveCur) > 0.02;
    moveBox.classList.toggle("catching", behind);
    if (mq("tl")) { tlDraw(); if (behind) mq("moveV").textContent = `${Math.round(moveCur) + 1} → ${Math.round(moveTarget) + 1}`; return; }
    if (!g) return;
    g.style.display = behind ? "block" : "none";
    if (behind) {
      const max = +r.max || 1, thumb = 16, w = r.offsetWidth;
      g.style.left = (thumb / 2 + (moveTarget / max) * (w - thumb)) + "px";
      mq("moveV").textContent = `${Math.round(moveCur) + 1} → ${Math.round(moveTarget) + 1}`;
    }
  }
  // ---- the timeline (header): x = program time; stage bands, GRIP / RELEASE, stiff (flagged) and collision marks ----
  let tlCum = [], tlTotal = 1, tlHits = new Set(), tlHitsCell = null;
  const STAGE_COL = ["#3a7bd5", "#8e5cd9", "#c9539b", "#d9822b", "#2aa198", "#6c8a1f", "#7a7f88", "#b5532a"];
  function tlX(sv) {                                // point index (fractional) -> 0..1 along the timeline
    if (!tlCum.length) return 0;
    const k = Math.max(0, Math.min(Math.floor(sv), tlCum.length - 1)), f = sv - k;
    const t = tlCum[k] + (k + 1 < tlCum.length ? (tlCum[k + 1] - tlCum[k]) * f : 0);
    return t / tlTotal;
  }
  function tlS(x) {                                 // 0..1 -> point index (fractional)
    const t = Math.max(0, Math.min(1, x)) * tlTotal;
    let k = 0;
    while (k + 1 < tlCum.length && tlCum[k + 1] <= t) k++;
    if (k + 1 >= tlCum.length) return tlCum.length - 1;
    const span = tlCum[k + 1] - tlCum[k];
    return k + (span > 0 ? (t - tlCum[k]) / span : 0);
  }
  async function tlLoadHits() {                     // collision.py's hits for this cell (move n = point n - 1)
    if (tlHitsCell === cellName) return;
    tlHitsCell = cellName; tlHits = new Set();
    try {
      const r = await fetch(base + "collisions.json?cell=" + encodeURIComponent(cellName || "cell_v8"), { cache: "no-cache" });
      const d = r.ok ? await r.json() : null;
      (d && d.hits || []).forEach(h => tlHits.add(h.move - 1));
    } catch (e) { /* no collision data: no red marks */ }
    buildTimeline(true);
  }
  function buildTimeline(noFetch) {
    const box = mq("tlMarks"); if (!box) return;
    tlCum = []; let t = 0;
    progP.forEach((p, k) => { t += k ? (p.dur || 0) + (progP[k - 1].grip ? GRIP_S : 0) : 0; tlCum.push(t); });
    tlTotal = Math.max(t, 1e-6);
    const pct = v => (100 * v).toFixed(3) + "%";
    let html = "", k0 = 0;
    for (let k = 1; k <= progP.length; k++) {      // stage bands
      if (k === progP.length || progP[k].stage !== progP[k0].stage) {
        const x0 = tlX(k0), x1 = k === progP.length ? 1 : tlX(k), st0 = progP[k0].stage;
        const nm = STAGE_NAMES[st0] || "stage " + st0;
        html += `<div class="band" style="left:${pct(x0)};width:calc(${pct(x1 - x0)} - 1px);background:${STAGE_COL[(st0 - 1) % STAGE_COL.length]}" title="${nm}">${st0} ${nm}</div>`;
        k0 = k;
      }
    }
    progP.forEach((p, k) => {
      const x = pct(tlX(k));
      if (p.grip) html += `<div class="mk ${p.grip === "grip" ? "g" : "r"}" style="left:${x}"></div>`;
      const bad = p.mu1_vfix > st.thr || p.mu1_full > D.full_thr || p.margin < D.limit_warn;
      if (tlHits.has(k)) html += `<div class="mk c" style="left:${x}"></div>`;
      else if (bad) html += `<div class="mk f" style="left:${x}"></div>`;
    });
    box.innerHTML = html;
    mq("tlTime").textContent = `${Math.round(tlTotal)} s at x1`;
    tlDraw();
    if (!noFetch) tlLoadHits();
  }
  const STAGE_NAMES = { 1: "planks", 2: "small half to A", 3: "big half to A", 4: "flip frame", 5: "small half back",
                        6: "big half back", 7: "bench to AMR", 8: "" };
  function tlDraw() {                               // the handle (robot) and the yellow pull marker
    const tl = mq("tl"); if (!tl) return;
    const cur = moveCur !== null ? moveCur : +mq("moveR").value;
    mq("thumb").style.left = (100 * tlX(cur)) + "%";
    const g = mq("ghost"), behind = moveTarget !== null && moveCur !== null && Math.abs(moveTarget - moveCur) > 0.02;
    g.style.display = behind ? "block" : "none";
    if (behind) g.style.left = (100 * tlX(moveTarget)) + "%";
  }
  // playback of the preview: "paused" when the robot is at the point you chose, Resume plays on to the end at Robot
  // speed, Pause stops it; the page shows it on its Pause / Resume button (onPreviewState)
  let playing = false, stateCb = null;
  function previewState() {
    if (!previewOn || !progP.length) return { mode: "off" };
    const cur = moveCur ?? +mq("moveR").value, k = Math.round(cur), atEnd = cur >= progP.length - 1 - 1e-6;
    const mode = playing ? "playing" : moveRunning && moveTarget !== moveCur ? "moving" : atEnd ? "end" : "paused";
    return { mode, step: k + 1, of: progP.length, name: progP[Math.min(k, progP.length - 1)].name };
  }
  const notify = () => { const st = previewState(); adjUpdate(st); try { stateCb?.(st); } catch (e) { /* page gone */ } };
  function jumpTo(v) {                             // straight there, no speed limit (timeline click, Home / End)
    v = Math.max(0, Math.min(v, progP.length - 1));
    playing = false;
    moveTarget = moveCur = v; moveRunning = false;
    moveTo(v); mq("moveR").value = v; showCatchUp(); notify();
  }
  function stepBy(d) {                             // one point back / forward, at Robot speed
    if (!progP.length) return;
    playing = false;
    const base = moveTarget ?? moveCur ?? +mq("moveR").value;
    if (!previewOn && moveCur === null) moveCur = +mq("moveR").value;
    setTarget(d > 0 ? Math.floor(base + 1e-6) + 1 : Math.ceil(base - 1e-6) - 1);
  }
  function setTarget(v) {                           // the robot heads for point v (speed-limited, see moveTick)
    moveTarget = Math.max(0, Math.min(v, progP.length - 1));
    if (moveCur === null) moveCur = previewOn ? moveTarget : +mq("moveR").value;
    showCatchUp();
    if (!moveRunning) { moveRunning = true; moveT = performance.now(); requestAnimationFrame(moveTick); }
    notify();
  }
  function moveTick(now) {
    const dt = Math.min(0.1, (now - moveT) / 1000); moveT = now;
    const spEl = document.getElementById("sp-num");                 // the page's Robot speed, live while you drag it
    let budget = dt * Math.max(0.05, (spEl && +spEl.value) || previewApi?.fast || 1);   // robot seconds this frame
    while (budget > 1e-6 && moveCur !== moveTarget) {
      const up = moveTarget > moveCur, k = up ? Math.floor(moveCur + 1e-9) : Math.ceil(moveCur - 1e-9) - 1;
      const secs = segSecs(Math.max(0, Math.min(k, progP.length - 2)));
      const edge = up ? Math.min(k + 1, moveTarget) : Math.max(k, moveTarget), dist = Math.abs(edge - moveCur);
      const can = budget / secs;                                      // fraction of this segment we can still do
      if (can >= dist) { moveCur = edge; budget -= dist * secs; } else { moveCur += (up ? 1 : -1) * can; budget = 0; }
    }
    moveTo(moveCur);
    mq("moveR").value = moveCur;                   // the handle shows where the robot is: it cannot run ahead of it
    showCatchUp();
    if (moveCur !== moveTarget) requestAnimationFrame(moveTick); else { moveRunning = false; playing = false; notify(); }
  }
  mq("moveR").addEventListener("pointerdown", e => { if (!previewOn) moveCur = +e.target.value; });   // start where the arm is
  mq("moveR").addEventListener("input", e => {
    moveTarget = +e.target.value;
    if (moveCur === null) moveCur = moveTarget;
    e.target.value = moveCur; showCatchUp();      // handle stays with the robot, the marker shows where you pull
    if (!moveRunning) { moveRunning = true; moveT = performance.now(); requestAnimationFrame(moveTick); }
  });
  mq("moveR").addEventListener("keydown", e => e.stopPropagation());
  const tl = mq("tl");
  if (tl) {
    const xAt = e => { const r = tl.getBoundingClientRect(); return (e.clientX - r.left) / r.width; };
    let dragging = false;
    tl.addEventListener("pointerdown", e => {       // click = JUMP there at once (every position is replayed from the
      dragging = true; tl.setPointerCapture(e.pointerId); tl.focus();   // start, so a jump ends exactly as driving
      jumpTo(tlS(xAt(e))); e.preventDefault();      // there would); dragging afterwards = the speed-limited pull
    });
    tl.addEventListener("pointermove", e => {
      const sv = tlS(xAt(e)), k = Math.round(sv), p = progP[k], h = mq("hov");
      if (p) { h.style.display = "block"; h.style.left = (100 * Math.max(0, Math.min(1, xAt(e)))) + "%";
        h.textContent = `${k + 1}: ${p.name}${p.grip ? " - " + p.grip.toUpperCase() : ""}${tlHits.has(k) ? " - COLLISION" : ""}`; }
      if (dragging) setTarget(sv);
    });
    ["pointerup", "pointercancel"].forEach(t => tl.addEventListener(t, () => { dragging = false; }));
    tl.addEventListener("pointerleave", () => { mq("hov").style.display = "none"; });
    tl.addEventListener("keydown", e => {           // arrows: one point; shift: one stage; Home / End
      const cur = moveTarget ?? moveCur ?? +mq("moveR").value;
      let v = null;
      if (e.key === "ArrowRight") v = Math.floor(cur + 1e-6) + 1;
      else if (e.key === "ArrowLeft") v = Math.ceil(cur - 1e-6) - 1;
      else if (e.key === "Home" || e.key === "End") { e.preventDefault(); e.stopPropagation(); jumpTo(e.key === "Home" ? 0 : progP.length - 1); return; }
      if (v !== null) { e.preventDefault(); e.stopPropagation(); if (!previewOn && moveCur === null) moveCur = +mq("moveR").value; setTarget(v); }
    });
    new ResizeObserver(tlDraw).observe(tl);
  }
  mq("liveB").onclick = backToLive;
  if (mq("prevB")) { mq("prevB").onclick = () => stepBy(-1); mq("nextB").onclick = () => stepBy(1); }
  q("stepR").addEventListener("keydown", e => e.stopPropagation());   // arrow keys step the slider, not the camera
  // stop orbit controls from reacting to the panel
  ["pointerdown", "wheel"].forEach(t => box.addEventListener(t, e => e.stopPropagation()));

  let vidSaved = null;                              // the user's layer settings while a video export overrides them
  function apply(k) {
    q("body").style.display = st.open ? "" : "none"; q("arrow").textContent = st.open ? "▾" : "▸";
    q("thrv").textContent = st.thr.toFixed(1); q("thrHelp").textContent = "μ1 " + st.thr.toFixed(1);
    q("more").style.display = st.more ? "" : "none"; q("legend").style.display = st.path ? "" : "none";
    q("mapH").textContent = st.heights.split(",").map(s => s.trim()).filter(Boolean).join(" / ") + " mm"; q("moreT").textContent = st.more ? "More settings ▾" : "More settings ▸";
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
    const w = t.mu1_vfix < Math.sqrt(st.thr) ? "Good" : t.mu1_vfix < st.thr ? "OK" : "Poor";
    const gr = t.grip ? `\n${t.grip === "grip" ? "GRIP: gripper closes on" : "RELEASE: gripper opens, puts down"} ${(t.grip_parts || []).join(", ")}` : "";
    tipEl.textContent = `#${t.i} ${t.name} (stage ${t.stage})${t.flag ? "   FLAGGED" : ""}${gr}\n` +
      `arm freedom ${w} (μ1 ${t.mu1_vfix}), joint limits ${t.margin}° to spare\n` +
      `details: μ1 J_v ${t.mu1_v}, μ1 6x6 ${t.mu1_full}, μ3 J_v ${t.mu3_v} (m/s)³ - ${curProg}`;
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
      const word = !isFinite(m.mu1) ? "Stuck (singular)" : m.mu1 < Math.sqrt(st.thr) ? "Good" : m.mu1 < st.thr ? "OK" : "Poor";
      const lim = m.margin < D.limit_warn ? `<span style="color:#c01010">joint J${m.marginJ} only ${m.margin.toFixed(0)}° from its limit ⚠</span>`
        : `joint limits: ${m.margin.toFixed(0)}° to spare`;
      q("readout").innerHTML = `Arm freedom: <b style="color:${css(traffic(m.mu1, st.thr))};text-shadow:0 0 1px #000">${word}</b>` +
        ` <span style="color:#666">(μ1 ${isFinite(m.mu1) ? m.mu1.toFixed(1) : "∞"})</span><br>${lim}`;
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
    onPreviewState(cb) { stateCb = cb; notify(); },  // the page's Pause / Resume follows the preview
    play() {                                       // Resume: on from here to the end, at Robot speed
      if (!progP.length) return;
      if (!previewOn) jumpTo(+mq("moveR").value || 0);
      if ((moveCur ?? 0) >= progP.length - 1 - 1e-6) jumpTo(0);   // at the end: from the start again
      playing = true; setTarget(progP.length - 1);
    },
    pause() { playing = false; if (moveCur !== null) moveTarget = moveCur; notify(); },
    step(d) { stepBy(d); },
    jump(k) { if (progP.length) jumpTo(k); },
    // the video export: "show" = gripper path + manipulability map on (the intro), "hide" = every 3D layer off (the
    // clean assembly), "restore" = the user's own settings back. Not saved to the user's settings.
    videoLayers(mode) {
      const KEYS = ["path", "planes", "iso", "slice", "tcp", "ell"];
      if (mode === "restore") { if (vidSaved) { Object.assign(st, vidSaved); vidSaved = null; apply(); } return; }
      if (!vidSaved) vidSaved = Object.fromEntries(KEYS.map(k => [k, st[k]]));
      KEYS.forEach(k => { st[k] = mode === "show" ? (k === "path" || k === "planes") : false; });
      apply();
    },      // straight to program point k (0-based = move k + 1), e.g. a collision clicked
    get previewState() { return previewState(); },
    resetMove() {                                  // the page's Reset: preview off, Move robot back at the start
      if (previewOn) backToLive();
      moveTarget = moveCur = null; moveRunning = false;
      mq("moveR").value = 0; showCatchUp(); if (mq("tl")) tlDraw();
      mq("moveV").textContent = ""; mq("moveName").textContent = "";
    },
    get live() { return last; }, state: st, data: D,
  };
}
