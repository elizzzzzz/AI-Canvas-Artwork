"""Assemble seven canonical scene drafts from the versioned GLBs, without approval.

The portrait views are representative static blocking, not 67 reviewed clip cameras.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tools.asset_library import scene, attach, scene_triangles, write_glb, render, mat

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'production/asset-library'
OUT = ROOT / 'production/scene-blockouts'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}


def load_glb_asset(record):
    """Read the actual exported local mesh, keeping the author's metre/Z-up frame."""
    path = LIB / record['file']
    raw = path.read_bytes()
    if digest(path) != record['sha256']:
        raise ValueError('Library mesh changed: ' + record['id'])
    magic, version, length = struct.unpack_from('<4sII', raw)
    if (magic, version, length) != (b'glTF', 2, len(raw)):
        raise ValueError('Invalid GLB header')
    size, tag = struct.unpack_from('<II', raw, 12)
    if tag != 0x4E4F534A:
        raise ValueError('Missing GLB JSON chunk')
    doc = json.loads(raw[20:20+size])
    binary_size, binary_tag = struct.unpack_from('<II', raw, 20+size)
    start = 28+size
    if binary_tag != 0x004E4942 or start+binary_size != len(raw):
        raise ValueError('Invalid embedded GLB buffer')
    if doc['nodes'][0]['name'] != 'AUTHOR_Z_UP_TO_GLTF_Y_UP':
        raise ValueError('Expected library coordinate root')
    def positions(index):
        acc = doc['accessors'][index]
        view = doc['bufferViews'][acc['bufferView']]
        if acc['componentType'] != 5126 or acc['type'] != 'VEC3' or view.get('byteStride'):
            raise ValueError('Unsupported library accessor layout')
        offset = view.get('byteOffset', 0)+acc.get('byteOffset', 0)
        if offset+acc['count']*12 > binary_size:
            raise ValueError('GLB accessor outside buffer')
        return np.frombuffer(raw, dtype='<f4', count=acc['count']*3, offset=start+offset).reshape(-1,3).astype(float)
    parents = {child: parent for parent,n in enumerate(doc['nodes']) for child in n.get('children', [])}
    result = scene(record['id'])
    result['extras'].update(asset_id=record['id'], source_glb=record['file'], source_sha256=record['sha256'])
    for index,n in enumerate(doc['nodes'][1:], 1):
        mesh = None
        color = (.5,.5,.5)
        if 'mesh' in n:
            primitives = doc['meshes'][n['mesh']]['primitives']
            if len(primitives) != 1 or primitives[0].get('mode',4) != 4 or 'indices' in primitives[0]:
                raise ValueError('Unsupported library primitive')
            primitive = primitives[0]
            vertices = positions(primitive['attributes']['POSITION'])
            if len(vertices)%3:
                raise ValueError('Non-triangular library primitive')
            mesh = (vertices, np.arange(len(vertices)).reshape(-1,3))
            color = tuple(doc['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor'][:3])
        parent = parents.get(index,0)
        result['nodes'].append({'name': n.get('name','part'), 'parent': None if parent==0 else parent-1,
            'matrix': np.array(n.get('matrix',np.eye(4).T.flatten())).reshape(4,4).T.tolist(),
            'mesh': mesh, 'color':color, 'extras':copy.deepcopy(n.get('extras',{}))})
        if parent==0:
            result['roots'].append(index-1)
    return result


def clip_near_polygon(points, eye, forward, near):
    output = []
    for a,b in zip(points, points[1:]+points[:1]):
        da,db = np.dot(a-eye,forward)-near, np.dot(b-eye,forward)-near
        if da >= 0:
            output.append(a)
        if (da>=0) != (db>=0):
            output.append(a+(b-a)*(da/(da-db)))
    return output


def camera_clipped_scene(source, eye, target, near=.06):
    """Clip crossing triangles rather than dropping an entire wall or road face."""
    eye=np.asarray(eye,float);forward=np.asarray(target,float)-eye;forward/=np.linalg.norm(forward)
    triangles,_,node_ids = scene_triangles(source)
    result=copy.deepcopy(source)
    for n in result['nodes']:
        n['matrix']=np.eye(4).tolist();n['mesh']=None
    for node_id in np.unique(node_ids):
        values=[]
        for tri in triangles[node_ids==node_id]:
            polygon=clip_near_polygon(list(tri),eye,forward,near)
            for k in range(1,len(polygon)-1):
                t=np.array([polygon[0],polygon[k],polygon[k+1]])
                if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-10:
                    values.extend(t)
        if values:
            vertices=np.array(values)
            result['nodes'][int(node_id)-1]['mesh']=(vertices,np.arange(len(vertices)).reshape(-1,3))
    return result


