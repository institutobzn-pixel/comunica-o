"""Renderiza os títulos animados como sequências PNG transparentes (30 fps) e codifica em .mov com alfa.
Uso: python3 render_titulos.py <pasta_trabalho> [--preview t1,t2,...]"""
import json, sys, os, pathlib, subprocess, shutil
from playwright.sync_api import sync_playwright
W = pathlib.Path(sys.argv[1]); aqui = pathlib.Path(__file__).resolve().parent
FONTS = "/tmp/claude-0/-home-user-comunica-o/b13c12c9-2298-5e04-a0eb-b70d13ae7f51/scratchpad/fonts/fontsource-cormorant-garamond-5.3.0/package/files"
LOGO = (aqui.parent.parent / "marca" / "logo-branca.png").resolve().as_uri()
tl = json.load(open(W / "timeline.json")); tr = json.load(open(W / "transcricao.json"))

def out_time(vid, s):
    for c in tl["cortes"]:
        if c["vid"] == vid and c["src_a"] - 0.02 <= s <= c["src_b"] + 0.02:
            return c["t"] + (s - c["src_a"]) / tl["VEL"]
# legendas do trecho das telas azuis (substituem as legendas originais cobertas pelas imagens novas)
words = [w for s in tr["W1016"] for w in s["w"] if 16.8 <= w["s"] <= 29.2]
CHUNKS = [(0, 5), (5, 9), (9, 14), (14, 19), (19, 21), (21, 25)]
leg = []
for k, (i, j) in enumerate(CHUNKS):
    a = out_time("W1016", words[i]["s"]); b = out_time("W1016", words[CHUNKS[k+1][0]]["s"]) if k + 1 < len(CHUNKS) else 94.9
    leg.append([round(a, 3), round(b, 3), " ".join(w["w"].strip() for w in words[i:j])])
print(leg)
html = (aqui / "titulos.html").read_text().replace("__FONTS__", FONTS).replace("__LOGO__", LOGO).replace("__LEGENDAS__", json.dumps(leg, ensure_ascii=False))
page = W / "titulos_render.html"; page.write_text(html)
FAIXAS = [(5.4, 13.6), (15.0, 19.65), (28.25, 33.05), (46.2, 50.95), (63.85, 68.65), (84.0, 96.15), (140.9, 154.25)]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(page.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
    if "--preview" in sys.argv:
        for t in sys.argv[sys.argv.index("--preview") + 1].split(","):
            pg.evaluate(f"render({t})"); pg.screenshot(path=str(W / f"prev_{t}.png"), omit_background=True)
    else:
        os.makedirs(W / "tit", exist_ok=True)
        for k, (a, z) in enumerate(FAIXAS):
            d = W / f"tit/f{k}"; shutil.rmtree(d, ignore_errors=True); d.mkdir()
            n = int(round((z - a) * 30))
            for i in range(n):
                pg.evaluate(f"render({a + i / 30:.4f})"); pg.screenshot(path=str(d / f"{i:05d}.png"), omit_background=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(d / "%05d.png"),
                            "-c:v", "png", "-pix_fmt", "rgba", str(W / f"tit/t{k}.mov")], check=True)
            shutil.rmtree(d); print("faixa", k, a, z, n, "quadros")
        json.dump(FAIXAS, open(W / "tit/faixas.json", "w"))
    b.close()
