// Tool camera for the 3D view (sim_scene.js loads it; panel bottom right of the 3D pane).
//
// Tool camera: a camera on the flange (joint 6), offset CAM.offset mm in the flange frame, looking along the tool
// (+z, the way the fingers point), image "up" = flange -y. The live view is drawn in the corner of the 3D canvas.
// "Photo" renders it at CAM.w x CAM.h and saves PNG + JSON through POST /vision/snap
// (-> tests/vision_lab/sim_shots/). The JSON has everything a vision script needs to check itself:
//   K (fx fy cx cy, pinhole, square pixels, no distortion), T_base_cam (OpenCV optical frame: x right, y down,
//   z forward; 4x4 row-major, mm, robot base frame), T_base_flange, joints, and the true pose of every moved object.
// A script asks for a photo with POST /vision/request (the mock emits "snap_request", this page takes it).
// Only objects marked userData.real (cell, robot, lights, floor) are in the photo - no axes, gizmos or overlays.
// The true jig poses in the JSON come from the Jigs panel (jig_layer.js).
// Where the TM5's built-in camera is: the lens of the end module's housing in Techman's link_6 mesh (tm5_links.glb) is a
// round recess centred at x 0, y +75 mm, between z 43 and the housing face at z 52 (joint-6 frame). The sim camera sits
// just in front of that face (z 53), so the recess walls don't block its view.
const CAM_DEFAULT = { offset: [0, 75, 53], fovY: 45, w: 1280, h: 960 };    // mm in the flange frame; deg; px
const CAM_KEY = "simToolCam2";                                              // v2: lens position from the robot model
const PIP_W = 320;                                                          // live view width, CSS px

