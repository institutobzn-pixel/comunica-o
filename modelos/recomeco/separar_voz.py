"""Separa a voz da música de fundo com o modelo UVR-MDX-NET-Voc_FT (ONNX).
Uso: python3 separar_voz.py modelo.onnx entrada.wav(44.1k estéreo) saida_voz.wav"""
import sys, wave, numpy as np, onnxruntime as ort

N_FFT, HOP, DIM_F, DIM_T, COMP = 7680, 1024, 3072, 256, 1.021
N_BINS = N_FFT // 2 + 1
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM
win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N_FFT) / N_FFT)  # hann periódica

def stft(x):  # x [C, CHUNK] -> [C, N_BINS, DIM_T] complexo (center=True, reflect)
    xp = np.pad(x, ((0, 0), (N_FFT // 2, N_FFT // 2)), mode="reflect")
    idx = np.arange(DIM_T)[:, None] * HOP + np.arange(N_FFT)[None, :]
    frames = xp[:, idx] * win  # [C, T, N_FFT]
    return np.fft.rfft(frames, axis=-1).transpose(0, 2, 1)

def istft(S):  # [C, N_BINS, DIM_T] -> [C, CHUNK]
    frames = np.fft.irfft(S.transpose(0, 2, 1), n=N_FFT, axis=-1) * win
    L = N_FFT + HOP * (DIM_T - 1)
    out = np.zeros((S.shape[0], L)); wsum = np.zeros(L)
    for t in range(DIM_T):
        out[:, t*HOP:t*HOP+N_FFT] += frames[:, t]; wsum[t*HOP:t*HOP+N_FFT] += win**2
    out /= np.maximum(wsum, 1e-8)
    return out[:, N_FFT//2:N_FFT//2 + CHUNK]

def to_in(S):  # [2, N_BINS, T] -> [1, 4, DIM_F, T]  (c0re, c0im, c1re, c1im)
    S = S[:, :DIM_F]
    return np.stack([S[0].real, S[0].imag, S[1].real, S[1].imag])[None].astype(np.float32)

def from_out(y):  # [1,4,DIM_F,T] -> [2, N_BINS, T]
    y = y[0]; S = np.zeros((2, N_BINS, DIM_T), complex)
    S[0, :DIM_F] = y[0] + 1j*y[1]; S[1, :DIM_F] = y[2] + 1j*y[3]
    return S

def main(model, inp, outp):
    w = wave.open(inp); sr = w.getframerate(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a.reshape(-1, ch).T
    if ch == 1: a = np.vstack([a, a])
    n = a.shape[1]; pad = GEN - n % GEN
    mix = np.concatenate([np.zeros((2, TRIM)), a, np.zeros((2, pad)), np.zeros((2, TRIM))], 1)
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    outs = []
    for i in range(0, n + pad, GEN):
        S = stft(mix[:, i:i+CHUNK]); x = to_in(S)
        y = 0.5 * sess.run(None, {"input": x})[0] - 0.5 * sess.run(None, {"input": -x})[0]  # "denoise"
        outs.append(istft(from_out(y))[:, TRIM:-TRIM])
    voc = np.concatenate(outs, 1)[:, :n] * COMP
    o = wave.open(outp, "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((np.clip(voc.T, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()

if __name__ == "__main__":
    main(*sys.argv[1:4])
