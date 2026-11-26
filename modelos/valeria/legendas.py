"""Legendas animadas (karaokê palavra a palavra) no estilo de Reels. Uso: python3 legendas.py <pasta_trabalho>"""
import json, sys, os
W = sys.argv[1]; os.chdir(W)
tr = json.load(open("transcricao.json")); words = [w for s in tr for w in s["w"]]
pl = json.load(open("plano.json")); VEL = pl["VEL"]
FIX = {"Desenho.": "BZN.", "Iatuba": "Indaiatuba", "Iatuba,": "Indaiatuba,"}
def ts(x): return f"0:{int(x // 60):02d}:{x % 60:05.2f}"
ev = []
for v in pl["voz"]:
    ws = [w for w in words if v["src_a"] - 0.05 <= w["s"] < v["src_b"]]
    out = lambda s: v["t"] + (s - v["src_a"]) / VEL
    grupo = []
    def fecha(g, fim):
        a = out(g[0]["s"]); txt = ""
        for i, w in enumerate(g):
            nxt = out(g[i+1]["s"]) if i + 1 < len(g) else fim
            dur = max(1, int(round((nxt - out(w["s"])) * 100)))
            palavra = FIX.get(w["w"].strip(), w["w"].strip()).upper()
            txt += f"{{\\k{dur}}}{palavra} "
        ev.append((a, fim, txt.strip()))
    for i, w in enumerate(ws):
        grupo.append(w); txt = " ".join(x["w"].strip() for x in grupo)
        nxt = ws[i+1] if i + 1 < len(ws) else None
        if w["w"].strip()[-1:] in ",.!?" or len(txt) > 15 or nxt is None:
            fim = out(nxt["s"]) if nxt else min(out(w["e"]) + 0.35, v["t"] + (v["src_b"] - v["src_a"]) / VEL)
            fecha(grupo, fim); grupo = []
cab = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display Black,92,&H00FFC97A,&H00FFFFFF,&H00221208,&H64000000,0,0,0,0,100,100,0,0,1,5,3,2,140,140,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# pop-in suave em cada grupo
linhas = [f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\fad(60,40)\\t(0,120,\\fscx104\\fscy104)\\t(120,220,\\fscx100\\fscy100)}}{t}\n" for a, b, t in ev]
open("legendas.ass", "w").write(cab + "".join(linhas)); print(len(linhas), "legendas")
for a, b, t in ev[:8]: print(round(a, 2), round(b, 2), t)
