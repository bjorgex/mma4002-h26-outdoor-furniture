"""/sim/ for the mock's view server: sim_view.html and its meshes from this folder (tmflow_mock.py, mock_sim.py);
sim_scene.js is the same 3D cell as a module, for tmflow_all_view.html (/all)."""
import mimetypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = {"": "sim_view.html", "sim_view.html": "sim_view.html", "cell.glb": "cell.glb",
         "tm5_links.glb": "tm5_links.glb", "cell_layout.json": "cell_layout.json", "sim_scene.js": "sim_scene.js",
         "cell_v5.glb": "cell_v5.glb", "cell_layout_v5.json": "cell_layout_v5.json"}   # v5: guide starts on base A


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
