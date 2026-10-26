#!/usr/bin/env python3
"""Validate the v4 words, picture timing, and identical end-tag samples.
This is a technical check; it cannot certify emotional quality or visual physics.
"""
import hashlib,json,pathlib,subprocess,wave,array
R=pathlib.Path(__file__).resolve().parents[1];O=R/'production/storytelling-v4';A=O/'audio'
script=json.loads((O/'narration.json').read_text());m=json.loads((O/'delivery-manifest.json').read_text());wf=json.loads((R/'production/workflow-v1.json').read_text())
forbidden=('主线','支线','任务','版本','调度','开发者','基础设施','模型','运镜','第一人称','拍摄','制片')
assert set(script)=={s['key'] for s in wf['shots']}
for k,t in script.items():assert not any(w in t for w in forbidden),(k,t)
def read(p):
 with wave.open(str(p)) as f:return f.getframerate(),array.array('h',f.readframes(f.getnframes()))
sr,tag=read(A/'unified-brand-tagline.wav');checks={}
for ep,entry in m['episodes'].items():
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(R/entry['file'])]));v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert (v['width'],v['height'],v['r_frame_rate'])==(720,1280,'24/1')
 assert a.get('channels')==2
 duration=float(probe['format']['duration']);assert duration<180
 rate,voice=read(R/entry['voiceover_file']);assert rate==sr
 seconds=len(voice)/rate;assert abs(seconds-duration)<.04
 pos=round((seconds-len(tag)/sr-.2)*sr)
 assert voice[pos:pos+len(tag)]==tag,ep+' does not contain identical branding samples'
 for row in entry['timing']:
  assert row['text']==script[row['shot']]
  assert row['voice_start']>=row['scene_start']
  assert row['voice_end']<=row['scene_start']+row['scene_duration']
 checks[ep]={'duration':duration,'size':[v['width'],v['height']],'fps':24,'narration_seconds':seconds,'same_brand_audio_samples':True,'script_matches_timed_manifest':True,'sha256':hashlib.sha256((R/entry['file']).read_bytes()).hexdigest()}
report={'status':'passed','story_paragraphs':len(script),'no_production_terms_in_story':True,'mandated_brand_line_exception':'为你的主任务保驾护航','episodes':checks,'limitation':'Does not certify subjective voice quality, generated in-frame text or picture physics.'}
(O/'qc/technical-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
