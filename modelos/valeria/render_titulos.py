"""Renderiza os textos animados do Reels da Valéria (PNG transparentes 30 fps -> .mov com alfa).
Uso: python3 render_titulos.py <pasta_trabalho> [--preview t1,t2]"""
import sys, os, json, pathlib, subprocess, shutil
from playwright.sync_api import sync_playwright
W = pathlib.Path(sys.argv[1]); aqui = pathlib.Path(__file__).resolve().parent
FUNDO = (aqui.parent.parent / "marca" / "fundo-story.png").resolve().as_uri()
pl = json.load(open(W / "plano.json")); mk = pl["marcas"]; cd = {c["nome"]: c for c in pl["cards"]}
def em(seg, s): return round(mk[seg]["t"] + (s - mk[seg]["src_a"]) / pl["VEL"], 3)   # tempo no Reels de um instante do original
T = {"hook": [0.1, round(cd["STING"]["t"] - 0.1, 3)], "sting": [cd["STING"]["t"], round(cd["STING"]["t"] + cd["STING"]["d"], 3)],
     "nome": [em("corpo", 0.9), em("corpo", 4.6)], "local": [em("corpo", 10.7), em("corpo", 13.0)],
     "ench": [em("corpo", 13.1), em("corpo", 17.6)], "nascer": [em("corpo", 18.3), em("corpo", 21.6)],
     "cursos": [em("corpo", 24.8), em("corpo", 28.2)], "result": [em("final", 42.8), em("final", 46.6)],
     "fim": [cd["FIM"]["t"], pl["total"]]}
FAIXAS = [(round(max(0, a - 0.05), 3), round(min(pl["total"], z + 0.05), 3)) for a, z in T.values()]
page = W / "tit.html"; page.write_text((aqui / "titulos.html").read_text().replace("__FUNDO__", FUNDO).replace("__T__", json.dumps(T)))
print(T)
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
