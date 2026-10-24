"""Build deterministic first-person motion plans for action clips."""
from __future__ import annotations
import json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'production/motion-blockouts'; FPS=24
PROFILES={
'战争冲突':('advance_and_evade',['guard_01','runner_01','torn_flag','report_0'],['line_clearance','hand_to_report_visibility']),
'战争撤退':('retreat_and_cover',['guard_01','runner_01','torn_flag','report_0'],['cover_clearance','fireline_visibility']),
'档室冲突':('entry_confrontation',['scribe_01','archive_guard','table_PR-SEAL-R'],['person_person_clearance','seal_hand_contact']),
'雪夜追车':('vehicle_chase',['cart_body','horse_01','wheel_left','wheel_right','medicine_chest','scribe_01'],['wheel_ground_contact','chest_transfer','vehicle_clearance']),
'车厢抢救':('vehicle_rescue',['medicine_chest','chest_report','backup_scroll','scribe_01','pov_right_hand'],['paper_contact','lid_hinge_state','hand_paper_contact']),
'封泥对峙':('threshold_intercept',['courier_01','archive_guard','table_PR-LETTERBOX','table_PR-SEAL-R'],['arm_clearance','box_support','seal_visibility']),
'锦囊拦截':('pouch_intercept',['PR-CLOUDBOX','PR-POUCH','pov_right_hand'],['hand_box_contact','seal_visibility']),
'三路派发':('three_route_dispatch',['CH-MSG-A','CH-MSG-B','CH-MSG-C','PR-MAP-NEW','seal_R','seal_G','seal_B'],['person_person_clearance','route_object_separation']),
'现场争执':('messenger_confrontation',['CH-MSG-A','CH-MSG-B','seal_R','PR-MAP-NEW','pov_right_hand'],['arm_clearance','seal_hand_contact']),
'路线冲突':('map_tug_and_stop',['CH-MSG-C','CH-MSG-A','PR-MAP-NEW','PR-MAP-OLD','pov_right_hand'],['paper_contact','person_person_clearance']),
'雨廊追截':('rain_corridor_pursuit',['CH-MSG-A','seal_R','PR-CLOUDBOX','pov_right_hand'],['corridor_clearance','seal_transfer']),
'灯号调度':('signal_reorder',['CH-MSG-A','CH-MSG-B','CH-MSG-C','PR-CLOUDBOX'],['route_clearance','signal_visibility']),
'急报冲入':('reporter_arrival',['RPT-A','RPT-B','CH-MSG-A','CH-MSG-B','pov_right_hand'],['person_person_clearance','report_hand_contact']),
'雨棚救援':('shelter_rescue',['zhuo_01','PR-COMPLAINT','road_awning','pov_right_hand'],['shelter_clearance','paper_contact','pursuer_clearance']),
'拦截追兵':('horse_intercept',['jingrui_01','horse_01','cart_body','zhuo_01'],['horse_ground_contact','vehicle_clearance','pursuer_clearance']),
'失控车轴':('axle_failure',['cart_body','wheel_left','wheel_right','axle_01','PR-COMPLAINT','pov_right_hand'],['wheel_ground_contact','axle_contact','paper_contact']),
'资源冲突':('resource_recovery',['medboy_01','road_guard','PR-MEDBUNDLE','PR-COMPLAINT','pov_right_hand'],['person_person_clearance','bundle_contact','report_contact']),
'雨路封锁':('roadblock_stop',['road_awning','cart_body','axle_01','road_guard','medboy_01','pov_right_hand'],['road_clearance','axle_contact','paper_contact']),
'高压同步':('high_pressure_sync',['desk_01','PR-COMPLAINT','PR-MEDBUNDLE','PR-MAP-NEW','cart_body','axle_01'],['object_separation','hand_object_contact','wheel_ground_contact']),
'封存抢救':('evidence_seal_rescue',['zhuo_01','PR-COMPLAINT','PR-MEDBUNDLE','PR-CLOUDBOX','pov_right_hand'],['paper_contact','seal_visibility','pursuer_clearance']),
'城门冲入':('gate_entry',['gate_opening','open_leaf_-2','open_leaf_2','gate_guard','jingrui_01','cart_body','paving_8'],['gate_clearance','vehicle_clearance','document_hand_contact'])}
def read(p): return json.loads((ROOT/p).read_text())
def ref(p):
 import hashlib
 x=ROOT/p; return {'path':str(p),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}
