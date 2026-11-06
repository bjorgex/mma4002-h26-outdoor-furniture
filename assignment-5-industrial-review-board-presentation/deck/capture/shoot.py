"""Screenshot the group's simulator. usage: shoot.py probe | run <scenario> <secs> <every> [maxsim]"""
import sys, time, os
from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(__file__), "shots")
os.makedirs(OUT, exist_ok=True)
mode = sys.argv[1]

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    VW, VH = int(os.environ.get("VW", 1920)), int(os.environ.get("VH", 1080))
    ctx = b.new_context(viewport={"width": VW, "height": VH}, record_video_dir=os.environ.get("REC") or None, record_video_size={"width": VW, "height": VH})
    pg = ctx.new_page()
    pg.goto("http://127.0.0.1:8090/all")
    pg.wait_for_timeout(6000)
    if mode == "probe":
        print(pg.eval_on_selector_all("#sc-sel option", "os => os.map(o => o.value + ' | ' + o.textContent)"))
        pg.screenshot(path=os.path.join(OUT, "probe.png"))
    else:
        sc, secs, every = sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
        tag = sys.argv[5] if len(sys.argv) > 5 else "all"
        pg.select_option("#sc-sel", sc)
        pg.wait_for_timeout(2500)
        def set_speed(v):
            pg.evaluate("""v => { const i = [...document.querySelectorAll('header input, input')]
                 .find(x => x.type !== 'range' && x.value === String(x.value) && /^\\d+(\\.\\d+)?$/.test(x.value) && x.offsetWidth < 120);
               if (i) { i.value = v; i.dispatchEvent(new Event('input', {bubbles:true})); i.dispatchEvent(new Event('change', {bubbles:true})); }
               const r = document.querySelector('input[type=range]');
               return i ? i.outerHTML : 'none'; }""", str(v))
        if os.environ.get("SPEED"):
            set_speed(os.environ["SPEED"])
        pg.click("#sc-run")
        if os.environ.get("SPEED"):
            pg.wait_for_timeout(500); set_speed(os.environ["SPEED"])
        if tag.startswith("sim"):
            pg.click("#p-sim .btn.max")
            pg.wait_for_timeout(500)
        if tag.startswith("simclean"):
            pg.evaluate("""() => {
              for (const l of document.querySelectorAll('label')) {
                const t = l.textContent;
                if (/heat planes|program path|labels on flagged/.test(t)) {
                  const c = l.querySelector('input[type=checkbox]'); if (c && c.checked) c.click(); }
              }
            }""")
            pg.wait_for_timeout(300)
            pg.evaluate("""() => { for (const el of document.querySelectorAll('.panel, .mpanel, .cpanel, [class*=panel]'))
                 if (el.offsetWidth < 700 && el.offsetWidth > 50) el.style.visibility = 'hidden'; }""")
            zoom = int(os.environ.get("ZOOM", "5"))
            pg.mouse.move(VW*0.6, VH*0.55)
            for _ in range(zoom):
                pg.mouse.wheel(0, -200); pg.wait_for_timeout(80)
        t0 = time.time(); i = 0
        while time.time() - t0 < secs:
            pg.wait_for_timeout(every * 1000)
            i += 1
            pg.screenshot(path=os.path.join(OUT, f"{tag}_{sc}_{i:03d}.png"))
        print(i, "shots")
        if os.environ.get("SPEED"):
            set_speed("25")
    ctx.close(); b.close()
