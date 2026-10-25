#!/usr/bin/env python3
"""Run the queued formal clips, keep <=3 active, download completed media,
and assemble title-card-free episodes with in-frame calligraphic subtitles."""
from __future__ import annotations
import os,json,time,requests,datetime,pathlib,subprocess,shlex
ROOT=pathlib.Path(__file__).resolve().parents[1]
HOST=os.environ.get('AICANVAS_HOST','https://aicanvas.qnlinking.com').rstrip('/')
KEY=os.environ['AICANVAS_API_KEY']; BOARD='6851506d-6617-46f5-a06e-a2e9954f2ea0'
H={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'}; STATE=ROOT/'production/full-generation-v2.json'; OUT=ROOT/'production/full-generation-v2'; MEDIA=OUT/'media'; WORK=OUT/'work'; LOG=OUT/'runner.log'
FONT='/System/Library/Fonts/Supplemental/Songti.ttc'

def req(method,path,**kw):
 r=requests.request(method,HOST+path,headers=H,timeout=120,**kw); r.raise_for_status(); d=r.json()
 if d.get('code') not in (0,None): raise RuntimeError(d)
 return d

def load(): return json.loads(STATE.read_text())
def save(s): STATE.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
def graph(): return req('GET',f'/api/canvas/boards/{BOARD}/graph')['data']
def log(msg):
 line=datetime.datetime.now().isoformat(timespec='seconds')+' '+msg+'\n'; print(line,end='',flush=True); LOG.parent.mkdir(parents=True,exist_ok=True); LOG.open('a').write(line)
def download_clip(rec,node):
 out=(node.get('current') or {}).get('outputs') or []
 if not out or out[0].get('status')!='completed' or not out[0].get('url'): return False
 url=out[0]['url']; signed=req('POST','/api/media/sign-urls',json={'urls':[url]})['data']['urls'][0]
 MEDIA.mkdir(parents=True,exist_ok=True); p=MEDIA/(rec['key']+'.mp4'); r=requests.get(signed,timeout=300); r.raise_for_status(); p.write_bytes(r.content)
 rec['local_file']=str(p.relative_to(ROOT)); rec['duration_actual']=out[0].get('duration'); rec['media_asset_id']=out[0].get('media_asset_id'); return True
def caption_for(shot):
 # Keep short in-frame captions; story information remains in action and voice track.
 text=(shot.get('voiceover') or shot.get('dialogue') or '').strip()
 return text.replace('：', '：')[:46]
def assemble(s,wf):
 clips_by={c['key']:(shot,c) for shot in wf['shots'] for c in shot['clips']}
 WORK.mkdir(parents=True,exist_ok=True)
 complete={r['key']:r for r in s['clips'] if r.get('status')=='completed' and r.get('local_file')}
 for ep in (1,2,3):
  rows=[(shot,c,complete.get(c['key'])) for shot in wf['shots'] if shot['episode']==ep for c in shot['clips']]
  if not rows or any(r is None for _,_,r in rows): continue
  norm=[]
  for idx,(shot,c,r) in enumerate(rows):
   src=ROOT/r['local_file']; out=WORK/f'EP{ep}-{idx:02d}.mp4'; txt=WORK/f'EP{ep}-{idx:02d}.txt'; txt.write_text(caption_for(shot),encoding='utf-8')
   # Text is in-frame, never a full-screen card. Only apply when the shot has narration/dialogue.
   vf='scale=768:1344:force_original_aspect_ratio=decrease,pad=768:1344:(ow-iw)/2:(oh-ih)/2,setsar=1'
   if caption_for(shot): vf+=f",drawtext=fontfile='{FONT}':textfile='{txt}':fontcolor=white:fontsize=40:borderw=3:bordercolor=black@0.65:x=(w-text_w)/2:y=h-190:enable='between(t,0,3.2)'"
   subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-vf',vf,'-r','24','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(out)],check=True)
   norm.append(out)
  concat=WORK/f'EP{ep}-concat.txt'; concat.write_text('\n'.join("file '"+str(x.resolve())+"'" for x in norm)+'\n')
  final=OUT/f'episode-{ep}-final-v1.mp4'; subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c:v','libx264','-c:a','aac','-movflags','+faststart',str(final)],check=True)
  s.setdefault('deliverables',{})[f'EP{ep}']=str(final.relative_to(ROOT)); log(f'assembled EP{ep} {final}')
 def complete_final(): return len(complete)==len(s['clips'])
 if complete_final():
  allp=[]
  for ep in (1,2,3): allp.append(OUT/f'episode-{ep}-final-v1.mp4')
  existing=[p for p in allp if p.exists()]
  if len(existing)==3:
   c=OUT/'full-film-concat.txt'; c.write_text('\n'.join("file '"+str(x.resolve())+"'" for x in existing)+'\n')
   final=OUT/'langya-cloud-order-final-v1.mp4'; subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(c),'-c:v','libx264','-c:a','aac','-movflags','+faststart',str(final)],check=True); s['deliverables']['full']=str(final.relative_to(ROOT)); log(f'assembled full film {final}')
def main():
 wf=json.loads((ROOT/'production/workflow-v1.json').read_text()); s=load(); s.setdefault('started_at',datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()); s['status']='running_formal_full_video_queue'; save(s)
 while True:
  g=graph(); byid=g['nodes']; active={}
  # reconcile active and completed
  for r in s['clips']:
   n=byid.get(r['node_id']);
   if not n: continue
   cur=n.get('current') or {}
   if cur.get('status')=='completed' and r.get('status')!='completed':
    if download_clip(r,n): r['status']='completed'; log('completed '+r['key'])
   elif cur.get('status')=='failed': r['status']='failed'; r['error_code']=cur.get('error_code'); log('failed '+r['key']+' '+str(r.get('error_code')))
  # active run count from server
  for ar in g.get('active_runs',[]): active[ar['root_node_id']]=ar
  # start queued nodes up to 3
  for r in s['clips']:
   if len(active)>=3: break
   if r.get('status') not in ('queued','submitted'): continue
   if r['node_id'] in active: continue
   try:
    d=req('POST',f'/api/canvas/boards/{BOARD}/runs',json={'scope':'node','root_node_id':r['node_id'],'idempotency_key':'full-v2-'+r['key']})
    r['status']='submitted'; r['run_id']=d['data']['run']['id']; active[r['node_id']]=d['data']['run']; log('submitted '+r['key'])
   except Exception as e:
    r['status']='failed'; r['error_code']=str(e); log('submit failed '+r['key']+' '+str(e))
  s['completed_count']=sum(x.get('status')=='completed' for x in s['clips']); s['failed_count']=sum(x.get('status')=='failed' for x in s['clips']); save(s)
  if s['completed_count']+s['failed_count']==len(s['clips']):
   assemble(s,wf); s['status']='completed_with_failures' if s['failed_count'] else 'completed'; s['finished_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(); save(s); log('queue finished'); return
  time.sleep(20)
if __name__=='__main__': main()
