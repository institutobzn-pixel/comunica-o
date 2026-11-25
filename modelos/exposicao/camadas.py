"""Exporta as camadas do story da exposição: base.png, texto.png (transparentes) e fim.png."""
import pathlib, sys
from playwright.sync_api import sync_playwright
aqui = pathlib.Path(__file__).resolve().parent
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto((aqui / "overlay.html").as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    for layer in ("base", "texto", "fim"):
        pg.evaluate(f"document.querySelectorAll('.l').forEach(e=>e.style.display='none');"
                    f"document.getElementById('{layer}').style.display='{'flex' if layer == 'fim' else 'block'}'")
        pg.screenshot(path=str(out / f"{layer}.png"), omit_background=(layer != "fim"))
    b.close()
print("camadas ok:", out)
