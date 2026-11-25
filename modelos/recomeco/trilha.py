"""Trilha instrumental original (sintetizada) para o Reels RECOMEÇO, sincronizada com a linha do tempo.
Uso: python3 trilha.py saida.wav"""
import sys, numpy as np, wave
SR = 44100; END = 154.25; N = int((END + 4) * SR)
rng = np.random.default_rng(7)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
A4 = 440.0
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
def hz(n):  # "F#4"
    nome, oit = n[:-1], int(n[-1]); return A4 * 2 ** ((NOTE[nome] + 12 * (oit - 4) - 9) / 12)

def put(sig, t0, amp=1.0, pan=0.0):
    s0 = int(t0 * SR); n = min(len(sig), N - s0)
    if n <= 0: return
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[s0:s0+n] += sig[:n] * amp * gl * 1.41; R[s0:s0+n] += sig[:n] * amp * gr * 1.41

def env_ar(n, att, rel):
    e = np.ones(n, np.float32); a = int(att * SR); r = int(rel * SR)
    if a: e[:a] = np.linspace(0, 1, a) ** 1.5
    if r: e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e

def pad(notes, t0, t1, amp=0.05, bright=1.7, att=1.4, rel=1.8):
    d = t1 - t0 + rel; n = int(d * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    for nt in notes:
        f = hz(nt)
        for det in (-0.004, 0.0, 0.0045):
            ph = rng.uniform(0, 2*np.pi)
            for h in range(1, 7):
                if f * h > 6000: break
                out += np.sin(2*np.pi*f*(1+det)*h*t + ph*h) / h ** bright
    out *= env_ar(n, att, rel) / (len(notes) * 3)
    lfo = 1 + 0.08 * np.sin(2*np.pi*0.13*t + rng.uniform(0, 6))
    put(out * lfo, t0, amp, rng.uniform(-0.3, 0.3))

def piano(nt, t0, amp=0.12, dur=4.5, pan=0.0):
    f = hz(nt); n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32); B = 0.0004
    for h in range(1, 11):
        fh = f * h * np.sqrt(1 + B * h * h)
        if fh > 9000: break
        out += np.sin(2*np.pi*fh*t) * (1 / h ** 1.1) * np.exp(-t * (0.9 + 0.55 * h) * (f / 440) ** 0.3)
    att = int(0.004 * SR); out[:att] *= np.linspace(0, 1, att)
    out *= env_ar(n, 0, 0.3)
    put(out / 2.2, t0, amp, pan)

def strings(nt, t0, t1, amp=0.03, att=0.6, rel=0.9, pan=0.0):
    f = hz(nt); d = t1 - t0 + rel; n = int(d * SR); t = np.arange(n) / SR
    vib = 1 + 0.0028 * np.sin(2*np.pi*5.3*t) * np.clip(t / 0.8, 0, 1)
    phase = 2*np.pi*f*np.cumsum(vib) / SR; out = np.zeros(n, np.float32)
    for h in range(1, 14):
        if f * h > 8000: break
        out += np.sin(h * phase) / h ** 1.25
    put(out * env_ar(n, att, rel) / 3, t0, amp, pan)

def boom(t0, amp=0.5):
    n = int(3.5 * SR); t = np.arange(n) / SR
    f = 30 + 32 * np.exp(-t * 3.5); ph = 2*np.pi*np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 1.3)
    nz = rng.standard_normal(n) * np.exp(-t * 6) * 0.25
    put((s + np.convolve(nz, np.ones(40) / 40, "same")).astype(np.float32), t0, amp)

def swell(t0, t1, amp=0.05):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n).astype(np.float32)
    nz = nz - np.convolve(nz, np.ones(9) / 9, "same")   # tira graves
    e = (t / (t1 - t0)) ** 2.5
    put(nz * e, t0, amp, 0)

