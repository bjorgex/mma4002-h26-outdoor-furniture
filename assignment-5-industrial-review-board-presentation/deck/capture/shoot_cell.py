import os
from playwright.sync_api import sync_playwright
OUT = os.path.join(os.path.dirname(__file__), "shots")
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1.5)
    pg.goto("http://127.0.0.1:8090/all"); pg.wait_for_timeout(6000)
    pg.select_option("#sc-sel", "v8-full"); pg.wait_for_timeout(2500)
    pg.click("#p-sim .btn.max"); pg.wait_for_timeout(800)
    def heat(on):
        pg.evaluate("""on => { for (const l of document.querySelectorAll('label')) {
            if (/heat planes|program path|labels on flagged/.test(l.textContent)) {
              const c = l.querySelector('input[type=checkbox]'); if (c && c.checked !== on) c.click(); } } }""", on)
    def panels(vis):
        pg.evaluate("""v => { for (const el of document.querySelectorAll('[class*=panel]'))
             if (el.offsetWidth < 700 && el.offsetWidth > 50 || el.style.visibility) el.style.visibility = v ? '' : 'hidden'; }""", vis)
    def cam(c, zoom):
        pg.click(f'#p-sim [data-cam="{c}"]'); pg.wait_for_timeout(800)
        pg.mouse.move(960, 500)
        for _ in range(zoom): pg.mouse.wheel(0, -200); pg.wait_for_timeout(80)
        pg.wait_for_timeout(1500)
    heat(True); panels(True); cam("iso", 0); pg.screenshot(path=f"{OUT}/cell_overlays.png")
    heat(False); panels(False)
    cam("iso", 4); pg.screenshot(path=f"{OUT}/cell_iso.png")
    cam("top", 5); pg.screenshot(path=f"{OUT}/cell_top.png")
    cam("side", 4); pg.screenshot(path=f"{OUT}/cell_side.png")
    b.close()
