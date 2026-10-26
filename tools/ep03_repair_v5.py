#!/usr/bin/env python3
"""EP03 correction: real proxy assemblies + full-frame deterministic blocking.
Local rendering only. New sources have no inherited human approval.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math,pathlib,sys,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.scene_blockouts import Stage, camera_clipped_scene
from tools.asset_library import mat,render,write_glb,world_transforms
O=R/'production/ep03-repair-v5';FPS=24

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':digest(p)}
def index(sc,ident):return next(i for i,n in enumerate(sc['nodes']) if n.get('extras',{}).get('instance_id')==ident)
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
def refs():return {x['id']:x for x in json.loads((R/'production/asset-library/catalog-v1.json').read_text())['assets']}
def base(key,eye,target):return Stage(key,key,'梅长苏',(eye,target),refs())
def hand(s,side,position):s.add('HAND-MCS-'+side,'hand_'+side,position,(-90,0,0),support='pov_forearm_outside_frame')
def cart(s):
 s.road();s.cart(0,0,True)
 # Correct the original proxy axle center from 0.465 to 0.515 m, use one axle only.
 i=index(s.model,'axle_01');s.model['nodes'][i]['matrix']=mat((0,0,.465)).tolist()
 # The source axle itself is offset +0.05m; .465 + .05 = wheel center .515.
 hand(s,'L',(-.21,.80,1.12));hand(s,'R',(.20,.80,1.12))
 s.model['extras']['axle_observation']={'source_axle_center_z':.05,'placement_z':.465,'world_center_z':.515,'wheel_center_z':.515,'wheel_radius':.515,'formal_contact_approved':False}
def make_stages():
 configs=[]
 s=base('EP03R5-STOP',[0,.60,1.67],[0,4.7,1.52]);cart(s)
 configs.append((s,12,'stopped',['EP03-S01-01','EP03-S01-02']))
 s=base('EP03R5-HANDOFF',[0,-.10,1.58],[0,.84,.74]);s.road();s.add('AR-DESK','table',(0,.95,0));s.add('AR-AWNING','fixed_awning',(0,1.15,0))
 for aid,ident,x in [('PR-COMPLAINT','complaint',-.38),('PR-MEDBUNDLE','medicine',0),('PR-MAP-NEW','map',.38)]:s.tabletop(aid,ident,x,.91)
 s.floor_object('CH-ZQY','witness',-.85,1.95,rotation=180);s.floor_object('CH-DRIVER','driver',.85,1.95,rotation=180)
 hand(s,'L',(-.3,.40,.9));hand(s,'R',(.3,.4,.9))
 configs.append((s,16,'sequential_handoff',['EP03-S04-01','EP03-S04-02','EP03-S08-01','EP03-S08-02']))
 s=base('EP03R5-STAMP',[0,-.05,1.55],[0,.9,.75]);s.road();s.add('AR-DESK','table',(0,.95,0));s.add('AR-AWNING','fixed_awning',(0,1.15,0))
 s.tabletop('PR-COMPLAINT','complaint',0,.90);s.tabletop('PR-INK','inkpad',.32,.93);s.tabletop('PR-STAMP','stamp',.32,.93,.88);s.tabletop('PR-SEAL-R','seal_reference',-.35,1.10)
 hand(s,'L',(-.13,.7,.81));hand(s,'R',(.32,.93,1.00))
 configs.append((s,14,'stamp_contact',['EP03-S09-01','EP03-S09-02']))
 s=base('EP03R5-RIDE',[0,.60,1.67],[0,4.7,1.52]);cart(s)
 s.add('AR-GATE','gate_opening',(0,15,0))
 for y in (15,21):
  for x in (-1.7,1.7):s.add('ENV-DIRT',f'road_extension_{x}_{y}',(x,y,0))
 s.floor_object('CH-GUARD','gate_guard',1.65,13,rotation=180)
 configs.append((s,16,'moving_cart',['EP03-S10-01','EP03-S10-02']))
 return configs

def frame_pose(stage,t,dur,profile):
 sc=copy.deepcopy(stage.model);eye=np.array(stage.camera['eye'],float);target=np.array(stage.camera['target'],float);contact=[]
 if profile in ('stopped','moving_cart'):
  distance=0 if profile=='stopped' else 0.45*t
  travel=mat((0,distance,0));dynamic={'cart_body','wheel_left','wheel_right','axle_01','cart_canopy','horse_01','saddle_01','hand_L','hand_R'}
  for ident in dynamic:
   n=sc['nodes'][index(sc,ident)];m=np.array(n['matrix']);n['matrix']=(travel@m).tolist()
   if ident.startswith('wheel'):
    center=np.array(m[:3,3])+[0,0,.515]
    n['matrix']=(travel@mat(center)@mat(rotation=(math.degrees(-distance/.515),0,0))@mat(-center)@m).tolist()
  eye+=np.array([0,distance,0]);target+=np.array([0,distance,0])
  if profile=='moving_cart':
   # Two-link sagittal IK for a slow walk. Stance hooves hold a world Y; swing hooves clear the ground.
   for leg in range(4):
    phase=(t/1.2+(0,.5,.5,0)[leg])%1;period=math.floor(t/1.2+(0,.5,.5,0)[leg])
    lead=.162;hip_offset=(-.5,-.5,.48,.48)[leg]
    if phase<.6:
     relative_y=lead-.45*(phase*1.2);foot_z=0.
    else:
     u=(phase-.6)/.4;relative_y=-lead+2*lead*smooth(u);foot_z=.075*math.sin(math.pi*u)
    dy=relative_y;dz=-(1.-foot_z);length=math.hypot(dy,dz);l1=.47;l2=.53;length=min(length,l1+l2-.0001)
    alpha=math.atan2(dy,-dz);beta=math.acos(max(-1,min(1,(l1*l1+length*length-l2*l2)/(2*l1*length))))
    theta1=alpha-beta;theta2=math.pi-math.acos(max(-1,min(1,(l1*l1+l2*l2-length*length)/(2*l1*l2))))
    ni=next(i for i,n in enumerate(sc['nodes']) if n['name']==f'leg_root_{leg}')
    n=sc['nodes'][ni];b=np.array(n['matrix']);n['matrix']=(b@mat(rotation=(math.degrees(theta1),0,0))).tolist()
    ki=next(i for i,n in enumerate(sc['nodes']) if n['name']==f'leg_knee_{leg}')
    sc['nodes'][ki]['matrix']=mat((0,0,-l1),(math.degrees(theta2),0,0)).tolist()
    hi=next(i for i,n in enumerate(sc['nodes']) if n['name']==f'hoof_{leg}')
    hoof=sc['nodes'][hi];hm=np.array(hoof['matrix'])@mat(rotation=(-math.degrees(theta1+theta2),0,0));hoof['matrix']=hm.tolist()
    worlds=world_transforms(sc);verts=np.c_[hoof['mesh'][0],np.ones(len(hoof['mesh'][0]))]@worlds[hi].T
    correction=foot_z-float(verts[:,2].min());parent=sc['nodes'][hi]['parent'];local=np.linalg.inv(worlds[parent][:3,:3])@np.array([0,0,correction]);hm[:3,3]+=local;hoof['matrix']=hm.tolist()
    contact.append({'leg':leg,'phase':phase,'stance':phase<.6,'target_hoof_z':foot_z,'ik_mode':'two_link_sagittal_proxy_no_physics','nominal_contact_plane_z':0.})
  # Stationary profile has zero displacement for horse, camera, wheels and cart throughout.
  contact.append({'vehicle_distance_m':distance,'camera_relative_cart_translation_m':0.0,'wheel_radius_m':.515,'wheel_angle_rad':-distance/.515,'horse_drawn':True,'gait_status':'two_link_walking_proxy_pending_full_visual_contact_review'})
 elif profile=='sequential_handoff':
  events=[('complaint',-.38,3.,'witness'),('medicine',0,6.,'driver'),('map',.38,9.,'driver')]
  active=None
  for ident,x,start,who in events:
   u=(t-start)/2.;lift=smooth(u*3) if u<1/3 else 1 if u<2/3 else 1-smooth((u-2/3)*3)
   lift=max(0,lift) if 0<u<1 else 0
   y=.91+.15*smooth(u);z=.74+.09*lift
   n=sc['nodes'][index(sc,ident)];n['matrix']=mat((x,y,z)).tolist()
   if 0<u<1:active=(ident,x,y,z)
   contact.append({'object':ident,'table_plane_z':.74,'bottom_z':z+(.02 if ident=='medicine' else 0),'move_fraction':max(0,min(1,u)),'recipient':who,'path':'lift_then_translate_then_return_to_same_fixed_table'})
  if active:
   ident,x,y,z=active;n=sc['nodes'][index(sc,'hand_R')];n['matrix']=mat((x+.03,y-.04,z+.085),(-90,0,0)).tolist()
  # Do not claim fingertip or recipient grasp contact solved by these proxy transforms.
 elif profile=='stamp_contact':
  # Three controlled phases: charge ink -> lift and translate -> press onto the same paper.
  stamp=sc['nodes'][index(sc,'stamp')]
  if t<2:x,y=.32,.93;z=.88-(.88-.752)*smooth(t/2)
  elif t<4:x,y=.32,.93;z=.752+.13*smooth((t-2)/2)
  elif t<7:u=smooth((t-4)/3);x=.32+(.055-.32)*u;y=.93+(.96-.93)*u;z=.882
  elif t<9:x,y=.055,.96;z=.882-(.882-.7405)*smooth((t-7)/2)
  elif t<10:x,y,z=.055,.96,.7405
  elif t<12:x,y=.055,.96;z=.7405+.13*smooth((t-10)/2)
  else:x,y,z=.055,.96,.8705
  stamp['matrix']=mat((x,y,z)).tolist();sc['nodes'][index(sc,'hand_R')]['matrix']=mat((x,y-.025,z+.105),(-90,0,0)).tolist()
  contact=[{'stamp_bottom_z':z,'paper_top_z':.7405,'inkpad_top_z':.752,'ink_contact':t<=2.001 and z<=.7521,'paper_contact':9<=t<=10,'paper_gap_m':round(z-.7405,8),'ink_gap_m':round(z-.752,8),'seal_appearance':'no_new_mesh_or_lid; impression is reserved for canonical texture state'}]
 return sc,eye.tolist(),target.tolist(),contact

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');ap.add_argument('--width',type=int,default=144);ap.add_argument('--setup');args=ap.parse_args();O.mkdir(parents=True,exist_ok=True);entries=[]
 if args.setup and (O/'manifest.json').exists():entries=[e for e in json.loads((O/'manifest.json').read_text())['setups'] if e['key']!=args.setup]
 for stage,dur,profile,scopes in make_stages():
  if args.setup and stage.key!=args.setup:continue
  out=O/stage.key;out.mkdir(parents=True,exist_ok=True)
  model=out/'scene.glb';write_glb(stage.model,model)
  metadata={'key':stage.key,'profile':profile,'scopes':scopes,'duration_seconds':dur,'fps':FPS,'asset_instances':stage.instances,'asset_sources':stage.sources,'camera':stage.camera,'state':'actual_proxy_assembly_pending_human_review','internal_approval':None,'formal_approval':None,'limitations':['Proxy anatomy does not establish final actor identity','No physical collision solver','Horse motion proxy has no certified gait','Hand grip and fingertips still need visual review'],'do_not_generate_yet':True}
  (out/'scene.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
  sample_frames=range(dur*FPS+1) if args.full else sorted({0,round(dur*FPS*.25),round(dur*FPS*.5),round(dur*FPS*.75),dur*FPS})
  frames=out/'frames';frames.mkdir(exist_ok=True);samples=[];images=[]
  for f in sample_frames:
   t=f/FPS;sc,eye,target,contact=frame_pose(stage,t,dur,profile);png=frames/f'{f:04d}.png'
   receipt=render(camera_clipped_scene(sc,eye,target,.06),png,args.width,round(args.width*16/9),eye,target,stage.camera['vertical_fov_degrees'],True)
   row={'frame':f,'time_seconds':t,'eye':eye,'target':target,'contact_observations':contact,'rgb':ref(png),'depth':ref(png.with_name(png.stem+'-depth-mm.png')),'object_ids':ref(png.with_name(png.stem+'-object-ids.png')),'object_id_legend':ref(png.with_name(png.stem+'-object-ids.json')),'render':receipt}
   samples.append(row)
   # Uncompressed depth is disposable, hashed 16-bit depth is retained.
   png.with_name(png.stem+'-depth-m.npy').unlink(missing_ok=True)
   if f in (0,dur*FPS//2,dur*FPS):images.append((t,Image.open(png).convert('RGB').resize((216,384))))
  timeline={'status':'rendered_proxy_motion_pending_human_review','sample_count':len(samples),'expected_count':dur*FPS+1,'full_24fps':args.full,'frames':samples,'all_frames_plus_ending_boundary':args.full,'human_review':None}
  (out/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
  sheet=Image.new('RGB',(3*240,438),'#182524');d=ImageDraw.Draw(sheet)
  for i,(t,im) in enumerate(images):sheet.paste(im,(i*240+12,12));d.text((i*240+12,407),f'{t:.2f}s',fill='white')
  sheet.save(out/'review.jpg');entry={'key':stage.key,'profile':profile,'scopes':scopes,'scene':ref(out/'scene.json'),'model':ref(model),'timeline':ref(out/'timeline.json'),'preview':ref(out/'review.jpg'),'human_approval':None,'status':'pending_review'};entries.append(entry);print(stage.key,len(samples),'frames',flush=True)
 manifest={'version':5,'episode':3,'source':'explicit_library_instances_and_frame_transforms','status':'pending_human_review','human_approval':None,'generated_paid_media':0,'setups':entries,'canonical_props':'../ep02-repair-v5/canonical-assets.json','fixed_requirements':['stopped_cart_camera_zero_relative_jitter','handoffs_sequential_never_three_hands_cross','stamp_charges_ink_and_contacts_paper_before_lift','horse_visible_between_viewpoint_and_gate','same_ep01_paper_and_seal_reference_assets'],'no_generation_approval_inferred':True}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 html='<!doctype html><meta charset="utf-8"><title>第三集修复灰模审核</title><style>body{background:#152323;color:#edf2e9;font:18px sans-serif;max-width:1080px;margin:40px auto}img{max-width:100%}section{padding:24px;border-top:1px solid #6b8f80}a{color:#b9dec2}</style><h1>第三集修复：真实3D灰模，待人工查看</h1><p>仅本地建模与渲染，尚未提交收费重绘。静态截图和诊断图不是成片；逐帧预演仍需检查。</p>'
 for e in entries:html+=f'<section><h2>{e["key"]} · {e["profile"]}</h2><p>{", ".join(e["scopes"])}</p><img src="{e["key"]}/review.jpg"><p><a href="{e["key"]}/scene.glb">GLB</a> · <a href="{e["key"]}/timeline.json">24fps逐帧记录</a></p></section>'
 (O/'review.html').write_text(html)
if __name__=='__main__':main()
