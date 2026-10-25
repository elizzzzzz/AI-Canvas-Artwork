#!/usr/bin/env python3
"""Run the queued formal clips, keep <=3 active, download completed media,
and assemble title-card-free episodes with in-frame calligraphic subtitles."""
from __future__ import annotations
import os,json,time,requests,datetime,pathlib,subprocess,shlex,uuid
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1]
HOST=os.environ.get('AICANVAS_HOST','https://aicanvas.qnlinking.com').rstrip('/')
KEY=os.environ['AICANVAS_API_KEY']; BOARD='6851506d-6617-46f5-a06e-a2e9954f2ea0'
H={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'}; STATE=ROOT/'production/full-generation-v2.json'; OUT=ROOT/'production/full-generation-v2'; MEDIA=OUT/'media'; WORK=OUT/'work'; LOG=OUT/'runner.log'
FONT='/System/Library/Fonts/Supplemental/Songti.ttc'
GATE='b30832a0-61c3-428c-aaa2-bfc7381016cc'

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
def add_h3_fallback(rec):
 # Seedance content rejection fallback: create a fresh H3 node with the same shot prompt.
 g=graph(); old=g['nodes'].get(rec['node_id']);
 if not old: raise RuntimeError('missing failed node')
 nid=str(uuid.uuid4()); spec=dict(old.get('spec',{})); spec['model']='minimax/minimax-h3'; spec['resolution']='768P'; spec.pop('gen_mode',None)
 title=rec.get('title',rec['key'])+' MiniMax-H3 fallback';
 body={'expected_revision':g['revision'],'ops':[{'op':'add_node','id':nid,'kind':'video','title':title,'spec':spec,'inputs':{'condition':[{'mode':'each','node':GATE,'field':'pilot_ready','match':'any'}]},'pause_after':False}]}
 d=req('POST',f'/api/canvas/boards/{BOARD}/ops',json=body)['data'];
 rec['previous_node_id']=rec['node_id']; rec['node_id']=nid; rec['title']=title; rec['status']='queued'; rec.pop('run_id',None); rec['model']='minimax/minimax-h3'; rec['resolution']='768P'; rec['fallback_for']='doubao-seedance-2-5-260628'; rec['retry_reason']='seedance_content_rejected_use_h3';
 log('created H3 fallback '+rec['key']); return d['revision']

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
   caption=caption_for(shot)
   if caption:
    png=WORK/f'EP{ep}-{idx:02d}-caption.png'
    try: font=ImageFont.truetype(FONT,42)
    except Exception: font=ImageFont.load_default()
    im=Image.new('RGBA',(768,180),(0,0,0,0)); d=ImageDraw.Draw(im); box=d.textbbox((0,0),caption,font=font); tw=box[2]-box[0]; x=(768-tw)//2
    d.text((x+3,62+3),caption,font=font,fill=(0,0,0,190)); d.text((x,62),caption,font=font,fill=(255,247,218,255)); im.save(png)
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-i',str(png),'-filter_complex',f'[0:v]{vf}[base];[base][1:v]overlay=(W-w)/2:H-h-80','-r','24','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(out)],check=True)
   else:
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
  # reconcile node versions and explicit run statuses
  for r in s['clips']:
   n=byid.get(r['node_id']);
   if not n: continue
   cur=n.get('current') or {}
   if r.get('status')=='submitted' and r.get('run_id'):
    try:
     run=req('GET',f'/api/canvas/boards/{BOARD}/runs/{r["run_id"]}')['data']
     if run.get('status')=='failed':
      code=run.get('error_code') or (run.get('node_states',{}).get(r['node_id'],{}).get('error_code'))
      if code=='UpstreamError.ContentRejected' and not r.get('fallback_for'):
       try: add_h3_fallback(r)
       except Exception as e: r['status']='failed'; r['error_code']=str(e); log('fallback failed '+r['key']+' '+str(e))
      else:
       r['status']='failed'; r['error_code']=code; log('failed '+r['key']+' '+str(r.get('error_code')))
     elif run.get('status')=='cancelled':
      r['status']='queued'; r.pop('run_id',None); log('cancelled '+r['key'])
    except Exception as e: log('run status check skipped '+r['key']+' '+str(e))
   cur=n.get('current') or {}
   if cur.get('status')=='completed' and r.get('status')!='completed':
    try:
     if download_clip(r,n): r['status']='completed'; log('completed '+r['key'])
    except Exception as e: log('download retry '+r['key']+' '+str(e))
   elif cur.get('status')=='failed' and r.get('status') not in ('failed','completed'):
    r['status']='failed'; r['error_code']=cur.get('error_code'); log('failed '+r['key']+' '+str(r.get('error_code')))
  # active run count from server
  for ar in g.get('active_runs',[]): active[ar['root_node_id']]=ar
  # start queued nodes up to 3
  for r in s['clips']:
   if len(active)>=3: break
   if r.get('status')!='queued': continue
   if r.get('run_id') or r['node_id'] in active: continue
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
