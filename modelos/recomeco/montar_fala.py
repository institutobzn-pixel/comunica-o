"""Gera os trechos de vídeo da fala (1080x1920, 15% mais rápidos) e a trilha de voz, e calcula a linha do tempo.
Uso: python3 montar_fala.py <pasta_trabalho>"""
import json, subprocess, sys, wave, numpy as np, os
W = sys.argv[1]; os.chdir(W)
VEL = 1.15; SR = 44100
T_OPEN = 13.9        # fim da abertura
FADE_IN = 0.5        # dissolve abertura -> fala
GAP_BLOCO = 0.35     # respiro entre blocos (s, já na saída)
cortes = json.load(open("cortes.json"))

def run(cmd): subprocess.run(cmd, check=True)
UPSCALE = ("scale=1088:1922:flags=lanczos,crop=1080:1920,hqdn3d=1.2:1.2:3:3,"
           "unsharp=5:5:0.55:5:5:0,eq=contrast=1.03:saturation=1.02,fps=30,format=yuv420p")

os.makedirs("seg", exist_ok=True)
t = T_OPEN - FADE_IN + 0.25   # a voz começa um pouco depois do início do dissolve
voz = []; timeline = []
for i, c in enumerate(cortes):
    ultimo = i + 1 == len(cortes) or cortes[i+1]["bloco"] != c["bloco"]
    extra = GAP_BLOCO if ultimo else 0.0
    if i + 1 == len(cortes): extra = 1.2      # sobra de imagem para o dissolve final
    src_dur = (c["b"] - c["a"]) + extra * VEL
    vdur = src_dur / VEL
    out = f"seg/s{i:02d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["a"]), "-t", f"{src_dur:.3f}", "-i", f"limpo_{c['vid']}.mp4",
         "-vf", f"setpts=(PTS-STARTPTS)/{VEL},{UPSCALE}", "-an", "-c:v", "libx264", "-crf", "16", "-preset", "fast", out])
    # voz do trecho (somente a parte falada, sem o 'extra')
    a = wave.open(f"{c['vid']}_voz.wav"); a.setpos(int(c["a"] * SR))
    x = np.frombuffer(a.readframes(int((c["b"] - c["a"]) * SR)), np.int16).reshape(-1, 2).astype(np.float32)
    timeline.append(dict(i=i, bloco=c["bloco"], vid=c["vid"], src_a=c["a"], src_b=c["b"], t=round(t, 3),
                         fala_fim=round(t + c["dur"], 3), vdur=round(vdur, 3), arq=out))
    voz.append((t, x)); t += vdur

T_FALA_FIM = t
# monta a voz: cada trecho acelerado com atempo (ffmpeg) e colocado no tempo certo
total = T_FALA_FIM + 20
mix = np.zeros((int(total * SR), 2), np.float32)
for k, (t0, x) in enumerate(voz):
    raw = f"seg/v{k:02d}.raw"; x.astype(np.int16).tofile(raw)
    sp = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", raw,
                         "-af", f"atempo={VEL}", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(sp, np.int16).reshape(-1, 2).astype(np.float32)
    n = len(y); fade = int(0.012 * SR); env = np.ones(n); env[:fade] = np.linspace(0, 1, fade); env[-fade:] = np.linspace(1, 0, fade)
    s0 = int(t0 * SR); mix[s0:s0+n] += y * env[:, None]
o = wave.open("voz_total.wav", "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes(np.clip(mix, -32768, 32767).astype(np.int16).tobytes()); o.close()
json.dump(dict(T_OPEN=T_OPEN, FADE_IN=FADE_IN, T_FALA_FIM=round(T_FALA_FIM, 3), VEL=VEL, cortes=timeline),
          open("timeline.json", "w"), indent=1)
print("fala de", T_OPEN - FADE_IN, "a", round(T_FALA_FIM, 2))
