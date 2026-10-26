"""Local EP02 repair package only. Never submits generation or writes global manifests."""
from __future__ import annotations
import argparse, copy, hashlib, html, json, math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'production/ep02-repair-v5'
REF=ROOT/'production/ep01-revision-v2/reference-images'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(Path(p).relative_to(ROOT)),'sha256':digest(p)}
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def canonical():
 tex=OUT/'textures';tex.mkdir(parents=True,exist_ok=True)
 src=REF/'EP01-S03.png';im=Image.open(src).convert('RGB')
 # Exact centre sheet from the real EP01 image. No generated replacement glyphs.
 quad=np.float32([[274,484],[512,486],[509,914],[321,947]])
 target=np.float64([[0,0],[699,0],[699,999],[0,999]]); rows=[]; values=[]
 for (x,y),(u,v) in zip(target,quad):
  rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);values.extend([u,v])
 coefficients=np.linalg.solve(np.array(rows),np.array(values))
 paper=im.transform((700,1000),Image.Transform.PERSPECTIVE,coefficients,Image.Resampling.BICUBIC)
 paper.save(tex/'report-canonical.png')
 stamp=im.crop((429,802,502,884));stamp.save(tex/'yan-stamp-source-crop.png')
 a=np.asarray(stamp).astype(float);mask=np.clip((a[:,:,0]-a[:,:,1]-5)*8,0,255).astype('uint8')
 rgba=Image.new('RGBA',stamp.size,(94,34,31,0));rgba.putalpha(Image.fromarray(mask));rgba.save(tex/'yan-stamp-alpha.png')
 # Paper substrate and old/valid maps are deterministic graphics, not AI generation.
 substrate=im.crop((360,735,390,765)).resize((700,1000));substrate.save(tex/'paper-substrate.png')
 for old in [False,True]:
  m=substrate.copy();d=ImageDraw.Draw(m);ink=(47,52,43);red=(104,39,32)
  d.rectangle((35,35,665,965),outline=ink,width=4)
  river=[(95,70),(190,210),(115,355),(245,480),(185,625),(290,760),(220,930)]
  d.line(river,fill=(65,87,85),width=11)
  route=[(565,880),(520,710),(540,540),(430,370),(470,175)]
  if old:route=[(565,880),(470,700),(250,580),(185,625),(100,430)]
  if old:
   for a,b in zip(route,route[1:]):
    for k in range(0,10,2):
     p=tuple(int(a[i]+(b[i]-a[i])*k/10) for i in (0,1));q=tuple(int(a[i]+(b[i]-a[i])*(k+1)/10) for i in (0,1));d.line([p,q],fill=ink,width=10)
   d.line([(145,585),(225,665)],fill=red,width=14);d.line([(225,585),(145,665)],fill=red,width=14)
  else:d.line(route,fill=red,width=11,joint='curve')
  for x,y in [route[0],route[-1]]:d.ellipse((x-17,y-17,x+17,y+17),outline=red,width=7)
  if old:d.polygon([(0,0),(120,0),(0,135)],fill=(0,0,0))
  m.save(tex/('route-expired.png' if old else 'route-valid.png'))
 source={'reference':ref(src),'source_pixels':{'report_quad_xy':quad.tolist(),'stamp_crop_xyxy':[429,802,502,884]},'method':'perspective rectification and direct pixel crop; no AI; no new glyph','review_status':'pending_human_review; EP01 real source inherited, not historical authentication'}
 assets={
 'REPORT-YAN-01':{'base_asset_id':'PR-REPORT','dimensions_m':[.21,.30,.0005],'texture':ref(tex/'report-canonical.png'),'purpose':'梅岭军报证据；不能作为送信路线图','layout':{'orientation':'short edge horizontal; north/top at image row 0','border_uv':[.04,.04,.96,.96],'arrow':'centre sheet upward arrow inherited from EP01','yan_stamp':'lower right, exact original pixels','partial_round_stamp':'left lower edge, inherited pixels','folds':'inherited original paper, no procedural randomization'},'source':source,'uv':'top face x=-.105→+.105 maps u=0→1; y=-.15→+.15 maps v=1→0; no mirror'},
 'YAN-STAMP-01':{'dimensions_m':[.035,.0393,0],'source':source,'texture':ref(tex/'yan-stamp-alpha.png'),'original_crop':ref(tex/'yan-stamp-source-crop.png'),'rule':'same exact raster glyph and border on every report; do not ask video model to invent 燕; alpha red extraction is not vector reconstruction'},
 'ROUTE-VALID-01':{'base_asset_id':'PR-MAP-NEW','dimensions_m':[.21,.30,.0005],'texture':ref(tex/'route-valid.png'),'purpose':'当前可通行送信路线；与军报不同；红色连续线绕开渡口，无燕印','rule':'right-side detour; two terminal circles; keep orientation and scale; no semantic seal/map conversion','derivation':'deterministic local drawing on EP01 paper substrate; new layout pending user review'},
 'ROUTE-EXPIRED-01':{'base_asset_id':'PR-MAP-OLD','dimensions_m':[.21,.30,.0005],'texture':ref(tex/'route-expired.png'),'purpose':'旧渡口路线；只放左侧收回区，禁止交给新出发信使','distinction':'upper-left missing corner proxy + dashed dark route + red crossed ferry','derivation':'same substrate; separate graphic; pending review'},
 'POUCH-01':{'base_asset_id':'PR-POUCH','dimensions_m':[.12,.10,.20],'material':'墨蓝布、棕绳；袋体不变形为纸或木盒','purpose':'唯一密信容器；留在谢听云手边直到核验完毕，只交一人','seal_id':'SEAL-CLAY-01','first_episode_style_anchor':ref(REF/'EP01-S10.png'),'inheritance_limit':'EP01 envelope/cord palette only, no EP01 pouch close-up exists; new pouch form pending review'},
 'SEAL-CLAY-01':{'base_asset_id':'PR-SEAL-R','dimensions_m':[.05,.05,.012],'material':'暗红封泥，贴在锦囊绳结上，有支撑接触，不是漂浮圆片','glyph_source':'YAN-STAMP-01','purpose':'只表示是否拆封；不代表路线，不替代军报','texture':ref(tex/'yan-stamp-alpha.png'),'old_grey_blue_seals':'not used for route coding; physical clay objects, never maps'},
 'RECEIPT-01':{'base_asset_id':'PR-RECEIPT','dimensions_m':[.21,.30,.0005],'texture':ref(tex/'paper-substrate.png'),'purpose':'送达回执；回执有封印不等于未拆开的原锦囊回到手中','rule':'arrives after pouch exits; never duplicate pouch to illustrate receipt'}
 }
 people=[]
 for id,model,desc in [('XTY','CH-XTY','谢听云；只见第一人称袖手，不另生一张脸'),('MSG-A','CH-MSG-A','青年长脸，无须，墨蓝窄袖，细长鼻梁'),('MSG-B','CH-MSG-B','中年方脸，短须，灰褐衣，浓眉'),('MSG-C','CH-MSG-C','年长瘦脸，花白鬓，深绿衣，颧骨明显'),('SCRIBE','CH-SCRIBE','秃额圆脸书吏，浅灰袍，不兼任三位信使')]:
  people.append({'stable_id':'EP02-PERSON-'+id,'library_asset_id':model,'face_anchor_source':None,'face_anchor_status':'missing: proxy is not identity evidence; must design and human-review separate portrait before generation','visual_direction':desc,'simultaneous_face_dedup_status':'not_verified'})
 c={'schema':'langya-canonical-assets-v5','version':5,'units':'metre','up_axis':'+Z','forward_axis':'+Y','status':'pending_human_review','no_paid_generation':True,'shared_use':['EP02','EP03'],'assets':assets,'people':people,'source_reference_images':[ref(REF/n) for n in ['EP01-S03.png','EP01-S06.png','EP01-S10.png']],'audio':{k:ref(ROOT/'production/storytelling-v4/audio'/name) for k,name in [('episode_narration','EP02-narration.wav'),('music','unified-original-music.wav'),('brand_tagline','unified-brand-tagline.wav'),('narration_timing','EP02-timing.json')]},'audio_rules':'reuse existing files byte-for-byte; no new TTS, captions or model sound; finale plays same brand recording; mature male story delivery without production terms','approval':{'status':'pending','reviewer':None,'current_source_hash_bound':False},'limitations':['UV textures in scene GLBs are mapped explicitly; CPU proxy renderer does not sample texture','faces are proxy geometry, identity is not approved','no paid generation or new approval flags']}
 dump(OUT/'canonical-assets.json',c)
 # Immediately useful image board.
 board=Image.new('RGB',(1500,1140),(236,232,219));d=ImageDraw.Draw(board)
 for idx,n in enumerate(['report-canonical.png','route-valid.png','route-expired.png']):
  t=Image.open(tex/n);t.thumbnail((440,930));board.paste(t,(30+idx*500,110));d.text((35+idx*500,35),n,fill='black')
 s=Image.open(tex/'yan-stamp-source-crop.png').resize((120,135));board.paste(s,(35,990));d.text((180,1020),'EXACT EP01 PIXELS / no new glyph / pending review',fill='black');board.save(OUT/'canonical-texture-board.jpg')
 return c


