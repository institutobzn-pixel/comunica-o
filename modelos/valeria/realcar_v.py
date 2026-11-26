"""Realça os trechos da Valéria (super-resolução + restauração de rosto), já recortados acima das legendas antigas.
Uso: python3 realcar_v.py <modelos_dir> <pasta_trabalho>"""
import sys, os, json, subprocess, time, numpy as np, cv2
MD, W = sys.argv[1], sys.argv[2]
sys.argv = ["x", MD]; sys.path.insert(0, "/home/user/comunica-o/modelos/recomeco")
import realcar   # carrega Real-ESRGAN, RetinaFace e GFPGAN
os.chdir(W); os.makedirs("vreal", exist_ok=True)
plano = json.load(open("plano.json")); VEL = plano["VEL"]
CROP = {"Vsit": ((60, 300, 360, 252), (1080, 756)), "Vstand": ((26, 0, 326, 580), (1080, 1920))}
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "src.mp4", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
FR = np.frombuffer(raw, np.uint8).reshape(-1, 848, 480, 3); FPS = 30
for k, p in enumerate(plano["pecas"]):
    if p["tipo"] not in CROP: continue
    out = f"vreal/p{k:02d}.mp4"
    if os.path.exists(out): continue
    (x, y, w, h), (ow, oh) = CROP[p["tipo"]]
    n = int(round(p["d"] * 30)); idx = [min(len(FR) - 1, int(round(p["src_a"] * FPS + i * VEL))) for i in range(n)]
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}", "-r", "30", "-i", "-",
                           "-vf", "unsharp=3:3:0.25:3:3:0,format=yuv420p", "-c:v", "libx264", "-crf", "14", "-preset", "fast", out + ".tmp.mp4"],
                          stdin=subprocess.PIPE)
    t0 = time.time(); last = (None, None)
    for i, fi in enumerate(idx):
        if fi != last[0]:
            up = realcar.super_res(FR[fi][y:y+h, x:x+w])
            up = cv2.resize(up, (ow, oh), interpolation=cv2.INTER_AREA)
            d = realcar.detect(up)
            if d is not None and (d[1][2] - d[1][0]) > 50: up = realcar.restore_face(up, d[2])
            last = (fi, up)
        pr.stdin.write(last[1].tobytes())
        if i % 30 == 0: print(f"peça {k} {p['tipo']} {i}/{n} {time.time() - t0:.0f}s", flush=True)
    pr.stdin.close(); pr.wait(); os.rename(out + ".tmp.mp4", out)
print("REALCE VALERIA OK")
