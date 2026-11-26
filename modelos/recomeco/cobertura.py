"""Nova faixa visual da fala: a Isabel só em planos limpos; o resto coberto pelas obras em alta qualidade (câmera lenta).
Gera fala_video.mp4 (de 13.65 a 141.2 s da linha do tempo) e legendas.ass (estilo das legendas originais).
Uso: python3 cobertura.py <pasta_trabalho>"""
import json, subprocess, sys, os
W = sys.argv[1]; os.chdir(W); os.makedirs("cob", exist_ok=True)
tl = json.load(open("timeline.json")); tr = json.load(open("transcricao.json")); VEL = tl["VEL"]
T0, T1 = 13.65, 141.2

UP = ("scale=1088:1922:flags=lanczos,crop=1080:1920,hqdn3d=1.2:1.2:3:3,unsharp=5:5:0.55:5:5:0,"
      "eq=contrast=1.03:saturation=1.02,fps=30,format=yuv420p")
def run(a): subprocess.run(a, check=True)

# versões enviadas depois, sem o ícone do Instagram (mesma linha do tempo das anteriores)
SEM_ICONE = {"W1016": "orig/ae878d51.mp4", "W1021": "orig/af0681e5.mp4", "W0931": "orig/f4252b95.mp4",
             "W0933": "orig/123e982c.mp4", "W0938": "orig/924f878a.mp4"}
X_ENQ = {"E": 20}   # deslocamento horizontal do enquadramento quando a artista está mais à esquerda

def isabel(nome, vid, s0, s1):  # plano da artista, sincronizado com a voz (15% mais rápido)
    """Enquadra acima da assinatura (y < 735): nenhuma marca precisa ser apagada."""
    if os.path.exists(f"cob/{nome}.mp4"): return (s1 - s0) / VEL
    x = X_ENQ.get(nome, 33)
    vf = (f"crop=413:735:{x}:0,setpts=(PTS-STARTPTS)/{VEL},scale=1080:1920:flags=lanczos,hqdn3d=1.2:1.2:3:3,"
          f"unsharp=5:5:0.6:5:5:0,eq=contrast=1.03:saturation=1.02,fps=30,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(s0), "-t", f"{s1 - s0:.3f}", "-i", SEM_ICONE[vid],
         "-vf", vf, "-an", "-c:v", "libx264", "-crf", "15", "-preset", "fast", f"cob/{nome}.mp4"])
    return (s1 - s0) / VEL

def obra(nome, img, ss, d, vel=0.7, z0=1.0, z1=1.06):  # vídeo IMG original em câmera lenta com zoom suave
    out = d / vel; z = f"({z0}+({z1}-{z0})*t/{out:.3f})"
    if os.path.exists(f"cob/{nome}.mp4"): return out
    vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=(PTS-STARTPTS)/{vel},"
          f"framerate=fps=30:interp_start=0:interp_end=255:scene=100,setsar=1,"
          f"scale=w='trunc(1080*{z}/2)*2':h=-2:eval=frame:flags=lanczos,crop=1080:1920,eq=contrast=1.04,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(d), "-i", f"src/{img}.mov", "-vf", vf, "-an",
         "-c:v", "libx264", "-crf", "15", "-preset", "fast", f"cob/{nome}.mp4"])
    return out