def embed_glb_textures(path, bindings, camera=None):
 """Embed PNG and TEXCOORD_0 onto named horizontal mesh nodes; author units metre/Z up.
 bindings = {node_name: texture_path}. Existing mesh must be horizontal paper/label.
 Camera: eye/target/vertical_fov_degrees; adds real glTF camera under conversion root.
 """
 raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=bytearray(raw[28+size:]);binary=binary[:doc['buffers'][0]['byteLength']]
 def append(data):
  while len(binary)%4:binary.append(0)
  i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary.extend(data);return i
 def positions(acc):
  a=doc['accessors'][acc];v=doc['bufferViews'][a['bufferView']];return np.frombuffer(binary,dtype='<f4',offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*3).reshape(-1,3).copy()
 doc['images']=[];doc['textures']=[];doc['samplers']=[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}];texture_cache={}
 for n in doc['nodes']:
  if n.get('name') not in bindings:continue
  texture=Path(bindings[n['name']]);key=str(texture)
  if key not in texture_cache:
   view=append(texture.read_bytes());idx=len(doc['images']);doc['images'].append({'bufferView':view,'mimeType':'image/png','name':texture.name});texture_cache[key]=len(doc['textures']);doc['textures'].append({'source':idx,'sampler':0})
  for primitive in doc['meshes'][n['mesh']]['primitives']:
   points=positions(primitive['attributes']['POSITION']);low=points[:,:2].min(axis=0);span=np.maximum(points[:,:2].max(axis=0)-low,1e-9);uv=(points[:,:2]-low)/span;uv[:,1]=1-uv[:,1]
   vi=append(uv.astype('<f4').tobytes());ai=len(doc['accessors']);doc['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(uv),'type':'VEC2'});primitive['attributes']['TEXCOORD_0']=ai
   material=len(doc['materials']);doc['materials'].append({'name':'canonical_'+texture.stem,'doubleSided':True,'alphaMode':'BLEND' if 'alpha' in texture.stem else 'OPAQUE','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':texture_cache[key]},'metallicFactor':0,'roughnessFactor':.9}});primitive['material']=material
 if camera:
  e=np.array(camera['eye']);f=np.array(camera['target'])-e;f/=np.linalg.norm(f);r=np.cross(f,[0,0,1]);r/=np.linalg.norm(r);u=np.cross(r,f);m=np.eye(4);m[:3,:3]=np.column_stack([r,u,-f]);m[:3,3]=e
  doc['cameras']=[{'name':'XTY_FIRST_PERSON','type':'perspective','perspective':{'aspectRatio':9/16,'yfov':math.radians(camera['vertical_fov_degrees']),'znear':.06,'zfar':80}}];idx=len(doc['nodes']);doc['nodes'].append({'name':'XTY_FIRST_PERSON','camera':0,'matrix':m.T.reshape(-1).tolist()});doc['nodes'][0]['children'].append(idx)
 while len(binary)%4:binary.append(0)
 doc['buffers'][0]['byteLength']=len(binary);encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
 path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(binary),0x004E4942)+binary)
 return {'embedded_textures':len(texture_cache),'bound_nodes':list(bindings),'texture_render_review':'pending; CPU preview is untextured geometry'}

