"""Gera camadas PNG (base, legendas palavra a palavra, cartão final) e o roteiro de tempos."""
import json, sys, pathlib, html
from playwright.sync_api import sync_playwright
aqui = pathlib.Path(__file__).resolve().parent
words = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
chunks = [[0,1,2,3],[4,5,6],[7,8,9],[10,11,12],[13,14],[15,16,17],[18,19,20]]
plan = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width":1080,"height":1920})
    pg.goto((aqui/"camadas.html").as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    def shot(layer, name, transparent=True):
        pg.evaluate(f"document.querySelectorAll('.l').forEach(e=>e.style.display='none');document.getElementById('{layer}').style.display='{'flex' if layer=='fim' else 'block'}'")
        pg.screenshot(path=str(out/name), omit_background=transparent)
    shot("base","base.png"); shot("fim","fim.png", False)
    n = 0
    for ci, ch in enumerate(chunks):
        for k, wi in enumerate(ch):
            parts = []
            for wj in ch:
                t = html.escape(words[wj]["w"].strip())
                parts.append(f"<em>{t}</em>" if wj == wi else (t if wj < wi else f"<i>{t}</i>"))
            pg.evaluate("h=>document.getElementById('legtxt').innerHTML=h", " ".join(parts))
            shot("leg", f"w{n:02d}.png")
            start = words[wi]["s"]
            # fica até a próxima palavra do mesmo trecho, ou até o próximo trecho
            if k + 1 < len(ch): end = words[ch[k+1]]["s"]
            elif ci + 1 < len(chunks): end = words[chunks[ci+1][0]]["s"]
            else: end = words[wi]["e"] + 0.7
            plan.append((f"w{n:02d}.png", round(start,2), round(end,2))); n += 1
    b.close()
json.dump(plan, open(out/"plan.json","w"))
print(len(plan), "camadas de legenda")
