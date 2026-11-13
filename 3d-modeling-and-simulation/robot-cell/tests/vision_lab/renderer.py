"""Headless renderer for sim photos: a hidden Edge/Chrome on http://127.0.0.1:8090/all?renderer, so test photos don't
depend on (or come from) a page someone has open. Photo requests with renderer=True are answered only by this page.

  python tests/vision_lab/renderer.py start      # needs the mock: python tests/tmflow_mock.py serve --sim
  python tests/vision_lab/renderer.py eval "window.__sim.jigs.model()"
  python tests/vision_lab/renderer.py stop
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

PORT = 9333
PROFILE = Path(tempfile.gettempdir()) / "sim-renderer-profile"
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
URL = "http://127.0.0.1:8090/all?renderer"


def pages():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=2) as r:
            return [p for p in json.loads(r.read()) if p.get("type") == "page"]
    except OSError:
        return []


def page():
    return next((p for p in pages() if "renderer" in p.get("url", "")), None)


def evaluate(expr, timeout=30):
    """Run JS in the renderer page (awaits promises) -> its value."""
    import websocket
    p = page()
    if not p:
        raise RuntimeError("renderer not running (renderer.py start)")
    ws = websocket.create_connection(p["webSocketDebuggerUrl"], timeout=timeout)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == 1:
                res = m.get("result", {})
                if "exceptionDetails" in res:
                    raise RuntimeError(res["exceptionDetails"].get("exception", {}).get("description")
                                       or res["exceptionDetails"].get("text"))
                return res.get("result", {}).get("value")
    finally:
        ws.close()


def start(wait=40):
    if page():
        return True
    exe = next((b for b in BROWSERS if os.path.exists(b)), None)
    if not exe:
        sys.exit("no Edge/Chrome found")
    subprocess.Popen([exe, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                      "--ignore-gpu-blocklist", "--window-size=1600,1000", f"--user-data-dir={PROFILE}",
                      f"--remote-debugging-port={PORT}", URL],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < wait:                      # until the 3D view, jigs and camera layers are up
        try:
            if page() and evaluate("!!(window.__sim && window.__sim.jigs && window.__sim.vision && window.__sim.jigs.model())", 5):
                return True
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("renderer page did not come up")


def stop():
    if sys.platform == "win32":
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe' or Name='chrome.exe'\" | "
                        f"Where-Object {{ $_.CommandLine -like '*{PROFILE.name}*' }} | "
                        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        print("renderer up" if start() else "?")
    elif cmd == "stop":
        stop(); print("stopped")
    elif cmd == "eval":
        print(json.dumps(evaluate(sys.argv[2]), indent=1))
