"""Realça os planos da artista: super-resolução (Real-ESRGAN general x4v3) + restauração de rosto (GFPGAN 1.4).
Uso: python3 realcar.py <modelos_dir> entrada.mp4 saida.mp4 x_crop inicio fim velocidade"""
import sys, cv2, numpy as np, onnxruntime as ort, subprocess, time

MD = sys.argv[1]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
SR = ort.InferenceSession(f"{MD}/realesr-general-x4v3.onnx", so, providers=["CPUExecutionProvider"])
DET = ort.InferenceSession(f"{MD}/retinaface_10g.onnx", so, providers=["CPUExecutionProvider"])
GF = ort.InferenceSession(f"{MD}/gfpgan_1.4.onnx", so, providers=["CPUExecutionProvider"])
FFHQ = np.array([[0.37691676, 0.46864664], [0.62285697, 0.46912813], [0.50123859, 0.61331904],
                 [0.39308822, 0.72541100], [0.61150205, 0.72490465]], np.float32) * 512

def super_res(img):  # BGR uint8 -> 4x
    x = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255
    y = SR.run(None, {"input": x})[0][0].transpose(1, 2, 0)
    return cv2.cvtColor((np.clip(y, 0, 1) * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)

def detect(img, thr=0.55):
    h, w = img.shape[:2]; s = 640 / max(h, w)
    r = cv2.resize(img, (int(w * s), int(h * s))); pad = np.zeros((640, 640, 3), np.uint8); pad[:r.shape[0], :r.shape[1]] = r
    x = ((pad.astype(np.float32) - 127.5) / 128.0).transpose(2, 0, 1)[None]
    out = DET.run(None, {"input": x}); best = None
    for k, st in enumerate((8, 16, 32)):
        sc, bb, kp = out[k][:, 0], out[k + 3], out[k + 6]
        n = 640 // st; cy, cx = np.mgrid[0:n, 0:n]; cen = np.stack([cx, cy], -1).reshape(-1, 2).repeat(2, 0) * st
        for i in np.where(sc > thr)[0]:
            box = np.concatenate([cen[i] - bb[i, :2] * st, cen[i] + bb[i, 2:] * st]) / s
            pts = (cen[i] + kp[i].reshape(5, 2) * st) / s
            area = (box[2] - box[0]) * (box[3] - box[1])
            if best is None or area > best[0]: best = (area, box, pts, sc[i])
    return best

def restore_face(img, pts, blend=0.8):
    M, _ = cv2.estimateAffinePartial2D(pts.astype(np.float32), FFHQ, method=cv2.LMEDS)
    face = cv2.warpAffine(img, M, (512, 512), borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_AREA)
    x = (cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255 - 0.5) / 0.5
    y = GF.run(None, {"input": x.transpose(2, 0, 1)[None]})[0][0].transpose(1, 2, 0)
    y = cv2.cvtColor(((np.clip(y, -1, 1) + 1) / 2 * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)
    mask = np.zeros((512, 512), np.float32); cv2.rectangle(mask, (40, 40), (472, 472), 1, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), 22)
    Mi = cv2.invertAffineTransform(M); h, w = img.shape[:2]
    back = cv2.warpAffine(y, Mi, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpAffine(mask, Mi, (w, h))[..., None] * blend
    return (img * (1 - m) + back * m).astype(np.uint8)

def process_frame(f, x0):
    crop = f[0:735, x0:x0 + 413]
    up = super_res(crop)                                   # 1652 x 2940
    up = cv2.resize(up, (1080, 1920), interpolation=cv2.INTER_AREA)
    d = detect(up)
    if d is not None and (d[1][2] - d[1][0]) > 60: up = restore_face(up, d[2])
    return up, d

if __name__ == "__main__":
    _, md, inp, outp, x0, a, b, vel = sys.argv; x0 = int(x0); a = float(a); b = float(b); vel = float(vel)
    cap = cv2.VideoCapture(inp); fps = cap.get(5)
    # extrai os quadros exatos com ffmpeg (busca precisa)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", f"{b - a:.3f}", "-i", inp, "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 848, 480, 3)
    # só os quadros que entram no vídeo (fala 15% mais rápida -> 30 fps na saída)
    n_out = int(round((b - a) / vel * 30)); idx = [min(len(fr) - 1, int(round(k * vel))) for k in range(n_out)]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1080x1920", "-r", "30",
                          "-i", "-", "-vf", "unsharp=3:3:0.25:3:3:0,format=yuv420p",
                          "-c:v", "libx264", "-crf", "14", "-preset", "fast", outp], stdin=subprocess.PIPE)
    t0 = time.time(); cache = {}
    for k, i in enumerate(idx):
        if i not in cache: cache = {i: process_frame(fr[i], x0)[0]}
        p.stdin.write(cache[i].tobytes())
        if k % 30 == 0: print(f"{k}/{n_out} {time.time() - t0:.0f}s", flush=True)
    p.stdin.close(); p.wait(); print("ok", outp)