class Stage:
    def __init__(self,key,name,owner,camera,records):
        self.key=key;self.records=records;self.model=scene(key)
        self.instances=[];self.supports=[];self.sources={};self.cache={}
        self.camera={'pov_owner':owner,'mode':'first_person','units':'metre','up_axis':'+Z',
            'eye':camera[0],'target':camera[1],'vertical_fov_degrees':72,'aspect_ratio':'9:16',
            'near_clip_m':.06,'status':'representative_static_camera_pending_review',
            'path_status':'not_animated_no_clip_motion_approval'}
        self.model['extras'].update(scene_key=key,name=name,units='metre',up_axis='+Z',
            forward_axis='+Y',approved_for_generation=False)
    def add(self,asset,instance,position=(0,0,0),rotation=(0,0,0),scale=(1,1,1),support=None):
        if any(x['instance_id']==instance for x in self.instances):raise ValueError('Duplicate instance')
        rec=self.records[asset]
        if asset not in self.cache:self.cache[asset]=load_glb_asset(rec)
        attach(self.model,self.cache[asset],instance,position,rotation,scale)
        self.instances.append({'instance_id':instance,'asset_id':asset,'position_m':list(position),
           'rotation_degrees':list(rotation),'scale':list(scale),'local_forward':'+Y','support':support})
        self.sources[asset]={'path':'production/asset-library/'+rec['file'],'sha256':rec['sha256']}
    def floor_object(self,asset,instance,x,y,z=0,rotation=0,support='ground'):
        bottom=self.records[asset]['bounds_m'][0][2]
        self.add(asset,instance,(x,y,z-bottom),(0,0,rotation),support=support)
    def tabletop(self,asset,instance,x,y,z=.74):
        self.floor_object(asset,instance,x,y,z,support='desk_top')
    def room(self):
        for x in [-1.5,1.5]:
            for y in [-1.5,1.5]:self.add('AR-FLOOR',f'floor_{x}_{y}',(x,y,-.08))
        for x in [-3,3]:self.add('AR-WALL',f'side_wall_{x}',(x,0,0),(0,0,90),(2,1,1))
        # Real aperture: separate masonry portions around a 1.0 x 1.2 m window.
        for x in [-1.75,1.75]:self.add('AR-WALL',f'rear_wall_{x}',(x,3,0),scale=(2.5/3,1,1))
        self.add('AR-WALL','window_sill_wall',(0,3,0),scale=(1/3,1,.9/2.8))
        self.add('AR-WALL','window_header_wall',(0,3,2.1),scale=(1/3,1,.7/2.8))
        self.add('AR-WINDOW','rear_window',(0,3,.9))
        for y in [-1.5,1.5]:self.add('AR-BEAM',f'beam_{y}',(0,y,2.8),scale=(2,1,1))
    def road(self,snow=False):
        for x in [-1.7,1.7]:
            for y in [-3,3,9]:self.add('ENV-SNOWROAD' if snow else 'ENV-DIRT',f'road_{x}_{y}',(x,y,0))
        for x in [-3.8,3.8]:
            for y in [1,6,11]:self.floor_object('ENV-SNOWBANK' if snow else 'ENV-ROCK',f'edge_{x}_{y}',x,y)
    def cart(self,x,y,horse=True):
        self.add('VH-CART','cart_body',(x,y,0),support='axle_01')
        for side,dx in [('left',-.68),('right',.68)]:self.add('VH-WHEEL','wheel_'+side,(x+dx,y,0),support='ground')
        self.add('VH-AXLE','axle_01',(x,y,.465),support='wheel_left,wheel_right')
        self.add('VH-CANOPY','cart_canopy',(x,y,.74),support='cart_body')
        if horse:
            self.floor_object('AN-HORSE','horse_01',x,y+4.1)
            self.add('EQ-SADDLE','saddle_01',(x,y+4.1,1.44),support='horse_01')
        self.supports.append({'kind':'wheel_axle_datum','wheel_center_z_m':.515,'axle_center_z_m':.515,
                              'verification':'datum_equal_only_harness_and_surface_contacts_pending'})
    def hand(self,owner,x,y,z):
        self.add('HAND-'+owner+'-R','pov_right_hand',(x,y,z),(-65,0,-8))