def detalhe_anonimos(nome, s0, s1, vel):
    """Detalhe da tela da série Anônimos (só existe nos vídeos da artista): recorte que exclui marcas e legendas."""
    if os.path.exists(f"cob/{nome}.mp4"): return (s1 - s0) / vel
    partes = []
    for a, b, (x, y, w, h) in [(s0, 27.0, (0, 0, 304, 540)), (27.0, s1, (176, 0, 304, 540))]:
        p = f"cob/{nome}_{len(partes)}.mp4"; d = b - a
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", f"{d:.3f}", "-i", "src/W1021.mp4", "-vf",
             f"crop={w}:{h}:{x}:{y},setpts=(PTS-STARTPTS)/{vel},framerate=fps=30:interp_start=0:interp_end=255:scene=100,"
             f"scale=1080:1920:flags=lanczos,hqdn3d=2:2:4:4,unsharp=7:7:0.7:5:5:0,eq=contrast=1.05,format=yuv420p",
             "-an", "-c:v", "libx264", "-crf", "15", "-preset", "fast", p]); partes.append(p)
    open("cob/lista_an.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in partes))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "cob/lista_an.txt", "-c", "copy", f"cob/{nome}.mp4"])
    return (s1 - s0) / vel

def azuis(nome):
    if not os.path.exists(f"cob/{nome}.mp4"):
        run(["ffmpeg", "-v", "error", "-y", "-i", "broll/e1.mp4", "-i", "broll/e2.mp4", "-i", "broll/e3.mp4", "-filter_complex",
             "[0:v][1:v]xfade=transition=fade:duration=0.6:offset=2.8[a];[a][2:v]xfade=transition=fade:duration=0.6:offset=7.4[v]",
             "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "15", "-preset", "fast", f"cob/{nome}.mp4"])
    return 94.9 - 83.972

# (início na linha do tempo, função, argumentos) — em ordem e sem buracos de T0 a T1
P = []
P.append(("A", isabel, ("A", "W1016", 0.02, 4.5)))                         # 13.65 entrada da artista
P.append(("H1a", obra, ("H1a", "IMG_1193", 3.0, 4.6)))
P.append(("H1b", obra, ("H1b", "IMG_1184", 0.0, 2.8)))
P.append(("B", isabel, ("B", "W1021", 0.02, 8.99)))                        # 28.10 Anônimos
P.append(("H2", detalhe_anonimos, ("H2", 24.2, 31.4, 0.71)))
P.append(("C", isabel, ("C", "W0931", 0.02, 3.0)))                         # 46.05 Palmas
P.append(("H3a", obra, ("H3a", "IMG_1183", 1.6, 8.3)))
P.append(("H3b", obra, ("H3b", "IMG_1197", 9.2, 2.2)))
P.append(("D", isabel, ("D", "W0933", 0.02, 5.66)))                        # 63.69 Enchentes
P.append(("H4a", obra, ("H4a", "IMG_1191", 0.2, 7.2, 0.75)))
P.append(("H4b", obra, ("H4b", "IMG_1186", 3.3, 3.3, 0.75)))
P.append(("H4c", obra, ("H4c", "IMG_1192", 2.2, 1.0, 0.73)))
P.append(("X", azuis, ("X",)))                                             # 83.97 telas azuis + ESPERANÇA
P.append(("H5", obra, ("H5", "IMG_1197", 4.6, 2.4)))                       # depois das telas azuis (84–94.9 já é alta qualidade)
P.append(("H5b", obra, ("H5b", "IMG_1193", 7.6, 1.2)))
P.append(("H6a", obra, ("H6a", "IMG_1183", 9.9, 2.1)))
P.append(("H6b", obra, ("H6b", "IMG_1184", 2.8, 2.6)))
P.append(("H6c", obra, ("H6c", "IMG_1193", 0.0, 2.6)))
P.append(("F", isabel, ("F", "W0938", 0.02, 4.66)))                        # 111.14 venda
P.append(("H7a", obra, ("H7a", "IMG_1197", 11.4, 4.4)))
P.append(("H7b", obra, ("H7b", "IMG_1186", 0.0, 3.3)))
P.append(("H7c", obra, ("H7c", "IMG_1184", 5.4, 2.2)))
P.append(("G", isabel, ("G", "W0938", 36.44, 41.56)))                      # 129.45 convite
P.append(("H8a", obra, ("H8a", "IMG_1187", 0.0, 3.3)))
P.append(("H8b", obra, ("H8b", "IMG_1184", 7.6, 2.0)))

# início desejado de cada plano da artista (sincronia com a voz)
def out_t(vid, s):
    for c in tl["cortes"]:
        if c["vid"] == vid and c["src_a"] - 0.02 <= s <= c["src_b"] + 0.6:
            return c["t"] + (s - c["src_a"]) / VEL
ALVO = {"A": out_t("W1016", 0.02), "B": out_t("W1021", 0.02), "C": out_t("W0931", 0.02), "D": out_t("W0933", 0.02),
"F": out_t("W0938", 0.02), "G": out_t("W0938", 36.44), "X": 83.972}
print({k: round(v, 2) for k, v in ALVO.items()})

durs = {}
for nome, fn, args in P: durs[nome] = fn(*args)
# monta: entre planos da artista, os clipes de obras são ajustados (trim) para a artista cair no tempo certo
ordem = [n for n, _, _ in P]; t = T0; pecas = []
for k, n in enumerate(ordem):
    if n in ALVO: assert abs(t - ALVO[n]) < 0.05, (n, t, ALVO[n])
    prox = next((ALVO[m] for m in ordem[k+1:] if m in ALVO), T1)
    resto = [m for m in ordem[k+1:ordem.index(next((m for m in ordem[k+1:] if m in ALVO), ordem[-1])) if any(m in ALVO for m in ordem[k+1:]) else len(ordem)]]
    d = durs[n]
    if n not in ALVO:
        # quanto falta até o próximo alvo, considerando os clipes restantes deste intervalo
        seg = []
        for m in ordem[k:]:
            if m in ALVO: break
            seg.append(m)
        alvo_fim = prox; disp = alvo_fim - t
        soma = sum(durs[m] for m in seg)
        d = durs[n] * disp / soma if soma > 0 else d   # distribui proporcionalmente
        for m in seg: durs[m] = durs[m] * disp / soma
    pecas.append((n, t, d)); t += d
assert abs(t - T1) < 0.05, t
# cada peça é recortada/esticada para a duração exata
lista = []
for n, t0, d in pecas:
    src = f"cob/{n}.mp4"; real = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    out = f"cob/fit_{n}.mp4"
    vf = f"setpts=PTS*{d/real:.5f},fps=30" if real < d - 0.04 else "fps=30"
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-t", f"{d:.3f}", "-an", "-c:v", "libx264", "-crf", "15", "-preset", "fast", out])
    lista.append(out)
open("cob/lista.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in lista))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "cob/lista.txt", "-c:v", "libx264", "-crf", "15", "-preset", "fast", "fala_video.mp4"])
json.dump([(n, round(t0, 3), round(d, 3)) for n, t0, d in pecas], open("cob/pecas.json", "w"), indent=1)

# ---------- legendas (somente onde a imagem da artista NÃO aparece; nos planos dela já há a legenda original) ----------
FIX = {"sadas": "engessadas", "Braza": "Brasa"}
janelas = [(t0, t0 + d) for n, t0, d in pecas if n not in ALVO]
def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h}:{m:02d}:{s:05.2f}"
ev = []
for c in tl["cortes"]:
    ws = [w for s in tr[c["vid"]] for w in s["w"] if c["src_a"] - 0.02 <= w["s"] <= c["src_b"]]
    chunk = []
    def fecha(ch, fim):
        txt = " ".join(FIX.get(w["w"].strip(), w["w"].strip()) for w in ch).replace("a um Instituto", "ao Instituto")
        a = c["t"] + (ch[0]["s"] - c["src_a"]) / VEL
        ev.append([a, fim, txt])
    for i, w in enumerate(ws):
        chunk.append(w); txt = " ".join(x["w"].strip() for x in chunk)
        nxt = ws[i+1] if i + 1 < len(ws) else None
        quebra = (w["w"].strip()[-1:] in ",.!?" or len(txt) > 26 or nxt is None or (nxt and nxt["s"] - w["e"] > 0.35))
        if quebra:
            fim = c["t"] + ((nxt["s"] if nxt else w["e"] + 0.5) - c["src_a"]) / VEL
            fecha(chunk, fim); chunk = []
for e in ev:  # junta pedaços de 1 palavra soltos ao anterior
    pass
linhas = []
for a, b, txt in ev:
    for j0, j1 in janelas:
        x0, x1 = max(a, j0 + 0.05), min(b, j1 - 0.02)
        if x1 - x0 > 0.25: linhas.append((x0, x1, txt))
cab = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,Inter Medium,56,&H005CDDD2,&H005CDDD2,&H00141C1C,&H00000000,0,0,0,0,100,100,0,0,1,2.6,0,2,70,70,610,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open("legendas.ass", "w").write(cab + "".join(f"Dialogue: 0,{ts(a)},{ts(b)},Leg,,0,0,0,,{t}\n" for a, b, t in linhas))
print(len(linhas), "legendas;", "faixa", T0, "->", round(t, 2))
