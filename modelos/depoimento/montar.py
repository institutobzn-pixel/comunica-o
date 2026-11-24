"""Monta o vídeo: python3 montar.py video.mov camadas/ saida.mp4"""
import json, sys, subprocess
vid, cam, outp = sys.argv[1:4]
plan = json.load(open(f"{cam}/plan.json"))
dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",vid]))
FIM = 2.5; total = dur + FIM
args = ["ffmpeg","-v","error","-y","-i",vid,"-loop","1","-t",str(total),"-i",f"{cam}/base.png"]
for f,_,_ in plan: args += ["-loop","1","-t",str(total),"-i",f"{cam}/{f}"]
args += ["-loop","1","-t",str(FIM),"-i",f"{cam}/fim.png"]
fi = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,"
      f"eq=contrast=1.06:saturation=1.05,tpad=stop_mode=clone:stop_duration={FIM}[v0];"
      f"[v0][1:v]overlay=0:0:enable='lt(t,{dur})'[c0];")
cur = "c0"
for i,(f,s,e) in enumerate(plan):
    fi += f"[{cur}][{i+2}:v]overlay=0:0:enable='between(t,{s},{e-0.001})'[c{i+1}];"; cur = f"c{i+1}"
fimi = len(plan)+2
fi += (f"[{fimi}:v]format=rgba,fade=in:st=0:d=0.5:alpha=1,setpts=PTS+{dur-0.3}/TB[f];"
       f"[{cur}][f]overlay=0:0:eof_action=pass,fade=in:d=0.3,fade=out:st={total-0.4}:d=0.4,format=yuv420p[vout];"
       f"[0:a]apad=pad_dur={FIM},afade=in:d=0.2,afade=out:st={dur-0.4}:d=0.6[aout]")
args += ["-filter_complex",fi,"-map","[vout]","-map","[aout]","-t",str(total),
         "-c:v","libx264","-crf","20","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",outp]
subprocess.run(args, check=True); print("ok:", outp, round(total,1), "s")
