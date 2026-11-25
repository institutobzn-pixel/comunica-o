"""Monta a lista de cortes da fala (fonte, entrada, saída) a partir da transcrição com tempos por palavra."""
import json, sys
tr = json.load(open(sys.argv[1]))
VEL = 1.15  # fala 15% mais rápida

# (bloco, vídeo, [intervalos aproximados de frases a manter]) — na ordem do Reels
BLOCOS = [
    ("artista",   "W1016", [(0.0, 16.08)]),
    ("anonimos",  "W1021", [(0.0, 12.72), (24.18, 31.42)]),
    ("palmas",    "W0931", [(0.0, 20.46)]),
    ("enchentes", "W0933", [(0.0, 23.86)]),
    ("esperanca", "W1016", [(16.88, 34.92), (35.58, 48.24)]),   # corta 49.5+ (cursos/site)
    ("venda",     "W0938", [(0.0, 4.50), (11.76, 27.72)]),
    ("convite",   "W0938", [(36.52, 49.74)]),
]
PAUSA_MAX = 0.55   # pausas maiores que isso dentro da fala são encurtadas

cortes = []
for bloco, vid, faixas in BLOCOS:
    words = [w for s in tr[vid] for w in s["w"]]
    for a, b in faixas:
        ws = [w for w in words if w["s"] >= a - 0.05 and w["e"] <= b + 0.3]
        # quebra em trechos onde a pausa entre palavras é grande
        def lim_a(w0):  # não invade a palavra anterior
            i = words.index(w0); prev = words[i-1]["e"] if i > 0 else 0
            return max(prev + 0.02, w0["s"] - 0.08, 0)
        def lim_b(w1, folga):  # não invade a palavra seguinte
            i = words.index(w1); nxt = words[i+1]["s"] if i + 1 < len(words) else 1e9
            return min(nxt - 0.03, w1["e"] + folga)
        ini = ws[0]; ant = ws[0]
        for w in ws[1:]:
            if w["s"] - ant["e"] > PAUSA_MAX:
                cortes.append(dict(bloco=bloco, vid=vid, a=lim_a(ini), b=lim_b(ant, 0.14)))
                ini = w
            ant = w
        cortes.append(dict(bloco=bloco, vid=vid, a=lim_a(ini), b=lim_b(ant, 0.16)))
t = 0
for c in cortes:
    c["dur"] = round((c["b"] - c["a"]) / VEL, 3); c["a"] = round(c["a"], 3); c["b"] = round(c["b"], 3); t += c["dur"]
json.dump(cortes, open(sys.argv[2], "w"), indent=1)
from collections import defaultdict
d = defaultdict(float)
for c in cortes: d[c["bloco"]] += c["dur"]
print(len(cortes), "cortes; fala total", round(t, 1), "s"); print({k: round(v, 1) for k, v in d.items()})
