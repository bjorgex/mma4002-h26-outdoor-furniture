// Collisions in the mock's 3D cell view (sim_scene.js in /all, sim_view.html at /sim/).
//   import("/sim/collision_layer.js").then(m => m.addCollisionLayer({ THREE, scene, el, base: "/sim/", log, extra }))
// Data: /sim/collisions.json?cell=<cell> = collision.py's check_program (parts check on) for that cell's moves file
// (collision_view.py; the server recomputes it in the background when the moves file, the cell or collision.py
// changed, and this panel polls until it is done). No collision maths here: one source of truth.
// While a program plays, the mock numbers each Listen-node move ("move" events, n = the program's move number);
// setMove(n) tints red every object of that move's colliding pairs (robot links, gripper, carried parts, fixtures)
// for the whole move (collision.py reports per move, not per sample), shows a red banner and logs the hit once.
// The "Collisions" panel (top right of the 3D pane) lists every hit; clicking one pins its objects red where they
// are now (the live view can't seek back to that move), click again to unpin. Choices kept in localStorage.

const KEY = "collisionLayer.v1";
const DEF = { open: true, tint: true };
const RED = 0xff1a1a;

function load() {
  try { return { ...DEF, ...JSON.parse(localStorage.getItem(KEY) || "{}") }; } catch (e) { return { ...DEF }; }
}
function save(st) { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* private window */ } }
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

