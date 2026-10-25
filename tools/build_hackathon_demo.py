"""Assemble a short vertical graybox demo from rendered motion evidence."""
from pathlib import Path
import json, subprocess, shutil
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'production/hackathon-demo'; TMP=OUT/'segments'; TMP.mkdir(parents=True,exist_ok=True)

def run(cmd): subprocess.run(cmd,check=True)
def main():
 m=json.loads((ROOT/'production/motion-evidence-v1/manifest-v1.json').read_text());segments=[]
 for idx,summary in enumerate(m['clips']):
  entry=json.loads((ROOT/summary['manifest']['path']).read_text());frames=ROOT/entry['samples'][0]['rgb']['path'].split('/')[0] if False else ROOT/Path(entry['samples'][0]['rgb']['path']).parent
  seg=TMP/f'{idx:02d}-{entry["clip_key"]}.mp4';
  if not seg.exists():
   run(['/opt/homebrew/bin/ffmpeg','-y','-framerate','24','-start_number','0','-i',str(frames/'%04d.png'),'-frames:v','72','-vf','scale=540:960:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(seg)])
  segments.append(seg)
 concat=OUT/'concat.txt';concat.write_text('\n'.join(f"file '{p}'" for p in segments)+'\n')
 final=OUT/'qiniu-langya-graybox-demo-v1.mp4';run(['/opt/homebrew/bin/ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)])
 print({'segments':len(segments),'output':str(final),'size_bytes':final.stat().st_size})
if __name__=='__main__':main()
