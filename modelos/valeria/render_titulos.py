"""Renderiza os textos animados do Reels da Valéria (PNG transparentes 30 fps -> .mov com alfa).
Uso: python3 render_titulos.py <pasta_trabalho> [--preview t1,t2]"""
import sys, os, json, pathlib, subprocess, shutil
from playwright.sync_api import sync_playwright
W = pathlib.Path(sys.argv[1]); aqui = pathlib.Path(__file__).resolve().parent
FUNDO = (aqui.parent.parent / "marca" / "fundo-story.png").resolve().as_uri()
page = W / "tit.html"; page.write_text((aqui / "titulos.html").read_text().replace("__FUNDO__", FUNDO))
FAIXAS = [(0.0, 6.0), (6.1, 7.62), (7.7, 11.85), (15.95, 17.6), (17.65, 21.75), (21.95, 25.3), (25.4, 29.9), (36.65, 40.1), (51.9, 56.71)]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium"); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(page.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
    if "--preview" in sys.argv:
        for t in sys.argv[sys.argv.index("--preview") + 1].split(","):
            pg.evaluate(f"render({t})"); pg.screenshot(path=str(W / f"tprev_{t}.png"), omit_background=True)
    else:
        os.makedirs(W / "tit", exist_ok=True)
        for k, (a, z) in enumerate(FAIXAS):
            d = W / f"tit/f{k}"; shutil.rmtree(d, ignore_errors=True); d.mkdir()
            for i in range(int(round((z - a) * 30))):
                pg.evaluate(f"render({a + i / 30:.4f})"); pg.screenshot(path=str(d / f"{i:05d}.png"), omit_background=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(d / "%05d.png"), "-c:v", "png", "-pix_fmt", "rgba", str(W / f"tit/t{k}.mov")], check=True)
            shutil.rmtree(d); print("faixa", k, a, z)
        json.dump(FAIXAS, open(W / "tit/faixas.json", "w"))
    b.close()
