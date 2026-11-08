// The TM5-900 cell in three.js as a module, for pages that already have the mock's /events (tmflow_all_view.html):
//   const sim = await createSim(el, { log });  sim.handle(ev) for every SSE event;  sim.setView("iso"|"top"|"side")
// Same robot, cell and motion as sim_view.html (which still has its own copy of this code). Files from /sim/.
// Parts follow the gripper: GRIP OK takes along the parts named by the last "carry" event (v4_replay.py sends the
// station's "Simulation: attach" names before each GRIP), else the cell part nearest the fingertips (within
// GRAB_MM). RELEASE / SET puts down everything held, where it is.
// The cell: cell.glb (v4 start), or the one a scenario reset names ("cell" in scenarios.json, e.g. cell_v5: the
// guide starts on base A) - swapped in on that reset.
// Spawned parts (cell_v8x2: bench 2's "frame1 #2", "plank3 #2", ... - names ending "#<n>"): hidden from the cell's load
// until the program's reload step sends a "spawn" event naming them; hidden again on Reset. The preview (Move robot)
// replays the spawn rows of manip_data (manipulability.py) like the GRIPs.
// Collisions (collision_layer.js, data from collision.py via /sim/collisions.json): the objects of a colliding move
// turn red while the 3D pane plays that move (the mock's numbered "move" events, applied at the pane's play time).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

// Techman nominal TM5-900 (tm5-900-nominal.urdf, tmr_ros1) = tm5_kin.GEOMETRY["techman"], mm
const D1 = 145.2, A2 = 429.0, A3 = 411.5, D4 = 122.3, D5 = 106.0, D6 = 113.15;
const CHAIN = [[[0, 0, D1], [0, 0, 0]], [[0, 0, 0], [-90, -90, 0]], [[A2, 0, 0], [0, 0, 0]],
               [[A3, 0, -D4], [0, 0, 90]], [[0, -D5, 0], [90, 0, 0]], [[0, -D6, 0], [90, 0, 0]]];
const TIP = 160;                                     // flange -> closed fingertips (bench_layout.json tip_mm)
const GAP_OPEN = 50, GAP_CLOSED = 12;                // finger gap [mm] (illustrative)
const NODE_SECS = { set: 3, grip: 4, release: 3 };   // tmflow_mock.NODE_TIME
const GRAB_MM = 40;                                  // GRIP takes a part whose box is this close to the fingertips
const PARTS = /^(plank|piece|frame|guide)/i;         // what can be carried (cell.glb names)
const SPAWNED = /#\d+$/;                             // parts that only appear at a "spawn" (bench 2: "frame1 #2")
const deg = Math.PI / 180;
const BASE = "/sim/";

