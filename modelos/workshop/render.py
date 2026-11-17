"""Gera o card a partir de um JSON:  python3 render.py dados.json saida.png"""
import json, sys, html, pathlib
from playwright.sync_api import sync_playwright

aqui = pathlib.Path(__file__).resolve().parent
dados = json.load(open(sys.argv[1], encoding="utf-8"))
base = pathlib.Path(sys.argv[1]).resolve().parent
foto = (base / dados["foto"]).resolve().as_uri()
logo = (base / dados.get("logo", str(aqui / "logo-provisorio.svg"))).resolve().as_uri()
e = html.escape

titulo = "<br>".join(e(l) for l in dados["titulo"]) + f'<div class="subtitulo">{e(dados["subtitulo"])}</div>'
d = dados["data"]
data = f'{e(d[0])}<b>{e(d[1])}</b>{e(d[2])}'
marca = f'<div class="marca">{e(dados.get("marca","instituto"))}' + \
        (f'<small>{e(dados["slogan"])}</small>' if dados.get("slogan") else "") + "</div>"
contato = f'{e(dados["contato_rotulo"])}<br><b>{e(dados["contato_numero"])}</b>'

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium" if pathlib.Path("/opt/pw-browsers/chromium").is_file() else None); pg = b.new_page(viewport={"width": 1080, "height": 1440})
    pg.goto((aqui / "card.html").as_uri())
    pg.evaluate("""([foto,titulo,data,logo,marca,contato,tam]) => {
      const c=document.getElementById('card'); c.style.setProperty('--foto',`url("${foto}")`);
      if(tam) c.style.setProperty('--tam-titulo',tam);
      document.getElementById('titulo').innerHTML=titulo;
      document.getElementById('data').innerHTML=data;
      document.getElementById('logo').innerHTML=`<img src="${logo}">`+marca;
      document.getElementById('contato').innerHTML=contato;
    }""", [foto, titulo, data, logo, marca, contato, dados.get("tamanho_titulo")])
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    # ajuste automático: reduz o título até caber na largura
    pg.evaluate("""() => {const t=document.getElementById('titulo');
      let s=parseFloat(getComputedStyle(t).fontSize);
      const fits=()=>[...t.childNodes].every(()=>t.scrollWidth<=t.clientWidth+1);
      while(!fits() && s>60){s-=2; t.style.fontSize=s+'px'}}""")
    pg.locator("#card").screenshot(path=sys.argv[2])
    b.close()
print("ok:", sys.argv[2])
