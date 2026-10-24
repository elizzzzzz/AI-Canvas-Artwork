"""Reproducible low-detail 3D proxy library, in metres, +Z up / +Y forward.

Exports real hierarchical GLB meshes and CPU-rendered geometry previews.
No paid generation, no artistic/physics approval, no final character likeness.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, struct
from pathlib import Path
import numpy as np

WOOD=(.31,.22,.15);DARK=(.13,.18,.20);CLOTH=(.28,.35,.37);SKIN=(.64,.51,.42)
IRON=(.25,.28,.29);BRASS=(.57,.43,.21);PAPER=(.75,.72,.62);STONE=(.47,.49,.48)
RED=(.36,.12,.11);SNOW=(.81,.85,.86);JADE=(.18,.36,.35)


def build_catalog():
    c=[]
    def add(id,name,category,recipe,scenes,**kw):
        c.append({'id':id,'name':name,'category':category,'recipe':recipe,'scene_keys':scenes.split(),
                  'source_basis':'剧本、角色/道具锚点及场景清单中的可见实体；尺寸为制作设计值，非实测',
                  'model_status':'proxy_mesh_v1','production_approval':False,**kw})
    actors=[('MCS','梅长苏','SC01 SC03 SC04 SC06 SC07'),('LS','林殊','SC02'),('XTY','谢听云','SC05'),
      ('SCRIBE','书吏','SC03 SC04 SC05 SC06'),('XJR','萧景睿','SC06 SC07'),('ZQY','卓青遥','SC06 SC07'),
      ('GUARD','护卫','SC04 SC06 SC07'),('DRIVER','车夫','SC04 SC06 SC07'),('MEDBOY','药童','SC06 SC07'),
      ('KEEPER','阁中人','SC05'),('MSG-A','信使甲','SC05'),('MSG-B','信使乙','SC05'),('MSG-C','信使丙','SC05'),
      ('RPT-A','来报人甲','SC05 SC07'),('RPT-B','来报人乙','SC05'),('COURIER','送信人','SC03 SC06')]
    for key,name,sc in actors:
        add('CH-'+key,name,'人物','human',sc,character_key=key,designed_height=1.52 if key=='MEDBOY' else 1.74,
            articulation='层级体块；无蒙皮或面容雕刻，动作须后续逐镜头设定')
    for who,name,sc in [('MCS','梅长苏','SC01 SC03 SC04 SC06 SC07'),('LS','林殊','SC02'),('XTY','谢听云','SC05')]:
        for side,label in [('L','左'),('R','右')]:add('HAND-'+who+'-'+side,name+label+'手与袖口','手部','hand',sc,side=side,owner=who)
    add('AN-HORSE','行旅马','动物','horse','SC04 SC06 SC07',articulation='四肢/颈头层级体块，步态未审核')
    equipment=[('ROBE','梅长苏长袍轮廓','robe','SC01 SC03 SC04 SC06 SC07'),('ARMOR','林殊皮甲','armor','SC02'),
      ('HELMET','战盔','helmet','SC02'),('CAPE','密使短披风','cape','SC05'),('BOOTS','靴','boots','SC02 SC04 SC06 SC07'),
      ('BELT','腰带','belt','SC01 SC03 SC04 SC05 SC06 SC07'),('SWORD','佩剑','sword','SC02 SC04 SC06'),
      ('SHIELD','残盾','shield','SC02'),('SCABBARD','剑鞘','scabbard','SC02 SC04 SC06'),('SADDLE','马鞍','saddle','SC04 SC06 SC07'),
      ('BRIDLE','马笼头与缰带','bridle','SC04 SC06 SC07')]
    for key,name,recipe,sc in equipment:add('EQ-'+key,name,'服装装备',recipe,sc)
    props=[('CHEST','药箱','chest','SC04 SC06'),('REPORT','湿损军报','paper','SC02 SC04'),('BACKUP','备用存卷','paper','SC04'),
      ('TOKEN','半枚赤焰旧令','token','SC01 SC03 SC04 SC07'),('FAN','折扇','fan','SC01 SC06'),('MEDBUNDLE','药包','bundle','SC01 SC06'),
      ('CLOUDBOX','云令匣','cloudbox','SC05 SC06'),('POUCH','麒麟锦囊','pouch','SC05'),('SEAL-R','暗红封泥','seal','SC03 SC05'),
      ('SEAL-G','灰白封泥','seal','SC05'),('SEAL-B','墨青封泥','seal','SC05'),('MAP-NEW','有效路线图','paper','SC05 SC06'),
      ('MAP-OLD','过期缺角地图','paper','SC05'),('RECEIPT','送达回执','paper','SC05'),('BADGE','身份木牌','badge','SC03 SC05'),
      ('STAMP','封印印章','stamp','SC03 SC05 SC06'),('INK','印泥盒','ink','SC03 SC05'),('BRUSH','毛笔','brush','SC03 SC05'),
      ('INKSTONE','砚台','inkstone','SC03 SC05'),('ARCHIVEBOX','档案木匣','archivebox','SC03'),('INDEX','索引牌','badge','SC03'),
      ('COMPLAINT','湿损状纸','paper','SC06 SC07'),('PERMIT','入京文牒','paper','SC06 SC07'),('LETTERBOX','新信匣','letterbox','SC03 SC05'),
      ('TIE','文书绳','tie','SC03 SC05 SC06'),('CANDLE','蜡烛','candle','SC01 SC03'),('STAND','烛台','stand','SC01 SC03'),
      ('LANTERN','宫灯','lantern','SC07'),('BOTTLE','药瓶','bottle','SC06'),('HERBS','药材盘','herbs','SC04 SC06'),('JUG','水壶','jug','SC06')]
    for key,name,recipe,sc in props:add('PR-'+key,name,'道具',recipe,sc)
    vehicles=[('CART','木车车体','cart','SC04 SC06 SC07'),('CANOPY','车篷','canopy','SC04 SC06 SC07'),('WHEEL','辐条车轮','wheel','SC04 SC06 SC07'),
      ('AXLE','完整车轴','axle','SC04 SC06'),('AXLE-BROKEN','断裂车轴','broken_axle','SC06'),('BOARD','车厢折叠板','foldboard','SC04'),
      ('DRAWBAR','辕木','drawbar','SC04 SC06'),('REINS','缰绳','reins','SC04 SC06 SC07')]
    for key,name,recipe,sc in vehicles:add('VH-'+key,name,'车马组件',recipe,sc)
    arch=[('WALL','室内墙体','wall','SC01 SC03 SC05'),('FLOOR','木地板','floor','SC01 SC03 SC05'),('BEAM','屋梁','beam','SC01 SC03 SC05 SC06'),
      ('COLUMN','廊柱','column','SC03 SC05'),('ROOF','瓦屋顶模块','roof','SC01 SC03 SC05 SC07'),('WINDOW','格窗','window','SC01 SC03 SC04'),
      ('DOOR','木门','door','SC01 SC03'),('BED','床榻','bed','SC01'),('DESK','长案','desk','SC01 SC03 SC05 SC06'),
      ('CABINET','档案高柜','cabinet','SC03'),('CHAIR','椅凳','chair','SC03 SC05'),('AWNING','路旁雨棚','awning','SC06'),
      ('GATEWALL','城墙','gatewall','SC07'),('GATE','城门门洞','gate','SC07'),('GATELEAF','朱门门扇','gateleaf','SC07'),
      ('LIGHT','宫灯悬架','lightframe','SC07'),('STEP','门槛台阶','step','SC01 SC03 SC05'),('BRIDGE','木桥','bridge','SC05')]
    for key,name,recipe,sc in arch:add('AR-'+key,name,'建筑家具',recipe,sc)
    env=[('DIRT','泥土道路','road','SC04 SC06'),('SNOWROAD','雪道路面','road','SC02 SC04'),('PAVING','湿石板路','paving','SC07'),
      ('SNOWBANK','雪堆','snowbank','SC02 SC04'),('ROCK','山石','rock','SC02 SC04'),('BROKENWOOD','断木','timber','SC02'),
      ('FLAG','残旗与旗杆','flag','SC02 SC04'),('TREE','落叶树体块','tree','SC04'),('BRAZIER','远处火盆','brazier','SC02')]
    for key,name,recipe,sc in env:add('ENV-'+key,name,'道路环境',recipe,sc)
    return c


def scene(name):return {'name':name,'nodes':[],'roots':[],'extras':{'units':'meter','up_axis':'+Z','forward_axis':'+Y','approved_for_generation':False}}
def mat(position=(0,0,0),rotation=(0,0,0),scale=(1,1,1)):
    x,y,z=np.radians(rotation);cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
    rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    m=np.eye(4);m[:3,:3]=(rz@ry@rx)@np.diag(scale);m[:3,3]=position;return m


def node(sc,name,mesh=None,color=STONE,parent=None,transform=None,extras=None):
    i=len(sc['nodes']);sc['nodes'].append({'name':name,'mesh':mesh,'color':list(color),'parent':parent,'matrix':(np.eye(4) if transform is None else transform).tolist(),'extras':extras or {}})
    if parent is None:sc['roots'].append(i)
    return i


def box(size):
    x,y,z=np.array(size)/2
    v=np.array([[-x,-y,-z],[x,-y,-z],[x,y,-z],[-x,y,-z],[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]])
    q=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
    return v,np.array([(a,b,c) for a,b,c,d in q]+[(a,c,d) for a,b,c,d in q])


def cyl(radius,height,top=None,n=12):
    top=radius if top is None else top
    v=[]
    for z,r in [(0,radius),(height,top)]:v += [[r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),z] for i in range(n)]
    v += [[0,0,0],[0,0,height]];f=[]
    for i in range(n):
        j=(i+1)%n;f.extend([(i,j,j+n),(i,j+n,i+n),(2*n,j,i),(2*n+1,i+n,j+n)])
    return np.array(v),np.array(f)


def ellipsoid(size,n=12,rings=6):
    v=[[0,0,-.5*size[2]]]
    for j in range(1,rings):
        phi=math.pi*j/rings
        for i in range(n):
            t=2*math.pi*i/n;v.append([.5*size[0]*math.sin(phi)*math.cos(t),.5*size[1]*math.sin(phi)*math.sin(t),-.5*size[2]*math.cos(phi)])
    v.append([0,0,.5*size[2]]);top=len(v)-1;f=[]
    for i in range(n):f.append((0,1+(i+1)%n,1+i))
    for j in range(rings-2):
        a=1+j*n;b=a+n
        for i in range(n):k=(i+1)%n;f.extend([(a+i,a+k,b+k),(a+i,b+k,b+i)])
    last=1+(rings-2)*n
    for i in range(n):f.append((last+i,last+(i+1)%n,top))
    return np.array(v),np.array(f)


def extrude_polygon(points, thickness):
    count=len(points);v=np.array([[x,y,z] for z in (0,thickness) for x,y in points]);f=[]
    for i in range(1,count-1):f.extend([(0,i+1,i),(count,count+i,count+i+1)])
    for i in range(count):j=(i+1)%count;f.extend([(i,j,j+count),(i,j+count,i+count)])
    return v,np.array(f)


def torus(radius,tube,n=20,m=6):
    v=[];f=[]
    for i in range(n):
        a=2*math.pi*i/n
        for j in range(m):
            b=2*math.pi*j/m;v.append([(radius+tube*math.cos(b))*math.cos(a),(radius+tube*math.cos(b))*math.sin(a),tube*math.sin(b)])
    for i in range(n):
        for j in range(m):
            a=i*m+j;b=((i+1)%n)*m+j;c=((i+1)%n)*m+(j+1)%m;d=i*m+(j+1)%m;f.extend([(a,b,c),(a,c,d)])
    return np.array(v),np.array(f)


def B(sc,name,size,pos=(0,0,0),color=WOOD,parent=None,rot=(0,0,0)):
    return node(sc,name,box(size),color,parent,mat(pos,rot))
def C(sc,name,radius,height,pos=(0,0,0),color=IRON,parent=None,rot=(0,0,0),top=None,n=12):
    return node(sc,name,cyl(radius,height,top,n),color,parent,mat(pos,rot))
def E(sc,name,size,pos=(0,0,0),color=SKIN,parent=None,rot=(0,0,0)):
    return node(sc,name,ellipsoid(size),color,parent,mat(pos,rot))
def rod(sc,name,a,b,r=.01,color=WOOD,parent=None):
    a=np.array(a);b=np.array(b);direction=b-a;length=np.linalg.norm(direction);z=direction/length;tmp=np.array([1.,0,0]) if abs(z[0])<.8 else np.array([0.,1,0]);x=np.cross(tmp,z);x/=np.linalg.norm(x);y=np.cross(z,x);m=np.eye(4);m[:3,:3]=np.stack([x,y,z],axis=1);m[:3,3]=a
    return node(sc,name,cyl(r,length),color,parent,m)
def ring(sc,name,r,t,pos=(0,0,0),color=IRON,parent=None,rot=(0,0,0)):
    return node(sc,name,torus(r,t),color,parent,mat(pos,rot))


def hand(sc,side='R',parent=None):
    sign=-1 if side=='L' else 1
    root=node(sc,'wrist_root',parent=parent)
    C(sc,'forearm',.035,.16,(0,0,-.16),CLOTH,root,top=.045)
    E(sc,'palm',(.085,.035,.10),(0,0,.04),SKIN,root)
    for i,(xx,length) in enumerate([(-.035,.06),(-.018,.083),(0,.09),(.018,.082),(.035,.064)]):
        p=node(sc,'finger_root_'+str(i),parent=root,transform=mat((sign*xx,.001,.075 if i else .035),rotation=(0,-sign*38 if i==0 else 0,0)))
        for j in range(3):
            joint=node(sc,f'finger_{i}_joint_{j}',parent=p,transform=mat((0,0,0 if j==0 else length/3),rotation=(8,0,0)));C(sc,f'finger_{i}_bone_{j}',.008,length/3,(0,0,0),SKIN,joint,top=.006);p=joint
    return root


def human(sc,a):
    h=a.get('designed_height',1.74);factor=h/1.74;key=a.get('character_key','');root=node(sc,'body_root',transform=mat(scale=(factor,)*3));dress=RED if key=='LS' else (CLOTH if key in ['MCS','XJR'] else (.28,.25,.21));
    for side,x in [('L',-.1),('R',.1)]:
        hip=node(sc,'hip_'+side,parent=root,transform=mat((x,0,.84)));C(sc,'thigh_'+side,.07,.4,(0,0,-.4),dress,hip,top=.06);knee=node(sc,'knee_'+side,parent=hip,transform=mat((0,0,-.4)));C(sc,'shin_'+side,.055,.36,(0,0,-.36),DARK,knee,top=.048);E(sc,'boot_'+side,(.13,.25,.12),(0,.045,-.37),DARK,knee)
    C(sc,'robe_skirt',.27,.70,(0,0,.17),dress,root,top=.15)
    E(sc,'torso',(.40,.25,.55),(0,0,1.12),dress,root);C(sc,'neck',.055,.1,(0,0,1.37),SKIN,root)
    head=node(sc,'head_joint',parent=root,transform=mat((0,0,1.58)));E(sc,'head',(.16,.20,.25),color=SKIN,parent=head);E(sc,'hair',(.17,.20,.16),(0,-.005,.10),DARK,head);E(sc,'hair_bun',(.075,.075,.09),(0,-.025,.22),DARK,head)
    E(sc,'nose',(.035,.045,.06),(0,.101,0),SKIN,head)
    for xx in [-.042,.042]:E(sc,'eye',(.018,.013,.009),(xx,.092,.027),(.05,.06,.06),head)
    for side,x in [('L',-.23),('R',.23)]:
        shoulder=node(sc,'shoulder_'+side,parent=root,transform=mat((x,0,1.30),rotation=(0,(-8 if side=='L' else 8),0)));C(sc,'upper_arm_'+side,.065,.28,(0,0,-.28),dress,shoulder,top=.075);elbow=node(sc,'elbow_'+side,parent=shoulder,transform=mat((0,0,-.28)));C(sc,'sleeve_'+side,.057,.27,(0,0,-.27),dress,elbow,top=.065);E(sc,'hand_proxy_'+side,(.065,.045,.11),(0,0,-.31),SKIN,elbow)
    B(sc,'belt',(.34,.27,.035),(0,0,.94),DARK,root)
    if key=='LS':B(sc,'chest_armor',(.35,.1,.4),(0,.14,1.12),IRON,root);E(sc,'helmet',(.23,.24,.18),(0,0,1.74),IRON,root)
    return root


def horse(sc):
    root=node(sc,'horse_root');E(sc,'barrel',(.6,1.4,.72),(0,0,1.16),(.32,.22,.16),root);E(sc,'hindquarters',(.64,.65,.70),(0,-.52,1.15),(.32,.22,.16),root)
    neck=node(sc,'neck_root',parent=root,transform=mat((0,.45,1.18),rotation=(-38,0,0)));E(sc,'neck',(.36,.38,.65),(0,0,.25),WOOD,neck);head=node(sc,'head_root',parent=neck,transform=mat((0,.05,.48)));E(sc,'skull',(.27,.55,.36),(0,.13,0),WOOD,head)
    for x in [-.07,.07]:E(sc,'ear',(.065,.09,.19),(x,.02,.19),WOOD,head);E(sc,'eye',(.032,.035,.032),(x*1.8,.14,.06),DARK,head)
    for i,(x,y) in enumerate([(-.22,-.5),(.22,-.5),(-.22,.48),(.22,.48)]):
        leg=node(sc,'leg_root_'+str(i),parent=root,transform=mat((x,y,1.0)));C(sc,'upper_leg_'+str(i),.062,.47,(0,0,-.47),WOOD,leg,top=.08);k=node(sc,'leg_knee_'+str(i),parent=leg,transform=mat((0,.03,-.47)));C(sc,'lower_leg_'+str(i),.04,.43,(0,0,-.43),WOOD,k,top=.048);B(sc,'hoof_'+str(i),(.11,.15,.10),(0,.02,-.48),DARK,k)
    rod(sc,'tail',(0,-.74,1.30),(0,-.96,.50),.045,DARK,root)


def chest(sc,angle=100,parent=None):
    root=node(sc,'chest_root',parent=parent);w,d,h,t=.36,.24,.18,.012
    B(sc,'chest_base',(w,d,t),(0,0,t/2),WOOD,root)
    for name,size,pos in [('front_wall',(w,t,h-t),(0,-d/2+t/2,(h+t)/2)),('rear_wall',(w,t,h-t),(0,d/2-t/2,(h+t)/2)),('left_wall',(t,d-2*t,h-t),(-w/2+t/2,0,(h+t)/2)),('right_wall',(t,d-2*t,h-t),(w/2-t/2,0,(h+t)/2))]:B(sc,name,size,pos,WOOD,root)
    hinge=node(sc,'lid_hinge_root',parent=root,transform=mat((0,d/2,h+.002),(-angle,0,0)),extras={'joint_type':'revolute','axis':[1,0,0],'opening_degrees':angle,'allowed_degrees':[0,110]})
    B(sc,'lid_board',(w,d,.01),(0,-d/2,.005),WOOD,hinge);B(sc,'lid_inner_frame',(.31,.19,.004),(0,-d/2,-.002),(.38,.28,.19),hinge)
    for x in [-.108,.108]:C(sc,'hinge_barrel',.008,.032,(x-.016,d/2,h+.002),BRASS,root,rot=(0,90,0))
    B(sc,'front_latch',(.025,.006,.035),(0,-.124,.145),BRASS,root)
    B(sc,'lid_latch',(.025,.006,.027),(0,-d,.014),BRASS,hinge)
    return root


def build_asset(a,opening_angle=100):
    sc=scene(a['id']);sc['extras'].update(asset_id=a['id'],name=a['name'],proxy_detail='blockout',designed_dimensions_not_measured=True)
    r=a['recipe'];id=a['id']
    if r=='human':human(sc,a)
    elif r=='hand':hand(sc,a.get('side','R'))
    elif r=='horse':horse(sc)
    elif r=='chest':chest(sc,opening_angle)
    elif r in ('robe','cape','armor'):
        C(sc,'cloth_body',.28,.85,(0,0,.1),CLOTH,top=.16)
        if r=='armor':
            for j in range(5):
                for i in range(5):B(sc,f'lamella_{i}_{j}',(.06,.015,.075),((i-2)*.064,.17,.50+j*.07),IRON)
    elif r=='helmet':
        E(sc,'dome',(.25,.27,.20),(0,0,.13),IRON);ring(sc,'rim',.132,.012,(0,0,.09),IRON);C(sc,'crest',.018,.13,(0,0,.22),RED)
    elif r=='boots':
        for x in [-.09,.09]:E(sc,'boot',(.13,.26,.12),(x,.04,.06),DARK);C(sc,'shaft',.065,.28,(x,0,.10),DARK)
    elif r=='belt':ring(sc,'belt',.17,.02,(0,0,.04),WOOD);B(sc,'buckle',(.06,.015,.04),(0,.18,.04),BRASS)
    elif r in ('sword','scabbard'):
        B(sc,'blade' if r=='sword' else 'sheath',(.038,.012,.72),(0,0,.36),IRON if r=='sword' else WOOD);B(sc,'guard',(.14,.025,.02),(0,0,.73),BRASS);C(sc,'grip',.018,.14,(0,0,.74),DARK)
    elif r=='shield':node(sc,'shield',cyl(.30,.035,n=16),IRON,transform=mat(rotation=(90,0,0)));B(sc,'handle',(.18,.04,.03),(0,-.045,0),WOOD)
    elif r=='saddle':B(sc,'saddle_pad',(.55,.60,.045),(0,0,.10),RED);E(sc,'seat',(.42,.42,.12),(0,0,.15),WOOD)
    elif r in ('bridle','reins','tie'):
        if r=='bridle':
            for x in [-.12,.12]:rod(sc,'cheek_strap',(x,-.12,.05),(x,.32,.28),.009,WOOD)
            ring(sc,'nose_band',.13,.008,(0,.25,.12),WOOD,rot=(90,0,0))
        else:
            for i in [-1,1]:rod(sc,'strap',(i*.06,-.55,.05),(i*.10,.55,.05),.007,WOOD)
    elif r=='paper':
        w,h=(.21,.30) if id not in ('PR-RECEIPT','PR-PERMIT') else (.12,.24)
        # A real thin mesh with a small notch; no generated or illegible story text.
        points=[[-w/2,-h/2],[w/2,-h/2],[w/2,h/2-.025],[w/2-.025,h/2],[-w/2,h/2]];node(sc,'paper_sheet',extrude_polygon(points,.0005),PAPER)
    elif r=='token':
        n=12;points=[[.045*math.cos(math.pi*i/n),.045*math.sin(math.pi*i/n)] for i in range(n+1)];node(sc,'broken_half_token',extrude_polygon(points,.004),IRON);C(sc,'lanyard_eye',.006,.004,(0,.025,.004),BRASS,n=8)
    elif r=='fan':
        for i in range(8):rod(sc,'fan_rib',(0,0,0),(.23*math.sin(i*.08),.23*math.cos(i*.08),.004),.003,WOOD)
    elif r in ('bundle','pouch'):
        E(sc,'cloth_packet',(.15,.12,.10) if r=='bundle' else (.12,.10,.20),(0,0,.07),PAPER if r=='bundle' else JADE);ring(sc,'tie',.042,.004,(0,0,.14),RED)
    elif r in ('cloudbox','archivebox','letterbox'):
        size=(.24,.13,.07) if r!='archivebox' else (.36,.23,.16);B(sc,'box',size,(0,0,size[2]/2),WOOD)
        for x in [-.055,0,.055]:B(sc,'copper_inlay',(.003,size[1],.003),(x,0,size[2]+.001),BRASS)
        if r=='cloudbox':
            for i in range(7):E(sc,'signal_point_'+str(i),(.007,.007,.004),((i-3)*.025,0,size[2]+.004),JADE)
    elif r in ('seal','ink','inkstone','herbs'):
        radius=.025 if r=='seal' else (.12 if r=='herbs' else .055);C(sc,'container',radius,.012,color=RED if id=='PR-SEAL-R' else (PAPER if id=='PR-SEAL-G' else WOOD))
        if r=='herbs':
            for i in range(12):E(sc,'herb',(.025,.01,.014),((i%4-1.5)*.04,(i//4-1)*.045,.019),(.29,.34,.18))
    elif r=='badge':B(sc,'wood_tag',(.045,.012,.13),(0,0,.065),WOOD);C(sc,'strap_hole',.005,.014,(0,-.007,.115),DARK,rot=(90,0,0))
    elif r=='stamp':B(sc,'seal_base',(.05,.05,.025),(0,0,.0125),BRASS);C(sc,'handle',.016,.055,(0,0,.025),WOOD)
    elif r=='brush':C(sc,'shaft',.004,.19,color=WOOD);C(sc,'tip',.004,.03,(0,0,-.03),DARK,top=.001)
    elif r in ('candle','stand','bottle','jug','brazier'):
        if r=='candle':C(sc,'wax',.012,.16,color=PAPER);rod(sc,'wick',(0,0,.16),(0,0,.17),.001,DARK)
        elif r=='stand':C(sc,'base',.055,.014,color=BRASS);C(sc,'stem',.009,.16,(0,0,.014),BRASS);C(sc,'tray',.035,.008,(0,0,.174),BRASS)
        elif r in ('bottle','jug'):
            E(sc,'vessel',(.09,.09,.13) if r=='bottle' else (.18,.18,.25),(0,0,.07 if r=='bottle' else .13),WOOD);C(sc,'neck',.02,.05,(0,0,.11 if r=='bottle' else .24),WOOD)
            if r=='jug':ring(sc,'handle',.07,.01,(.11,0,.18),WOOD,rot=(90,0,0))
        else:
            C(sc,'bowl',.18,.12,(0,0,.40),IRON,top=.25)
            for x,y in [(-.13,-.12),(.13,-.12),(0,.15)]:rod(sc,'leg',(x,y,0),(x,y,.45),.018,IRON)
    elif r=='lantern':
        C(sc,'paper_shade',.16,.42,(0,0,.10),(.65,.24,.14),n=8);C(sc,'top',.19,.025,(0,0,.52),WOOD,n=8);C(sc,'base',.18,.025,(0,0,.075),WOOD,n=8)
        for i in range(8):t=i*math.pi/4;rod(sc,'rib',(.163*math.cos(t),.163*math.sin(t),.1),(.163*math.cos(t),.163*math.sin(t),.52),.008,WOOD)
        ring(sc,'hanging_ring',.025,.005,(0,0,.57),IRON,rot=(90,0,0))
    elif r=='wheel':
        ring(sc,'rim',.48,.035,(0,0,.515),WOOD,rot=(0,90,0));C(sc,'hub',.07,.16,(-.08,0,.515),WOOD,rot=(0,90,0))
        for i in range(12):a=i*math.pi/6;rod(sc,'spoke',(0,0,.515),(0,.46*math.cos(a),.515+.46*math.sin(a)),.014,WOOD)
    elif r in ('axle','broken_axle','drawbar'):
        length=1.55 if r!='drawbar' else 2.4
        if r=='broken_axle':rod(sc,'broken_left',(-length/2,0,.05),(-.04,0,.05),.045);rod(sc,'broken_right',(.02,.02,.07),(length/2,.12,.16),.045)
        else:rod(sc,'beam',(-length/2,0,.05),(length/2,0,.05),.045)
    elif r=='foldboard':
        B(sc,'folding_board',(.62,.40,.035),(0,0,.0175));rod(sc,'brace',(-.2,.16,-.3),(-.2,-.1,0),.012);rod(sc,'brace',(.2,.16,-.3),(.2,-.1,0),.012)
    elif r in ('cart','canopy'):
        if r=='cart':
            B(sc,'bed', (1.10,1.90,.1),(0,0,.69));B(sc,'left_rail',(.06,1.9,.5),(-.55,0,.99));B(sc,'right_rail',(.06,1.9,.5),(.55,0,.99));B(sc,'rear_board',(1.1,.05,.5),(0,-.93,.99));
            for x in [-.47,.47]:rod(sc,'shaft',(x,.3,.6),(x,2.9,.4),.035)
        else:
            for y in [-.8,0,.8]:
                points=[(-.55,y,0),(-.55,y,.9),(-.32,y,1.16),(0,y,1.24),(.32,y,1.16),(.55,y,.9),(.55,y,0)]
                for aa,bb in zip(points,points[1:]):rod(sc,'canopy_arch',aa,bb,.018)
            B(sc,'canvas_roof',(1.1,1.8,.035),(0,0,1.23),CLOTH)
    elif r=='desk':
        B(sc,'tabletop',(1.20,.70,.05),(0,0,.715));
        for x in [-.49,.49]:
            for y in [-.25,.25]:B(sc,'table_leg',(.07,.07,.69),(x,y,.345))
    elif r in ('wall','floor','beam','column','gatewall','step','lightframe','timber'):
        sizes={'wall':(3,.14,2.8),'floor':(3,3,.08),'beam':(3,.18,.23),'column':(.24,.24,2.8),'gatewall':(8,1.2,7),'step':(1.3,.34,.12),'lightframe':(.1,.65,.1),'timber':(.18,1.3,.15)}
        size=sizes[r];B(sc,r,size,(0,0,size[2]/2),STONE if r in ('wall','gatewall','step') else WOOD)
    elif r=='window':
        for x in [-.45,.45]:B(sc,'frame',(.06,.08,1.2),(x,0,.6));
        for z in [0,1.2]:B(sc,'frame',(.96,.08,.06),(0,0,z))
        for x in np.linspace(-.36,.36,7):B(sc,'lattice',(.018,.025,1.1),(x,0,.6))
        for z in np.linspace(.1,1.1,5):B(sc,'lattice',(.84,.025,.018),(0,0,z))
    elif r in ('door','gateleaf'):
        w,h=(.9,2.05) if r=='door' else (2.1,4.5);hinge=node(sc,'door_hinge',extras={'joint_type':'revolute','axis':[0,0,1],'allowed_degrees':[0,100]});B(sc,'door_leaf',(w,.09,h),(w/2,0,h/2),RED if r=='gateleaf' else WOOD,hinge)
        ring(sc,'handle',.045,.009,(w*.8,-.07,h*.48),BRASS,hinge,rot=(90,0,0))
    elif r=='bed':
        B(sc,'platform',(1.35,2.05,.13),(0,0,.30));B(sc,'bedding',(1.25,1.9,.10),(0,0,.42),CLOTH);E(sc,'pillow',(.6,.35,.12),(0,.66,.52),PAPER)
        for x in [-.56,.56]:
            for y in [-.85,.85]:B(sc,'bed_leg',(.1,.1,.3),(x,y,.15))
    elif r=='cabinet':
        B(sc,'back',(1.1,.05,2.15),(0,.24,1.075));
        for x in [-.55,.55]:B(sc,'side',(.05,.5,2.15),(x,0,1.075))
        for z in np.linspace(.04,2.15,7):B(sc,'shelf',(1.1,.5,.04),(0,0,z))
        for i in range(2):B(sc,'door',(.52,.04,2.03),((i-.5)*.55,-.26,1.1))
    elif r=='chair':
        B(sc,'seat',(.42,.42,.045),(0,0,.43));
        for x in [-.16,.16]:
            for y in [-.16,.16]:B(sc,'leg',(.04,.04,.42),(x,y,.21))
        B(sc,'back',(.42,.04,.40),(0,.19,.67))
    elif r in ('roof','awning'):
        if r=='awning':
            for x in [-1.1,1.1]:
                for y in [-.8,.8]:C(sc,'post',.05,2.2,(x,y,0),WOOD)
        B(sc,'roof_left',(1.3,2,.08),(-.6,0,2.4 if r=='awning' else .4),CLOTH if r=='awning' else STONE,rot=(0,-20,0));B(sc,'roof_right',(1.3,2,.08),(.6,0,2.4 if r=='awning' else .4),CLOTH if r=='awning' else STONE,rot=(0,20,0))
    elif r=='gate':
        B(sc,'left_pier',(2.0,1.1,6),(-3,0,3),STONE);B(sc,'right_pier',(2.0,1.1,6),(3,0,3),STONE);B(sc,'lintel',(8,1.1,1.4),(0,0,5.6),STONE)
    elif r=='bridge':
        B(sc,'bridge_deck',(1.8,4,.12),(0,0,.30));
        for x in [-.86,.86]:
            for y in [-1.8,0,1.8]:C(sc,'post',.055,1.0,(x,y,.3),WOOD)
            rod(sc,'rail',(x,-1.9,1.2),(x,1.9,1.2),.05)
    elif r in ('road','paving'):
        if r=='road':B(sc,'roadbed',(3.4,6,.08),(0,0,-.04),SNOW if id=='ENV-SNOWROAD' else (.31,.28,.22))
        else:
            for x in range(5):
                for y in range(7):B(sc,'paving_slab',(.49,.69,.06),((x-2)*.51,(y-3)*.71,-.03),STONE)
    elif r in ('snowbank','rock'):E(sc,r,(1.7,1.15,.6) if r=='snowbank' else (.8,.6,.7),(0,0,.15),SNOW if r=='snowbank' else STONE)
    elif r=='flag':
        rod(sc,'pole',(0,0,0),(0,0,2.3),.025);v=np.array([[0,0,2.2],[.8,0,2.1],[.66,0,1.9],[.86,0,1.68],[0,0,1.66]]);node(sc,'torn_flag',(v,np.array([(0,1,2),(0,2,4),(2,3,4)])),RED)
    elif r=='tree':
        C(sc,'trunk',.13,3.8,color=WOOD,top=.045)
        for a0 in range(6):t=a0*1.05;rod(sc,'branch',(0,0,2.1),(.85*math.cos(t),.85*math.sin(t),3.5),.035)
    else:raise ValueError('No actual model recipe for '+str(r))
    return sc


def world_transforms(sc):
    result=[]
    for n in sc['nodes']:
        m=np.array(n['matrix']);result.append(m if n['parent'] is None else result[n['parent']]@m)
    return result


def scene_triangles(sc):
    tris=[];colors=[];ids=[];transforms=world_transforms(sc)
    for i,(n,m) in enumerate(zip(sc['nodes'],transforms)):
        if n['mesh'] is None:continue
        v,f=n['mesh'];v=(np.c_[v,np.ones(len(v))]@m.T)[:,:3];tri=v[f];tris.extend(tri);colors.extend([n['color']]*len(tri));ids.extend([i+1]*len(tri))
    return np.array(tris,dtype=float),np.array(colors,dtype=float),np.array(ids,dtype=np.uint32)


def write_glb(sc,path):
    data=bytearray();doc={'asset':{'version':'2.0','generator':'Langya local proxy asset builder'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'AUTHOR_Z_UP_TO_GLTF_Y_UP','matrix':mat(rotation=(-90,0,0)).T.reshape(-1).tolist(),'children':[i+1 for i in sc['roots']],'extras':{'authoring_up_axis':'+Z','units':'metre'}}],'meshes':[],'materials':[],'bufferViews':[],'accessors':[],'extras':sc['extras']};material_ids={}
    def accessor(array,kind,component,target,bounds=False):
        while len(data)%4:data.append(0)
        start=len(data);raw=array.tobytes();data.extend(raw);vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(raw),'target':target});entry={'bufferView':vi,'componentType':component,'count':len(array),'type':kind}
        if bounds:entry.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
        ai=len(doc['accessors']);doc['accessors'].append(entry);return ai
    for i,n in enumerate(sc['nodes']):
        nd={'name':n['name'],'matrix':np.array(n['matrix']).T.reshape(-1).tolist(),'extras':n['extras']}
        children=[j+1 for j,c in enumerate(sc['nodes']) if c['parent']==i]
        if children:nd['children']=children
        if n['mesh'] is not None:
            v,f=n['mesh'];p=v[f].reshape(-1,3).astype('<f4');tri=p.reshape(-1,3,3);normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None];normals=np.repeat(normals,3,axis=0).astype('<f4');color=tuple(n['color'])
            if color not in material_ids:
                material_ids[color]=len(doc['materials']);doc['materials'].append({'name':'proxy_'+'_'.join(str(round(c*255)) for c in color),'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':list(color)+[1],'metallicFactor':0.05,'roughnessFactor':0.8}})
            mesh=len(doc['meshes']);doc['meshes'].append({'name':n['name'],'primitives':[{'attributes':{'POSITION':accessor(p,'VEC3',5126,34962,True),'NORMAL':accessor(normals,'VEC3',5126,34962)},'material':material_ids[color]}]});nd['mesh']=mesh
        doc['nodes'].append(nd)
    while len(data)%4:data.append(0)
    doc['buffers']=[{'byteLength':len(data)}];encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    encoded+=b' '*((-len(encoded))%4);total=12+8+len(encoded)+8+len(data)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(data),0x004E4942)+data)


def attach(target,src,instance_id,position=(0,0,0),rotation=(0,0,0),scale=(1,1,1)):
    base=node(target,instance_id,transform=mat(position,rotation,scale),extras={'instance_id':instance_id,'asset_id':src['extras']['asset_id']});offset=len(target['nodes'])
    for n in src['nodes']:
        clone=copy.deepcopy(n);clone['parent']=base if n['parent'] is None else offset+n['parent'];target['nodes'].append(clone)
    return base


def p01_assembly():
    cat={a['id']:a for a in build_catalog()};sc=scene('P01 full relation blockout');instances=[]
    def put(a,id,p=(0,0,0),rot=(0,0,0),scale=(1,1,1)):
        attach(sc,build_asset(cat[a]),id,p,rot,scale);instances.append({'instance_id':id,'asset_id':a,'position_m':list(p),'rotation_degrees':list(rot),'scale':list(scale)})
    put('AR-DESK','table_01');put('PR-CHEST','chest_01',(0,0,.74));put('PR-REPORT','report_01',(0,0,.752),scale=(.84,.57,1));put('PR-TOKEN','token_01',(.29,-.17,.74));put('PR-HERBS','herbs_01',(-.36,.15,.742))
    # Visible hands are explicit scene instances. Contact is provisional, not claimed solved.
    put('HAND-MCS-L','hand_left',(-.19,-.16,.91),(-90,0,-15));put('HAND-MCS-R','hand_right',(.22,.13,1.08),(-35,-20,0))
    put('ENV-PAVING','ground_01',(0,0,-.02));put('AR-WALL','back_wall',(0,1.8,0))
    sc['extras'].update(instances=instances,assembly_checks={'tabletop_z':.74,'chest_bottom_z':.74,'report_bottom_z':.752,'chest_inner_floor_z':.752,'hinge_world_z':.922,'hand_contact':'not_solved_requires_pose_review','occlusion':'not_reviewed','opening_degrees':100},camera={'eye':[0,-.55,1.65],'target':[0,0,.91],'vertical_fov_degrees':72,'aspect':9/16},approved_for_generation=False)
    return sc


def render(sc,path,width=240,height=300,eye=None,target=None,fov=42,save_channels=False):
    from PIL import Image
    tris,colors,ids=scene_triangles(sc);lo=tris.min(axis=(0,1));hi=tris.max(axis=(0,1));center=(lo+hi)/2;extent=max(hi-lo)
    automatic=eye is None
    if automatic:eye=center+np.array([1.35,1.9 if sc['name'].startswith(('CH-','AN-')) else -1.9,1.05])*max(extent,.05);target=center
    eye=np.array(eye);target=np.array(target);forward=target-eye;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1.]);right/=np.linalg.norm(right);up=np.cross(right,forward);basis=np.stack([right,up,forward],axis=1);camera=(tris-eye)@basis
    image=np.full((height,width,3),[232,237,238],dtype=np.uint8);zbuf=np.full((height,width),np.inf);idbuf=np.zeros((height,width),np.uint32);f=height/(2*math.tan(math.radians(fov)/2));light=np.array([-.5,-.7,1.2]);light/=np.linalg.norm(light)
    offset_x=width/2;offset_y=height/2
    if automatic:
        xy=camera[:,:,:2]/camera[:,:,2:3];lo2=xy.min(axis=(0,1));hi2=xy.max(axis=(0,1));f=min((width-24)/(hi2[0]-lo2[0]),(height-24)/(hi2[1]-lo2[1]));offset_x=width/2-f*(lo2[0]+hi2[0])/2;offset_y=height/2+f*(lo2[1]+hi2[1])/2;fov=math.degrees(2*math.atan(height/(2*f)))
    normals=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None];shade=.52+.48*np.abs(normals@light)
    for n,t in enumerate(camera):
        if np.any(t[:,2]<=.001):continue
        projected=np.stack([offset_x+f*t[:,0]/t[:,2],offset_y-f*t[:,1]/t[:,2]],axis=1);a,b,c=projected;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:continue
        x0=max(0,math.floor(projected[:,0].min()));x1=min(width-1,math.ceil(projected[:,0].max()));y0=max(0,math.floor(projected[:,1].min()));y1=min(height-1,math.ceil(projected[:,1].max()))
        if x1<x0 or y1<y0:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w2=1-w0-w1;inside=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6);inv=w0/t[0,2]+w1/t[1,2]+w2/t[2,2];depth=np.divide(1,inv,out=np.full_like(inv,np.inf),where=inv>0);sub=zbuf[y0:y1+1,x0:x1+1];hit=inside&(depth<sub);sub[hit]=depth[hit];idbuf[y0:y1+1,x0:x1+1][hit]=ids[n];image[y0:y1+1,x0:x1+1][hit]=np.clip(colors[n]*shade[n]*255,0,255).astype(np.uint8)
    path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(image).save(path)
    if save_channels:
        valid=np.isfinite(zbuf);millimetres=np.where(valid,np.minimum(zbuf*1000,65534),0).astype(np.uint16);Image.fromarray(millimetres).save(path.with_name(path.stem+'-depth-mm.png'));rgb=np.stack([idbuf&255,(idbuf>>8)&255,(idbuf>>16)&255],axis=2).astype(np.uint8);Image.fromarray(rgb).save(path.with_name(path.stem+'-object-ids.png'));np.save(path.with_name(path.stem+'-depth-m.npy'),zbuf.astype(np.float32));mapping={}
        for i,n in enumerate(sc['nodes']):
            if n['mesh'] is None:continue
            parent=i;instance_id=None;asset_id=sc['extras'].get('asset_id')
            while parent is not None:
                ex=sc['nodes'][parent].get('extras',{})
                if ex.get('instance_id'):instance_id=ex['instance_id'];asset_id=ex.get('asset_id');break
                parent=sc['nodes'][parent]['parent']
            mapping[str(i+1)]={'part_name':n['name'],'instance_id':instance_id,'asset_id':asset_id}
        path.with_name(path.stem+'-object-ids.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    return {'eye':eye.tolist(),'target':target.tolist(),'vertical_fov_degrees':fov,'width':width,'height':height,'visible_object_ids':[int(i) for i in np.unique(idbuf) if i],'depth_units':'metres (.npy); millimetres (16-bit png), zero png background'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path('production/asset-library'));parser.add_argument('--skip-previews',action='store_true');args=parser.parse_args();out=args.out;cat=build_catalog();index=[]
    for i,a in enumerate(cat):
        sc=build_asset(a);path=out/'models'/(a['id']+'.glb');write_glb(sc,path);tri,_,_=scene_triangles(sc);bounds=[tri.min(axis=(0,1)).tolist(),tri.max(axis=(0,1)).tolist()];record={**a,'file':'models/'+path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangle_count':len(tri),'dimensions_m':(np.array(bounds[1])-bounds[0]).round(6).tolist(),'bounds_m':bounds,'units':'metre','authoring_up_axis':'+Z','glb_export_up_axis':'+Y','material_status':'flat_proxy_colors','preview':'previews/'+a['id']+'.png','limitations':['代理体块，未经最终美术和逐镜头几何验收','人物无精确面容雕刻与蒙皮；动物步态/碰撞尚未求解']}
        if not args.skip_previews:render(sc,out/record['preview'],180,240)
        index.append(record)
        if (i+1)%20==0:print('MODELED',i+1,'of',len(cat),flush=True)
    sc=p01_assembly();write_glb(sc,out/'scenes/P01-assembly-v1.glb');(out/'scenes/P01-assembly-v1.json').write_text(json.dumps(sc['extras'],ensure_ascii=False,indent=2)+'\n');cam=sc['extras']['camera']
    if not args.skip_previews:
        camera_receipt=render(sc,out/'scenes/P01-pov-v1.png',540,960,cam['eye'],cam['target'],cam['vertical_fov_degrees'],True);(out/'scenes/P01-camera-v1.json').write_text(json.dumps(camera_receipt,ensure_ascii=False,indent=2)+'\n');render(sc,out/'scenes/P01-diagnostic-v1.png',900,700,save_channels=True)
    (out/'catalog-v1.json').write_text(json.dumps({'version':1,'asset_count':len(index),'units':'metre','status':'proxy_meshes_built_not_approved','generated_with':'tools/asset_library.py','assets':index,'p01_assembly':'scenes/P01-assembly-v1.glb'},ensure_ascii=False,indent=2)+'\n');print('DONE',len(index),'actual reusable GLB assets; P01 assembly remains unapproved',flush=True)


if __name__=='__main__':main()
