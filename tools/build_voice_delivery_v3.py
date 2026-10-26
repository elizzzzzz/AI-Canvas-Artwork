#!/usr/bin/env python3
"""Clean picture assembly + scene-timed male narration, no burned captions.
Narration is synthetic zh-CN-YunyangNeural; approval of perceived age/emotion stays human.
"""
import asyncio,json,pathlib,subprocess,sys,wave,datetime,hashlib
import numpy as np
import edge_tts
R=pathlib.Path(__file__).resolve().parents[1]; O=R/'production/audio-delivery-v3'; A=O/'audio'; W=O/'work'; Q=O/'qc'
for p in (A,W,Q):p.mkdir(parents=True,exist_ok=True)
SK=pathlib.Path('/Users/elizhang/.agents/skills/ffmpeg-skill/scripts'); PY='/Library/Frameworks/Python.framework/Versions/3.11/bin/python3'
VOICE='zh-CN-YunyangNeural'; RATE='-4%'; PITCH='-5Hz'
WF=json.loads((R/'production/workflow-v1.json').read_text())
T={
'EP01-S01':'我又梦见梅岭。十二年过去，那一夜的风雪，仍在耳边。',
'EP01-S02':'梦里的我，还是林殊。我勒马望去，残旗倒在雪中，同袍再也没有起身。我们等的援军，终究没有来。',
'EP01-S03':'三份军报，同样的纸，同样的军印，却指向三条不同的路。不是消息迟了，是有人把我们的生路，写成了死局。',
'EP01-S04':'箭雨落下的时候，我才明白，我们等来的不是援军。醒来以后，我总想找回，那张没有送到的原报。',
'EP01-S05':'我让书吏取来梅岭旧档。十二年的封存，一页也不能少。我要查原卷，因为每一次改动，都可能留下痕迹。',
'EP01-S06':'可最要紧的一页，竟被误放进药箱，随车出了库。查案还没迈出第一步，我就得先放下旧档，去挽救这条支线。',
'EP01-S07':'我追着药车赶进雪夜。那一页不能丢，它可能是十二年来，离真相最近的线索。终于追上了，先把车停下，再找原报。',
'EP01-S08':'原页受了潮，幸好备卷还在。字迹可以对照恢复，封印却不能凭记忆重画。我让人把原页和备卷，一同留下。',
'EP01-S09':'残角上的燕字，让我停住了手。这不是我记忆里的北魏军印。原来那一夜，还有一只藏得更深的手。',
'EP01-S10':'我把印记重新对照。十二年过去，仍有人替它送信。找回这一页，才算重新走回我的主线。',
'EP01-S11':'若有人把支线接稳，我便能专心追查旧案。七牛云准备好一站式AI基础设施，让开发者专注自己的主任务。',
'EP02-S01':'我是谢听云。琅琊阁这场雨，已经下了一夜。我要做的，是把一个锦囊，送到真正该收到的人手里。',
'EP02-S02':'阁中只交代一句：送到北燕六皇子手中，不得拆阅，不得改字。我封好锦囊，也接下了这份责任。',
'EP02-S03':'来报的人告诉我，六皇子的兄长各有兵马，他却只有一座空宫。选中他，也许正因为，他已经没有退路。',
'EP02-S04':'我让三路信使同时出发。路可以不同，任务却必须相同。只要有一处不对，就立即回来核验。',
'EP02-S05':'偏偏封泥对不上口令，口令又对不上路线。看似各自齐备，合起来却寸步难行。我只好先停下送令，逐项核对。',
'EP02-S06':'第三名信使又带来了旧地图。图上那条路从前能走，如今却未必。旧图并非全错，只是不属于这一次任务。',
'EP02-S07':'锦囊还得送，眼前的混乱也必须收住。我重新核验身份、封泥和路线，把旧版本移开，只留一份有效清单。',
'EP02-S08':'我把所有回报收回同一处。灯号终于接上，三路信使认的是同一个版本。我也终于能把心思，放回送达这件事。',
'EP02-S09':'回执送回雨廊，封泥完整。信使当面告诉我，北燕已立六皇子为储君。锦囊送到了，该知道的人自然会知道。',
'EP02-S10':'两府的人也来了。太子和誉王同时在找麒麟才子：得之，可得天下。雨廊之外，另一场争夺已经开始。',
'EP02-S11':'我只管把任务送达。七牛云接好模型、数据和调度，让开发者把精力，留给真正重要的事。',
'EP03-S01':'我本想借一场病，入一座城。可金陵还没到，路上的风雨，先把另一桩公道交到了我手里。',
'EP03-S02':'卓青遥抱着状纸来见我。他说，证据是真的，可若进不了京，就没人听得到他的诉求。我决定带他同行。',
'EP03-S03':'前方是萧景睿。他愿意引我们入城，也替这趟难走的路，留出了一道门。我要护住的，已不只是自己。',
'EP03-S04':'状纸随身，药包随车，路线重新核对。证据、药和路，少一样，卓青遥就到不了金陵。我把每一项分别交代。',
'EP03-S05':'雨打湿了纸边，车轴又传来异响。车夫停住马车，护卫过来查看。我先护住状纸，赶路只能暂缓。',
'EP03-S06':'药在后车，密报上的官名又错了。支线一多，出错的便不止一件东西。我得追回药，再把信改正。',
'EP03-S07':'若此刻继续赶路，我们只会带着错误一起进城。我叫众人停下，把状纸、药包和路线，重新带到眼前。',
'EP03-S08':'我让几路支持归到同一份清单。证据有人保管，药包有人送回，路线有人复核。接稳这些，我才能继续护人入城。',
'EP03-S09':'状纸确认完整，我重新封存。封签留在原处，原件也一同保留。证据只有经得起核验，才值得带进金陵。',
'EP03-S10':'城门终于近了。我守着证人，也守着这份状纸。把他们一起带进去，这一程才算走完。',
'EP03-S11':'车门旁又递来一封密报，纸角的燕形印记，竟与旧案呼应。入京不是终点，真正的棋局，才刚开始。',
'EP03-S12':'主线要走得远，支线就得接得稳。七牛云准备好一站式AI基础设施，让开发者专注把自己的故事做完。'
}
TAG='七牛云，一站式AI Infra，为你的主任务保驾护航。'
def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def dur(p):return float(probe(p)['format']['duration'])
def video_seconds(p):
 x=probe(p); v=next(s for s in x['streams'] if s['codec_type']=='video'); return float(v.get('duration') or x['format']['duration'])
