"""Remove as marcas d'água dos vídeos da artista: assinatura (fixa) e ícone + @ do Instagram (muda de lugar).
Uso: python3 marcas.py entrada.mp4 saida.mp4 [--debug]"""
import sys, cv2, numpy as np, subprocess

SIG = (158, 740, 322, 800)                       # x0,y0,x1,y1 assinatura
# O ícone + @ do Instagram alterna a cada 9 s: [0,9) direita, [9,18) esquerda, ... (com animação de entrada)
POS = {  # quadrado do ícone e faixa do @ (com folga para a animação de entrada)
    "dir": dict(icon=(404, 182, 480, 238), text=(318, 226, 480, 258)),
    "esq": dict(icon=(16, 482, 92, 538), text=(18, 528, 172, 560)),
}
PERIODO, FOLGA = 9.0, 0.12

def lados(t):
    k = int(t // PERIODO); fase = t - k * PERIODO
    atual = "dir" if k % 2 == 0 else "esq"; outro = "esq" if atual == "dir" else "dir"
    return [atual, outro] if (fase < FOLGA or fase > PERIODO - FOLGA) and t > FOLGA else [atual]

K = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

def grad(g):
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    return cv2.magnitude(gx, gy)

def _icon_score(gray, box):
    """Mede quanto a região parece um quadrado arredondado com círculo (o ícone)."""
    x0, y0, x1, y1 = box; r = gray[y0:y1, x0:x1].astype(np.float32)
    g = grad(r); h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]; cx, cy = w / 2, h / 2
    ring_sq = (np.maximum(abs(xx - cx), abs(yy - cy)) > w * 0.30) & (np.maximum(abs(xx - cx), abs(yy - cy)) < w * 0.45)
    d = np.hypot(xx - cx, yy - cy); ring_c = (d > w * 0.12) & (d < w * 0.24)
    inside = (np.maximum(abs(xx - cx), abs(yy - cy)) < w * 0.28) & ~ring_c
    return (g[ring_sq].mean() + g[ring_c].mean()) / 2 - g[inside].mean() * 0.8

def white_strokes(gray, box, thr=22):
    x0, y0, x1, y1 = box; r = gray[y0:y1, x0:x1]
    th = cv2.morphologyEx(r, cv2.MORPH_TOPHAT, K)
    m = (th > thr).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=1)

def molde_assinatura(videos, amostras=60):
    """A assinatura é fixa: a mediana do top-hat em muitos quadros guarda só ela."""
    tops = []
    for v in videos:
        cap = cv2.VideoCapture(v); total = int(cap.get(7))
        for i in np.linspace(0, total * 0.85, amostras // len(videos) + 1).astype(int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(i)); ok, f = cap.read()
            if not ok: continue
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); x0, y0, x1, y1 = SIG
            tops.append(cv2.morphologyEx(g[y0:y1, x0:x1], cv2.MORPH_TOPHAT, K))
    med = np.median(np.stack(tops), 0)
    m = (med > 12).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)

SIG_MASK = None

def process(inp, outp, debug=False):
    cap = cv2.VideoCapture(inp); fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(3)); h = int(cap.get(4))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                          "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", outp],
                         stdin=subprocess.PIPE)
    scores = []; n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        mask = np.zeros((h, w), np.uint8)
        x0, y0, x1, y1 = SIG; mask[y0:y1, x0:x1] |= SIG_MASK
        sc = {}
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        for k in lados(n / fps):
            for parte in ("icon", "text"):
                x0, y0, x1, y1 = POS[k][parte]
                m = white_strokes(gray, POS[k][parte], 16)
                hb = hsv[y0:y1, x0:x1]
                pele = ((hb[..., 0] >= 4) & (hb[..., 0] <= 24) & (hb[..., 1] > 45) & (hb[..., 2] < 232)).astype(np.uint8) * 255
                amarelo = ((hb[..., 0] >= 22) & (hb[..., 0] <= 42) & (hb[..., 1] > 70) & (hb[..., 2] > 120)).astype(np.uint8) * 255
                m &= ~cv2.dilate(pele | amarelo, np.ones((3, 3), np.uint8), iterations=1)   # nunca mexe em pele nem na legenda
                if parte == "icon":  # ícone colorido: só roxo/magenta (nunca tons de pele)
                    hh, ss, vv = hsv[y0:y1, x0:x1, 0], hsv[y0:y1, x0:x1, 1], hsv[y0:y1, x0:x1, 2]
                    vivo = ((ss > 90) & (vv > 90) & (hh > 128) & (hh < 172)).astype(np.uint8) * 255
                    m |= cv2.dilate(vivo, np.ones((3, 3), np.uint8), iterations=1)
                mask[y0:y1, x0:x1] |= m
        scores.append(sc)
        out = cv2.inpaint(f, mask, 4, cv2.INPAINT_TELEA) if mask.any() else f
        p.stdin.write(out.tobytes()); n += 1
    p.stdin.close(); p.wait()
    if debug:
        import json; json.dump(scores, open(outp + ".scores.json", "w"))

if __name__ == "__main__":
    # uso: marcas.py molde.png saida.mp4 entrada.mp4  |  marcas.py --molde molde.png v1.mp4 v2.mp4 ...
    if sys.argv[1] == "--molde":
        cv2.imwrite(sys.argv[2], molde_assinatura(sys.argv[3:]))
    else:
        SIG_MASK = cv2.imread(sys.argv[1], 0)
        process(sys.argv[3], sys.argv[2])
