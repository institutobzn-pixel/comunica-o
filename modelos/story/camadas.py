"""Exporta as camadas transparentes do story (base.png e texto.png)."""
import pathlib, sys
from playwright.sync_api import sync_playwright
aqui = pathlib.Path(__file__).resolve().parent; out = pathlib.Path(sys.argv[1])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width":1080,"height":1920})
    pg.goto((aqui/"overlay.html").as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    for show, hide in (("base","texto"),("texto","base")):
        pg.evaluate(f"document.getElementById('{show}').style.display='block';document.getElementById('{hide}').style.display='none'")
        pg.screenshot(path=str(out/f"{show}.png"), omit_background=True)
    b.close()