export function createSim(el, { log = () => {} } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled = true;
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf4f5f6);     // TMflow has no dark theme: stay light
  THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
  const camera = new THREE.PerspectiveCamera(40, 1, 10, 20000);
  camera.up.set(0, 0, 1);
  const controls = new OrbitControls(camera, renderer.domElement);
  const views = { iso: [[900, -1500, 1100], [-450, 0, 200]], top: [[-450, 0, 2600], [-450, 0, 0]],
                  side: [[-450, -2200, 400], [-450, 0, 300]] };
  function setView(v) { camera.position.set(...views[v][0]); controls.target.set(...views[v][1]); controls.update(); }
  setView("iso");

  scene.add(new THREE.HemisphereLight(0xffffff, 0x777766, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(800, -1200, 2500);
  sun.castShadow = true;
  Object.assign(sun.shadow.camera, { left: -1500, right: 1500, top: 1500, bottom: -1500, far: 6000 });
  sun.shadow.mapSize.set(2048, 2048);
  scene.add(sun);
  const floorZ = -750 - 5;                           // bench_cell_v4.TABLE_H below the table top
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(6000, 6000), new THREE.MeshStandardMaterial({ color: 0xe2e4e6 }));
  floor.position.z = floorZ; floor.receiveShadow = true; scene.add(floor);
  const grid = new THREE.GridHelper(6000, 60, 0x999999, 0xcfd2d6);
  grid.rotation.x = Math.PI / 2; grid.position.z = floorZ + 1; scene.add(grid);
  // XYZ triads (x red, y green, z blue, labelled, drawn on top): the robot base frame and the tool frame at the
  // fingertips (z along the gripper, x the fingers' closing direction) - the frames of the Adjust panel's Base / Tool
  function triad(len, tag) {
    const g = new THREE.Group();
    [[1, 0, 0, 0xe0322d, "X"], [0, 1, 0, 0x22a24a, "Y"], [0, 0, 1, 0x2f6fde, "Z"]].forEach(([x, y, z, c, n]) => {
      const dir = new THREE.Vector3(x, y, z);
      const a = new THREE.ArrowHelper(dir, new THREE.Vector3(), len, c, len * .16, len * .08);
      a.traverse(o => { if (o.material) { o.material.depthTest = false; o.material.transparent = true; } o.renderOrder = 999; });
      a.line.material.linewidth = 2;
      g.add(a);
      const cv = document.createElement("canvas"); cv.width = 128; cv.height = 64;
      const cx = cv.getContext("2d");
      cx.font = "bold 44px system-ui, sans-serif"; cx.textAlign = "center"; cx.textBaseline = "middle";
      cx.lineWidth = 6; cx.strokeStyle = "#fff"; cx.strokeText(n + tag, 64, 34);
      cx.fillStyle = "#" + c.toString(16).padStart(6, "0"); cx.fillText(n + tag, 64, 34);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), depthTest: false, transparent: true }));
      sp.scale.set(len * .36, len * .18, 1); sp.position.copy(dir).multiplyScalar(len * 1.16); sp.renderOrder = 1000;
      g.add(sp);
    });
    return g;
  }
  const axesStore = (() => { try { return JSON.parse(localStorage.getItem("simAxes") || "null"); } catch { return null; } })();
  const axes = { base: triad(250, ""), tool: triad(110, "t") };
  scene.add(axes.base);
  axes.base.visible = axesStore ? !!axesStore.base : true;
  axes.tool.visible = axesStore ? !!axesStore.tool : false;
  function setAxes(which, on) {
    axes[which].visible = on;
    try { localStorage.setItem("simAxes", JSON.stringify({ base: axes.base.visible, tool: axes.tool.visible })); } catch {}
    return on;
  }

  const loader = new GLTFLoader();
  function shade(root, opts = {}) {
    root.traverse(o => { if (o.isMesh) {
      o.castShadow = o.receiveShadow = true;
      if (opts.flat) { o.material.flatShading = true; o.material.needsUpdate = true; }
      if (!o.geometry.attributes.normal) o.geometry.computeVertexNormals();
      if (/^(frame|Table)/.test(o.name)) { o.material.transparent = true; o.material.opacity = o.name === "Table" ? .9 : .8; }
    } });
  }
  let cell = null, cellName = null, loadedName = null;   // loadedName: the cell whose .glb is in the scene
  const start = new Map();                           // carriable part -> where it was in cell.glb (for a reset)
  const spawnable = new Set();                       // parts hidden until a "spawn" (SPAWNED names)
  const hideSpawned = () => spawnable.forEach(o => { o.visible = false; });
  function spawn(names) {                            // the program's reload step: these parts appear (start poses)
    let n = 0;
    for (const nm of names || []) { const o = partByName(nm); if (o) { o.visible = true; n++; } }
    return n;
  }
  function loadCell(name) {                          // "cell" (v4 start) or "cell_v5" (guide on base A)
    if (name === cellName) return;
    cellName = name;
    loader.load(BASE + name + ".glb", g => {
      if (name !== cellName) return;                 // another cell asked for meanwhile
      if (cell) { held.forEach(([o]) => o.removeFromParent()); held = []; cell.removeFromParent(); }
      start.clear(); spawnable.clear();
      shade(g.scene, { flat: true }); scene.add(g.scene); cell = g.scene;
      cell.traverse(o => { if (o !== cell && PARTS.test(o.name))
        start.set(o, { parent: o.parent, pos: o.position.clone(), quat: o.quaternion.clone(), scale: o.scale.clone() }); });
      start.forEach((_, o) => { if (SPAWNED.test(o.name)) spawnable.add(o); });
      hideSpawned(); loadedName = name;
      log("ev", `3D: cell ${name}.glb`);
    },
      undefined, e => log("err", `${name}.glb not loaded: ` + e.message));
  }
  // start on the newest cell: the default preset's (scenarios.json "default": true), until a run's reset says otherwise
  fetch("/scenarios").then(r => r.ok ? r.json() : null).then(j => {
    const d = j && (j.scenarios.find(s => s.default) || null);
    const c = d && d.cell;
    if (c && cellName === "cell" && !gotReset) { loadCell(c); manip?.setCell(c); coll?.setCell(c); }
  }).catch(() => {});
  let gotReset = false;                              // a run's (or the robot viewer's) reset already chose the cell
  loadCell("cell");

  // robot: each joint a fixed group (URDF origin: xyz, then R = Rz Ry Rx) holding a group that turns about z
  const white = new THREE.MeshStandardMaterial({ color: 0xeeeeea, roughness: .5 });
  const grey = new THREE.MeshStandardMaterial({ color: 0x55585e, roughness: .6 });
  const blue = new THREE.MeshStandardMaterial({ color: 0x2c6fbf, roughness: .5 });
  function cyl(parent, a, b, r, mat) {
    const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, va.distanceTo(vb), 32), mat);
    m.position.copy(va).add(vb).multiplyScalar(.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vb.clone().sub(va).normalize());
    m.castShadow = true; parent.add(m); return m;
  }
  function boxAt(parent, lo, hi, mat) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), mat);
    m.position.set((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2);
    m.castShadow = true; parent.add(m); return m;
  }
  const joints = [];
  let parent = scene;
  for (const [xyz, rpy] of CHAIN) {
    const fixed = new THREE.Group();
    fixed.position.set(...xyz);
    fixed.rotation.set(rpy[0] * deg, rpy[1] * deg, rpy[2] * deg, "ZYX");
    const turn = new THREE.Group();
    fixed.add(turn); parent.add(fixed); joints.push(turn); parent = turn;
  }
  const [L1, L2, L3, L4, L5, L6] = joints;
  const simple = [];                                 // shown until (or if not) Techman's link meshes load
  const S = m => { simple.push(m); return m; };
  S(cyl(scene, [0, 0, 0], [0, 0, D1 - 40], 80, white)); S(cyl(scene, [0, 0, 0], [0, 0, 12], 95, grey));
  S(cyl(L1, [0, 0, -40], [0, 0, 60], 72, white));
  S(cyl(L2, [0, 0, -10], [0, 0, 150], 70, blue)); S(cyl(L2, [0, 0, 70], [A2, 0, 70], 52, white));
  S(cyl(L3, [0, 0, 20], [0, 0, 140], 60, blue)); S(cyl(L3, [0, 0, 60], [A3, 0, 60], 42, white));
  S(cyl(L3, [A3, 0, 60], [A3, 0, -D4 - 45], 48, white));
  S(cyl(L4, [0, 0, -45], [0, 0, 45], 50, blue)); S(cyl(L4, [0, 0, 0], [0, -D5 + 45, 0], 46, white));
  S(cyl(L5, [0, 0, -45], [0, 0, 45], 46, blue)); S(cyl(L5, [0, 0, 0], [0, -D6 + 10, 0], 42, white));
  S(cyl(L6, [0, 0, -10], [0, 0, 0], 32, grey));
  axes.tool.position.set(0, 0, TIP); L6.add(axes.tool);   // tool frame at the fingertips (TCP)
  loader.load(BASE + "tm5_links.glb", g => {         // link_0 on the base, link_i on joint i
    for (let i = 0; i <= 6; i++) {
      const n = g.scene.getObjectByName("link_" + i);
      if (n) { shade(n); (i === 0 ? scene : joints[i - 1]).add(n); }
    }
    simple.forEach(m => m.removeFromParent());
  }, undefined, e => log("err", "tm5_links.glb not loaded (simple shapes instead): " + e.message));
  // gripper: body 94 x 90 x 123 (Schunk EGP box, as in the RoboDK station: bench_cell_v4.EGP) + two fingers to TIP
  const egpBody = boxAt(L6, [-47, -45, 0], [47, 45, 123], grey);
  const fingers = [-1, 1].map(() => boxAt(L6, [-1.5, -4, 123], [1.5, 4, TIP], new THREE.MeshStandardMaterial({ color: 0xd0d3d8 })));
  let gap = GAP_OPEN, gapFrom = GAP_OPEN, gapTo = GAP_OPEN, gapT0 = 0, gapDur = 1;
  const setGap = g => { fingers[0].position.x = -g / 2 - 1.5; fingers[1].position.x = g / 2 + 1.5; };
  setGap(gap);
  function animateGrip(to, secs) { gapFrom = gap; gapTo = to; gapT0 = performance.now(); gapDur = Math.max(.2, secs) * 1000; }

  const moveLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
    new THREE.LineBasicMaterial({ color: 0xe60012 }));
  moveLine.visible = false; scene.add(moveLine);

  // parts follow the gripper
  let held = [], carry = null;                       // held: [[part, parent before]]; carry: names for the next GRIP
  const heldName = () => !held.length ? null : held.length <= 3 ? held.map(([o]) => o.name).join(", ")
    : `${held[0][0].name} + ${held.length - 1} parts`;
  function settle() {                               // the arm at the newest joint sample (it stands still at a GRIP /
    if (buf.length) {                                // RELEASE), also when the render loop is throttled (hidden tab)
      const [at, q] = buf[buf.length - 1];
      shown = q.slice(); floorAt = at;               // playback never goes back before this
    }
    shown.forEach((a, i) => joints[i].rotation.z = a * deg);
    L6.updateWorldMatrix(true, false);
  }
  function tipWorld() { L6.updateWorldMatrix(true, false); return new THREE.Vector3(0, 0, TIP - 10).applyMatrix4(L6.matrixWorld); }
  function grab() {
    if (!cell || held.length) return;
    settle();
    if (carry) {                                     // exactly what the RoboDK station attaches
      const names = carry, missing = [];
      carry = null;
      for (const n of names) {
        const o = cell.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(n));   // GLTFLoader: "piece A1" -> "piece_A1"
        if (o) { held.push([o, o.parent]); L6.attach(o); } else missing.push(n);
      }
      if (missing.length) log("err", `3D: not in cell.glb, not carried: ${missing.join(", ")}`);
      if (held.length) return log("ev", `3D: ${heldName()} ${held.length > 1 ? "follow" : "follows"} the gripper`);
    }
    const tip = tipWorld(), box = new THREE.Box3();
    let best = null, bestD = GRAB_MM;
    cell.traverse(o => {
      if (o === cell || !PARTS.test(o.name) || !o.visible || (o.parent !== cell && PARTS.test(o.parent.name))) return;
      const d = box.setFromObject(o).distanceToPoint(tip);
      if (d < bestD) { best = o; bestD = d; }
    });
    if (!best) return log("ev", `3D: GRIP OK, but no part within ${GRAB_MM} mm of the fingertips (${tip.toArray().map(v => v.toFixed(0)).join(", ")})`);
    held = [[best, best.parent]];
    L6.attach(best);
    log("ev", `3D: ${best.name} follows the gripper`);
  }
  function drop() {
    if (!held.length) return;
    settle();
    held.forEach(([o, from]) => from.attach(o));
    log("ev", `3D: ${heldName()} put down`);
    held = [];
  }

  // joint motion: "j" samples (25 Hz, each with the mock's time "at" the joints are for) played back `delay` s behind
  // the newest, interpolated between the two samples around the play time: the motion the mock computed, at its own
  // pace, whatever the network or the speed slider does - no easing lag, no catch-up jumps. Until the first "j"
  // (an older mock), the 5 Hz "state" joints feed the same buffer.
  // The delay adapts to how late samples come (a busy PC delivers them in bursts): the late ones' excess over the
  // lowest delay, decaying over ~10 s, plus a margin; 0.1 .. 0.6 s.
  let shown = [0, 0, 90, 0, 90, 0], buf = [], off = null, jSeen = false, floorAt = -Infinity, fast = 1;
  let jitter = 0.1, delay = 0.15;
  function pushJoints(at, q) {
    const now = performance.now() / 1000, l = now - at;
    off = off === null || l < off ? l : off + (l - off) * 0.01;   // clock offset: lowest delay seen, slowly relaxed
    jitter = Math.max(l - off, jitter * 0.996);
    delay = Math.min(0.6, Math.max(0.1, jitter + 0.05));
    const end = buf.length ? buf[buf.length - 1][0] : -Infinity;
    if (at <= end) { if (at < end - 1) { buf = []; floorAt = -Infinity; } else return; }   // repeat, or a restarted mock
    buf.push([at, q.slice()]);
    while (buf.length > 2 && buf[1][0] < at - 3) buf.shift();       // hidden tab: no render loop pruning
  }
  function playback() {                              // the joints at play time, from buf
    if (!buf.length || off === null) return shown;
    const tr = Math.max(floorAt, performance.now() / 1000 - off - delay);
    while (buf.length > 2 && buf[1][0] <= tr) buf.shift();         // keep one sample at or before tr
    const [a0, q0] = buf[0];
    if (tr <= a0 || buf.length === 1) return q0;
    const [a1, q1] = buf[1];
    const s = Math.min(1, (tr - a0) / (a1 - a0));
    return q0.map((a, i) => a + (q1[i] - a) * s);
  }
  const gripperGap = text => /^closed/.test(text) ? GAP_CLOSED : text === "open" ? GAP_OPEN : null;

  function handle(ev) {
    if (liveSnap && ["carry", "grip", "node", "reset", "spawn"].includes(ev.t)) { pending.push(ev); return; }   // previewing
    switch (ev.t) {
      case "hello": off = null; buf = []; floorAt = -Infinity; jitter = 0.1; if (ev.fast) fast = ev.fast; break;   // (re)connected
      case "j": jSeen = true; pushJoints(ev.at, ev.q); break;
      case "speed": fast = ev.fast || fast; break;
      case "state": {
        if (!jSeen) pushJoints(ev.at, ev.joints);
        if (ev.fast) fast = ev.fast;
        const g = gripperGap(ev.gripper);
        if (g !== null && performance.now() - gapT0 > gapDur && Math.abs(g - gap) > .5) animateGrip(g, .3);
        break;
      }
      case "node":
        if (ev.kind === "grip") animateGrip(GAP_CLOSED, NODE_SECS.grip / fast);   // the node's time at this speed
        if (ev.kind === "release" || ev.kind === "set") { animateGrip(GAP_OPEN, NODE_SECS[ev.kind] / fast); drop(); }
        break;
      case "grip": if (ev.result === "ok") grab(); else carry = null; break;
      case "carry":                                  // from the script (POST /step): what the next GRIP takes along
        if (ev.action === "grip") carry = (ev.parts || []).slice();
        break;
      case "spawn": {                                // the program's reload step (v8x2): the next bench's parts appear
        const n = spawn(ev.parts);
        log("ev", `3D: ${n} parts reloaded into the jig (${(ev.parts || []).slice(0, 2).join(", ")}${(ev.parts || []).length > 2 ? " ..." : ""})`);
        break;
      }
      case "reset":                                  // a scenario reset the mock: parts back where they started
        gotReset = true;
        held = []; carry = null; manip?.setCell(ev.cell);
        movesAt = []; coll?.reset(); coll?.setCell(ev.cell || "cell");
        if ((ev.cell || "cell") !== cellName) { loadCell(ev.cell || "cell"); animateGrip(GAP_OPEN, .2); break; }
        start.forEach((s, o) => { s.parent.add(o); o.position.copy(s.pos); o.quaternion.copy(s.quat); o.scale.copy(s.scale); });
        hideSpawned();
        animateGrip(GAP_OPEN, .2); moveLine.visible = false;
        break;
      case "move":
        moveLine.geometry.setFromPoints([new THREE.Vector3(...ev.frm), new THREE.Vector3(...ev.to)]);
        moveLine.visible = true;
        movesAt.push([ev.at ?? -Infinity, ev.n || null]);   // n: the program's move number (Listen-node moves)
        break;
    }
  }
  // the move the pane shows now: "move" events take effect at the play time (the joints run `delay` s behind)
  let movesAt = [];
  function playMoves() {
    const tr = off === null ? Infinity : Math.max(floorAt, performance.now() / 1000 - off - delay);
    let n;
    while (movesAt.length && movesAt[0][0] <= tr) n = movesAt.shift()[1];
    if (n !== undefined) { coll?.setMove(n); if (n !== null) onMoveCb?.(n); }
  }

  function resize() {
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(el); resize();
  // preview (manip_layers' "move the robot" slider): the arm at a point of the program path, and the parts where the
  // program's GRIPs / RELEASEs up to that point have put them (replayed from the cell's start, every time).
  // The live state (parts, held) is kept aside and put back by end(); gripper events from a run that arrive meanwhile
  // wait and are applied after it.
  let preview = null, previewGap = null, liveSnap = null, pending = [], onMoveCb = null;
  const setJ = q => { q.forEach((a, i) => joints[i].rotation.z = a * deg); L6.updateWorldMatrix(true, false); };
  const partByName = n => cell && cell.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(n));
  const previewApi = {
    path(P, s) {                                   // P: manip_data's program points (q, grip, grip_parts); s: 0..len-1
      if (!cell || !P.length || !P[0].q) return null;
      if (!liveSnap) {
        const m = new Map();
        start.forEach((_, o) => m.set(o, { parent: o.parent, pos: o.position.clone(), quat: o.quaternion.clone(), vis: o.visible }));
        liveSnap = { m, held: held.slice() };
      }
      start.forEach((st, o) => { st.parent.add(o); o.position.copy(st.pos); o.quaternion.copy(st.quat); o.scale.copy(st.scale); });
      hideSpawned();
      const k = Math.min(Math.floor(s), P.length - 1), f = s - k;
      let ph = [], closed = false;
      const missing = new Set();
      for (let n = 0; n <= k; n++) {
        const t = P[n];
        if (t.spawn) spawn(t.spawn);                 // a reload step after this point: the next bench's parts appear
        if (!t.grip) continue;
        setJ(t.q);
        if (t.grip === "grip") {
          for (const name of t.grip_parts || []) {
            const o = partByName(name);
            if (o) { ph.push([o, o.parent]); L6.attach(o); } else missing.add(name);
          }
          closed = true;
        } else { ph.forEach(([o, from]) => from.attach(o)); ph = []; closed = false; }
      }
      const a = P[k], b = P[Math.min(k + 1, P.length - 1)];
      preview = a.q.map((v, j) => v + (b.q[j] - v) * f);
      previewGap = closed ? GAP_CLOSED : GAP_OPEN;
      return { closed, carrying: ph.map(([o]) => o.name), missing: [...missing], cell: cellName };
    },
    end() {                                        // back to live: parts and held as before, then the waiting events
      preview = previewGap = null;
      if (liveSnap) {
        liveSnap.m.forEach((v, o) => { v.parent.add(o); o.position.copy(v.pos); o.quaternion.copy(v.quat); o.visible = v.vis; });
        held = liveSnap.held; liveSnap = null;
      }
      const ev = pending; pending = []; ev.forEach(handle);
    },
    onMove(cb) { onMoveCb = cb; },                 // a running program's move number n (path point n - 1), at play time
    get active() { return !!liveSnap; },
    get fast() { return fast; },                   // the page's Speed (x real time), for the slider's speed limit
  };
  function setPreview(q, closed = null) {          // joints only (kept for older callers)
    preview = q ? q.slice() : null;
    previewGap = q && closed !== null ? (closed ? GAP_CLOSED : GAP_OPEN) : null;
  }
  renderer.setAnimationLoop(() => {
    shown = playback();
    playMoves();
    (preview || shown).forEach((a, i) => joints[i].rotation.z = a * deg);
    const u = Math.min(1, (performance.now() - gapT0) / gapDur);
    gap = gapFrom + (gapTo - gapFrom) * u; setGap(previewGap ?? gap);
    controls.update(); renderer.render(scene, camera);
    if (frameCb) try { frameCb(renderer.domElement); } catch (e) { frameCb = null; log("err", "frame hook: " + e.message); }
  });
  let frameCb = null;                                // onFrame: called right after each render (the video export)
  // manipulability layers (manip_layers.js, data from manipulability.py): own panel, bottom left; optional
  let manip = null;
  import(BASE + "manip_layers.js").then(m => m.addManipLayers({ THREE, scene, camera, joints, el, base: BASE, tip: TIP, log, setPreview, previewApi }))
    .then(m => { manip = m; manip.setCell(cellName); }).catch(e => log("err", "manipulability layers not loaded: " + e.message));
  // collisions (collision_layer.js, collision.py's hits for the cell's moves file): own panel, top right; optional
  let coll = null;
  import(BASE + "collision_layer.js").then(m => m.addCollisionLayer({ THREE, scene, el, base: BASE, log,
    extra: { EGP: [egpBody, ...fingers] } }))
    .then(m => { coll = m; coll.setCell(cellName); coll.onPick = n => manip?.jump(n - 1); })   // a hit clicked: the timeline jumps to that move
    .catch(e => log("err", "collision layer not loaded: " + e.message));
  // a preset's cell for the 3D view without a run (the video export): resolves once its .glb is in the scene
  function useCell(c) {
    c = c || "cell";
    loadCell(c); manip?.setCell(c); coll?.setCell(c);
    return new Promise((res, rej) => {
      const t0 = performance.now(), iv = setInterval(() => {
        if (loadedName === c) { clearInterval(iv); res(c); }
        else if (performance.now() - t0 > 20000) { clearInterval(iv); rej(new Error(`${c}.glb not loaded`)); }
      }, 100);
    });
  }
  return { handle, setView, camera, controls, setAxes, useCell, onFrame(cb) { frameCb = cb; }, get canvas() { return renderer.domElement; }, axesOn: w => axes[w].visible, scene, joints, get held() { return heldName(); }, get delay() { return delay; },
           get manip() { return manip; }, get collisions() { return coll; } };
}
