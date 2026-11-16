// Jig mover for the 3D view (sim_scene.js loads it; own panel, bottom left of the 3D pane).
//
// Select: tick jigs in the list, or click them in 3D while the panel is open (click = only that one, Ctrl/Shift-click
// = add/remove). Move the selection with the arrows (X/Y/Z) or the ring (Turn Rz, about the selection's centre), or
// type the offset of the first selected jig - the others move by the same amount.
// Lock: "Lock together" makes the selected jigs one group: selecting any of them selects the group, so they always
// move as one. "Unlock" takes the selected out of their groups.
// "Take along" also moves what sits on a moved jig (box centre inside its footprint at the CAD start, above its bottom).
// State per cell: each moved object's 4x4 relative to its CAD start + the lock groups, kept in the browser and in
// tests/vision_lab/sim_jig_offsets.json (POST /vision/jigs, with each object's x y z rz and box = the "truth" a vision
// script checks itself against). The program and the collision check don't follow moved jigs - vision has to find them.
import { TransformControls } from "three/addons/controls/TransformControls.js";

const FIXED = /^(Table|T-slot plate|AMR)/;           // never moved, never "on" a jig
const JIG = /^(Base|Plank rack|Guide)/;              // listed first
// ArUco markers (DICT_4X4_50, /sim/markers/aruco_<id>.png: 6 black/white cells + a 1-cell white margin), one per jig, on
// a flat spot of its top found by casting rays down at the CAD start; the biggest size that fits (black square, mm).
const MARKER_IDS = { "Base A": 1, "Base B": 2, "Plank rack": 3, "Guide small": 4, "Guide big": 5 };
const MARKER_SIZES = [40, 30, 22, 16, 12, 10];
const MARKER_TAB = 22;                               // smaller than this fits: glue a 22 mm marker on a 1 mm tab instead
// Lift a marker on a post above taller things close by (only for the jigs listed: the test showed the plank rack would
// need a ~160 mm post because of the standing planks - a photo straight above the rack is the better answer)
const POST_FOR = new Set();

