"""Trilha original (sintetizada) para o Reels da Valéria: 100 bpm, Sol maior, I–V–vi–IV, clima positivo e caloroso.
Uso: python3 trilha.py saida.wav"""
import sys, wave, numpy as np
SR = 44100; END = 56.71; N = int((END + 3) * SR); rng = np.random.default_rng(3)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
NT = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
hz = lambda n: 440 * 2 ** ((NT[n[:-1]] + 12 * (int(n[-1]) - 4) - 9) / 12)
def put(s, t0, amp=1, pan=0):
    a = int(t0 * SR); n = min(len(s), N - a)
    if n > 0:
        L[a:a+n] += s[:n] * amp * np.cos((pan + 1) * np.pi / 4) * 1.41; R[a:a+n] += s[:n] * amp * np.sin((pan + 1) * np.pi / 4) * 1.41
def env(n, a, r):
    e = np.ones(n, np.float32); a = int(a * SR); r = int(r * SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if r: e[-r:] *= np.linspace(1, 0, r)
    return e
def pad(ns, t0, t1, amp=.04, att=.8, rel=1.2):
    n = int((t1 - t0 + rel) * SR); t = np.arange(n) / SR; o = np.zeros(n, np.float32)
    for x in ns:
        f = hz(x)
        for d in (-.003, .003):
            for h in range(1, 6): o += np.sin(2 * np.pi * f * (1 + d) * h * t + rng.uniform(0, 6)) / h ** 1.8
    put(o * env(n, att, rel) / (len(ns) * 2), t0, amp, rng.uniform(-.2, .2))
def piano(x, t0, amp=.1, dur=2.5, pan=0):
    f = hz(x); n = int(dur * SR); t = np.arange(n) / SR; o = np.zeros(n, np.float32)
    for h in range(1, 9):
        if f * h > 9000: break
        o += np.sin(2 * np.pi * f * h * np.sqrt(1 + .0004 * h * h) * t) / h ** 1.1 * np.exp(-t * (1.2 + .6 * h))
    o[:int(.004 * SR)] *= np.linspace(0, 1, int(.004 * SR)); put(o * env(n, 0, .2) / 2, t0, amp, pan)
def pluck(x, t0, amp=.05, pan=0):
    f = hz(x); n = int(.6 * SR); t = np.arange(n) / SR
    o = (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) + .25 * np.sin(6 * np.pi * f * t)) * np.exp(-t * 7)
    put(o.astype(np.float32), t0, amp, pan)
def kick(t0, amp=.35):
    n = int(.35 * SR); t = np.arange(n) / SR; f = 45 + 80 * np.exp(-t * 30)
    put((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32), t0, amp)
def clap(t0, amp=.07):
    n = int(.18 * SR); t = np.arange(n) / SR; z = rng.standard_normal(n).astype(np.float32)
    z = z - np.convolve(z, np.ones(6) / 6, "same"); put(z * np.exp(-t * 28), t0, amp)
def hat(t0, amp=.025):
    n = int(.05 * SR); z = rng.standard_normal(n).astype(np.float32); z = np.diff(np.concatenate([[0], z])); put(z * np.exp(-np.arange(n) / SR * 90), t0, amp, .3)
def boom(t0, amp=.4):
    n = int(2.5 * SR); t = np.arange(n) / SR; f = 32 + 40 * np.exp(-t * 4)
    put((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)).astype(np.float32), t0, amp)
def whoosh(t0, t1, amp=.08):
    n = int((t1 - t0) * SR); z = rng.standard_normal(n).astype(np.float32); z = z - np.convolve(z, np.ones(12) / 12, "same")
    e = np.sin(np.linspace(0, np.pi, n)) ** 2; put(z * e, t0, amp)
def riser(t0, t1, amp=.05):
    n = int((t1 - t0) * SR); z = rng.standard_normal(n).astype(np.float32); z = z - np.convolve(z, np.ones(5) / 5, "same"); put(z * np.linspace(0, 1, n) ** 3, t0, amp)

B = 60 / 100; BAR = 4 * B
CH = {"G": (["G3", "B3", "D4"], "G2", ["G4", "B4", "D5", "B4"]), "D": (["F#3", "A3", "D4"], "D2", ["F#4", "A4", "D5", "A4"]),
      "Em": (["E3", "G3", "B3"], "E2", ["E4", "G4", "B4", "G4"]), "C": (["E3", "G3", "C4"], "C2", ["E4", "G4", "C5", "G4"])}
PROG = ["G", "D", "Em", "C"]
def secao(t0, t1, nivel, bateria=False, cordas=False, arp=True):
    t = t0; k = 0
    while t < t1 - 0.05:
        c = PROG[k % 4]; tf = min(t + BAR, t1); ns, bx, ar = CH[c]
        pad(ns, t, tf, .035 * nivel); pad([bx], t, tf, .03 * nivel)
        if cordas: pad([n[:-1] + str(int(n[-1]) + 1) for n in ns], t, tf, .02 * nivel, att=.4)
        for j in range(8):
            tj = t + j * B / 2
            if tj >= tf: break
            if arp: piano(ar[j % 4], tj, .045 * nivel, pan=.3 * np.sin(j))
            if bateria:
                hat(tj + B / 4, .02 * nivel)
                if j % 2 == 0: kick(tj, .28 * nivel)
                if j in (2, 6): clap(tj, .06 * nivel)
        pluck(ar[2], t, .04 * nivel, -.3); t = tf; k += 1

# gancho (0–6.1): piano suave, sem bateria
pad(["G3", "B3", "D4"], 0, 6.1, .03, att=1.5)
for i, x in enumerate(["D5", "B4", "G4", "B4", "D5", "E5", "D5", "B4"]): piano(x, 0.3 + i * B * 1.5, .07, pan=.2 * (-1) ** i)
riser(4.6, 6.1, .05); whoosh(5.7, 6.5, .1)
# vinheta (6.1–7.6)
boom(6.107, .35); [piano(x, 6.11, .09) for x in ("G4", "B4", "D5", "G5")]
# história (7.6–36.6): cama calorosa
secao(7.6, 36.63, 0.9)
# clímax (36.6–51.9): bateria leve + cordas
riser(35.1, 36.63, .04); boom(36.63, .2)
secao(36.63, 51.915, 1.15, bateria=True, cordas=True)
# final (51.9–56.7)
whoosh(51.4, 52.2, .09); boom(51.915, .35)
secao(51.915, 55.5, 1.25, bateria=True, cordas=True)
pad(["G3", "B3", "D4", "G4"], 55.5, 56.6, .05, att=.1, rel=1.5); [piano(x, 55.5, .1, dur=3) for x in ("G3", "D4", "G4", "B4", "D5")]

def reverb(x, s):
    r = np.random.default_rng(s); n = int(2.2 * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n).astype(np.float32) * np.exp(-t / .5); ir /= np.sqrt((ir ** 2).sum())
    m = 1 << int(np.ceil(np.log2(len(x) + n))); return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)].astype(np.float32)
L2 = L * .8 + reverb(L, 1) * .35; R2 = R * .8 + reverb(R, 2) * .35
e = int(END * SR); s = int((END - 1.2) * SR)
for ch in (L2, R2): ch[s:e] *= np.linspace(1, 0, e - s); ch[e:] = 0
st = np.stack([L2, R2], 1)[:e]; st /= np.abs(st).max() / .89
o = wave.open(sys.argv[1], "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((st * 32767).astype(np.int16).tobytes()); o.close()
print("trilha ok")