def path_points(camera,duration,phase):
 eye=camera['eye'];target=camera['target']; mag={'advance_and_evade':.34,'retreat_and_cover':.28,'entry_confrontation':.10,'vehicle_chase':.55,'vehicle_rescue':.10,'threshold_intercept':.12,'pouch_intercept':.08,'three_route_dispatch':.16,'messenger_confrontation':.08,'map_tug_and_stop':.06,'rain_corridor_pursuit':.48,'signal_reorder':.10,'reporter_arrival':.22,'shelter_rescue':.18,'horse_intercept':.42,'axle_failure':.16,'resource_recovery':.20,'roadblock_stop':.12,'high_pressure_sync':.08,'evidence_seal_rescue':.10,'gate_entry':.60}[phase]
 forward=phase in ('advance_and_evade','vehicle_chase','rain_corridor_pursuit','gate_entry','horse_intercept'); points=[]
 for i in range(int(duration*2)+1):
  t=round(min(duration,i/2),3);u=t/duration if duration else 1;ease=u*u*(3-2*u); e=list(eye);tar=list(target)
  if forward:e[1]+=mag*ease;tar[1]+=mag*.65*ease
  if phase in ('retreat_and_cover','roadblock_stop'):e[0]+=.08*math.sin(u*math.pi)
  if phase in ('vehicle_rescue','axle_failure','high_pressure_sync'):e[2]-=.06*math.sin(u*math.pi)
  points.append({'time_seconds':t,'eye_m':e,'target_m':tar,'fov_degrees':camera['vertical_fov_degrees']})
 return points
def build():
 workflow=read('production/workflow-v1.json'); scenes=read('production/scene-blockouts/manifest-v1.json'); metas={s['scene_key']:read(Path(s['files']['scene']['path'])) for s in scenes['scenes']};OUT.mkdir(parents=True,exist_ok=True);clips=[]
 for shot in workflow['shots']:
  if not shot.get('action_scene'):continue
  meta=metas[shot['scene_key']];cam=json.loads((ROOT/'production/scene-blockouts'/shot['scene_key']/(shot['scene_key']+'-camera.json')).read_text());phase,default,checks=PROFILES[shot['action_type']];available={i['instance_id'] for i in meta['instances']};entities=[x for x in default if x in available]
  for clip in shot['clips']:
   dur=clip['duration'];sample_count=int(round(dur*FPS))+1
   clips.append({'clip_key':clip['key'],'episode':shot['episode'],'logical_shot':shot['key'],'scene_key':shot['scene_key'],'action_type':shot['action_type'],'motion_profile':phase,'duration_seconds':dur,'target_fps':FPS,'sample_count':sample_count,'pov_owner':shot['pov_owner'],'camera':{'mode':'first_person','base_scene_camera':cam,'path_points':path_points(cam,dur,phase),'path_status':'draft_not_reviewed'},'entities':entities,'adaptive_checkpoints':[{'name':n,'required':True,'status':'pending_geometry_review'} for n in checks],'frame_samples':{'first_frame':0,'last_frame':sample_count-1,'ending_boundary_time_seconds':dur,'coverage_status':'not_rendered'},'evidence':{'scene':ref(Path('production/scene-blockouts')/shot['scene_key']/(shot['scene_key']+'-scene.json')),'camera':ref(Path('production/scene-blockouts')/shot['scene_key']/(shot['scene_key']+'-camera.json')),'preview':ref(Path('production/scene-blockouts')/shot['scene_key']/(shot['scene_key']+'-pov.png')),'depth':ref(Path('production/scene-blockouts')/shot['scene_key']/(shot['scene_key']+'-pov-depth-mm.png')),'object_ids':ref(Path('production/scene-blockouts')/shot['scene_key']/(shot['scene_key']+'-pov-object-ids.png'))},'status':'motion_blockout_draft_pending_full_frame_review','approved_for_generation':False})
 manifest={'version':1,'status':'motion_blockouts_v1_pending_24fps_review','target_fps':FPS,'clip_count':len(clips),'action_clip_count':len(clips),'rule':'Draft paths are not full-frame motion evidence; all action clips remain blocked until rendered and reviewed.','clips':clips};(OUT/'manifest-v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 W,H=1600,((len(clips)+3)//4)*165+100;img=Image.new('RGB',(W,H),'#182524');d=ImageDraw.Draw(img);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',20);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',15);d.text((28,20),'42 个动作片段 / 第一人称运动草稿 · 尚未验收',font=font,fill='#e7eee9')
 for n,c in enumerate(clips):
  x=28+(n%4)*390;y=70+(n//4)*165;d.rounded_rectangle((x,y,x+360,y+132),8,fill='#243735',outline='#4e6a62');d.text((x+14,y+12),c['clip_key'],font=font,fill='#f2d6a3');d.text((x+14,y+47),c['action_type'],font=small,fill='#d7e8dc');d.text((x+14,y+72),f"{c['scene_key']} · {c['duration_seconds']}s · 24fps",font=small,fill='#a9c5b8');d.text((x+14,y+97),f"实体 {len(c['entities'])} · 末帧待审",font=small,fill='#a9c5b8')
 img.save(OUT/'motion-overview-v1.jpg',quality=92);print(json.dumps({'clip_count':len(clips),'fps':FPS},ensure_ascii=False))
if __name__=='__main__':build()
