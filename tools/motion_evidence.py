"""Render selected first-person 24fps graybox motion evidence."""
from __future__ import annotations
import copy,hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.scene_blockouts import build_stages,camera_clipped_scene
from tools.asset_library import render
OUT=ROOT/'production/motion-evidence-v1';MOTION=ROOT/'production/motion-blockouts/manifest-v1.json';FPS=24
TARGETS={'EP01-S07-01':'chase','EP02-S07-01':'pursuit','EP03-S05-01':'axle_failure','EP01-S02-01':'war','EP02-S05-01':'confrontation','EP03-S10-01':'gate'}
def ref(p):
 p=ROOT/p;return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def root_index(sc,i): return next(k for k,n in enumerate(sc['nodes']) if n.get('extras',{}).get('instance_id')==i)
def tx(x=0,y=0,z=0):
 m=np.eye(4);m[:3,3]=[x,y,z];return m
def rx(deg):
 a=math.radians(deg);c,s=math.cos(a),math.sin(a);return np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1.]])
def delta(profile,i,u):
 if profile=='chase' and i in {'cart_body','wheel_left','wheel_right','axle_01','cart_canopy','horse_01','saddle_01','medicine_chest','scribe_01'}:return tx(y=.50*u)
 if profile=='pursuit' and i=='CH-MSG-A':return tx(y=.75*u)
 if profile=='pursuit' and i=='CH-MSG-B':return tx(y=.28*u)
 if profile=='war' and i=='guard_01':return tx(y=.40*u,x=-.08*math.sin(math.pi*u))
 if profile=='war' and i=='runner_01':return tx(y=.55*u,x=.10*math.sin(math.pi*u))
 if profile=='confrontation' and i=='CH-MSG-A':return tx(y=.12*u,x=-.10*u)
 if profile=='confrontation' and i=='CH-MSG-B':return tx(y=.12*u,x=.10*u)
 if profile=='gate' and i in {'jingrui_01','reporter_01'}:return tx(y=.70*u)
 if profile=='gate' and i=='gate_guard':return tx(x=.12*math.sin(math.pi*u))
 if profile=='axle_failure' and i=='cart_body':return tx(y=.12*u,z=.02*math.sin(math.pi*u))@rx(-2.5*math.sin(math.pi*u))
 if profile=='axle_failure' and i in {'wheel_left','wheel_right','axle_01'}:return tx(y=.12*u,z=.015*math.sin(math.pi*u))@rx(-3*math.sin(math.pi*u))
 if profile=='axle_failure' and i=='pov_right_hand':return tx(z=-.035*math.sin(math.pi*u))
 return np.eye(4)
def main():
 motion=json.loads(MOTION.read_text());by={c['clip_key']:c for c in motion['clips']};stages={s.key:s for s in build_stages()};entries=[]
 for key,profile in TARGETS.items():
  clip=by[key];stage=stages[clip['scene_key']];scene=stage.model;dur=clip['duration_seconds'];total=round(dur*FPS)+1;out=OUT/key
  if out.exists():shutil.rmtree(out)
  folders=[out/x for x in ('frames','depth-mm','object-ids','object-id-maps')]
  for p in folders:p.mkdir(parents=True,exist_ok=True)
  frames,depth,ids,maps=folders;base={n['extras']['instance_id']:np.array(n['matrix']) for n in scene['nodes'] if n.get('extras',{}).get('instance_id')};samples=[]
  camfile=ROOT/'production/scene-blockouts'/clip['scene_key']/(clip['scene_key']+'-camera.json')
  for f in range(total):
   u=f/max(1,total-1);posed=copy.deepcopy(scene)
   for inst,b in base.items():posed['nodes'][root_index(posed,inst)]['matrix']=(b@delta(profile,inst,u)).tolist()
   point=clip['camera']['path_points'][min(len(clip['camera']['path_points'])-1,round(f/12))];render_scene=camera_clipped_scene(posed,point['eye_m'],point['target_m'],.06);rgb=frames/f'{f:04d}.png';render(render_scene,rgb,180,320,point['eye_m'],point['target_m'],point['fov_degrees'],True)
   for suffix,folder in [('-depth-mm.png',depth),('-object-ids.png',ids),('-object-ids.json',maps)]:rgb.with_name(rgb.stem+suffix).replace(folder/(rgb.stem+suffix))
   rgb.with_name(rgb.stem+'-depth-m.npy').unlink(missing_ok=True);samples.append({'frame':f,'time_seconds':round(f/FPS,6),'rgb':ref(rgb),'depth_mm':ref(depth/f'{f:04d}-depth-mm.png'),'object_ids':ref(ids/f'{f:04d}-object-ids.png'),'object_id_map':ref(maps/f'{f:04d}-object-ids.json')})
  entry={'clip_key':key,'scene_key':clip['scene_key'],'profile':profile,'duration_seconds':dur,'target_fps':FPS,'sample_count':total,'pov_owner':clip['pov_owner'],'status':'rendered_motion_draft_pending_human_review','approved_for_generation':False,'entity_motion_note':'Procedural graybox transforms only; no physics solver or rig.','camera_source':ref(camfile),'samples':samples,'adaptive_checkpoints':clip['adaptive_checkpoints']};(out/'manifest.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n');entries.append(entry);print(key,total,flush=True)
 manifest={'version':1,'status':'selected_motion_evidence_v1_pending_human_review','target_fps':FPS,'clip_count':len(entries),'clips':[{'clip_key':e['clip_key'],'manifest':ref(OUT/e['clip_key']/'manifest.json'),'sample_count':e['sample_count']} for e in entries],'limitation':'Six selected high-risk clips only; remaining 36 action clips still have motion plans only.'};(OUT/'manifest-v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 sheet=Image.new('RGB',(1500,650),'#172423');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',24);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',16);d.text((20,18),'高风险动作 / 逐帧灰模证据草稿（首帧与末帧）',font=font,fill='#e7efe9')
 for n,e in enumerate(entries):
  x=20+n*500;y=65;first=Image.open(ROOT/e['samples'][0]['rgb']['path']).resize((210,373));last=Image.open(ROOT/e['samples'][-1]['rgb']['path']).resize((210,373));sheet.paste(first,(x,y));sheet.paste(last,(x+230,y));d.text((x,y+390),e['clip_key']+' · '+e['profile'],font=small,fill='#f0d4a2');d.text((x,y+420),f"{e['sample_count']}帧 · 24fps · 末帧已输出",font=small,fill='#a9c4b7');d.text((x,y+448),'尚未人工签核',font=small,fill='#a9c4b7')
 sheet.save(OUT/'motion-evidence-overview-v1.jpg',quality=92)
if __name__=='__main__':main()
