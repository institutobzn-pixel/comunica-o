#!/usr/bin/env bash
# Uso: montar.sh <pasta_camadas> <saida.mp4> <video1>:<inicio> <video2>:<inicio> ...
set -euo pipefail
CAM=$1; OUT=$2; shift 2
DUR=4; XF=0.6
ins=(); f=""; i=0
for arg in "$@"; do
  v=${arg%:*}; s=${arg##*:}
  ins+=(-ss "$s" -t "$DUR" -i "$v")
  # zoom lento (1.00 -> 1.06), cor um pouco mais contrastada e fria
  f+="[$i:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
  f+="scale=w='trunc(1080*(1+0.06*t/$DUR)/2)*2':h=-2:eval=frame,crop=1080:1920,setsar=1,"
  f+="eq=contrast=1.08:saturation=1.05:brightness=-0.02,colorbalance=bs=0.04:bm=0.03,format=yuv420p[v$i];"
  f+="[$i:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.6[a$i];"
  i=$((i+1))
done
n=$i
prev=v0; preva=a0; off=0
for ((k=1;k<n;k++)); do
  off=$(python3 -c "print($off+$DUR-$XF)")
  f+="[$prev][v$k]xfade=transition=fade:duration=$XF:offset=$off[x$k];"
  f+="[$preva][a$k]acrossfade=d=$XF[y$k];"
  prev=x$k; preva=y$k
done
total=$(python3 -c "print($n*$DUR-($n-1)*$XF)")
ins+=(-loop 1 -i "$CAM/base.png" -loop 1 -i "$CAM/texto.png")
B=$n; T=$((n+1))
f+="[$B:v]format=rgba[b];[$T:v]format=rgba,fade=in:st=0.4:d=0.8:alpha=1[t];"
f+="[$prev][b]overlay=0:0:shortest=1[o1];"
f+="[o1][t]overlay=x=0:y='max(0,80-80*(t-0.4)/0.8)':shortest=1,"
f+="fade=in:st=0:d=0.4,fade=out:st=$(python3 -c "print($total-0.5)"):d=0.5,format=yuv420p[vout];"
f+="[$preva]afade=in:d=0.4,afade=out:st=$(python3 -c "print($total-0.8)"):d=0.8[aout]"
ffmpeg -v error -y "${ins[@]}" -filter_complex "$f" -map "[vout]" -map "[aout]" -t "$total" \
  -c:v libx264 -preset medium -crf 20 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$OUT"
echo "ok: $OUT (${total}s)"
