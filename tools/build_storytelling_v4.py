#!/usr/bin/env python3
"""Clean picture assembly + scene-timed male narration, no burned captions.
Narration is synthetic zh-CN-YunyangNeural; approval of perceived age/emotion stays human.
"""
import asyncio,json,pathlib,subprocess,sys,wave,datetime,hashlib
import numpy as np
import edge_tts
R=pathlib.Path(__file__).resolve().parents[1]; O=R/'production/storytelling-v4'; A=O/'audio'; W=O/'work'; Q=O/'qc'
for p in (A,W,Q):p.mkdir(parents=True,exist_ok=True)
SK=pathlib.Path('/Users/elizhang/.agents/skills/ffmpeg-skill/scripts'); PY='/Library/Frameworks/Python.framework/Versions/3.11/bin/python3'
VOICE='zh-CN-YunyangNeural'; RATE='-4%'; PITCH='-5Hz'
WF=json.loads((R/'production/workflow-v1.json').read_text())
T=json.loads((R/'production/storytelling-v4/narration.json').read_text())
FORBIDDEN=('主线','支线','任务','版本','调度','开发者','基础设施','模型','运镜','第一人称','拍摄','制片')
assert len(T)==34
for key,text in T.items():
 if any(term in text for term in FORBIDDEN):raise ValueError(f'Production terminology in story: {key}')

TAG='七牛云，一站式AI Infra，为你的主任务保驾护航。'
def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def dur(p):return float(probe(p)['format']['duration'])
def video_seconds(p):
 x=probe(p); v=next(s for s in x['streams'] if s['codec_type']=='video'); return float(v.get('duration') or x['format']['duration'])
def tool(name,args,result,plan=True):
 cmd=[PY,str(SK/(name+'.py')),*map(str,args),('--json' if name=='check' else '--json-brief')]+(['--overwrite'] if name!='check' else [])
 if plan:
  x=subprocess.run(cmd+['--dry-run'],capture_output=True,text=True);(Q/(result+'-plan.json')).write_text(x.stdout); 
  if x.returncode:raise RuntimeError(x.stderr+x.stdout)
 x=subprocess.run(cmd,capture_output=True,text=True);(Q/(result+'.json')).write_text(x.stdout)
 if x.returncode:raise RuntimeError(x.stderr[-1500:]+x.stdout[-1500:])
def decode(p):
 x=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','s16le','-acodec','pcm_s16le','-ar','24000','-ac','1','-'])
 return np.frombuffer(x,dtype='<i2').astype(np.float64)/32768

def wav(p,x,sr=24000):
 with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(x,-.98,.98)*32767).astype('<i2').tobytes())
def sources():
 revised={c['key']:R/c['local_file'] for c in json.loads((R/'production/ep01-revision-v2.json').read_text())['clips']}
 return {c['key']:(revised[c['key']] if s['episode']==1 else R/'production/full-generation-v2/media'/ (c['key']+'.mp4')) for s in WF['shots'] for c in s['clips']}
