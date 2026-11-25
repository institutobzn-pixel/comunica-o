"""Monta o vídeo curado da exposição.
Uso: python3 montar.py video.mov camadas/ saida.mp4 [--limpo]
--limpo: só as cenas curadas, sem textos, logo e cartão final.

Curadoria (tempos no vídeo original de 15,8 s, uma panorâmica contínua):
  - os quadros azuis aparecem várias vezes seguidas (2 s a 7,5 s): esse trecho foi cortado;
  - cada conjunto de obras entra uma vez só;
  - os cortes e enquadramentos evitam as plaquinhas de informação/preço.
"""
import sys, subprocess
vid, cam, outp = sys.argv[1:4]
limpo = "--limpo" in sys.argv
LENTO = 1.3   # câmera lenta leve, deixa a panorâmica mais suave
XF = 0.5      # duração da transição entre cenas
FIM = 2.5     # cartão final
# (início, fim, zoom, âncora x 0=esq 1=dir, âncora y 0=topo 1=base)
CENAS = [
    (0.0, 2.3, 1.00, .5, .5),   # canto da galeria: quadros azuis e mezanino
    (7.8, 9.8, 1.12, 1., .5),   # tríptico das mãos (preto e branco, azul, vermelho)
    (10.2, 11.2, 1.12, 0., .5), # quadros vermelhos
    (13.8, 15.8, 1.30, 0., .1), # quadros azuis com a luz do sol (fechado, sem o banner)
]
ins, fi = [], ""
durs = []
for i, (s, e, z, ax, ay) in enumerate(CENAS):
    ins += ["-ss", str(s), "-t", str(e - s), "-i", vid]
    W, H = round(1080 * z / 2) * 2, round(1920 * z / 2) * 2
    fi += (f"[{i}:v]scale=1080:1920,setsar=1,setpts={LENTO}*(PTS-STARTPTS),framerate=fps=30,"
           f"scale={W}:{H},crop=1080:1920:{(W-1080)*ax}:{(H-1920)*ay},"
           f"eq=contrast=1.06:saturation=1.08:brightness=-0.01,format=yuv420p[c{i}];")
    durs.append((e - s) * LENTO)
prev, off = "c0", 0.0
for k in range(1, len(CENAS)):
    off += durs[k - 1] - XF
    fi += f"[{prev}][c{k}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{k}];"
    prev = f"x{k}"
cenas = sum(durs) - XF * (len(CENAS) - 1)
n = len(CENAS)
if limpo:
    total = cenas
    fi += f"[{prev}]fade=in:d=0.3,fade=out:st={total-0.5:.3f}:d=0.5,format=yuv420p[vout]"
else:
    total = cenas + FIM - XF
    ins += ["-loop", "1", "-t", str(total), "-i", f"{cam}/base.png",
            "-loop", "1", "-t", str(total), "-i", f"{cam}/texto.png",
            "-loop", "1", "-t", str(FIM), "-i", f"{cam}/fim.png"]
    B, T, Fm = n, n + 1, n + 2
    fi += (f"[{B}:v]format=rgba[b];"
           f"[{T}:v]format=rgba,fade=in:st=0.4:d=0.8:alpha=1,fade=out:st=3.4:d=0.5:alpha=1[t];"
           f"[{Fm}:v]format=yuv420p,fps=30,setsar=1,settb=1/30[f0];"
           f"[{prev}][b]overlay=0:0:shortest=1[o1];"
           f"[o1][t]overlay=x=0:y='max(0,80-80*(t-0.4)/0.8)':shortest=1,format=yuv420p,fps=30,settb=1/30[o2];"
           f"[o2][f0]xfade=transition=fade:duration={XF}:offset={cenas-XF:.3f},"
           f"fade=in:d=0.3,fade=out:st={total-0.4:.3f}:d=0.4,format=yuv420p[vout]")
ins += ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=44100:cl=stereo"]
aud = len(CENAS) + (0 if limpo else 3)
args = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fi, "-map", "[vout]", "-map", f"{aud}:a",
        "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", outp]
subprocess.run(args, check=True)
print("ok:", outp, f"{total:.1f}s")
