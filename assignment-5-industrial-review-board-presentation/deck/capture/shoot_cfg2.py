import sys, pathlib
from playwright.sync_api import sync_playwright
src = pathlib.Path(sys.argv[1]).resolve().as_uri()
OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5)
    pg.goto(src); pg.wait_for_timeout(5000)
    pg.locator("#tool").scroll_into_view_if_needed(); pg.wait_for_timeout(1500)
    cv = pg.locator("#tool canvas").first
    cv.scroll_into_view_if_needed()
    # hide overlay buttons for clean shots
    def hide():
        pg.evaluate("""() => { const c = document.querySelector('#tool canvas'); let n = c;
          while (n.parentElement && n.parentElement.querySelectorAll('button').length === 0) n = n.parentElement;
          for (const s of n.parentElement.children) if (s !== n && !s.contains(c)) s.style.visibility = 'hidden';
          for (const e of n.querySelectorAll('*')) if (e !== c && !e.contains(c)) e.style.visibility = 'hidden'; }""")
    def shot(name, back, deco, env="studio", explode=None, light="golden", zoom=2, view="b-three"):
        pg.evaluate("() => document.querySelectorAll('#tool *').forEach(e => e.style.visibility = '')")
        pg.click(f'[data-env="{env}"]'); pg.click(f'[data-light="{light}"]')
        pg.select_option("#c-back", back); pg.select_option("#c-decoration", deco)
        pg.click(f"#{view}"); pg.wait_for_timeout(1500)
        box = cv.bounding_box()
        pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        for _ in range(zoom):
            pg.mouse.wheel(0, -120); pg.wait_for_timeout(60)
        if explode is not None:
            pg.evaluate("""v => { const r = [...document.querySelectorAll('#tool input[type=range]')];
                const e = r[r.length-1]; e.value = e.max * v; e.dispatchEvent(new Event('input', {bubbles:true})); }""", explode)
        pg.wait_for_timeout(2500)
        hide(); pg.wait_for_timeout(300)
        cv.screenshot(path=str(OUT / f"{name}.png"))
        if explode is not None:
            pg.evaluate("""() => { const r = [...document.querySelectorAll('#tool input[type=range]')];
                const e = r[r.length-1]; e.value = 0; e.dispatchEvent(new Event('input', {bubbles:true})); }""")
    shot("p_high_laser", "high", "laser")
    shot("p_none_laser", "none", "laser")
    shot("p_high_shield", "high", "shield")
    shot("p_joint", "high", "laser", view="b-joint", zoom=0)
    shot("p_under", "high", "laser", view="b-under", zoom=0)
    shot("p_allee", "high", "laser", env="allee", light="midday", zoom=6)
    b.close()
