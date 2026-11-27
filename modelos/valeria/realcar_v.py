"""Realça os trechos da Valéria (super-resolução + restauração de rosto), já recortados acima das legendas antigas.
Uso: python3 realcar_v.py <modelos_dir> <pasta_trabalho>"""
import sys, os, json, subprocess, time, numpy as np, cv2
MD, W = sys.argv[1], sys.argv[2]
sys.argv = ["x", MD]; sys.path.insert(0, "/home/user/comunica-o/modelos/recomeco")
import realcar   # carrega Real-ESRGAN e RetinaFace
import onnxruntime as ort
_so = ort.SessionOptions(); _so.intra_op_num_threads = 4
CF = ort.InferenceSession(f"{MD}/codeformer.onnx", _so, providers=["CPUExecutionProvider"])

def codeformer(img, pts, w=0.9, blend=0.6):
    """CodeFormer com fidelidade alta: realça sem mudar o rosto da pessoa."""
    M_, _ = cv2.estimateAffinePartial2D(pts.astype(np.float32), realcar.FFHQ, method=cv2.LMEDS)
    face = cv2.warpAffine(img, M_, (512, 512), borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_AREA)
    x = (cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255 - 0.5) / 0.5
    y = CF.run(["output"], {"input": x.transpose(2, 0, 1)[None], "weight": np.array(w, dtype=np.float64)})[0][0].transpose(1, 2, 0)
    y = cv2.cvtColor(((np.clip(y, -1, 1) + 1) / 2 * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)
    mask = np.zeros((512, 512), np.float32); cv2.rectangle(mask, (40, 40), (472, 472), 1, -1); mask = cv2.GaussianBlur(mask, (0, 0), 22)
    Mi = cv2.invertAffineTransform(M_); h, ww = img.shape[:2]
    back = cv2.warpAffine(y, Mi, (ww, h), borderMode=cv2.BORDER_REPLICATE); m = cv2.warpAffine(mask, Mi, (ww, h))[..., None] * blend
    return (img * (1 - m) + back * m).astype(np.uint8)
os.chdir(W); os.makedirs("vreal", exist_ok=True)
plano = json.load(open("plano.json")); VEL = plano["VEL"]
CROP = {"Vsit": ((24, 280, 432, 302), (1000, 700)), "Vstand": ((0, 106, 480, 470), (900, 882))}
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
            c = FR[fi][y:y+h, x:x+w]
            up = cv2.resize(realcar.super_res(c), (ow, oh), interpolation=cv2.INTER_AREA)
            up = cv2.addWeighted(up, 0.72, cv2.resize(c, (ow, oh), interpolation=cv2.INTER_LANCZOS4), 0.28, 0)   # textura natural
            d = realcar.detect(up)
            if d is not None and (d[1][2] - d[1][0]) > 40: up = codeformer(up, d[2])
            last = (fi, up)
        pr.stdin.write(last[1].tobytes())
        if i % 30 == 0: print(f"peça {k} {p['tipo']} {i}/{n} {time.time() - t0:.0f}s", flush=True)
    pr.stdin.close(); pr.wait(); os.rename(out + ".tmp.mp4", out)
print("REALCE VALERIA OK")