def make_scenes(c):
 from tools.scene_blockouts import Stage, camera_clipped_scene
 from tools.asset_library import node,mat,box,write_glb,render
 records={a['id']:a for a in json.loads((ROOT/'production/asset-library/catalog-v1.json').read_text())['assets']}
 def plane(s,name,texture,x,y,z=.7408,old=False):
  # Cut corner is geometry, not black ink. .5mm sheet; decal 0.3mm above top.
  vertices=np.array([[-.105,-.15,0],[.105,-.15,0],[.105,.15,0],[-.069,.15,0],[-.105,.1095,0]] if old else [[-.105,-.15,0],[.105,-.15,0],[.105,.15,0],[-.105,.15,0]],float)
  faces=np.array([[0,i,i+1] for i in range(1,len(vertices)-1)])
  node(s.model,name,(vertices,faces),(.7,.66,.5),transform=mat((x,y,z)),extras={'canonical_id':name,'texture_source':ref(OUT/'textures'/texture),'surface_contact':'top of paper on desk','not_a_global_asset_registration':True})
  s.bindings[name]=OUT/'textures'/texture
 def stage(key,name,eye,target):
  s=Stage(key,name,'谢听云',(eye,target),records);s.bindings={};s.camera['vertical_fov_degrees']=62
  for y in [-1.5,1.5,4.5,7.5]:
   s.add('AR-FLOOR','floor_'+str(y),(0,y,-.08))
   for x in [-1.25,1.25]:s.add('AR-COLUMN',f'column_{x}_{y}',(x,y,0))
   s.add('AR-BEAM','beam_'+str(y),(0,y,2.8));s.add('AR-ROOF','roof_'+str(y),(0,y,2.8))
  s.add('AR-DESK','desk',(0,1.2,0));return s
 stages=[]
 s=stage('EP02-SET01','核验台：军报、有效图、旧图、封闭锦囊', [0,.02,1.58],[0,1.25,.78])
 for asset,inst,x,y in [('PR-REPORT','report',-.38,1.1),('PR-MAP-NEW','valid_route',0,1.1)]:s.tabletop(asset,inst,x,y)
 plane(s,'report-top','report-canonical.png',-.38,1.1);plane(s,'route-valid-top','route-valid.png',0,1.1)
 plane(s,'route-expired-top','route-expired.png',.36,1.1,old=True)
 s.floor_object('PR-POUCH','sealed_pouch',.36,1.37,.74,support='desk');s.add('PR-SEAL-R','clay_on_cord',(.36,1.322,.91),(90,0,0),support='sealed_pouch_tie')
 plane(s,'seal-stamp-top','yan-stamp-alpha.png',.36,1.37,.9125)
 # Seal decal must be 5cm, not paper-sized.
 s.model['nodes'][-1]['matrix']=mat((.36,1.309,.91),(90,0,0),scale=(.22,.15,1)).tolist()
 s.floor_object('CH-SCRIBE','EP02-PERSON-SCRIBE',.75,2.3,rotation=180);stages.append(s)
 s=stage('EP02-SET02','三名不同身份信使，分开候命与交接', [0,-.3,1.60],[0,2.1,1.12])
 for a,person,x,y in [('CH-MSG-A','EP02-PERSON-MSG-A',-.75,2.5),('CH-MSG-B','EP02-PERSON-MSG-B',.75,3.4),('CH-MSG-C','EP02-PERSON-MSG-C',-.7,4.5)]:s.floor_object(a,person,x,y,rotation=180)
 s.tabletop('PR-MAP-NEW','valid_route',0,1.2);plane(s,'route-valid-top','route-valid.png',0,1.2)
 s.floor_object('PR-POUCH','sealed_pouch',.34,1.2,.74);s.add('PR-SEAL-R','clay_on_cord',(.34,1.152,.91),(90,0,0),support='sealed_pouch_tie');stages.append(s)
 s=stage('EP02-SET03','雨廊追截：落脚接地，无人物相同脸通过宣称', [0,-.5,1.6],[0,4.0,1.15])
 # Foreground desk removed from chase space: use side table at x=-2, outside corridor.
 for inst in s.instances:
  if inst['instance_id']=='desk':inst['position_m']=[-2,1.2,0]
 for nd in s.model['nodes']:
  if nd['name']=='desk':nd['matrix']=mat((-2,1.2,0)).tolist()
 s.floor_object('CH-MSG-A','EP02-PERSON-MSG-A',.4,3.6,rotation=180)
 s.floor_object('CH-MSG-B','EP02-PERSON-MSG-B',-.4,6.4,rotation=180);stages.append(s)
 s=stage('EP02-SET04','回执与落幕：原锦囊不复制，众人到齐', [0,-.3,1.6],[0,2.5,1.15])
 s.tabletop('PR-RECEIPT','receipt',-.2,1.2);plane(s,'receipt-top','paper-substrate.png',-.2,1.2)
 for a,person,x,y in [('CH-MSG-A','EP02-PERSON-MSG-A',-.75,2.5),('CH-MSG-B','EP02-PERSON-MSG-B',.75,2.5),('CH-MSG-C','EP02-PERSON-MSG-C',0,3.6)]:s.floor_object(a,person,x,y,rotation=180)
 stages.append(s)
 results=[]
 for s in stages:
  for n in s.model['nodes']:
   if n['name']=='cloth_packet':n['color']=[.13,.20,.25]
   elif n['name']=='tie':n['color']=[.33,.23,.15]
  directory=OUT/'scenes'/s.key;directory.mkdir(parents=True,exist_ok=True)
  s.model['extras'].update(instances=s.instances,camera=s.camera,canonical_assets='production/ep02-repair-v5/canonical-assets.json',status='pending_human_review')
  p=directory/(s.key+'.glb');write_glb(s.model,p);texture_receipt=embed_glb_textures(p,s.bindings,s.camera)
  cam=s.camera;clipped=camera_clipped_scene(s.model,cam['eye'],cam['target'])
  rr=render(clipped,directory/'pov.png',360,640,cam['eye'],cam['target'],cam['vertical_fov_degrees'],True)
  render(s.model,directory/'diagnostic.png',600,450)
  dump(directory/'scene.json',{'scene_key':s.key,'name':s.model['extras']['name'],'status':'pending_human_review','units':'metre','instances':s.instances,'sources':s.sources,'texture_binding':texture_receipt,'faces':'all library proxies share approximate structure; identity dedup NOT verified','contacts':'floor_object uses actual source bottom bound; hand/prop grasp not solved','limitations':['static representative setup only','no complete full-frame motion evidence','no human review on this source','not registered to global catalog per delegated write scope']})
  dump(directory/'camera.json',cam)
  results.append({'key':s.key,'name':s.model['extras']['name'],'model':ref(p),'scene':ref(directory/'scene.json'),'camera':ref(directory/'camera.json'),'preview':ref(directory/'pov.png'),'diagnostic':ref(directory/'diagnostic.png'),'depth':ref(directory/'pov-depth-mm.png'),'object_ids':ref(directory/'pov-object-ids.png'),'render_receipt':rr,'texture_binding':texture_receipt})
  print('Scene written:',s.key,flush=True)
 return results

