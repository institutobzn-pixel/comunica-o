"""Roteiro do Reels 'Seja como a Valéria' (v4): fala contínua na velocidade natural (sem cortes no meio = sem "pulos"),
Valéria em tela cheia de corpo inteiro. Uso: python3 roteiro.py <pasta_trabalho>  -> plano.json"""
import json, sys, os
W = sys.argv[1]; os.chdir(W)
VEL = 1.0; GAP = 0.2; STING, FIM = 1.5, 4.8
# (nome, início, fim, [(de, até, tipo_imagem)]) — tempos do vídeo original
SEGS = [
    ("gancho", 35.50, 42.55, [(35.50, 42.55, "V")]),                       # "faço questão de ser associada..."
    ("STING", None, None, None),
    ("corpo", 0.80, 34.74, [(0.80, 34.74, "V")]),                          # do "Olá" até "...lugar preferido para estar" (inclui "Instituto BZN" inteiro)
    ("final", 42.75, 60.05, [(42.75, 46.70, "B:resultados"), (46.70, 51.00, "B:aula2"), (51.00, 60.05, "V")]),
    ("FIM", None, None, None),
]
t = 0.0; pecas = []; voz = []; cards = []; marcas = {}
for nome, a, b, vis in SEGS:
    if a is None:
        d = STING if nome == "STING" else FIM
        cards.append(dict(nome=nome, t=round(t, 3), d=d)); pecas.append(dict(tipo=nome, t=round(t, 3), d=d)); t += d; continue
    voz.append(dict(seg=nome, src_a=a, src_b=b, t=round(t, 3)))
    marcas[nome] = dict(t=round(t, 3), src_a=a)
    for va, vb, tipo in vis:
        pecas.append(dict(seg=nome, tipo=tipo, src_a=va, src_b=vb, t=round(t + (va - a), 3), d=round(vb - va, 3)))
    t += b - a + GAP
    pecas[-1]["d"] = round(pecas[-1]["d"] + GAP, 3)   # a imagem segura no respiro
json.dump(dict(VEL=VEL, total=round(t, 3), pecas=pecas, voz=voz, cards=cards, marcas=marcas), open("plano.json", "w"), indent=1)
print("total", round(t, 2), "s;", len(pecas), "peças")
for p in pecas: print(p)
