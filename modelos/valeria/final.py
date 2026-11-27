"""Montagem final do Reels 'Seja como a Valéria'. Uso: python3 final.py <pasta_trabalho> saida.mp4"""
import json, subprocess, sys, os, wave, numpy as np
from PIL import Image, ImageDraw, ImageFilter
W = sys.argv[1]; OUT = os.path.abspath(sys.argv[2]); os.chdir(W); os.makedirs("comp", exist_ok=True)
pl = json.load(open("plano.json")); VEL = pl["VEL"]; END = pl["total"]
def run(a): subprocess.run(a, check=True)
# máscara de cantos arredondados da janela e logo com sombra
JAN = {"Vsit": (40, 600, 1000, 700), "Vstand": (90, 590, 900, 882)}
for nome, (_, _, WW, WH) in JAN.items():
    m = Image.new("L", (WW, WH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, WW - 1, WH - 1), 38, fill=255); m.save(f"comp/mask_{nome}.png")
    sh = Image.new("RGBA", (WW + 120, WH + 120), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((60, 75, 60 + WW, 75 + WH), 38, fill=(0, 0, 0, 150))
    sh.filter(ImageFilter.GaussianBlur(28)).save(f"comp/sombra_{nome}.png")
lg = Image.open("/home/user/comunica-o/marca/logo-branca.png").convert("RGBA"); lg = lg.resize((150, int(150 * lg.height / lg.width)), Image.LANCZOS)
cv = Image.new("RGBA", (lg.width + 40, lg.height + 40), (0, 0, 0, 0)); sd = Image.new("RGBA", lg.size, (0, 0, 0, 160)); sd.putalpha(lg.split()[3].point(lambda v: v * .55))
cv.alpha_composite(sd, (20, 24)); cv = cv.filter(ImageFilter.GaussianBlur(6)); cv.alpha_composite(lg, (20, 20)); cv.save("comp/logo.png")

pecas = []
for k, p in enumerate(pl["pecas"]):
    o = f"comp/c{k:02d}.mp4"; d = p["d"]
    if p["tipo"] in JAN:
        WX, WY, WW, WH = JAN[p["tipo"]]; tp = p["tipo"]
        fc = (f"[0:v]setpts=(PTS-STARTPTS)/{VEL},fps=30,crop=480:575:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3,eq=brightness=-0.12:saturation=1.15[bg];"
              f"[1:v]scale={WW}:{WH}:flags=lanczos,unsharp=5:5:0.35:5:5:0,noise=alls=5:allf=t,format=rgba[w0];[2:v]format=gray[mk];[w0][mk]alphamerge[w];"
              f"[bg][3:v]overlay={WX-60}:{WY-75}[b2];[b2][w]overlay={WX}:{WY},format=yuv420p[v]")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(p["src_a"]), "-t", f"{d*VEL+0.2:.3f}", "-i", "src.mp4", "-i", f"vreal/p{k:02d}.mp4",
             "-loop", "1", "-i", f"comp/mask_{tp}.png", "-loop", "1", "-i", f"comp/sombra_{tp}.png", "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}",
             "-c:v", "libx264", "-crf", "14", "-preset", "fast", o])
    elif p["tipo"].startswith("B:"):
        run(["ffmpeg", "-v", "error", "-y", "-i", f"broll/p{k:02d}.mp4", "-t", f"{d:.3f}", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "14", "-preset", "fast", o])
    else:  # vinheta/final: os cartões vêm opacos na camada de títulos
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x13339c:s=1080x1920:r=30:d={d:.3f}", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", o])
    pecas.append(o)
open("comp/l.txt", "w").write("".join(f"file '{os.path.basename(x)}'\n" for x in pecas))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "comp/l.txt", "-c", "copy", "comp/base.mp4"])

# voz: trechos acelerados colocados no tempo certo
SR = 44100; a = wave.open("voz.wav"); raw = np.frombuffer(a.readframes(a.getnframes()), np.int16).reshape(-1, 2)
mix = np.zeros((int((END + 2) * SR), 2), np.float32)
for v in pl["voz"]:
    x = raw[int(v["src_a"] * SR):int(v["src_b"] * SR)]
    y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", f"atempo={VEL}", "-f", "s16le", "-"],
                                     input=x.tobytes(), capture_output=True, check=True).stdout, np.int16).reshape(-1, 2).astype(np.float32)
    f = int(.012 * SR); e = np.ones(len(y)); e[:f] = np.linspace(0, 1, f); e[-f:] = np.linspace(1, 0, f)
    s0 = int(v["t"] * SR); mix[s0:s0 + len(y)] += y * e[:, None]
o = wave.open("comp/voz.wav", "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(np.clip(mix, -32768, 32767).astype(np.int16).tobytes()); o.close()

faixas = json.load(open("tit/faixas.json")); cards = [(c["t"], c["t"] + c["d"]) for c in pl["cards"]] + [(0, pl["cards"][0]["t"])]  # sem logo no gancho (texto no topo)
ins = ["-i", "comp/base.mp4", "-loop", "1", "-i", "comp/logo.png"]; fg = []
nao_card = "*".join(f"not(between(t,{a:.3f},{b:.3f}))" for a, b in cards)
fg.append(f"[0:v][1:v]overlay=W-w-40:215:enable='{nao_card}'[v0]"); cur = "[v0]"
for k, (a0, z) in enumerate(faixas):
    ins += ["-i", f"tit/t{k}.mov"]; i = 2 + k
    fg.append(f"[{i}:v]setpts=PTS+{a0}/TB[t{k}]"); fg.append(f"{cur}[t{k}]overlay=eof_action=pass[w{k}]"); cur = f"[w{k}]"
fg.append(f"{cur}ass=legendas.ass:fontsdir=/usr/share/fonts/opentype/inter,fade=in:st=0:d=0.25,trim=0:{END},format=yuv420p[vout]")
iv = 2 + len(faixas); im = iv + 1; ins += ["-i", "comp/voz.wav", "-i", "trilha.wav"]
fg.append(f"[{iv}:a]atrim=0:{END},highpass=f=85,lowpass=f=12500,acompressor=threshold=-20dB:ratio=3:attack=6:release=160:makeup=2,equalizer=f=3200:t=q:w=1.2:g=2.5,asplit=2[voz][key]")
fg.append(f"[{im}:a]volume=1.5[mus]"); fg.append("[mus][key]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=380:knee=4[musd]")
fg.append(f"[voz][musd]amix=inputs=2:normalize=0,alimiter=limit=0.89,atrim=0:{END}[aout]")
run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fg), "-map", "[vout]", "-map", "[aout]", "-t", str(END),
     "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
     "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", OUT + ".tmp.mp4"])
run(["ffmpeg", "-v", "error", "-y", "-i", OUT + ".tmp.mp4", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
     "-ar", "44100", "-movflags", "+faststart", OUT]); os.remove(OUT + ".tmp.mp4"); print("ok:", OUT)