# ---------------- harmonia ----------------
CH = {  # acordes (vozes para pad) e baixo
    "D":  (["D3", "A3", "F#4", "E4"], "D2"), "Bm": (["B2", "F#3", "D4", "A4"], "B1"),
    "G":  (["G2", "D3", "B3", "F#4"], "G1"), "A":  (["A2", "E3", "C#4", "E4"], "A1"),
    "Asus": (["A2", "E3", "D4", "E4"], "A1"), "Em": (["E3", "B3", "G4", "D4"], "E2"),
    "F#m": (["F#2", "C#3", "A3", "E4"], "F#1"),
}
ARP = {"D": ["D4", "A4", "F#5", "A4"], "Bm": ["B3", "F#4", "D5", "F#4"], "G": ["G3", "D4", "B4", "D4"],
       "A": ["A3", "E4", "C#5", "E4"], "Asus": ["A3", "E4", "D5", "E4"], "Em": ["E4", "B4", "G5", "B4"], "F#m": ["F#3", "C#4", "A4", "C#4"]}

# S1 — abertura misteriosa (0 – 5.5)
pad(["D3", "A3", "E4"], 0.0, 5.5, amp=0.06, att=3.5, rel=1.5)
pad(["D2"], 0.6, 5.5, amp=0.05, bright=3, att=3, rel=1.5)
for t, nt in [(0.35, "A5"), (1.6, "F#5"), (3.3, "E5"), (4.85, "D5")]:
    piano(nt, t, 0.10, pan=0.25); piano(nt[:-1] + str(int(nt[-1]) - 1), t + 0.02, 0.05, pan=-0.2)
swell(3.3, 5.5, 0.035)

# S2 — RECOMEÇO cresce (5.5 – 13.65)
prog = ["D", "Bm", "G", "Asus", "D"]; dur = 1.666
boom(5.48, 0.28)
for k, c in enumerate(prog):
    t0 = 5.5 + k * dur; t1 = t0 + dur if k < 4 else 13.9
    lvl = 0.06 + 0.03 * k / 4
    pad(CH[c][0], t0, t1, amp=lvl, att=0.5, rel=1.2)
    strings(CH[c][1].replace("1", "2").replace("2", "2"), t0, t1, amp=0.05, att=0.3, rel=0.8)
    for j in range(8):  # arpejo em colcheias
        piano(ARP[c][j % 4], t0 + j * dur / 8, 0.05 + 0.02 * k / 4, dur=2.5, pan=0.3 * np.sin(j))
    for j in range(4):  # ostinato de cordas
        strings(CH[c][0][1].replace("3", "4"), t0 + j * dur / 4, t0 + j * dur / 4 + 0.22, amp=0.022, att=0.03, rel=0.2, pan=-0.3)
strings("A5", 8.83, 13.6, amp=0.018, att=2.0, rel=1.5, pan=0.35)

# S3/S5 — fundo calmo durante a fala
def cama(t_ini, t_fim, prog, bar=3.333, lvl=0.045):
    t = t_ini; k = 0
    while t < t_fim - 0.5:
        c = prog[k % len(prog)]; t1 = min(t + bar, t_fim)
        pad(CH[c][0], t, t1, amp=lvl, att=1.0, rel=1.6)
        pad([CH[c][1].replace("1", "2")], t, t1, amp=lvl * 0.8, bright=3.0, att=1.0, rel=1.6)
        for j in range(4):
            if t + j * bar / 4 < t1: piano(ARP[c][j], t + j * bar / 4, 0.035, dur=3.0, pan=0.3 * np.cos(j + k))
        t = t1; k += 1
cama(13.65, 84.0, ["D", "Bm", "G", "A"])
for ts in (28.25, 46.2, 63.85):  # sinos discretos nas séries
    piano("A5", ts, 0.06, pan=0.3); piano("D6", ts + 0.05, 0.04, pan=-0.3)

# S4 — telas azuis: esperança (84 – 95)
prog = [("G", 84.0), ("A", 86.8), ("Bm", 88.6), ("F#m", 90.1), ("G", 91.4), ("Asus", 92.6), ("D", 93.6)]
for k, (c, t0) in enumerate(prog):
    t1 = prog[k+1][1] if k + 1 < len(prog) else 98.0
    lvl = 0.05 + 0.05 * k / 6
    pad(CH[c][0], t0, t1, amp=lvl, bright=1.5, att=0.6, rel=1.8)
    strings(CH[c][1].replace("1", "2"), t0, t1, amp=0.045 + 0.02 * k / 6, att=0.4)
    for j in range(6):
        if t0 + j * (t1 - t0) / 6 < t1: piano(ARP[c][j % 4], t0 + j * (t1 - t0) / 6, 0.045 + 0.03 * k / 6, dur=3.0, pan=0.35 * np.sin(j))
