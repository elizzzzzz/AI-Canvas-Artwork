"""Build a chaptered story-continuity graybox preview from existing evidence."""
from pathlib import Path
import json, subprocess
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'production/final-cut-v1'; CARDS=OUT/'cards'; SEG=OUT/'segments'; OUT.mkdir(parents=True,exist_ok=True); CARDS.mkdir(exist_ok=True);SEG.mkdir(exist_ok=True)
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf';NAVY=(15,24,47);GREEN=(124,216,75);WHITE=(245,247,242);MUTED=(167,174,190);CARD=(31,43,70)
def card(path,title,subtitle,lines):
 im=Image.new('RGB',(540,960),NAVY);d=ImageDraw.Draw(im);f=lambda n:ImageFont.truetype(FONT,n);d.rectangle((0,0,540,8),fill=GREEN);d.text((38,58),title,font=f(32),fill=WHITE);d.text((40,130),subtitle,font=f(18),fill=GREEN)
 y=245
 for line in lines:d.rounded_rectangle((38,y,502,y+95),14,fill=CARD,outline=GREEN,width=2);d.text((60,y+25),line,font=f(22),fill=WHITE);y+=130
 d.text((40,895),'GRAYBOX REVIEW  /  NOT FINAL MEDIA',font=f(14),fill=MUTED);im.save(path)
def run(cmd):subprocess.run(cmd,check=True)
def main():
 m=json.loads((ROOT/'production/motion-evidence-v1/manifest-v1.json').read_text());by={x['clip_key']:x for x in m['clips']}
 episodes=[('EP01','第一集《梅岭旧令》','发现旧案异常 → 追回证据',['主任务：查清矛盾军报','动作：梅岭火线 · 雪夜追车','钩子：燕字残角']),('EP02','第二集《麒麟锦囊》','执行锦囊任务 → 统一支线',['主任务：把锦囊送达','动作：信使争执 · 雨廊追截','钩子：两府同时得信']),('EP03','第三集《入京》','救下证人 → 带证据入京',['主任务：保护状纸入城','动作：雨路救援 · 城门冲入','钩子：金陵棋局开启'])]
 order={'EP01':['EP01-S02-01','EP01-S07-01','EP01-S06-01'],'EP02':['EP02-S05-01','EP02-S07-01','EP02-S08-01'],'EP03':['EP03-S02-01','EP03-S05-01','EP03-S10-01']}; allsegments=[]
 for ep,title,sub,lines in episodes:
  c=CARDS/f'{ep}-title.png';card(c,title,sub,lines);seg=SEG/f'{ep}-title.mp4';run(['/opt/homebrew/bin/ffmpeg','-y','-loop','1','-i',str(c),'-t','2','-r','24','-c:v','libx264','-pix_fmt','yuv420p',str(seg)]);allsegments.append(seg)
  for key in order[ep]:
   if key not in by:continue
   entry=json.loads((ROOT/by[key]['manifest']['path']).read_text());frames=ROOT/Path(entry['samples'][0]['rgb']['path']).parent;out=SEG/f'{key}.mp4';run(['/opt/homebrew/bin/ffmpeg','-y','-framerate','24','-i',str(frames/'%04d.png'),'-frames:v','72','-vf','scale=540:960:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out)]);allsegments.append(out)
 end=CARDS/'end.png';card(end,'七牛云','一站式 AI Infra', ['为你的主任务保驾护航。']);endseg=SEG/'end.mp4';run(['/opt/homebrew/bin/ffmpeg','-y','-loop','1','-i',str(end),'-t','2','-r','24','-c:v','libx264','-pix_fmt','yuv420p',str(endseg)]);allsegments.append(endseg)
 concat=OUT/'concat.txt';concat.write_text('\n'.join(f"file '{p}'" for p in allsegments)+'\n');final=OUT/'qiniu-langya-continuity-preview-v1.mp4';run(['/opt/homebrew/bin/ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)]);print(final)
if __name__=='__main__':main()