export async function addCollisionLayer({ THREE, scene, el, base = "/sim/", log = () => {}, extra = {},
                                          pos = "right:10px;top:10px" }) {
  const st = load();
  let data = null, cell = null, move = null, pinned = null, poll = null, loggedFor = null, gen = 0, onPick = null;

  // ---- tint: each mesh gets a red clone of its material, the original back on untint -----------------------
  const tinted = new Map();                          // mesh -> original material
  function find(name) {                              // cell.glb / tm5_links.glb node names (GLTFLoader sanitizes)
    if (extra[name]) return extra[name];
    const o = scene.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(name)) || scene.getObjectByName(name);
    return o ? [o] : [];
  }
  function redOf(m) {
    const c = m.clone();
    if (c.color) c.color.setHex(RED);
    if (c.emissive) { c.emissive.setHex(0x880000); c.emissiveIntensity = 1; }
    return c;
  }
  function tintNames(names) {
    const missing = [];
    for (const n of names) {
      const objs = find(n);
      if (!objs.length) missing.push(n);
      objs.forEach(obj => obj.traverse(o => {
        if (!o.isMesh || tinted.has(o)) return;
        tinted.set(o, o.material);
        o.material = Array.isArray(o.material) ? o.material.map(redOf) : redOf(o.material);
      }));
    }
    return missing;
  }
  function untint() {
    tinted.forEach((orig, o) => {
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose());
      o.material = orig;
    });
    tinted.clear();
  }
  const hitsOf = n => (data && data.hits || []).filter(h => h.move === n);
  const namesOf = hs => [...new Set(hs.flatMap(h => h.objects || h.pairs.flat()))];
  function redraw() {
    untint();
    if (!st.tint) return;
    const names = namesOf(hitsOf(move));
    if (pinned) names.push(...namesOf([pinned]));
    const missing = tintNames(names);
    if (missing.length && move !== loggedFor) log("err", `collisions: not in the 3D view, not tinted: ${missing.join(", ")}`);
  }

  // ---- panel ---------------------------------------------------------------------------------------------
  if (getComputedStyle(el).position === "static") el.style.position = "relative";
  const box = document.createElement("div");
  box.className = "coll-panel";
  box.style.cssText = `position:absolute;${pos};z-index:5;width:300px;max-height:calc(100% - 20px);overflow:auto;` +
    "background:#ffffffeb;color:#222;border:1px solid #ccc;border-radius:8px;padding:8px 10px;font:12px/1.35 system-ui,sans-serif;";
  box.innerHTML = `<style>
      .coll-panel label{display:block;margin:2px 0}.coll-panel input{vertical-align:middle}
      .coll-panel .hit{padding:3px 4px;margin:2px 0;border-radius:4px;cursor:pointer;border:1px solid transparent}
      .coll-panel .hit:hover{background:#f6e3e3}.coll-panel .hit.now{background:#ff1a1a;color:#fff}
      .coll-panel .hit.pin{border-color:#ff1a1a}.coll-panel .pairs{font:11px ui-monospace,Consolas,monospace;color:inherit;opacity:.8}
      .coll-panel .ok{color:#1e8a4c;font-weight:600}.coll-panel .bad{color:#c0392b;font-weight:600}</style>
    <div style="display:flex;justify-content:space-between;align-items:center;cursor:pointer" data-k="toggle">
      <b>Collisions <span data-k="count"></span></b><span data-k="arrow">▾</span></div>
    <div data-k="banner" style="display:none;margin:6px 0 2px;padding:4px 6px;border-radius:5px;background:#ff1a1a;color:#fff;font-weight:600"></div>
    <div data-k="body">
      <label><input type="checkbox" data-s="tint"> tint colliding objects red while they collide</label>
      <div data-k="state" style="margin:4px 0;color:#666"></div>
      <div data-k="list"></div>
      <div style="color:#666;font-size:11px;margin-top:4px">From collision.py (robot links + gripper vs fixtures and parts,
        carried parts vs parts, fixtures and the arm), per move of the program the mock plays. Click a hit to pin its
        objects red and jump the 3D view (timeline) to that move; click again to unpin.</div>
    </div>`;
  el.appendChild(box);
  const q = k => box.querySelector(`[data-k="${k}"]`);
  const tintBox = box.querySelector('[data-s="tint"]');
  tintBox.checked = st.tint;
  tintBox.onchange = () => { st.tint = tintBox.checked; save(st); redraw(); };
  q("toggle").onclick = () => { st.open = !st.open; save(st); panel(); };
  ["pointerdown", "wheel"].forEach(t => box.addEventListener(t, e => e.stopPropagation()));
  q("list").addEventListener("click", e => {
    const d = e.target.closest(".hit");
    if (!d) return;
    const h = data.hits[+d.dataset.i];
    pinned = pinned === h ? null : h;
    if (pinned) try { onPick?.(h.move); } catch (err) { log("err", "jump to the collision: " + err.message); }
    redraw(); panel();
  });

  function panel() {
    q("body").style.display = st.open ? "" : "none"; q("arrow").textContent = st.open ? "▾" : "▸";
    const hits = data && data.hits, n = data && data.n_moves;
    const now = hitsOf(move);
    q("banner").style.display = now.length ? "" : "none";
    if (now.length) q("banner").textContent = `COLLISION in move #${move} ${now[0].name}: ` +
      now.flatMap(h => h.pairs.map(p => p.join(" / "))).slice(0, 4).join(", ") +
      (now.reduce((s, h) => s + h.pairs.length, 0) > 4 ? " …" : "");
    let s = "";
    if (!data) s = "loading…";
    else if (data.state === "none") s = esc(data.error || "no moves file for this cell");
    else if (data.state === "error") s = `<span class="bad">check failed:</span> ${esc(data.error)}`;
    if (data && data.state === "computing")
      s = `checking ${esc(data.moves_file || "the moves file")} with collision.py… (${Math.round(data.running_s || 0)} s, ~30 s for v8)` +
          (hits ? "<br>(the list below is from before the change)" : "");
    if (hits) {
      const head = data.free ? `<span class="ok">collision-free</span>: all ${n} moves of ${esc(data.moves_file)}`
        : `<span class="bad">${hits.length} colliding move${hits.length > 1 ? "s" : ""}</span> of ${n} in ${esc(data.moves_file)}`;
      s = (s ? s + "<br>" : "") + head + `<br><span style="font-size:11px">checked ${esc(data.generated)}, cell ${esc(data.cell_file)}` +
        (move ? `, now playing move ${move}` : "") + "</span>";
    }
    q("state").innerHTML = s;
    q("count").innerHTML = !hits ? "" : data.free ? '<span class="ok">✓ free</span>' : `<span class="bad">(${hits.length})</span>`;
    q("list").innerHTML = (hits || []).map((h, i) => {
      const pairs = h.pairs.map(p => p.join(" / "));
      return `<div class="hit${h.move === move ? " now" : ""}${h === pinned ? " pin" : ""}" data-i="${i}">` +
        `<b>#${h.move}</b> ${esc(h.name)} <span style="opacity:.7">(${h.check}${h.stage ? ", stage " + h.stage : ""})</span>` +
        `<div class="pairs">${esc(pairs.slice(0, 8).join(", "))}${pairs.length > 8 ? ` … +${pairs.length - 8}` : ""}</div>` +
        `<div style="font-size:11px;opacity:.7">${esc(h.context)}</div></div>`;
    }).join("");
  }
  panel();

  async function fetchData() {
    const my = ++gen;
    clearTimeout(poll);
    let d;
    try {
      const r = await fetch(base + "collisions.json?cell=" + encodeURIComponent(cell), { cache: "no-cache" });
      if (r.status === 404) d = { state: "error", error: "this mock's server has no /sim/collisions.json yet: restart tmflow_mock.py serve" };
      else d = await r.json();
    } catch (e) { d = { state: "error", error: e.message }; }
    if (my !== gen) return;                           // another cell asked for meanwhile
    const had = data && data.hits && data.generated;
    data = d.hits || !data || data.cell !== d.cell ? d : { ...data, ...d, hits: data.hits };
    if (d.state === "computing") poll = setTimeout(fetchData, 3000);
    else if (d.hits && d.generated !== had)
      log(d.free ? "ev" : "err", `collisions (${d.moves_file}): ${d.free ? "collision-free" : d.hits.length + " colliding moves: #" + d.hits.map(h => h.move).join(", #")}`);
    pinned = null;
    redraw(); panel();
  }

  return {
    setCell(c) { c = c || "cell"; if (c === cell) return fetchData(); cell = c; data = null; move = null; panel(); return fetchData(); },
    setMove(n) {                                      // the program's move now playing (null = none)
      if (n === move) return;
      move = n;
      const hs = hitsOf(n);
      if (hs.length && loggedFor !== n)
        log("err", `COLLISION move #${n} ${hs[0].name}: ${hs.flatMap(h => h.pairs.map(p => p.join("/"))).slice(0, 6).join(", ")}`);
      redraw(); loggedFor = n; panel();
    },
    reset() { move = null; pinned = null; redraw(); panel(); },
    set onPick(cb) { onPick = cb; },                  // a hit clicked in the list: cb(its move number) - the timeline jumps there
    refresh: fetchData,
    get data() { return data; }, state: st,
  };
}