async def generate():
 sem=asyncio.Semaphore(3)
 async def one(k,text):
  p=A/(k+'.mp3');j=A/(k+'-boundaries.json');(A/(k+'.txt')).write_text(text)
  fingerprint=hashlib.sha256(json.dumps({'text':text,'voice':VOICE,'rate':RATE,'pitch':PITCH},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
  cache=A/(k+'-request.sha256')
  if p.exists() and j.exists() and cache.exists() and cache.read_text()==fingerprint:return
  async with sem:
   for n in range(3):
    try:
     data=[]
     with p.with_suffix('.part').open('wb') as f:
      async for c in edge_tts.Communicate(text,VOICE,rate=RATE,pitch=PITCH,boundary='SentenceBoundary').stream():
       if c['type']=='audio':f.write(c['data'])
       elif c['type']=='SentenceBoundary':data.append(c)
     p.with_suffix('.part').replace(p);cache.write_text(fingerprint);j.write_text(json.dumps(data,ensure_ascii=False,indent=2));print('voiced',k,flush=True);return
    except Exception:
     if n==2:raise
     await asyncio.sleep(2)
 await asyncio.gather(*(one(k,t) for k,t in {**T,'unified-brand-tagline':TAG}.items()))
def srt_time(t):
 n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
def main():
 src=sources();timeline={};manifest={'voice':VOICE,'rate':RATE,'pitch':PITCH,'synthetic_voice':True,'burned_captions':False,'source_ep01':'ep01-revision-v2','ep02_ep03_visual_fixes':'pending_not_claimed','story_script':'production/storytelling-v4/narration.json','story_terminology_check':'passed; mandated brand tagline stored separately','voice_age_emotion':'mature male direction; subjective listening review still required','episodes':{}}
 for ep in (1,2,3):
  rows=[];at=0
  for s in WF['shots']:
   if s['episode']!=ep:continue
   fs=[src[c['key']] for c in s['clips']];sd=sum(round(video_seconds(p)*24)/24 for p in fs);rows.append((s,fs,at,sd));at+=sd
  timeline[ep]=(rows,at)
 asyncio.run(generate())
 # Original minimal pentatonic score, same theme and source file across all episodes.
 sr=24000;length=max(t[1] for t in timeline.values())+2;music=np.zeros(int(length*sr));rng=np.random.default_rng(42)
 notes=[146.832,164.814,195.998,220.,261.626,293.665,261.626,220.]
 for i,on in enumerate(np.arange(0,length,2.5)):
  f=notes[i%len(notes)];tt=np.arange(int(sr*4.5))/sr;sig=sum(np.sin(2*np.pi*f*h*tt+rng.uniform(-.1,.1))*np.exp(-tt*(1.2+.4*h))/(h*h) for h in range(1,6))*(1-np.exp(-tt*60))*.085
  a=int(on*sr);b=min(a+len(sig),len(music));music[a:b]+=sig[:b-a]
 tt=np.arange(len(music))/sr;music+=.018*np.sin(2*np.pi*73.416*tt)*(.7+.3*np.sin(2*np.pi*tt/11));music*=np.minimum(tt/3,1)*np.minimum((length-tt)/4,1)
 wav(A/'unified-original-music.wav',music)
 tagline=decode(A/'unified-brand-tagline.mp3');wav(A/'unified-brand-tagline.wav',tagline)
 for ep,(rows,total) in timeline.items():
  voice=np.zeros(round(total*sr));srt=[];clips=[];segments=[]
  for idx,(s,fs,start,sd) in enumerate(rows):
   clips+=fs;x=decode(A/(s['key']+'.mp3'));islast=idx==len(rows)-1
   tail=len(tagline)/sr+.6 if islast else .5;avail=sd-tail-.25
   if len(x)/sr>avail:
    raise RuntimeError(f'{s["key"]}: narration is too long; shorten the sentence instead of changing pitch or cutting words')
   begin=start+.2;off=round(begin*sr);voice[off:off+len(x)]+=x
   srt.append((begin,begin+len(x)/sr,T[s['key']]))
   segments.append({'shot':s['key'],'scene_start':start,'scene_duration':sd,'voice_start':begin,'voice_end':begin+len(x)/sr,'text':T[s['key']]})
   if islast:
    begin=total-len(tagline)/sr-.2;off=round(begin*sr);voice[off:off+len(tagline)]+=tagline;srt.append((begin,begin+len(tagline)/sr,TAG))
  vp=A/f'EP0{ep}-narration.wav';wav(vp,voice)
  (A/f'EP0{ep}-timing.json').write_text(json.dumps(segments,ensure_ascii=False,indent=2))
  (A/f'EP0{ep}-optional-synced.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{t}' for i,(a,b,t) in enumerate(srt)))
  # Skill owns join and audio mixing operations; no subtitle filters or text graphics.
  picture=R/f'production/audio-delivery-v3/work/EP0{ep}-clean-picture.mp4'
  if not picture.exists():
   picture=W/f'EP0{ep}-clean-picture.mp4'
   tool('join',[*clips,'--transition','none','--width','720','--height','1280','--fps','24','--quality','20','--preset','veryfast','-o',picture],f'EP0{ep}-picture')
  narr= W/f'EP0{ep}-narration-video.mp4'
  tool('audio',[picture,'--replace',vp,'--stereo','-o',narr],f'EP0{ep}-narration')
  final=O/f'EP0{ep}-no-subtitles-male-narration-v4.mp4'
  tool('audio',[narr,'--music',A/'unified-original-music.wav','--music-volume','-11','--duck','--music-fade-out','3','--limit','--limit-ceiling','-1','--stereo','-o',final],f'EP0{ep}-mixed')
  tool('check',[final],f'EP0{ep}-check',False)
  manifest['episodes'][f'EP0{ep}']={'file':str(final.relative_to(R)),'duration':dur(final),'timing':segments,'no_subtitle_graphics_added':True,'voiceover_file':str(vp.relative_to(R))}
  (O/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('DELIVERED',ep,flush=True)
 files=[O/f'EP0{ep}-no-subtitles-male-narration-v4.mp4' for ep in (1,2,3)]
 tool('join',[*files,'--transition','none','--preset','veryfast','-o',O/'three-episodes-storytelling-v4.mp4'],'full-film')
 (O/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print('ALL DONE',flush=True)
if __name__=='__main__':main()
