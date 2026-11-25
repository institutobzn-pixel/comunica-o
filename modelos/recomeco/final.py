"""Composição final do Reels RECOMEÇO (vídeo + títulos + voz + trilha).
Uso: python3 final.py <pasta_trabalho> saida.mp4"""
import json, subprocess, sys, os
W = sys.argv[1]; OUT = os.path.abspath(sys.argv[2]); os.chdir(W)
tl = json.load(open("timeline.json")); faixas = json.load(open("tit/faixas.json"))
END = 154.25
D = lambda f: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))

ins = []; fg = []
def inp(f, extra=()):
    ins.extend([*extra, "-i", f]); return len(ins_files) if False else None
files = []
def add(f): files.append(f); return len(files) - 1

def chain(clips, xf, label):
    """Encadeia clipes com dissolve (xfade)."""
    idx = [add(c) for c in clips]; cur = f"[{idx[0]}:v]"; off = 0.0
    for k in range(1, len(idx)):
        off += D(clips[k-1]) - xf if k == 1 else D(clips[k-1]) - xf
        if k == 1: acc = D(clips[0]) - xf
        else: acc += D(clips[k-1]) - xf
        nxt = f"[{label}{k}]" if k < len(idx) - 1 else f"[{label}]"
        fg.append(f"{cur}[{idx[k]}:v]xfade=transition=fade:duration={xf}:offset={acc:.3f}{nxt}")
        cur = nxt
    return cur

op = chain(["broll/o1.mp4", "broll/o2.mp4", "broll/o3.mp4", "broll/o4.mp4", "broll/o5.mp4"], 0.4, "op")
esp = chain(["broll/e1.mp4", "broll/e2.mp4", "broll/e3.mp4"], 0.6, "es")
fim = chain(["broll/c1.mp4", "broll/c2.mp4", "broll/c3.mp4"], 0.6, "fi")
segs = [add(c["arq"]) for c in tl["cortes"]]
fg.append("".join(f"[{i}:v]" for i in segs) + f"concat=n={len(segs)}:v=1:a=0,setpts=PTS+{tl['cortes'][0]['t']}/TB[sp]")
fg.append(f"color=c=black:s=1080x1920:r=30:d={END},format=yuv420p[bk]")
fg.append(f"{op}format=rgba,fade=out:st=13.65:d=0.55:alpha=1[opa]")
fg.append(f"{esp}setpts=PTS+84.0/TB,format=rgba,fade=in:st=84.0:d=0.4:alpha=1,fade=out:st=94.55:d=0.35:alpha=1[esa]")
fg.append(f"{fim}setpts=PTS+140.35/TB,format=rgba,fade=in:st=140.35:d=0.8:alpha=1[fia]")
fg.append("[bk][sp]overlay=eof_action=pass[v1]")
fg.append("[v1][opa]overlay=eof_action=pass[v2]")
fg.append("[v2][esa]overlay=eof_action=pass[v3]")
fg.append("[v3][fia]overlay=eof_action=pass[v4]")
cur = "[v4]"
for k, (a, z) in enumerate(faixas):
    i = add(f"tit/t{k}.mov")
    fg.append(f"[{i}:v]setpts=PTS+{a}/TB[tt{k}]")
    fg.append(f"{cur}[tt{k}]overlay=eof_action=pass[w{k}]"); cur = f"[w{k}]"
fg.append(f"{cur}fade=in:st=0:d=0.5,trim=0:{END},format=yuv420p[vout]")
# áudio
iv = add("voz_total.wav"); im = add("trilha.wav")
fg.append(f"[{iv}:a]atrim=0:{END},highpass=f=80,lowpass=f=12000,acompressor=threshold=-22dB:ratio=3:attack=8:release=180:makeup=2,"
          f"equalizer=f=3000:t=q:w=1.2:g=2,asplit=2[voz][key]")
fg.append(f"[{im}:a]volume=1.6[mus]")
fg.append("[mus][key]sidechaincompress=threshold=0.015:ratio=9:attack=25:release=450:knee=4[musd]")
fg.append(f"[voz][musd]amix=inputs=2:normalize=0,alimiter=limit=0.89,atrim=0:{END}[aout]")

args = ["ffmpeg", "-v", "error", "-y"]
for f in files: args += ["-i", f]
args += ["-filter_complex", ";".join(fg), "-map", "[vout]", "-map", "[aout]", "-t", str(END),
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "4.6M", "-bufsize", "9.2M", "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
         "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", OUT + ".tmp.mp4"]
subprocess.run(args, check=True)
# normalização de loudness para o Instagram (-14 LUFS)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT + ".tmp.mp4", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", OUT], check=True)
os.remove(OUT + ".tmp.mp4"); print("ok:", OUT)