export function addVisionLayer({ THREE, scene, camera, renderer, controls, el, L6, log, axes, cell, cellName, settle, truth, model, setAxes }) {
  const deg = Math.PI / 180;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} } };
  const CAM = { ...CAM_DEFAULT, ...store.get(CAM_KEY, {}) };

  // ---- tool camera -------------------------------------------------------------------------------------------
  const mount = new THREE.Group();                 // on the flange; the camera inside looks down its -z = flange +z
  L6.add(mount);
  const cam = new THREE.PerspectiveCamera(CAM.fovY, CAM.w / CAM.h, 5, 5000);
  cam.rotation.x = Math.PI;                        // -z -> +z (along the tool), y -> -y
  mount.add(cam);
  // no extra camera body: Techman's link_6 mesh already has the housing with the lens
  const helper = new THREE.CameraHelper(cam);      // the frustum in the 3D view (not in photos)
  helper.visible = false; scene.add(helper);
  function applyCam() {
    mount.position.set(...CAM.offset);
    cam.fov = CAM.fovY; cam.aspect = CAM.w / CAM.h; cam.far = 1200; cam.updateProjectionMatrix();
    helper.update();
    store.set(CAM_KEY, { offset: CAM.offset, fovY: CAM.fovY, w: CAM.w, h: CAM.h });
  }
  applyCam(); cam.far = 1200;

  // hide everything that isn't "real" (axes, gizmo, overlays of other layers) while the tool camera renders
  function renderReal(fn) {
    const hidden = [];
    scene.children.forEach(o => { if (!o.userData.real && o.visible) { o.visible = false; hidden.push(o); } });
    const toolAxes = axes.tool.visible; axes.tool.visible = false;
    try { return fn(); } finally { hidden.forEach(o => { o.visible = true; }); axes.tool.visible = toolAxes; }
  }

  let pipOn = store.get("simToolCamPip", false);
  const pipLabel = document.createElement("div");
  pipLabel.className = "vis-pip-label"; pipLabel.textContent = "Tool camera";
  el.appendChild(pipLabel);
  function afterRender() {                         // the live view, bottom right of the 3D canvas
    padLabels?.();
    helper.visible = pipOn && frustumOn;
    pipLabel.style.display = pipOn ? "" : "none";
    if (!pipOn) return;
    const W = el.clientWidth, H = el.clientHeight;
    const pw = Math.min(PIP_W, W * 0.45), ph = pw * CAM.h / CAM.w;
    const x = W - pw - 10, y = 10;                 // from the bottom left (WebGL viewport)
    pipLabel.style.right = "10px"; pipLabel.style.bottom = (y + ph) + "px";
    cam.updateMatrixWorld(true);
    const ac = renderer.autoClear;
    renderer.setScissorTest(true); renderer.setScissor(x, y, pw, ph); renderer.setViewport(x, y, pw, ph);
    renderReal(() => renderer.render(scene, cam));
    renderer.setScissorTest(false); renderer.setViewport(0, 0, W, H); renderer.autoClear = ac;
  }

  const m4 = M => { const e = M.elements; return [0, 1, 2, 3].map(r => [0, 1, 2, 3].map(c => +e[c * 4 + r].toFixed(5))); };
  function shoot() {                               // full-size photo: PNG data URL + the camera's numbers
    settle?.();                                    // the arm at the newest pose (the view plays ~0.2-0.6 s behind)
    L6.updateWorldMatrix(true, true);
    const rt = new THREE.WebGLRenderTarget(CAM.w, CAM.h, { type: THREE.FloatType, samples: 4 });
    const buf = new Float32Array(CAM.w * CAM.h * 4);
    try {
      renderReal(() => { renderer.setRenderTarget(rt); renderer.clear(); renderer.render(scene, cam); });
      renderer.readRenderTargetPixels(rt, 0, 0, CAM.w, CAM.h, buf);
    } finally { renderer.setRenderTarget(null); rt.dispose(); }
    const cv = document.createElement("canvas"); cv.width = CAM.w; cv.height = CAM.h;
    const cx = cv.getContext("2d"), img = cx.createImageData(CAM.w, CAM.h), d = img.data;
    const srgb = v => 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055);   // linear -> sRGB
    for (let r = 0; r < CAM.h; r++) {              // WebGL rows run bottom-up
      const src = (CAM.h - 1 - r) * CAM.w * 4, dst = r * CAM.w * 4;
      for (let i = 0; i < CAM.w * 4; i += 4) {
        d[dst + i] = srgb(buf[src + i]); d[dst + i + 1] = srgb(buf[src + i + 1]); d[dst + i + 2] = srgb(buf[src + i + 2]); d[dst + i + 3] = 255;
      }
    }
    cx.putImageData(img, 0, 0);
    const fy = (CAM.h / 2) / Math.tan(CAM.fovY * deg / 2);
    const opt = cam.matrixWorld.clone().multiply(new THREE.Matrix4().makeScale(1, -1, -1));   // three cam -> OpenCV axes
    const q = [0, 1, 2, 3, 4, 5].map(i => {        // joint angles, deg (L6's chain: joints[i].rotation.z)
      let o = L6; for (let k = 5; k > i; k--) o = o.parent.parent; return +(o.rotation.z / deg).toFixed(3); });
    const meta = {
      cell: cellName(), w: CAM.w, h: CAM.h, fov_y_deg: CAM.fovY,
      K: [[+fy.toFixed(3), 0, CAM.w / 2], [0, +fy.toFixed(3), CAM.h / 2], [0, 0, 1]],
      cam_offset_flange_mm: CAM.offset, joints_deg: q,
      T_base_cam: m4(opt), T_base_flange: m4(L6.matrixWorld),
      jig_model: model?.() ?? null,                // the jigs at the CAD start: pivot, box, marker corners
      board: boardPose ? { T_base_board: m4(boardPose), squares: [7, 5], square_mm: 30, marker_mm: 22, dict: "DICT_5X5_100" } : null,
      objects: truth(),                            // jig_layer.js: what was moved, and where to
      note: "mm, robot base frame; T_base_cam in OpenCV axes (x right, y down, z forward); objects: true pose of each " +
            "moved object relative to its CAD start (offset x y z mm, rz deg about its footprint centre) + its box now",
    };
    return { png: cv.toDataURL("image/png"), meta };
  }
  const RENDERER = new URLSearchParams(location.search).has("renderer");   // /all?renderer: the test renderer page
  // position pass (for reference photos): every pixel's 3D point (robot base, mm) and which cell object it is, at half
  // resolution: Float32 [x, y, z, id] per pixel, rows top-down. id = 1 + index of the top-level cell object
  // (meta.xyz_ids), -2 = something else real (robot, floor), 0 = nothing (background).
  const xyzMat = new THREE.ShaderMaterial({
    uniforms: { oid: { value: 0 } },
    vertexShader: "varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }",
    fragmentShader: "uniform float oid; varying vec3 vW; void main(){ gl_FragColor = vec4(vW, oid); }",
    side: THREE.DoubleSide });
  function shootXYZ() {
    const w = CAM.w / 2, h = CAM.h / 2, c = cell(), ids = {}, saved = [];
    c.children.forEach((o, i) => { ids[i + 1] = o.name.replace(/_/g, " "); });
    scene.traverse(m => {
      if (!m.isMesh) return;
      let top = m; while (top.parent && top.parent !== c && top.parent !== scene) top = top.parent;
      const id = top.parent === c ? c.children.indexOf(top) + 1 : -2;
      saved.push([m, m.onBeforeRender]);
      m.onBeforeRender = () => { xyzMat.uniforms.oid.value = id; xyzMat.uniformsNeedUpdate = true; };
    });
    const rt = new THREE.WebGLRenderTarget(w, h, { type: THREE.FloatType });
    const buf = new Float32Array(w * h * 4), bg = scene.background, cc = renderer.getClearColor(new THREE.Color()), ca = renderer.getClearAlpha();
    try {
      scene.background = null; scene.overrideMaterial = xyzMat; renderer.setClearColor(0x000000, 0);
      renderReal(() => { renderer.setRenderTarget(rt); renderer.clear(); renderer.render(scene, cam); });
      renderer.readRenderTargetPixels(rt, 0, 0, w, h, buf);
    } finally {
      renderer.setRenderTarget(null); rt.dispose(); scene.overrideMaterial = null; scene.background = bg; renderer.setClearColor(cc, ca);
      saved.forEach(([m, f]) => { m.onBeforeRender = f; });
    }
    const out = new Float32Array(w * h * 4);       // rows top-down, like the PNG
    for (let r = 0; r < h; r++) out.set(buf.subarray((h - 1 - r) * w * 4, (h - r) * w * 4), r * w * 4);
    const u8 = new Uint8Array(out.buffer); let bin = "";
    for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    return { xyz: btoa(bin), shape: [h, w, 4], ids };
  }
  async function snap(source = "button", id = null, opts = {}) {
    if (!cell()) throw new Error("no cell loaded");
    const { png, meta } = shoot();
    meta.source = source;
    let xyz = null;
    if (opts.xyz) { const x = shootXYZ(); xyz = x.xyz; meta.xyz_shape = x.shape; meta.xyz_ids = x.ids; }
    const r = await fetch("/vision/snap", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ png, meta, id, renderer: RENDERER, xyz }) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.msg || r.status);
    log("ev", `3D: photo saved: ${j.path}`);
    return j;
  }
  async function snapRequest(ev) {                 // a script's POST /vision/request - every open page gets it:
    if (ev.renderer && !RENDERER) return;          // a script that wants the renderer page (/all?renderer) only
    if (document.visibilityState !== "visible") {  // a page in a background tab waits, so a visible one answers
      await new Promise(r => setTimeout(r, 1500));
      const r = await fetch("/vision/result?id=" + encodeURIComponent(ev.id)).catch(() => null);
      if (r && r.ok) return;
    }
    snap("script", ev.id, { xyz: !!ev.xyz }).catch(e => { if (!/already taken/.test(e.message)) log("err", "photo failed: " + e.message); });
  }

  // ---- ChArUco calibration board (print_markers.py BOARD: 7 x 5 squares of 30 mm), for testing calibrate.py ------
  // A script turns it on with a pose (POST /vision/board {on, pose: [x, y, z, rz]} = the board centre, flat, face up).
  // Its frame as OpenCV's board: origin at the chessboard's top-left corner, x along the printed rows, y down the page,
  // z into the board. The photo's JSON gets board.T_base_board (the truth for the calibration tests).
  const BW = 7 * 30, BH = 5 * 30, BM = 10;           // chessboard and its white margin, mm
  let board = null, boardPose = null;
  function setBoard(ev) {
    if (board) { scene.remove(board); board = null; boardPose = null; }
    if (!ev.on) return;
    const tex = new THREE.TextureLoader().load("/sim/markers/charuco_board.png");
    tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
    board = new THREE.Mesh(new THREE.PlaneGeometry(BW + 2 * BM, BH + 2 * BM), new THREE.MeshStandardMaterial({ map: tex, roughness: .9 }));
    const [x, y, z, rz] = ev.pose || [-365, 7, 60, 0];
    board.position.set(x, y, z); board.rotation.set(0, 0, rz * deg);
    board.userData.real = true; scene.add(board);
    board.updateMatrixWorld(true);
    boardPose = board.matrixWorld.clone().multiply(new THREE.Matrix4().set(1, 0, 0, -BW / 2, 0, -1, 0, BH / 2, 0, 0, -1, 0, 0, 0, 0, 1));
  }

  // ---- panel -------------------------------------------------------------------------------------------------
  const css = document.createElement("style");
  css.textContent = `
    .vis-panel { position: absolute; z-index: 2; right: 10px; bottom: 10px; font: 12px system-ui, sans-serif; color: #222;
      background: #ffffffeb; border: 1px solid #c9ccd1; border-radius: 6px; padding: 6px 8px; max-width: 330px; }
    .vis-panel.pip { bottom: calc(20px + var(--pip-h, 240px)); }
    .vis-panel b { font-weight: 600; } .vis-panel .row { display: flex; gap: 4px; align-items: center; margin-top: 5px; flex-wrap: wrap; }
    .vis-panel button { font: inherit; padding: 2px 7px; border: 1px solid #b8bcc3; border-radius: 4px; background: #f6f7f8; cursor: pointer; }
    .vis-panel button.on { background: #2c6fbf; color: #fff; border-color: #2c6fbf; }
    .vis-panel input[type=number] { width: 54px; font: inherit; } .vis-panel select { font: inherit; max-width: 150px; }
    .vis-panel .body, .vis-panel .jog { display: none; } .vis-panel.open .body, .vis-panel.jogging .jog { display: block; }
    .vis-panel .jog button { min-width: 34px; }
    .vis-panel .pad-row { align-items: flex-start; gap: 12px; }
    .vis-panel .pad { display: grid; grid-template-columns: repeat(3, 38px); grid-auto-rows: 34px; gap: 3px; }
    .vis-panel .pad { grid-template-columns: repeat(3, 46px); grid-auto-rows: 40px; }
    .vis-panel .pad button { font-size: 14px; padding: 0; line-height: 1.05; }
    .vis-panel .pad button i { display: block; font: 600 11px system-ui, sans-serif; }
    .vis-panel .ax { font-weight: 600; } .vis-panel .ax.x, .vis-panel i.x { color: #e0322d; } .vis-panel .ax.y, .vis-panel i.y { color: #22a24a; }
    .vis-panel .ax.z, .vis-panel i.z { color: #2f6fde; } .vis-panel .pad .dot { display: grid; place-items: center; color: #888; }
    .vis-panel .side { display: flex; flex-direction: column; gap: 4px; } .vis-panel .side div { display: flex; gap: 4px; }
    .vis-panel .side div button { flex: 1; font-size: 13px; } .vis-panel .side select { font: inherit; } .vis-panel button:disabled { opacity: .45; }
    .vis-panel .muted { color: #666; } .vis-panel label { white-space: nowrap; }
    .vis-pip-label { position: absolute; z-index: 1; font: 11px system-ui, sans-serif; background: #000a; color: #fff; padding: 1px 6px; border-radius: 3px 3px 0 0; }`;
  document.head.appendChild(css);
  const panel = document.createElement("div");
  panel.className = "vis-panel";
  panel.innerHTML = `
    <div class="row" style="margin-top:0"><b>Camera</b><span style="flex:1"></span>
      <button data-k="pip" title="Show the tool camera's live view (bottom right)">Camera view</button>
      <button data-k="snap" title="Save a photo from the tool camera (tests/vision_lab/sim_shots/)">📷 Photo</button>
      <button data-k="jog" title="Free move: jog the arm (and so the camera) - the program and the taught points are not changed">✥ Free move</button>
      <button data-k="open" title="Camera settings: where it sits on the flange, field of view">⚙</button></div>
    <div class="jog" title="Moves only the sim arm (Listen node), not the program or the taught points. Needs the mock idle at its Listen node.">
      <div class="row pad-row">
        <div class="pad">
          <span></span><button data-a="1,1" title="+Y (keyboard ↑)">▲<i></i></button><span></span>
          <button data-a="0,-1" title="−X (←)">◀<i></i></button><span class="dot">✥</span><button data-a="0,1" title="+X (→)">▶<i></i></button>
          <span></span><button data-a="1,-1" title="−Y (↓)">▼<i></i></button><span></span>
        </div>
        <div class="side">
          <div><button data-k="frame" title="Tool: move along the tool tip's own X Y Z (the Tool XYZ triad). Base: along the robot base's X Y Z (the Base XYZ triad).">Tool frame</button>
            <select data-k="step" title="Step per click, mm / deg">
              <option>1</option><option>5</option><option selected>10</option><option>25</option><option>50</option></select></div>
          <button data-a="2,1" title="PgUp">+Z</button>
          <button data-a="2,-1" title="PgDn">−Z</button>
          <div><button data-a="5,1" title="Turn about Z (Q)">⟲ <b class="ax z">+Rz</b></button><button data-a="5,-1" title="Turn about Z (E)">⟳ <b class="ax z">−Rz</b></button></div>
        </div>
      </div>
      <div class="row"><button data-k="down" title="Camera straight down (Rx 180, Ry 0), keep x y z rz">Look down</button>
        <span class="muted" data-k="pose">—</span></div>
    </div>
    <div class="body">
      <div class="row"><span class="muted">Camera on flange (mm)</span>
        <label>x <input type="number" step="5" data-c="0"></label><label>y <input type="number" step="5" data-c="1"></label>
        <label>z <input type="number" step="5" data-c="2"></label><label>FOV° <input type="number" step="1" data-c="fov"></label>
        <label><input type="checkbox" data-k="frustum" checked> frustum</label></div>
    </div>`;
  el.appendChild(panel);
  const q = s => panel.querySelector(s);
  const ui = { pip: q('[data-k="pip"]'), snap: q('[data-k="snap"]'), frustum: q('[data-k="frustum"]') };
  let open = false, frustumOn = true;
  function showCam() {
    panel.querySelectorAll("[data-c]").forEach(i => { i.value = i.dataset.c === "fov" ? CAM.fovY : CAM.offset[+i.dataset.c]; });
    ui.pip.classList.toggle("on", pipOn);
    panel.classList.toggle("pip", pipOn);
    panel.style.setProperty("--pip-h", (Math.min(PIP_W, el.clientWidth * 0.45) * CAM.h / CAM.w + 18) + "px");
  }
  ui.pip.onclick = () => { pipOn = !pipOn; store.set("simToolCamPip", pipOn); showCam(); };
  ui.snap.onclick = () => { ui.snap.disabled = true; snap().catch(e => log("err", "photo failed: " + e.message)).finally(() => { ui.snap.disabled = false; }); };
  q('[data-k="open"]').onclick = () => { open = !open; panel.classList.toggle("open", open); q('[data-k="open"]').classList.toggle("on", open); };
  ui.frustum.onchange = () => { frustumOn = ui.frustum.checked; };
  // free move: POST /vision/jog (vision_api.py) - the arm only, never the program
  const fmt = p => p ? `x ${p[0].toFixed(1)}  y ${p[1].toFixed(1)}  z ${p[2].toFixed(1)}  rz ${p[5].toFixed(1)}` : "—";
  async function jog(body) {
    const btns = panel.querySelectorAll(".jog button"); btns.forEach(b => { b.disabled = true; });
    try {
      const r = await fetch("/vision/jog", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.msg || r.status);
      q('[data-k="pose"]').textContent = fmt(j.flange);
    } catch (e) { log("err", "free move: " + e.message); q('[data-k="pose"]').textContent = e.message; }
    finally { btns.forEach(b => { b.disabled = false; }); }
  }
  q('[data-k="jog"]').onclick = async () => {
    const on = panel.classList.toggle("jogging"); q('[data-k="jog"]').classList.toggle("on", on);
    if (on) { setAxes?.("tool", true); document.querySelectorAll('[data-axes="tool"]').forEach(b => b.classList.add("on")); padLabels(true); }
    if (on) { const r = await fetch("/vision/pose").then(r => r.json()).catch(() => null); q('[data-k="pose"]').textContent = fmt(r && r.flange); }
  };
  // the buttons move along the chosen frame's axes: Tool = the tool tip's own X Y Z (as its triad shows; Rz turns about
  // the tool's Z), Base = the robot base's X Y Z. Labels and colours = the axis (X red, Y green, Z blue, as the triads).
  let frame = store.get("simJogFrame", "tool");
  function labels() {
    q('[data-k="frame"]').textContent = frame === "tool" ? "Tool frame" : "Base frame";
    q('[data-k="frame"]').classList.toggle("on", frame === "tool");
    panel.querySelectorAll(".pad [data-a]").forEach(b => {
      const [a, s] = b.dataset.a.split(",").map(Number), i = b.querySelector("i");
      i.textContent = (s > 0 ? "+" : "−") + "XYZ"[a]; i.className = "xyz"[a];
    });
    L6.updateWorldMatrix(true, false);
    const down = frame === "tool" ? L6.matrixWorld.elements[10] < 0 : false;   // tool +Z points down (fingers) when looking down
    q('[data-a="2,1"]').innerHTML = `${down ? "⬇" : "⬆"} <b class="ax z">+Z</b>${frame === "tool" ? " tool" : " up"}`;
    q('[data-a="2,-1"]').innerHTML = `${down ? "⬆" : "⬇"} <b class="ax z">−Z</b>${frame === "tool" ? " tool" : " down"}`;
  }
  function padLabels(force) { if (force || panel.classList.contains("jogging")) { const t = performance.now(); if (force || t - (padLabels.t || 0) > 500) { padLabels.t = t; labels(); } } }
  q('[data-k="frame"]').onclick = () => { frame = frame === "tool" ? "base" : "tool"; store.set("simJogFrame", frame); labels(); };
  function step(a, s) {
    const d = [0, 0, 0, 0, 0, 0];
    d[a] = s * +q('[data-k="step"]').value;
    jog({ d, frame });
  }
  panel.querySelectorAll("[data-a]").forEach(b => b.onclick = () => { const [a, s] = b.dataset.a.split(",").map(Number); step(a, s); });
  window.addEventListener("keydown", e => {                // keyboard, while Free move is open and no field has focus
    if (!panel.classList.contains("jogging") || /INPUT|SELECT|TEXTAREA/.test(document.activeElement?.tagName || "")) return;
    const k = { ArrowUp: [1, 1], ArrowDown: [1, -1], ArrowLeft: [0, -1], ArrowRight: [0, 1], PageUp: [2, 1], PageDown: [2, -1],
                q: [5, 1], e: [5, -1] }[e.key];
    if (k && !panel.querySelector(".jog button:disabled")) { e.preventDefault(); step(...k); }
  });
  q('[data-k="down"]').onclick = async () => {
    const r = await fetch("/vision/pose").then(r => r.json()).catch(() => null);
    if (r && r.flange) jog({ to: [r.flange[0], r.flange[1], r.flange[2], 180, 0, r.flange[5]] });
  };
  panel.querySelectorAll("[data-c]").forEach(i => i.onchange = () => {
    if (i.dataset.c === "fov") CAM.fovY = Math.min(120, Math.max(10, +i.value || CAM_DEFAULT.fovY));
    else CAM.offset[+i.dataset.c] = +i.value || 0;
    CAM.offset = CAM.offset.slice(); applyCam(); showCam();
  });
  showCam();
  new ResizeObserver(showCam).observe(el);

  return { afterRender, snap, snapRequest, shoot, setBoard, get cam() { return { ...CAM }; } };
}
