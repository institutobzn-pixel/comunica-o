"""Roteiro do Reels 'Seja como a Valéria': cortes de fala (sem pausas longas, 8% mais rápido) e tipo de imagem de cada trecho.
Uso: python3 roteiro.py <pasta_trabalho>  -> plano.json"""
import json, sys, os
W = sys.argv[1]; os.chdir(W)
tr = json.load(open("transcricao.json")); words = [w for s in tr for w in s["w"]]
VEL = 1.08; PAUSA = 0.45; GAP = 0.2
STING, FIM = 1.5, 4.8
# (nome, início, fim, [(de, até, tipo_imagem)])
SEGS = [
    ("gancho", 35.50, 41.95, [(35.50, 41.95, "Vstand")]),
    ("STING", None, None, None),
    ("s1", 0.80, 9.75, [(0.80, 9.75, "Vsit")]),
    ("s2", 10.65, 21.45, [(10.65, 13.00, "Vsit"), (13.00, 17.60, "B:enchentes"), (17.60, 21.45, "Vsit")]),
    ("s3", 22.40, 27.20, [(22.40, 27.20, "B:aula1")]),
    ("s4", 27.70, 34.70, [(27.70, 34.70, "Vstand")]),
    ("s5", 42.75, 46.30, [(42.75, 46.30, "B:resultados")]),
    ("s6", 46.80, 55.20, [(46.80, 50.90, "B:aula2"), (50.90, 55.20, "B:aula3")]),
    ("s7", 55.55, 60.05, [(55.55, 60.05, "Vstand")]),
    ("FIM", None, None, None),
]
def falas(a, b):
    ws = [w for w in words if w["s"] >= a - 0.05 and w["e"] <= b + 0.3]
    out = []; ini = ws[0]; ant = ws[0]
    for w in ws[1:]:
        if w["s"] - ant["e"] > PAUSA:
            out.append((max(a, ini["s"] - 0.08), ant["e"] + 0.14)); ini = w
        ant = w
    out.append((max(a, ini["s"] - 0.08), min(b, ant["e"] + 0.2)))
    return out
t = 0.0; pecas = []; voz = []; cards = []
for nome, a, b, vis in SEGS:
    if a is None:
        d = STING if nome == "STING" else FIM
        cards.append(dict(nome=nome, t=round(t, 3), d=d)); pecas.append(dict(tipo=nome, t=round(t, 3), d=d)); t += d; continue
    for fa, fb in falas(a, b):
        voz.append(dict(seg=nome, src_a=round(fa, 3), src_b=round(fb, 3), t=round(t, 3)))
        for va, vb, tipo in vis:   # interseção do trecho falado com o tipo de imagem
            x0, x1 = max(fa, va), min(fb, vb)
            if x1 - x0 > 0.02:
                pecas.append(dict(seg=nome, tipo=tipo, src_a=round(x0, 3), src_b=round(x1, 3), t=round(t + (x0 - fa) / VEL, 3), d=round((x1 - x0) / VEL, 3)))
        t += (fb - fa) / VEL
    t += GAP
    pecas[-1]["d"] = round(pecas[-1]["d"] + GAP, 3)   # a imagem segura no respiro
json.dump(dict(VEL=VEL, total=round(t, 3), pecas=pecas, voz=voz, cards=cards), open("plano.json", "w"), indent=1)
print("total", round(t, 2), "s;", len(pecas), "peças")
for p in pecas: print(p)