def plan(scenes,c):
 timing=json.loads((ROOT/'production/storytelling-v4/audio/EP02-timing.json').read_text());workflow=json.loads((ROOT/'production/workflow-v1.json').read_text());shots={s['key']:s for s in workflow['shots'] if s['episode']==2}
 setups=[1,1,2,2,3,1,3,3,4,3,4]
 beats=[
 ['0–3s：廊下停稳，桌面锦囊闭合。','3–10s：慢俯看绳结与封泥，不拆囊。','10–结束：抬眼等候，保留剪辑尾。'],
 ['0–3s：封泥原位、绳结受力。','3–10s：仅指向结绳，手不穿入囊内。','10–结束：手退出，锦囊保持原位。'],
 ['0–3s：信使A到面前，其他人不复制。','3–11s：听他口述六皇子的处境，不切异地皇宫。','11–结束：目光回到桌上。'],
 ['0–3s：三人一前两后，站位错开。','3–9s：只向A交有效图，B和C候命。','9–结束：先后转身，步行离开；原锦囊仍在台上。'],
 ['0–3s：从本人眼位追上返回者。','3–11s：人物接地停稳后报告口令差异；封泥只是封口证据。','11–结束：叫停众人，回向核验台。'],
 ['0–3s：先看左侧旧图缺角。','3–11s：指出红叉旧渡口；右侧有效图红线绕行。','11–结束：旧图留桌左收回区，不叠成军报。'],
 ['0–3s：追截结束停稳，人物站位固定。','3–12s：询问姓名、封口是否完整与路线，动作不并行。','12–结束：锦囊由原持有人交A；B和C只带口信，不能复制锦囊。'],
 ['0–3s：本人视线沿廊前行，脚步与位移对应。','3–10s：信使先后送回回执，灯由人点亮。','10–结束：回执放台面，不变成地图或封泥。'],
 ['0–3s：最后信使面前停稳。','3–11s：口述册立消息，回执留印，原锦囊不返回复制。','11–结束：收回执，情绪放松。'],
 ['0–3s：两府来客先后步入，互不克隆。','3–9s：在谢听云面前求问麒麟才子，不切异地。','9–结束：看向雨幕，留呼吸。'],
 ['0–3s：三名信使和书吏依次在面前站定。','3–6s：收住当夜故事，不出现制片术语。','6–结束：沿用同一广告原录音，音乐压低，画面保留。']]
 plans=[]
 for row,setup,action in zip(timing,setups,beats):
  key=row['shot'];shot=shots[key];sd=row['scene_duration'];scene_key=f'EP02-SET0{setup}'
  clips=[x['key'] for x in shot['clips']]
  plans.append({'key':key+'-REPAIR-V5','replaces_logical_shot':key,'affected_exact_scopes':clips,'scene_key':scene_key,'duration_seconds':sd,'target_fps':24,'planned_frame_count_including_boundary':math.ceil(sd*24)+1,'mode':'one_continuous_take','narration':row,'narration_source':ref(ROOT/'production/storytelling-v4/audio/EP02-narration.wav'),'action':shot['action_scene'],'camera':{'owner':'谢听云','mode':'first_person','height_m':1.60,'rule':'眼位连贯，不显示自己脸或后背；人物初登场在同一第一人称镜头中留约1秒缓速观察','path_status':'static representative camera plus written motion intention, NOT reviewed full motion'},'beats':action,'canonical_asset_manifest':'production/ep02-repair-v5/canonical-assets.json','prompt_status':'new local treatment only; not written to global prompt; new hash review required','generation_status':'blocked_pending_scope_registration_current_hash_and_human_review','internal_approval':{'status':'pending','reviewer':None},'editable_handles_seconds':[1,1],'voice_matching':'existing story timing kept; do not reorder visuals across narration beats'})
 out={'schema':'langya-long-take-plan-v5','episode':2,'status':'pending_human_review','shots':plans,'total_seconds':sum(x['duration_seconds'] for x in plans),'action_seconds':sum(x['duration_seconds'] for x in plans if x['action']),'duration_strategy':'11 logical continuous takes, 12–18.083 seconds, replaces old 6–9s split; first/last second for edit; live capability must confirm max duration before paid run','generation_model_direction':'Seedance 2.5 480p requested; MiniMax-H3 fallback only on valid scopes; neither capability nor new budget asserted','no_generation_submitted':True,'remaining':['unique face anchors','hand grip/release contact poses','motion and occlusion full-frame validation','global registration by main agent','per-exact-scope internal preflight after current-source user review','price quote and applicable budget confirmation'],'music':c['audio']['music'],'brand_tagline':c['audio']['brand_tagline'],'caption_rule':'no generated or burned subtitles; no title cards; remove inaccurate source text in new picture generation','audio_semantic_flags':[{'shot':'EP02-S05','existing_line':'他手里的封泥，竟和另一人的口令对不上','issue':'seal is tamper evidence, cannot encode or validate spoken passphrase; preserve audio file but label semantic mismatch for main edit decision'},{'shot':'EP02-S09','existing_line':'带回了完整的封印','issue':'visualize intact receipt seal, not original pouch copied back'}]}
 dump(OUT/'long-take-plan.json',out)
 dump(OUT/'long-take-plan.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','title':'EP02 repair long take plan','type':'object','required':['schema','episode','status','shots','no_generation_submitted'],'properties':{'episode':{'const':2},'status':{'const':'pending_human_review'},'no_generation_submitted':{'const':True},'shots':{'type':'array','minItems':11,'maxItems':11,'items':{'type':'object','required':['key','scene_key','duration_seconds','target_fps','generation_status','beats','internal_approval'],'properties':{'target_fps':{'const':24},'duration_seconds':{'type':'number','minimum':10,'maximum':19},'internal_approval':{'type':'object','properties':{'status':{'const':'pending'}}}}}}}})
 manifest={'schema':'langya-ep02-repair-v5','status':'local_proxy_scene_package_pending_human_review','canonical_assets':ref(OUT/'canonical-assets.json'),'long_take_plan':ref(OUT/'long-take-plan.json'),'plan_schema':ref(OUT/'long-take-plan.schema.json'),'scene_count':len(scenes),'scenes':scenes,'source_script':ref(Path(__file__)),'formal_evidence_complete':False,'new_approval_granted':False,'paid_submissions':0,'write_scope':'production/ep02-repair-v5 and tools/ep02_repair_v5.py only','generation_blockers':out['remaining']}
 dump(OUT/'manifest.json',manifest)
 rows=''.join(f'<article><h2>{s["key"]} {html.escape(s["name"])}</h2><a href="scenes/{s["key"]}/{s["key"]}.glb">打开 / 下载带贴图GLB</a> · <a href="scenes/{s["key"]}/scene.json">实体与限制</a> · <a href="scenes/{s["key"]}/camera.json">相机</a><div class="pair"><img src="scenes/{s["key"]}/pov.png"><img src="scenes/{s["key"]}/diagnostic.png"></div><p>左：第一人称几何预览；右：制作诊断图，不作成片镜头。CPU预览没有纹理采样；GLB内含PNG与UV，实际贴图渲染待审核。人物为代理体块，面容未通过。</p></article>' for s in scenes)
 table=''.join(f'<tr><td>{p["replaces_logical_shot"]}</td><td>{p["duration_seconds"]:.3f}s</td><td>{p["scene_key"]}</td><td>{html.escape(" / ".join(p["beats"]))}</td></tr>' for p in plans)
 (OUT/'review.html').write_text('<!doctype html><html lang="zh"><meta charset="UTF-8"><title>第二集修复v5 · 待人工审核</title><style>body{max-width:1200px;margin:40px auto;background:#eee9df;color:#252725;font:17px/1.7 system-ui;padding:0 20px}h1{font-size:36px}article{border-top:1px solid #999;margin-top:36px}.pair{display:flex;gap:20px;align-items:start}.pair img{width:44%;object-fit:contain;background:#d5d8d8}img.board{width:100%}a{color:#594135}td{vertical-align:top;padding:12px;border-bottom:1px solid #ccc}strong{color:#8d302b}</style><h1>第二集修复 v5：真实3D装配与统一道具</h1><p><strong>全部待审核；未提交付费生成，不能称为重绘完成。</strong>4套代表场景 / 11个长段落。没有伪造审批；旧scope通过不能放行新方案。</p><p><a href="canonical-assets.json">共享道具规范</a> · <a href="manifest.json">包清单</a> · <a href="long-take-plan.json">11段计划</a> · <a href="preflight-report.json">实际预检</a></p><h2>唯一参考纹理</h2><p>军报与“燕”印继承第一集实际像素；锦囊载密信，封泥只证封口，路线图单独表示通路。状纸不加军印。</p><img class="board" src="canonical-texture-board.jpg">'+rows+'<h2>长镜头计划（沿用v4声轨）</h2><table><tr><th>镜头</th><th>时长</th><th>装配</th><th>画面动作</th></tr>'+table+'</table><h2>尚待修正</h2><p>三信使与书吏各有独立ID，但旧库脸部体块相同，不能证明人脸去重；尚无独立肖像锚点。手部接触、交接、全帧运镜仍待建模审查。本包是代表静态装配，不是完整动态验收。</p></html>')
 print('Plan / manifest / review.html written',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--canonical-only',action='store_true');args=parser.parse_args()
 c=canonical()
 if not args.canonical_only:plan(make_scenes(c),c)
