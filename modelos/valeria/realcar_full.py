"""Realça a Valéria em TELA CHEIA (super-resolução + CodeFormer de alta fidelidade com pontos do rosto suavizados = sem tremer).
A faixa de baixo (legendas antigas) fica sob o painel, então só é ampliada.  Uso: python3 realcar_full.py <modelos> <pasta>"""
import sys, os, json, subprocess, time, numpy as np, cv2
MD, W = sys.argv[1], sys.argv[2]
sys.argv = ["x", MD]; sys.path.insert(0, "/home/user/comunica-o/modelos/recomeco")
import realcar
import onnxruntime as ort
CF = ort.InferenceSession(f"{MD}/codeformer.onnx", providers=["CPUExecutionProvider"])
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "realcar_v.py")).read()
exec(src[src.index("def codeformer"):src.index("os.chdir(W)")])
os.chdir(W); os.makedirs("vfull", exist_ok=True)
plano = json.load(open("plano.json"))
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "src.mp4", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
FR = np.frombuffer(raw, np.uint8).reshape(-1, 848, 480, 3)
TOP = 560; S = 1088 / 480; HT = int(round(TOP * S))          # parte de cima com IA: 0..560 px do original
for k, p in enumerate(plano["pecas"]):
    if p["tipo"] != "V": continue
    out = f"vfull/p{k:02d}.mp4"
    if os.path.exists(out): continue
    n = int(round(p["d"] * 30)); idx = [min(len(FR) - 1, int(round(p["src_a"] * 30)) + i) for i in range(n)]
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1080x1920", "-r", "30", "-i", "-",
                           "-vf", "hqdn3d=0:0:3:3,unsharp=3:3:0.2:3:3:0,format=yuv420p", "-c:v", "libx264", "-crf", "14", "-preset", "fast", out + ".tmp.mp4"], stdin=subprocess.PIPE)
    t0 = time.time(); ema = None
    for i, fi in enumerate(idx):
        f = FR[fi]
        base = cv2.resize(f, (1088, 1920), interpolation=cv2.INTER_LANCZOS4)
        c = f[:TOP]
        up = cv2.resize(realcar.super_res(c), (1088, HT), interpolation=cv2.INTER_AREA)
        up = cv2.addWeighted(up, 0.72, base[:HT], 0.28, 0)        # textura natural
        d = realcar.detect(up[150:1250])
        if d is not None and (d[1][2] - d[1][0]) > 40:
            pts = d[2] + np.array([0, 150])
            ema = pts if ema is None or np.abs(pts - ema).max() > 25 else ema * 0.6 + pts * 0.4   # suaviza: rosto não "treme"
            up = codeformer(up, ema, w=0.9, blend=0.55)
        base[:HT - 20] = up[:HT - 20]
        m = np.linspace(1, 0, 20)[:, None, None]; base[HT - 20:HT] = (up[HT - 20:] * m + base[HT - 20:HT] * (1 - m)).astype(np.uint8)
        pr.stdin.write(np.ascontiguousarray(base[:, 4:1084]).tobytes())
        if i % 60 == 0: print(f"peça {k} {i}/{n} {time.time() - t0:.0f}s", flush=True)
    pr.stdin.close(); pr.wait(); os.replace(out + ".tmp.mp4", out)
print("REALCE TELA CHEIA OK")