def build_stages():
    cat=json.loads((LIB/'catalog-v1.json').read_text());r={a['id']:a for a in cat['assets']}
    stages=[]
    s=Stage('SC01','梅长苏卧房','梅长苏',([0,-.85,1.18],[0,.55,.80]),r);s.room()
    s.add('AR-BED','bed_01',(-1.45,-.2,0));s.add('AR-DESK','desk_01',(0,.55,0))
    s.tabletop('PR-TOKEN','old_token',0,.35);s.tabletop('PR-FAN','folded_fan',.22,.55)
    s.tabletop('PR-STAND','candle_stand',-.36,.62);s.tabletop('PR-CANDLE','candle',-.36,.62,.922)
    s.hand('MCS',.10,-.45,.72);stages.append(s)
    s=Stage('SC02','梅岭雪原','林殊',([0,-1.6,1.68],[0,2,.85]),r);s.road(True)
    s.floor_object('ENV-FLAG','torn_flag',1.1,3);s.floor_object('ENV-BROKENWOOD','broken_timber',-1.2,1)
    for k,(x,y) in enumerate([(-.3,.4),(0,.65),(.34,.45)]):s.floor_object('PR-REPORT','report_'+str(k),x,y,.015)
    s.floor_object('PR-TOKEN','military_token',.1,.2,.02);s.floor_object('ENV-BRAZIER','brazier',-1.5,4)
    s.hand('LS',.13,-1.05,1.12);stages.append(s)
    s=Stage('SC03','江左盟旧档室','梅长苏',([0,-.1,1.60],[0,1.2,.94]),r);s.room()
    s.add('AR-DESK','desk_01',(0,1.2,0))
    for x in [-1.9,1.9]:s.floor_object('AR-CABINET',f'cabinet_{x}',x,2.3,rotation=0)
    for k,a in enumerate(['PR-TOKEN','PR-INDEX','PR-LETTERBOX','PR-SEAL-R']):s.tabletop(a,'table_'+a,-.4+k*.25,1.17)
    s.floor_object('CH-SCRIBE','scribe_01',.65,2.5,rotation=180)
    s.floor_object('CH-COURIER','courier_01',-1.1,1.8,rotation=160)
    s.hand('MCS',.12,.35,1.03);stages.append(s)
    s=Stage('SC04','雪路与追车','梅长苏',([-1.0,-1.0,1.60],[.2,3.8,1.0]),r);s.road(True);s.cart(.55,2.6)
    s.add('PR-CHEST','medicine_chest',(.55,2.15,.74),support='cart_body')
    s.add('PR-REPORT','chest_report',(.55,2.15,.752),scale=(.84,.57,1),support='medicine_chest')
    s.add('PR-BACKUP','backup_scroll',(.65,2.8,.74),support='cart_body')
    s.floor_object('CH-SCRIBE','scribe_01',-.7,3.6,rotation=160)
    s.floor_object('ENV-TREE','road_tree',-3.5,8);stages.append(s)
    s=Stage('SC05','琅琊阁雨廊','谢听云',([0,-.5,1.60],[0,1.3,1.0]),r)
    for y in [0,3,6]:
        s.add('AR-FLOOR',f'floor_{y}',(0,y,-.08))
        for x in [-1.25,1.25]:s.add('AR-COLUMN',f'column_{x}_{y}',(x,y,0))
        s.add('AR-BEAM',f'beam_{y}',(0,y,2.8));s.add('AR-ROOF',f'roof_{y}',(0,y,2.8),scale=(1,1.5,1))
    s.add('AR-DESK','desk_01',(0,1.2,0))
    for a,x,y in [('PR-MAP-NEW',-.1,1.1),('PR-POUCH',-.4,1.35),('PR-CLOUDBOX',.28,1.35),('PR-RECEIPT',.28,1.05)]:s.tabletop(a,a,x,y)
    for k,c in enumerate(['R','G','B']):s.tabletop('PR-SEAL-'+c,'seal_'+c,-.25+k*.12,1.4)
    for a,x,y in [('CH-MSG-A',-.85,2.5),('CH-MSG-B',.85,2.5)]:s.floor_object(a,a,x,y,rotation=180)
    s.hand('XTY',.15,.12,1.0);stages.append(s)
    s=Stage('SC06','入京雨路','梅长苏',([-.5,-.7,1.60],[0,1.2,1.0]),r);s.road();s.add('AR-AWNING','road_awning',(-.25,1.25,0))
    s.add('AR-DESK','desk_01',(-.25,1.2,0))
    for a,x,y in [('PR-COMPLAINT',-.5,1.1),('PR-MEDBUNDLE',-.16,1.4),('PR-MAP-NEW',.03,1.12),('PR-CLOUDBOX',-.5,1.43)]:s.tabletop(a,a,x,y)
    s.floor_object('CH-ZQY','zhuo_01',-.40,2.6,rotation=170);s.floor_object('CH-XJR','jingrui_01',.65,2.5,rotation=190)
    s.cart(2.35,4);s.hand('MCS',-.15,-.12,1.0);stages.append(s)
    s=Stage('SC07','金陵城门','梅长苏',([0,0,1.65],[0,6,2.0]),r)
    for y in [0,4,8,12]:s.add('ENV-PAVING','paving_'+str(y),(0,y,0),scale=(2.5,1,1))
    s.add('AR-GATE','gate_opening',(0,7,0))
    for x in [-8,8]:s.add('AR-GATEWALL','wall_'+str(x),(x,7,0))
    for x in [-2,2]:s.add('AR-GATELEAF','open_leaf_'+str(x),(x,7,0),(0,0,90))
    for x in [-3,3]:
        s.add('AR-LIGHT','lantern_bracket_'+str(x),(x,6.1,3.4))
        s.add('PR-LANTERN','lantern_'+str(x),(x,5.9,2.85),support='lantern_bracket_'+str(x))
    s.floor_object('CH-XJR','jingrui_01',-.9,3.5,rotation=170);s.floor_object('CH-COURIER','reporter_01',.95,4.0,rotation=190)
    s.hand('MCS',.10,.65,1.25);stages.append(s)
    return stages