strings("D5", 88.6, 97.5, amp=0.022, att=3.0, rel=2.0, pan=0.3); strings("F#5", 90.1, 97.5, amp=0.02, att=2.5, rel=2.0, pan=-0.3)
strings("A5", 92.6, 97.5, amp=0.02, att=1.2, rel=2.0, pan=0.1)
swell(91.6, 93.6, 0.03); boom(93.58, 0.18)
piano("D6", 93.6, 0.09); piano("A5", 93.62, 0.07); piano("F#5", 93.64, 0.06)
cama(95.0, 140.35, ["D", "G", "Bm", "A"], lvl=0.045)

# S6 — encerramento grandioso (140.35 – 154.25)
boom(140.35, 0.4); swell(138.6, 140.35, 0.035)
prog = ["D", "A", "Bm", "G", "D", "Em", "Asus", "D"]; bar = 1.74
mel = ["F#5", "E5", "D5", "D5", "F#5", "G5", "E5", "D5"]
for k, c in enumerate(prog):
    t0 = 140.35 + k * bar; t1 = t0 + bar if k < 7 else 154.0
    lvl = 0.07 + 0.04 * min(k, 6) / 6
    pad(CH[c][0], t0, t1, amp=lvl, bright=1.4, att=0.4, rel=2.2)
    pad([CH[c][1].replace("1", "2")], t0, t1, amp=lvl * 0.9, bright=2.6, att=0.4, rel=2.2)
    strings(CH[c][1].replace("1", "2"), t0, t1, amp=0.06, att=0.3, rel=1.5)
    strings(CH[c][0][2], t0, t1, amp=0.03, att=0.4, rel=1.5, pan=0.3)
    piano(mel[k], t0, 0.11, dur=4.0, pan=0.1); piano(mel[k][:-1] + str(int(mel[k][-1]) - 1), t0 + 0.01, 0.06, dur=4.0, pan=-0.1)
    for j in range(4):
        piano(ARP[c][j], t0 + j * bar / 4, 0.045, dur=2.5, pan=0.35 * np.sin(j + k))
strings("D6", 151.25, 154.0, amp=0.02, att=1.0, rel=2.0); piano("D6", 151.25, 0.08); piano("A5", 151.27, 0.06); piano("D5", 151.3, 0.06)
boom(151.25, 0.2)

# ---------------- reverb (convolução) + acabamento ----------------
def reverb(x, seed):
    r = np.random.default_rng(seed); n = int(3.2 * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n).astype(np.float32) * np.exp(-t / 0.75); ir[:int(0.02*SR)] *= 0.2
    ir = np.convolve(ir, np.ones(6) / 6, "same"); ir /= np.sqrt((ir ** 2).sum())
    m = 1 << int(np.ceil(np.log2(len(x) + n)))
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)].astype(np.float32)
wl, wr = reverb(L, 1), reverb(R, 2)
L2 = L * 0.75 + wl * 0.5; R2 = R * 0.75 + wr * 0.5
# corta graves muito baixos e brilho excessivo (FFT)
def eq(x):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / np.sqrt(1 + (28 / np.maximum(f, 1)) ** 4) / np.sqrt(1 + (f / 11000) ** 4)
    return np.fft.irfft(X * g, len(x)).astype(np.float32)
L2, R2 = eq(L2), eq(R2)
# fade final
fe = int(END * SR); fs = int((END - 1.6) * SR)
for ch in (L2, R2):
    ch[fs:fe] *= np.linspace(1, 0, fe - fs) ** 1.5; ch[fe:] = 0
st = np.stack([L2, R2], 1)[:fe]
st /= np.abs(st).max() / 0.89
o = wave.open(sys.argv[1], "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((st * 32767).astype(np.int16).tobytes()); o.close()
print("trilha ok", round(len(st) / SR, 2), "s")