def tool(name,args,result,plan=True):
 cmd=[PY,str(SK/(name+'.py')),*map(str,args),'--json-brief']+(['--overwrite'] if name!='check' else [])
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
  if p.exists() and j.exists():return
  async with sem:
   for n in range(3):
    try:
     data=[]
     with p.with_suffix('.part').open('wb') as f:
      async for c in edge_tts.Communicate(text,VOICE,rate=RATE,pitch=PITCH,boundary='SentenceBoundary').stream():
       if c['type']=='audio':f.write(c['data'])
       elif c['type']=='SentenceBoundary':data.append(c)
     p.with_suffix('.part').replace(p);j.write_text(json.dumps(data,ensure_ascii=False,indent=2));print('voiced',k,flush=True);return
    except Exception:
     if n==2:raise
     await asyncio.sleep(2)
 await asyncio.gather(*(one(k,t) for k,t in {**T,'unified-brand-tagline':TAG}.items()))
def srt_time(t):
 n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
def main():
 src=sources();timeline={};manifest={'voice':VOICE,'rate':RATE,'pitch':PITCH,'synthetic_voice':True,'burned_captions':False,'source_ep01':'ep01-revision-v2','ep02_ep03_visual_fixes':'pending_not_claimed','voice_age_emotion':'mature male direction; subjective listening review still required','episodes':{}}
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
    factor=len(x)/(avail*sr)
    if factor>1.35:raise RuntimeError(f'{s["key"]}: narration too long ({factor:.2f})')
    x=np.interp(np.linspace(0,len(x)-1,round(avail*sr)),np.arange(len(x)),x)
   begin=start+.2;off=round(begin*sr);voice[off:off+len(x)]+=x
   srt.append((begin,begin+len(x)/sr,T[s['key']]))
   segments.append({'shot':s['key'],'scene_start':start,'scene_duration':sd,'voice_start':begin,'voice_end':begin+len(x)/sr,'text':T[s['key']]})
   if islast:
    begin=total-len(tagline)/sr-.2;off=round(begin*sr);voice[off:off+len(tagline)]+=tagline;srt.append((begin,begin+len(tagline)/sr,TAG))
  vp=A/f'EP0{ep}-narration.wav';wav(vp,voice)
  (A/f'EP0{ep}-timing.json').write_text(json.dumps(segments,ensure_ascii=False,indent=2))
  (A/f'EP0{ep}-optional-synced.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{t}' for i,(a,b,t) in enumerate(srt)))
  # Skill owns join and audio mixing operations; no subtitle filters or text graphics.
  picture=W/f'EP0{ep}-clean-picture.mp4'
  tool('join',[*clips,'--transition','none','--width','720','--height','1280','--fps','24','--quality','20','--preset','veryfast','-o',picture],f'EP0{ep}-picture')
  narr= W/f'EP0{ep}-narration-video.mp4'
  tool('audio',[picture,'--replace',vp,'--stereo','-o',narr],f'EP0{ep}-narration')
  final=O/f'EP0{ep}-no-subtitles-male-narration-v3.mp4'
  tool('audio',[narr,'--music',A/'unified-original-music.wav','--music-volume','-11','--duck','--music-fade-out','3','--limit','--limit-ceiling','-1','--stereo','-o',final],f'EP0{ep}-mixed')
  tool('check',[final],f'EP0{ep}-check',False)
  manifest['episodes'][f'EP0{ep}']={'file':str(final.relative_to(R)),'duration':dur(final),'timing':segments,'no_subtitle_graphics_added':True,'voiceover_file':str(vp.relative_to(R))}
  (O/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('DELIVERED',ep,flush=True)
 files=[O/f'EP0{ep}-no-subtitles-male-narration-v3.mp4' for ep in (1,2,3)]
 tool('join',[*files,'--transition','none','--preset','veryfast','-o',O/'three-episodes-no-subtitles-v3.mp4'],'full-film')
 (O/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print('ALL DONE',flush=True)
if __name__=='__main__':main()