def build(output=OUT):
    output.mkdir(parents=True,exist_ok=True)
    entries=[]
    for s in build_stages():
        directory=output/s.key;directory.mkdir(parents=True,exist_ok=True)
        s.model['extras'].update(instances=s.instances,camera=s.camera)
        model=directory/(s.key+'.glb');write_glb(s.model,model)
        metadata={'scene_key':s.key,'name':s.model['extras']['name'],'status':'assembled_proxy_draft_pending_review',
            'approved_for_generation':False,'units':'metre','up_axis':'+Z','forward_axis':'+Y',
            'instances':s.instances,'source_assets':s.sources,'datum_observations':s.supports,
            'scope':'one_representative_static_setup_not_all_subspaces_or_67_clip_paths',
            'remaining':['precise_faces_and_costumes','hand_and_prop_contacts','harness_and_animal_motion',
                         'collision_and_occlusion_review','all_subspaces_and_clip_camera_paths','full_frame_motion_review','named_human_approval']}
        meta=directory/(s.key+'-scene.json');meta.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        cam=s.camera;clipped=camera_clipped_scene(s.model,cam['eye'],cam['target'],cam['near_clip_m'])
        receipt=render(clipped,directory/(s.key+'-pov.png'),360,640,cam['eye'],cam['target'],cam['vertical_fov_degrees'],True)
        camera_path=directory/(s.key+'-camera.json');camera_path.write_text(json.dumps({**cam,'render':receipt},ensure_ascii=False,indent=2)+'\n')
        render(s.model,directory/(s.key+'-diagnostic.png'),640,480)
        files={label:reference(directory/(s.key+suffix)) for label,suffix in
               [('model','.glb'),('scene','-scene.json'),('camera','-camera.json'),('preview','-pov.png'),
                ('depth','-pov-depth-mm.png'),('object_ids','-pov-object-ids.png'),('id_legend','-pov-object-ids.json'),('diagnostic','-diagnostic.png')]}
        entries.append({'scene_key':s.key,'name':metadata['name'],'status':metadata['status'],
                        'pov_owner':cam['pov_owner'],'instance_count':len(s.instances),'files':files,
                        'source_assets':s.sources,'approval':None})
        print(s.key,'assembled',len(s.instances),'instances',flush=True)
    manifest={'version':1,'scene_count':len(entries),'approved_count':0,
              'limitation':'Static representative drafts. No 67-clip camera or collision approval.', 'scenes':entries}
    (output/'manifest-v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    # A review sheet uses the actual generated portrait previews, not imagined scenery.
    sheet=Image.new('RGB',(4*300+40,2*610+100),'#182524');d=ImageDraw.Draw(sheet)
    font_path='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    font=ImageFont.truetype(font_path,19);heading=ImageFont.truetype(font_path,28)
    d.text((20,20),'七个主场景 / 第一人称组合草模 · 尚未验收',font=heading,fill='#e6eee9')
    for i,e in enumerate(entries):
        x=20+(i%4)*300;y=80+(i//4)*610
        im=Image.open(ROOT/e['files']['preview']['path']).resize((288,512))
        sheet.paste(im,(x,y));d.text((x,y+521),e['scene_key']+' '+e['name'],font=font,fill='#dfebe5')
        d.text((x,y+551),e['pov_owner']+'主观 · 机位与接触待核',font=font,fill='#a3c3b4')
    sheet.save(output/'scene-overview-v1.jpg',quality=92)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args();build()
