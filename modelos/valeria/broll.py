"""Vídeos de apoio (originais em alta qualidade) para o Reels da Valéria. Uso: python3 broll.py <pasta_trabalho>"""
import json, subprocess, sys, os
W = sys.argv[1]; os.chdir(W); os.makedirs("broll", exist_ok=True)
U = "/root/.claude/uploads/b13c12c9-2298-5e04-a0eb-b70d13ae7f51"
R = "/tmp/claude-0/-home-user-comunica-o/b13c12c9-2298-5e04-a0eb-b70d13ae7f51/scratchpad/recomeco/src"
SRC = {"1191": f"{R}/IMG_1191.mov", "1192": f"{R}/IMG_1192.mov", "1130": f"{U}/1c04a3fd-IMG_1130.mov", "1135": f"{U}/7ce75509-IMG_1135.mov",
       "1149": f"{U}/c7f7a429-IMG_1149.mov", "1136": f"{U}/757e99f9-IMG_1136.mov", "1133": f"{U}/f63cf550-IMG_1133.mov",
       "1137": f"{U}/85717d0b-IMG_1137.mov", "1134": f"{U}/6072658e-IMG_1134.mov", "1132": f"{U}/b2125603-IMG_1132.mov"}
# tipo -> [(vídeo, início, fração da duração, zoom0, zoom1)]
MAPA = {"B:enchentes": [("1191", 0.2, .52, 1.08, 1.0), ("1192", 0.3, .48, 1.0, 1.08)],
        "B:aula1": [("1130", 0.3, .5, 1.0, 1.06), ("1135", 1.0, .5, 1.06, 1.0)],
        "B:resultados": [("1149", 7.4, .5, 1.04, 1.10), ("1136", 1.0, .5, 1.0, 1.06)],
        "B:aula2": [("1133", 0.4, .52, 1.0, 1.06), ("1137", 2.0, .48, 1.05, 1.0)],
        "B:aula3": [("1134", 1.5, .5, 1.0, 1.06), ("1132", 0.5, .5, 1.06, 1.0)]}
plano = json.load(open("plano.json"))
for k, p in enumerate(plano["pecas"]):
    if p["tipo"] not in MAPA: continue
    partes = []
    for j, (v, ss, fr, z0, z1) in enumerate(MAPA[p["tipo"]]):
        d = p["d"] * fr; z = f"({z0}+({z1}-{z0})*t/{d:.3f})"; o = f"broll/p{k:02d}_{j}.mp4"
        vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,"
              f"scale=w='trunc(1080*{z}/2)*2':h=-2:eval=frame:flags=lanczos,crop=1080:1920,eq=contrast=1.05:saturation=1.06,format=yuv420p")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", f"{d:.3f}", "-i", SRC[v], "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "15", "-preset", "fast", o], check=True); partes.append(o)
    open("broll/l.txt", "w").write("".join(f"file '{os.path.basename(x)}'\n" for x in partes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "broll/l.txt", "-t", f"{p['d']:.3f}",
                    "-c:v", "libx264", "-crf", "15", "-preset", "fast", f"broll/p{k:02d}.mp4"], check=True)
    print(k, p["tipo"], "ok")
