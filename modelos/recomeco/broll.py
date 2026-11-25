"""Renderiza os trechos das obras (vídeos IMG originais) com zoom lento e cor natural.
Uso: python3 broll.py <pasta_trabalho>"""
import subprocess, sys, os, json
W = sys.argv[1]; os.chdir(W); os.makedirs("broll", exist_ok=True)
# nome: (vídeo, início, duração, zoom inicial, zoom final)
CLIPES = {
    # abertura
    "o1": ("IMG_1192", 0.2, 1.9, 1.10, 1.02),
    "o2": ("IMG_1183", 2.2, 2.2, 1.02, 1.10),
    "o3": ("IMG_1185", 1.0, 2.0, 1.08, 1.00),
    "o4": ("IMG_1197", 7.0, 5.6, 1.00, 1.07),
    "o5": ("IMG_1182", 2.5, 4.1, 1.06, 1.00),
    # telas azuis (esperança)
    "e1": ("IMG_1182", 0.0, 3.4, 1.00, 1.06),
    "e2": ("IMG_1185", 3.4, 5.2, 1.03, 1.10),
    "e3": ("IMG_1184", 10.0, 3.5, 1.04, 1.12),
    # encerramento
    "c1": ("IMG_1197", 0.0, 4.5, 1.00, 1.06),
    "c2": ("IMG_1193", 7.5, 3.9, 1.05, 1.00),
    "c3": ("IMG_1182", 6.5, 4.3, 1.00, 1.08),
}
for nome, (v, ss, d, z0, z1) in CLIPES.items():
    z = f"({z0}+({z1}-{z0})*t/{d})"
    vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,"
          f"scale=w='trunc(1080*{z}/2)*2':h=-2:eval=frame:flags=lanczos,crop=1080:1920,"
          f"eq=contrast=1.04:saturation=1.0,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(d), "-i", f"src/{v}.mov",
                    "-vf", vf, "-an", "-c:v", "libx264", "-crf", "15", "-preset", "fast", f"broll/{nome}.mp4"], check=True)
    print(nome, "ok")
json.dump({k: v[2] for k, v in CLIPES.items()}, open("broll/duracoes.json", "w"))
