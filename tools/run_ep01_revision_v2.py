#!/usr/bin/env python3
import os,json,time,requests,pathlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1];HOST=os.environ['AICANVAS_HOST'].rstrip('/');KEY=os.environ['AICANVAS_API_KEY'];BOARD='6851506d-6617-46f5-a06e-a2e9954f2ea0';H={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'};STATE=ROOT/'production/ep01-revision-v2.json';OUT=ROOT/'production/ep01-revision-v2';MEDIA=OUT/'media';LOG=OUT/'runner.log'
def req(m,p,**kw):
 r=requests.request(m,HOST+p,headers=H,timeout=120,**kw);r.raise_for_status();d=r.json();
 if d.get('code') not in (0,None):raise RuntimeError(d)
 return d
def graph():return req('GET',f'/api/canvas/boards/{BOARD}/graph')['data']
def save(s):STATE.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
def log(x):
 line=datetime.datetime.now().isoformat(timespec='seconds')+' '+x+'\n';print(line,end='',flush=True);LOG.parent.mkdir(parents=True,exist_ok=True);LOG.open('a').write(line)
def main():
 s=json.loads(STATE.read_text()); MEDIA.mkdir(parents=True,exist_ok=True)
 while True:
  g=graph(); active={r['root_node_id']:r for r in g.get('active_runs',[])}; by=g['nodes']
  for r in s['clips']:
   n=by.get(r['node_id']);
   if not n:continue
   cur=n.get('current') or {}
   if cur.get('status')=='completed' and r.get('status')!='completed':
    o=(cur.get('outputs') or [{}])[0]
    if o.get('url'):
     signed=req('POST','/api/media/sign-urls',json={'urls':[o['url']]})['data']['urls'][0];p=MEDIA/(r['key']+'.mp4')
     ok=False
     for attempt in range(5):
      try:
       with requests.get(signed,timeout=300,stream=True) as rr:
        rr.raise_for_status();tmp=p.with_suffix('.part');
        with tmp.open('wb') as fh:
         for chunk in rr.iter_content(chunk_size=1024*1024):
          if chunk: fh.write(chunk)
        tmp.replace(p);ok=True;break
      except Exception as e:
       log('download retry '+r['key']+' '+str(e));time.sleep(3)
     if not ok: continue
     r['local_file']=str(p.relative_to(ROOT));r['duration_actual']=o.get('duration');r['media_asset_id']=o.get('media_asset_id');r['status']='completed';log('completed '+r['key'])
   elif cur.get('status')=='failed':r['status']='failed';r['error_code']=cur.get('error_code');log('failed '+r['key']+' '+str(r.get('error_code')))
  for r in s['clips']:
   if len(active)>=3:break
   if r.get('status')!='queued' or r['node_id'] in active:continue
   d=req('POST',f'/api/canvas/boards/{BOARD}/runs',json={'scope':'node','root_node_id':r['node_id'],'idempotency_key':'ep01r2-'+r['key']});r['status']='submitted';r['run_id']=d['data']['run']['id'];active[r['node_id']]=d['data']['run'];log('submitted '+r['key'])
  s['completed_count']=sum(x.get('status')=='completed' for x in s['clips']);s['failed_count']=sum(x.get('status')=='failed' for x in s['clips']);save(s)
  if s['completed_count']+s['failed_count']==len(s['clips']):s['status']='completed_with_failures' if s['failed_count'] else 'videos_completed';s['finished_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat();save(s);return
  time.sleep(20)
if __name__=='__main__':main()
