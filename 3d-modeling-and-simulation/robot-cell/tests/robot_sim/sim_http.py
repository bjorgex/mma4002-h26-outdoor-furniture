"""/sim/ for the mock's view server: sim_view.html and its meshes from this folder (tmflow_mock.py, mock_sim.py);
sim_scene.js is the same 3D cell as a module, for tmflow_all_view.html (/all).
/sim/collisions.json?cell=cell_v8: collision.py's hits for that cell's moves file (collision_view.py; recomputed in
the background when stale), for the Collisions panel (collision_layer.js)."""
import json
import mimetypes
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = {"": "sim_view.html", "sim_view.html": "sim_view.html", "cell.glb": "cell.glb",
         "tm5_links.glb": "tm5_links.glb", "cell_layout.json": "cell_layout.json", "sim_scene.js": "sim_scene.js",
         "cell_v5.glb": "cell_v5.glb", "cell_layout_v5.json": "cell_layout_v5.json",   # v5: guide starts on base A
         "cell_v6.glb": "cell_v6.glb", "cell_layout_v6.json": "cell_layout_v6.json",   # v6: as v5, no parking pad
         "cell_v8.glb": "cell_v8.glb", "cell_layout_v8.json": "cell_layout_v8.json",   # v8: Jig V5, T-slot plate
         "cell_v8x2.glb": "cell_v8x2.glb", "cell_layout_v8x2.json": "cell_layout_v8x2.json",   # v8x2: 2 benches
         "cell_v9.glb": "cell_v9.glb", "cell_layout_v9.json": "cell_layout_v9.json",   # v9: Guide split V6
         "cell_v9x2.glb": "cell_v9x2.glb", "cell_layout_v9x2.json": "cell_layout_v9x2.json",   # v9x2: 2 benches
         "manip_layers.js": "manip_layers.js",                                     # manipulability layers (3D view)
         "collision_layer.js": "collision_layer.js",                               # collisions panel (3D view)
         "manip_data.json": "manipulability/manip_data.json"}                      # manipulability.py all


def sim_get(handler):
    """/sim, /sim/ and /sim/<file>: the 3D view and its meshes. True if handled."""
    path = handler.path.split("?")[0]
    if path == "/sim":
        handler.send_response(301)
        handler.send_header("Location", "/sim/")
        handler.end_headers()
        return True
    if not path.startswith("/sim/"):
        return False
    if path == "/sim/collisions.json":                     # ?cell=cell_v8: collision_view.py's list (recomputed when stale)
        return _collisions(handler)
    name = FILES.get(path[len("/sim/"):])
    f = HERE / name if name else None
    if not f or not f.exists():
        handler.send_error(404)
        return True
    body = f.read_bytes()
    handler.send_response(200)
    ctype = {".glb": "model/gltf-binary", ".js": "text/javascript"}.get(f.suffix) or         mimetypes.guess_type(f.name)[0] or "text/plain"         # modules need a JS type (the registry may say otherwise)
    handler.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") else ""))
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
    return True


def _collisions(handler):
    """collision_view.status(cell) as JSON: the last check of the cell's moves file + whether a new one is running."""
    import collision_view                                   # robot_sim/ is on sys.path (tmflow_mock.py puts it there)
    cell = urllib.parse.parse_qs(urllib.parse.urlsplit(handler.path).query).get("cell", ["cell"])[0]
    try:
        code, d = 200, collision_view.status(cell)
    except ValueError as e:
        code, d = 400, {"state": "error", "error": str(e)}
    body = json.dumps(d).encode()
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
    return True
