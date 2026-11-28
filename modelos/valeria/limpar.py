"""Remove as legendas antigas gravadas no vídeo da Valéria usando pixels REAIS de quadros vizinhos (câmera parada),
sem borrão. Uso: python3 limpar.py <pasta_trabalho>  -> src_limpo.mkv (+ mascaras.npy)"""
import sys, os, subprocess, numpy as np, cv2
W = sys.argv[1]; os.chdir(W)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "src.mp4", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, 848, 480, 3).copy(); N = len(F)
Y0, Y1, X0, X1 = 520, 848, 0, 330                       # zona onde aparecem as legendas antigas
R = F[:, Y0:Y1, X0:X1].astype(np.int16)
mn, ptp = R.min(3), R.max(3) - R.min(3); lum = R.mean(3)
CENA = 28.0                                              # ela levanta ~28 s (câmera parada nas duas cenas)
cenas = [(0, int(CENA * 30)), (int(CENA * 30), N)]
branco = (mn > 228) & (ptp < 22)
plate = np.zeros(R.shape[1:], np.float32); M = np.zeros(R.shape[:3], bool)
for a, b in cenas:
    seg = R[a:b:2].astype(np.float32); seg[branco[a:b:2]] = np.nan
    pl = np.nanpercentile(seg, 20, axis=0); del seg
    plate_c = np.nan_to_num(pl, nan=128.0)
    d = lum[a:b] - plate_c.mean(2)[None]
    cinza = (ptp[a:b] < 18) & (d > 30) & (lum[a:b] > 110)  # texto branco semitransparente (palavras "apagadas")
    M[a:b] = branco[a:b] | cinza
    if a == 0: plate0 = plate_c.copy()
    else: plate1 = plate_c.copy()
k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)); k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
for i in range(N):   # só manchas com forma de letra: remove pontinhos soltos, fecha letras e alarga bordas (antialias/compressão)
    m = cv2.morphologyEx(M[i].astype(np.uint8), cv2.MORPH_OPEN, k3)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 12
    m = keep[lab].astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k7); M[i] = cv2.dilate(m, k7, iterations=1) > 0
# preenche cada pixel coberto com o mesmo pixel do quadro mais próximo em que ele está livre (dentro da mesma cena)
out = R.copy(); falta = M.copy()
for a, b in cenas:
    for dlt in range(1, 91):
        for s in (dlt, -dlt):
            lo, hi = max(a, a - s), min(b, b - s)
            if hi <= lo: continue
            src = slice(lo + s, hi + s); dst = slice(lo, hi)
            pode = falta[dst] & ~M[src]
            out[dst][pode] = R[src][pode]; falta[dst] &= ~pode
    pl = (plate0 if a == 0 else plate1).astype(np.int16)
    for i in range(a, b): out[i][falta[i]] = pl[falta[i]]
print("pixels sem vizinho livre (usou fundo médio):", int(falta.sum()))
print("pixels cobertos:", int(M.sum()))
np.save("mascaras.npy", np.packbits(M, axis=-1))
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "480x848", "-r", "30", "-i", "-",
                      "-c:v", "ffv1", "-pix_fmt", "bgr0", "src_limpo.mkv"], stdin=subprocess.PIPE)
for i in range(N):   # junta com borda suave, quadro a quadro
    m = cv2.GaussianBlur(M[i].astype(np.float32), (0, 0), 1.2)[..., None]; g = F[i]
    g[Y0:Y1, X0:X1] = (out[i] * m + R[i] * (1 - m)).clip(0, 255).astype(np.uint8); p.stdin.write(g.tobytes())
p.stdin.close(); p.wait(); print("ok src_limpo.mkv", N, "quadros")
