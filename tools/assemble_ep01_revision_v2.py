#!/usr/bin/env python3
import json, pathlib, subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1]; STATE=json.loads((ROOT/'production/ep01-revision-v2.json').read_text()); WF=json.loads((ROOT/'production/workflow-v1.json').read_text()); OUT=ROOT/'production/ep01-revision-v2'; MEDIA=OUT/'media'; WORK=OUT/'work'; WORK.mkdir(parents=True,exist_ok=True); FONT='/System/Library/Fonts/Supplemental/Songti.ttc'
shots={c['key']:(s,c) for s in WF['shots'] if s['episode']==1 for c in s['clips']}
clips=[x for s in WF['shots'] if s['episode']==1 for c in s['clips'] for x in STATE['clips'] if x['key']==c['key']]
if len(clips)!=21 or any(x.get('status')!='completed' for x in clips): raise SystemExit('EP01 clips incomplete')
norm=[]
for i,r in enumerate(clips):
 shot,c=shots[r['key']]; src=ROOT/r['local_file']; out=WORK/f'{i:02d}-{r["key"]}.mp4'; caption=(shot.get('voiceover') if shot.get('voiceover')!='无' else shot.get('dialogue')) or ''
 png=WORK/f'{i:02d}-caption.png'; im=Image.new('RGBA',(768,180),(0,0,0,0));d=ImageDraw.Draw(im)
 if caption:
  try:font=ImageFont.truetype(FONT,40)
  except:font=ImageFont.load_default()
  box=d.textbbox((0,0),caption,font=font);x=(768-(box[2]-box[0]))//2;d.text((x+3,62+3),caption,font=font,fill=(0,0,0,190));d.text((x,62),caption,font=font,fill=(255,247,218,255))
 im.save(png)
 filt='scale=768:1344:force_original_aspect_ratio=decrease,pad=768:1344:(ow-iw)/2:(oh-ih)/2,setsar=1'
 if caption:
  fc=f'[0:v]{filt}[base];[base][1:v]overlay=(W-w)/2:H-h-80'
  cmd=['ffmpeg','-y','-v','error','-i',str(src),'-i',str(png),'-filter_complex',fc,'-r','24','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(out)]
 else: cmd=['ffmpeg','-y','-v','error','-i',str(src),'-vf',filt,'-r','24','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(out)]
 subprocess.run(cmd,check=True);norm.append(out)
concat=WORK/'EP01-concat.txt';concat.write_text('\n'.join("file '"+str(x.resolve())+"'" for x in norm)+'\n')
video=WORK/'EP01-picture-lock-v2.mp4';subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c:v','libx264','-c:a','aac','-movflags','+faststart',str(video)],check=True)
dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(video)]))
final=OUT/'EP01-final-review-v2.mp4';voice=OUT/'audio/ep01-voiceover.m4a';music=OUT/'audio/ep01-background-music.m4a'
fc='[1:a]volume=1.0,apad[vo];[2:a]volume=0.16[bg];[vo][bg]amix=inputs=2:duration=longest:dropout_transition=2,atrim=duration='+str(dur)+'[a]'
subprocess.run(['ffmpeg','-y','-v','error','-i',str(video),'-i',str(voice),'-i',str(music),'-filter_complex',fc,'-map','0:v:0','-map','[a]','-t',str(dur),'-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(final)],check=True)
print(final,dur)