export function addJigLayer({ THREE, scene, camera, renderer, controls, el, log, cell, cellName, start }) {
  const deg = Math.PI / 180;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} } };
  const orig = new Map(), footprint = new Map();     // top-level cell object -> matrix / box at the CAD start
  let moved = {}, locks = [], sel = new Set();       // moved: name -> Matrix4 (CAD start -> now); locks: [[names]]
  let open = false;
  let markersOn = store.get("simMarkers", false);
  const markerInfo = {};                             // name -> { id, size, centre (CAD), corners (CAD, TL TR BR BL) }
  const texLoader = new THREE.TextureLoader();
  const pretty = o => o.name.replace(/_/g, " ");
  const tops = () => { const c = cell(); return c ? c.children.filter(o => !FIXED.test(pretty(o))) : []; };
  const byName = n => tops().find(o => pretty(o) === n);
  const pivotOf = n => { const b = footprint.get(byName(n)); return b.getCenter(new THREE.Vector3()).setZ(b.min.z); };
  const M = n => moved[n] || new THREE.Matrix4();
  const groupOf = n => locks.find(g => g.includes(n)) || [n];

  // ---- state -------------------------------------------------------------------------------------------------
  function onCell(name) {
    orig.clear(); footprint.clear();
    const c = cell(); if (!c) return;
    c.updateMatrixWorld(true);
    c.children.forEach(o => { orig.set(o, o.matrix.clone()); footprint.set(o, new THREE.Box3().setFromObject(o)); });
    placeMarkers();
    loadState(name);
    if (Object.keys(moved).length) log("ev", `3D: ${Object.keys(moved).length} object(s) moved (Jigs panel)`);
  }
  function loadState(name) {                         // the saved moves on top of the CAD start (orig), never twice
    const s = store.get("simJigs2:" + name, {});
    moved = {}; Object.entries(s.moved || {}).forEach(([n, a]) => { if (byName(n)) moved[n] = new THREE.Matrix4().fromArray(a); });
    locks = (s.locks || []).map(g => g.filter(byName)).filter(g => g.length > 1);
    tops().forEach(o => place(pretty(o)));
    sel = new Set(); fillList(); attach();
  }
  function place(n) {                                // the object at M(n) x its CAD start (unless the gripper holds it)
    const o = byName(n); if (!o || o.parent !== cell()) return;
    M(n).clone().multiply(orig.get(o)).decompose(o.position, o.quaternion, o.scale);
    const s = start.get(o);                          // sim_scene's reset puts parts back here
    if (s) { s.pos.copy(o.position); s.quat.copy(o.quaternion); }
  }
  function along(n) {                                // what sits on n at the CAD start
    const fp = footprint.get(byName(n));
    return tops().filter(p => pretty(p) !== n && !JIG.test(pretty(p))).filter(p => {
      const b = footprint.get(p), c = b.getCenter(new THREE.Vector3());
      return c.x > fp.min.x - 2 && c.x < fp.max.x + 2 && c.y > fp.min.y - 2 && c.y < fp.max.y + 2 && b.min.z >= fp.min.z - 1;
    }).map(pretty);
  }
  function movingSet() {                             // the selection + what sits on it (if ticked)
    const s = new Set(sel);
    if (ui.along.checked) sel.forEach(n => along(n).forEach(a => s.add(a)));
    return [...s];
  }
  function applyDelta(D, names, from) {              // names[i] at D x from[i]
    names.forEach((n, i) => { moved[n] = D.clone().multiply(from[i]); place(n); });
  }
  function offsetOf(n) {                             // x y z (pivot moved, mm) and rz (deg) of n's move
    const m = M(n), p = pivotOf(n), q = p.clone().applyMatrix4(m), e = m.elements;
    return { x: +(q.x - p.x).toFixed(1), y: +(q.y - p.y).toFixed(1), z: +(q.z - p.z).toFixed(1),
             rz: +(Math.atan2(e[1], e[0]) / deg).toFixed(1) };
  }
  function matrixOf(n, f) {                          // the move with offset f about n's pivot
    const p = pivotOf(n);
    return new THREE.Matrix4().makeTranslation(p.x + f.x, p.y + f.y, p.z + f.z)
      .multiply(new THREE.Matrix4().makeRotationZ(f.rz * deg)).multiply(new THREE.Matrix4().makeTranslation(-p.x, -p.y, -p.z));
  }
  function tidy() { Object.keys(moved).forEach(n => { if (moved[n].equals(new THREE.Matrix4())) delete moved[n]; }); }
  function m4(Mx) { const e = Mx.elements; return [0, 1, 2, 3].map(r => [0, 1, 2, 3].map(c => +e[c * 4 + r].toFixed(5))); }
  function truth() {                                 // true poses, for the photos' JSON and the offsets file
    const out = {};
    Object.keys(moved).forEach(n => {
      const o = byName(n); if (!o) return;
      const b = new THREE.Box3().setFromObject(o);
      out[n] = { ...offsetOf(n), T_move: m4(M(n)), locked_with: groupOf(n).filter(x => x !== n),
                 box_min: b.min.toArray().map(v => +v.toFixed(2)), box_max: b.max.toArray().map(v => +v.toFixed(2)) };
    });
    return out;
  }
  function save() {
    tidy();
    const s = { moved: Object.fromEntries(Object.entries(moved).map(([n, m]) => [n, m.toArray()])), locks };
    store.set("simJigs2:" + cellName(), s);
    fetch("/vision/jigs", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cell: cellName(), offsets: Object.fromEntries(Object.keys(moved).map(n => [n, offsetOf(n)])),
                             locks, truth: truth() }) }).catch(() => {});
    fillList();
  }

  // ---- ArUco markers ----------------------------------------------------------------------------------------
  function heightMap(o, b, GRID, nx, ny) {           // top surface of o on a grid: z, and whether it faces up
    const H = Array.from({ length: nx + 1 }, () => new Array(ny + 1).fill(null));
    const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3(), n = new THREE.Vector3();
    o.traverse(m => {
      if (!m.isMesh || m.userData.marker) return;
      const pos = m.geometry.attributes.position, idx = m.geometry.index, W = m.matrixWorld;
      const tri = idx ? idx.count / 3 : pos.count / 3;
      for (let t = 0; t < tri; t++) {
        const k = idx ? [idx.getX(3 * t), idx.getX(3 * t + 1), idx.getX(3 * t + 2)] : [3 * t, 3 * t + 1, 3 * t + 2];
        A.fromBufferAttribute(pos, k[0]).applyMatrix4(W); B.fromBufferAttribute(pos, k[1]).applyMatrix4(W); C.fromBufferAttribute(pos, k[2]).applyMatrix4(W);
        n.subVectors(B, A).cross(C.clone().sub(A)); const len = n.length(); if (len < 1e-9) continue; n.divideScalar(len);
        if (Math.abs(n.z) < 1e-6) continue;             // vertical: no height of its own
        const i0 = Math.max(0, Math.ceil((Math.min(A.x, B.x, C.x) - b.min.x) / GRID)), i1 = Math.min(nx, Math.floor((Math.max(A.x, B.x, C.x) - b.min.x) / GRID));
        const j0 = Math.max(0, Math.ceil((Math.min(A.y, B.y, C.y) - b.min.y) / GRID)), j1 = Math.min(ny, Math.floor((Math.max(A.y, B.y, C.y) - b.min.y) / GRID));
        const d = (B.y - C.y) * (A.x - C.x) + (C.x - B.x) * (A.y - C.y); if (Math.abs(d) < 1e-9) continue;
        for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
          const x = b.min.x + i * GRID, y = b.min.y + j * GRID;
          const u = ((B.y - C.y) * (x - C.x) + (C.x - B.x) * (y - C.y)) / d, v = ((C.y - A.y) * (x - C.x) + (A.x - C.x) * (y - C.y)) / d, w = 1 - u - v;
          if (u < -1e-6 || v < -1e-6 || w < -1e-6) continue;
          const z = u * A.z + v * B.z + w * C.z;
          if (!H[i][j] || z > H[i][j].z + 1e-6) H[i][j] = { z, up: n.z > 0.95 };
        }
      }
    });
    return H;
  }
  function placeMarkers() {                          // at the CAD start (called before the saved moves are applied)
    Object.keys(markerInfo).forEach(k => delete markerInfo[k]);
    const GRID = 4;                                  // mm
    for (const [name, id] of Object.entries(MARKER_IDS)) {
      const o = byName(name); if (!o) continue;
      const b = footprint.get(o), nx = Math.floor((b.max.x - b.min.x) / GRID), ny = Math.floor((b.max.y - b.min.y) / GRID);
      const T = heightMap(o, b, GRID, nx, ny);
      // covered by another object above (its own surface higher there): not visible from above
      const over = tops().concat(cell().children.filter(c => FIXED.test(pretty(c)))).filter(c => {
        const ob = footprint.get(c);
        return c !== o && ob.max.z > b.min.z && ob.min.x < b.max.x && ob.max.x > b.min.x && ob.min.y < b.max.y && ob.max.y > b.min.y;
      }).map(c => heightMap(c, b, GRID, nx, ny));
      const H = T.map((col, i) => col.map((h, j) => {
        if (!h || !h.up) return null;
        return over.some(Hc => Hc[i][j] && Hc[i][j].z > h.z + 0.5) ? null : h.z;
      }));
      // anything taller close by (the jig itself or a neighbour, e.g. planks standing in the rack) hides a marker from a
      // camera that isn't straight above it: keep CLEAR mm away from surfaces more than 5 mm above the marker
      const CLEAR = 40, tall = (i, j) => Math.max(T[i][j] ? T[i][j].z : -1e9, ...over.map(Hc => Hc[i][j] ? Hc[i][j].z : -1e9));
      const Z = T.map((col, i) => col.map((_, j) => tall(i, j)));
      function clear(i, j, half, z0) {
        const r = half + Math.ceil(CLEAR / GRID);
        for (let a = Math.max(0, i - r); a <= Math.min(nx, i + r); a++)
          for (let c = Math.max(0, j - r); c <= Math.min(ny, j + r); c++) if (Z[a][c] > z0 + 5) return false;
        return true;
      }
      let best = null;
      for (const size of MARKER_SIZES) {             // biggest marker whose square (with margin) is flat and this jig's
        const half = Math.ceil(size * 7 / 6 / 2 / GRID);   // needs at least half a cell of white margin around it
        const cx = (b.min.x + b.max.x) / 2, cy = (b.min.y + b.max.y) / 2;
        for (let i = half; i <= nx - half; i++) for (let j = half; j <= ny - half; j++) {
          const z0 = H[i][j]; if (z0 === null) continue;
          let ok = true;
          for (let a = -half; a <= half && ok; a++) for (let c = -half; c <= half && ok; c++) {
            const z = H[i + a][j + c]; if (z === null || Math.abs(z - z0) > 0.3) ok = false; }
          if (!ok) continue;
          const open = clear(i, j, half, z0);
          const x = b.min.x + i * GRID, y = b.min.y + j * GRID;
          const d = Math.hypot(x - cx, y - cy) - z0 * 2 + (open ? 0 : 1e6);   // clear of taller things, then high, then central
          if (!best || d < best.d) best = { x, y, z: z0, d, size, open, i, j, half };
        }
        if (best) break;
      }
      if (!best) { log("err", `3D: no flat spot for a marker on ${name}`); continue; }
      let tab = false, post = 0;
      if (!best.open && POST_FOR.has(name)) {        // something taller close by hides it: lift it on a post above that
        const r = best.half + Math.ceil(CLEAR / GRID);
        let top = best.z;
        for (let a = Math.max(0, best.i - r); a <= Math.min(nx, best.i + r); a++)
          for (let c = Math.max(0, best.j - r); c <= Math.min(ny, best.j + r); c++) top = Math.max(top, Z[a][c]);
        post = Math.ceil(top - best.z + 5);
        const stick = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, post, 12), new THREE.MeshStandardMaterial({ color: 0x777777 }));
        stick.rotation.x = Math.PI / 2;
        stick.position.set(best.x, best.y, best.z + post / 2).applyMatrix4(orig.get(o).clone().invert());
        stick.userData.marker = true; stick.visible = markersOn; o.add(stick);
        best.z += post;
      }
      if (best.size < MARKER_TAB || post) {          // as on a real jig: a small plate with the marker, on its flat spot
        tab = true; best.size = MARKER_TAB; best.z += 1;
        const plate = new THREE.Mesh(new THREE.BoxGeometry(MARKER_TAB * 8 / 6, MARKER_TAB * 8 / 6, 1), new THREE.MeshStandardMaterial({ color: 0xf2f2f2 }));
        plate.position.set(best.x, best.y, best.z - 0.5).applyMatrix4(orig.get(o).clone().invert());
        plate.userData.marker = true; plate.visible = markersOn; o.add(plate);
      }
      const s = best.size / 2;
      markerInfo[name] = { id, size: best.size, tab, post_mm: post, centre: [best.x, best.y, best.z],
        corners: [[best.x - s, best.y + s, best.z], [best.x + s, best.y + s, best.z], [best.x + s, best.y - s, best.z], [best.x - s, best.y - s, best.z]] };
      const w = best.size * 8 / 6;                   // with the white margin
      const tex = texLoader.load(`/sim/markers/aruco_${id}.png`);
      tex.colorSpace = THREE.SRGBColorSpace; tex.magFilter = THREE.NearestFilter;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, w), new THREE.MeshStandardMaterial({ map: tex, roughness: .9 }));
      m.name = "aruco " + id; m.userData.marker = true;
      m.position.set(best.x, best.y, best.z + 0.3).applyMatrix4(orig.get(o).clone().invert());   // in the jig's own frame
      m.visible = markersOn; o.add(m);
    }
    log("ev", `3D: ArUco markers: ${Object.entries(markerInfo).map(([n, m]) => `${n} #${m.id} ${m.size} mm${m.post_mm ? ` (on a ${m.post_mm} mm post)` : m.tab ? " (tab)" : ""}`).join(", ")}`);
  }
  function setMarkers(on) {
    markersOn = !!on; store.set("simMarkers", markersOn);
    tops().forEach(o => o.children.forEach(c => { if (c.userData.marker) c.visible = markersOn; }));
    const b = panel.querySelector('[data-k="markers"]'); if (b) b.classList.toggle("on", markersOn);
  }
  function model() {                                 // the jigs at the CAD start, for a photo's JSON (vision scripts)
    const out = {};
    Object.keys(MARKER_IDS).forEach(n => {
      const o = byName(n); if (!o) return;
      const b = footprint.get(o), p = pivotOf(n);
      out[n] = { pivot: p.toArray().map(v => +v.toFixed(2)), box_min: b.min.toArray().map(v => +v.toFixed(2)),
                 box_max: b.max.toArray().map(v => +v.toFixed(2)), marker: markerInfo[n] || null };
    });
    return { jigs: out, markers_visible: markersOn, marker_dict: "DICT_4X4_50" };
  }
  function setJigs(ev) {                             // a script's POST /vision/jigs/set: {offsets: {name: {x,y,z,rz}}, along, reset}
    if (ev.reset) Object.keys(moved).forEach(n => { delete moved[n]; place(n); });
    Object.entries(ev.offsets || {}).forEach(([n, f]) => {
      if (!byName(n)) return log("err", `3D: no jig "${n}"`);
      const Mx = matrixOf(n, { x: 0, y: 0, z: 0, rz: 0, ...f });
      [n, ...(ev.along === false ? [] : along(n))].forEach(a => { moved[a] = Mx.clone(); place(a); });
    });
    save(); attach();
  }

  // ---- selection, gizmo, highlight ---------------------------------------------------------------------------
  const gizmo = new TransformControls(camera, renderer.domElement);
  gizmo.setSize(0.9); gizmo.setSpace("world");
  const proxy = new THREE.Object3D(); scene.add(proxy, gizmo);
  const boxes = new THREE.Group(); scene.add(boxes);  // a yellow box around each selected object (not in photos)
  let drag = null;                                   // at drag start: proxy matrix, names, their matrices
  gizmo.addEventListener("dragging-changed", e => {
    controls.enabled = !e.value;
    if (e.value) { const names = movingSet(); proxy.updateMatrix(); drag = { P0: proxy.matrix.clone(), names, from: names.map(n => M(n).clone()) }; }
    else { drag = null; save(); attach(); }
  });
  gizmo.addEventListener("objectChange", () => {
    if (!drag) return;
    proxy.updateMatrix();
    applyDelta(proxy.matrix.clone().multiply(drag.P0.clone().invert()), drag.names, drag.from);
    showFields(); outline();
  });
  function attach() {                                // gizmo at the selection's centre (bottom of its box)
    gizmo.detach();
    if (open && sel.size) {
      const b = new THREE.Box3(); sel.forEach(n => { const o = byName(n); if (o) b.expandByObject(o); });
      proxy.position.copy(b.getCenter(new THREE.Vector3()).setZ(b.min.z)); proxy.rotation.set(0, 0, 0);
      gizmo.attach(proxy);
    }
    outline(); showFields(); showList();
  }
  function outline() {
    boxes.clear();
    if (!open) return;
    sel.forEach(n => { const o = byName(n); if (o) boxes.add(new THREE.BoxHelper(o, 0xf2b705)); });
  }
  function select(n, add) {                          // n with its lock group; add = Ctrl/Shift (toggle)
    const g = groupOf(n);
    if (add) { const on = sel.has(n); g.forEach(x => on ? sel.delete(x) : sel.add(x)); }
    else sel = new Set(g);
    attach();
  }

  // ---- panel -------------------------------------------------------------------------------------------------
  const css = document.createElement("style");
  css.textContent = `
    .jig-panel { position: absolute; z-index: 2; left: 10px; bottom: 10px; font: 12px system-ui, sans-serif; color: #222;
      background: #ffffffeb; border: 1px solid #c9ccd1; border-radius: 6px; padding: 6px 8px; width: 300px; }
    .jig-panel b { font-weight: 600; } .jig-panel .row { display: flex; gap: 4px; align-items: center; margin-top: 5px; flex-wrap: wrap; }
    .jig-panel button { font: inherit; padding: 2px 7px; border: 1px solid #b8bcc3; border-radius: 4px; background: #f6f7f8; cursor: pointer; }
    .jig-panel button.on { background: #2c6fbf; color: #fff; border-color: #2c6fbf; }
    .jig-panel button:disabled { opacity: .45; cursor: default; }
    .jig-panel input[type=number] { width: 52px; font: inherit; }
    .jig-panel .body { display: none; } .jig-panel.open .body { display: block; }
    .jig-panel .list { max-height: 170px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 2px 4px; margin-top: 5px; }
    .jig-panel .list label { display: flex; gap: 5px; align-items: center; padding: 1px 0; cursor: pointer; }
    .jig-panel .list .mv { font-weight: 600; } .jig-panel .tag { color: #2c6fbf; font-size: 11px; }
    .jig-panel .sep { border-top: 1px solid #eee; margin: 2px 0; } .jig-panel .muted { color: #666; }`;
  document.head.appendChild(css);
  const panel = document.createElement("div");
  panel.className = "jig-panel";
  panel.innerHTML = `
    <div class="row" style="margin-top:0"><b>Jigs</b><span class="muted" data-k="sum"></span><span style="flex:1"></span>
      <button data-k="markers" title="Show / hide the ArUco markers on the jigs (for marker-based vision)">🏷️<span class="lbl"> Markers</span></button>
      <button data-k="open" title="Move jigs: select, lock together, move / turn">✋<span class="lbl"> Move jigs</span></button></div>
    <div class="body">
      <div class="list" data-k="list"></div>
      <div class="row"><button data-k="lock" title="The selected jigs become one group: they are always selected and moved together">🔗 Lock together</button>
        <button data-k="unlock" title="Take the selected jigs out of their groups">Unlock</button>
        <button data-k="none" title="Select nothing">Clear</button></div>
      <div class="row"><button data-k="mode" title="Arrows = move X/Y/Z, ring = turn about Z">Move XYZ</button>
        <label title="Also move the parts that sit on a moved jig"><input type="checkbox" data-k="along" checked> take along what's on it</label></div>
      <div class="row"><span class="muted" data-k="first">offset of —</span></div>
      <div class="row"><label>X <input type="number" step="5" data-f="x"></label><label>Y <input type="number" step="5" data-f="y"></label>
        <label>Z <input type="number" step="5" data-f="z"></label><label>Rz° <input type="number" step="5" data-f="rz"></label></div>
      <div class="row"><button data-k="reset" title="The selected back to their CAD positions">Reset selected</button>
        <button data-k="resetall" title="Everything back (locks stay)">Reset all</button></div>
      <div class="row muted">mm / deg from the CAD start, robot base frame. Click in 3D = select (Ctrl-click = add).
        Typing moves the whole selection by the same amount.</div>
    </div>`;
  el.appendChild(panel);
  const q = s => panel.querySelector(s);
  const ui = { list: q('[data-k="list"]'), along: q('[data-k="along"]'), mode: q('[data-k="mode"]'), sum: q('[data-k="sum"]'),
               first: q('[data-k="first"]'), open: q('[data-k="open"]') };
  ui.along.checked = store.get("simJigsAlong", true);
  q('[data-k="markers"]').onclick = () => setMarkers(!markersOn);
  q('[data-k="markers"]').classList.toggle("on", markersOn);
  ui.along.onchange = () => store.set("simJigsAlong", ui.along.checked);
  function fillList() {
    const names = tops().map(pretty).sort((a, b) => (JIG.test(b) - JIG.test(a)) || a.localeCompare(b));
    let sep = false;
    ui.list.innerHTML = names.map(n => {
      const g = locks.findIndex(x => x.includes(n));
      const line = (!JIG.test(n) && !sep ? (sep = true, '<div class="sep"></div>') : "") +
        `<label class="${moved[n] ? "mv" : ""}"><input type="checkbox" data-n="${n}">${n}` +
        (g >= 0 ? ` <span class="tag" title="locked with ${locks[g].filter(x => x !== n).join(", ")}">🔗${g + 1}</span>` : "") + `</label>`;
      return line;
    }).join("");
    ui.list.querySelectorAll("[data-n]").forEach(c => c.onchange = () => select(c.dataset.n, true));
    ui.sum.textContent = Object.keys(moved).length ? ` · ${Object.keys(moved).length} moved` : "";
    showList();
  }
  function showList() { ui.list.querySelectorAll("[data-n]").forEach(c => { c.checked = sel.has(c.dataset.n); }); }
  function showFields() {
    const n = [...sel][0], f = n ? offsetOf(n) : null;
    ui.first.textContent = n ? `offset of ${n}${sel.size > 1 ? ` (+${sel.size - 1} more move along)` : ""}` : "select a jig";
    panel.querySelectorAll("[data-f]").forEach(i => { i.disabled = !f; i.value = f ? f[i.dataset.f] : ""; });
    ["lock", "unlock", "reset", "none"].forEach(k => { q(`[data-k="${k}"]`).disabled = !sel.size; });
    q('[data-k="lock"]').disabled = sel.size < 2;
  }
  panel.querySelectorAll("[data-f]").forEach(i => i.onchange = () => {
    const n = [...sel][0]; if (!n) return;
    const f = { ...offsetOf(n), [i.dataset.f]: +i.value || 0 };
    const D = matrixOf(n, f).multiply(M(n).clone().invert());   // what takes the first jig there; all move by it
    const names = movingSet();
    applyDelta(D, names, names.map(x => M(x).clone()));
    save(); attach();
  });
  ui.open.onclick = () => { open = !open; panel.classList.toggle("open", open); ui.open.classList.toggle("on", open); attach(); };
  let mode = "move";
  ui.mode.onclick = () => {
    mode = mode === "move" ? "turn" : "move";
    gizmo.setMode(mode === "turn" ? "rotate" : "translate");
    gizmo.showX = gizmo.showY = mode !== "turn";
    ui.mode.textContent = mode === "turn" ? "Turn Rz" : "Move XYZ"; ui.mode.classList.toggle("on", mode === "turn");
  };
  q('[data-k="lock"]').onclick = () => {
    const g = new Set(sel);                          // merge with the groups they were in
    locks = locks.filter(x => { if (x.some(n => g.has(n))) { x.forEach(n => g.add(n)); return false; } return true; });
    locks.push([...g]); sel = g; save(); attach();
    log("ev", `3D: locked together: ${[...g].join(", ")}`);
  };
  q('[data-k="unlock"]').onclick = () => {
    locks = locks.map(x => x.filter(n => !sel.has(n))).filter(x => x.length > 1); save(); attach();
  };
  q('[data-k="none"]').onclick = () => { sel = new Set(); attach(); };
  function reset(names) {
    const s = new Set(names); if (ui.along.checked) names.forEach(n => along(n).forEach(a => s.add(a)));
    s.forEach(n => { delete moved[n]; place(n); });
    save(); attach();
  }
  q('[data-k="reset"]').onclick = () => reset([...sel]);
  q('[data-k="resetall"]').onclick = () => reset(Object.keys(moved));

  // click in 3D (panel open): the top-level cell object under the pointer
  const ray = new THREE.Raycaster(); let down = null;
  renderer.domElement.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", e => {
    if (!open || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4 || gizmo.dragging) return;
    const r = renderer.domElement.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1), camera);
    const hit = ray.intersectObjects(tops(), true)[0];
    if (!hit) { if (!(e.ctrlKey || e.shiftKey)) { sel = new Set(); attach(); } return; }
    let o = hit.object; while (o.parent && o.parent !== cell()) o = o.parent;
    if (o.parent === cell()) select(pretty(o), e.ctrlKey || e.shiftKey || e.metaKey);
  });
  showFields();
  // another tab of this page changed the jigs: take its state (same browser = same localStorage)
  // (2026-11-13: was onCell, which took the already moved objects as the CAD start -> every move applied twice)
  window.addEventListener("storage", e => { if (e.key === "simJigs2:" + cellName() && cell() && orig.size) loadState(cellName()); });

  let empty = false;
  function setEmpty(on) {                            // calibration on the bare plate: jigs + parts out of the cell
    empty = !!on; tops().forEach(o => { o.visible = !empty; }); if (empty) { sel = new Set(); attach(); }
  }
  return { onCell: n => { onCell(n); setEmpty(empty); }, setEmpty, truth, model, setJigs, setMarkers, select: (n, add) => select(n, add), get moved() { return Object.fromEntries(Object.keys(moved).map(n => [n, offsetOf(n)])); },
           get locks() { return locks.map(g => g.slice()); }, get selected() { return [...sel]; } };
}
