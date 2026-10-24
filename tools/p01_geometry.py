"""Deterministic articulated P01 medicine-chest guide. Units: centimetres.

This produces geometry references, never a paid image/video generation request.
"""
from __future__ import annotations
import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

WIDTH, DEPTH, HEIGHT, WALL, LID_THICKNESS = 36.0, 24.0, 18.0, 1.2, 1.0
HINGE_Z = HEIGHT + 0.2


def hinge_axis():
    return ((-WIDTH / 2, DEPTH / 2, HINGE_Z), (WIDTH / 2, DEPTH / 2, HINGE_Z))


def hinge_transform(point, opening_degrees):
    """Rotate about the rear upper X axis; the front edge rises, not translates."""
    x, local_y, local_z = point
    a = math.radians(opening_degrees)
    return (x, DEPTH / 2 + local_y * math.cos(a) + local_z * math.sin(a),
            HINGE_Z - local_y * math.sin(a) + local_z * math.cos(a))


def lid_corners(opening_degrees=100):
    inner = [(-WIDTH / 2, 0, 0), (WIDTH / 2, 0, 0),
             (WIDTH / 2, -DEPTH, 0), (-WIDTH / 2, -DEPTH, 0)]
    return [hinge_transform(p, opening_degrees) for p in inner + [(x, y, LID_THICKNESS) for x, y, _ in inner]]


def lid_inner_normal(opening_degrees=100):
    a = math.radians(opening_degrees)
    return (0, -math.sin(a), -math.cos(a))


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def unit(v):
    n = math.sqrt(dot(v, v))
    return tuple(x / n for x in v)


@dataclass
class Part:
    name: str
    vertices: list
    faces: list
    color: tuple


BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]


def block(name, x0, x1, y0, y1, z0, z1, color):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    return Part(name, v, BOX_FACES, color)


def model(opening_degrees=100):
    wood = (143, 157, 167)
    parts = [
        block('base',-18,18,-12,12,0,WALL,wood),
        block('front_wall',-18,18,-12,-12+WALL,WALL,HEIGHT,wood),
        block('rear_wall',-18,18,12-WALL,12,WALL,HEIGHT,wood),
        block('left_wall',-18,-18+WALL,-12+WALL,12-WALL,WALL,HEIGHT,wood),
        block('right_wall',18-WALL,18,-12+WALL,12-WALL,WALL,HEIGHT,wood),
        Part('lid_shell',lid_corners(opening_degrees),
             [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],(183,194,201)),
    ]
    # A shallow inset shows the lid's inner face without introducing a second lid.
    panel = [(-16,-2,-0.08),(16,-2,-0.08),(16,-22,-0.08),(-16,-22,-0.08)]
    parts.append(Part('lid_inner_panel',[hinge_transform(p,opening_degrees) for p in panel],[(0,1,2,3)],(204,214,219)))
    for i, xc in enumerate((-10.8, 10.8), 1):
        vertices=[];segments=20
        for x in (xc-1.6,xc+1.6):
            for k in range(segments):
                a=2*math.pi*k/segments
                vertices.append((x,12+0.8*math.cos(a),HINGE_Z+0.8*math.sin(a)))
        faces=[tuple(range(segments-1,-1,-1)),tuple(range(segments,2*segments))]
        faces += [(k,(k+1)%segments,(k+1)%segments+segments,k+segments) for k in range(segments)]
        parts.append(Part('hinge_'+str(i),vertices,faces,(164,135,79)))
    return parts


def write_obj(parts, path):
    mtl=path.with_suffix('.mtl'); lines=['# P01 rigid rear-hinge correction; units cm','mtllib '+mtl.name];materials=[];offset=1
    for p in parts:
        lines += ['o '+p.name,'usemtl '+p.name]
        lines += ['v '+' '.join(f'{x:.7f}' for x in v) for v in p.vertices]
        lines += ['f '+' '.join(str(i+offset) for i in face) for face in p.faces]
        materials += ['newmtl '+p.name,'Kd '+' '.join(f'{x/255:.5f}' for x in p.color),'Ka 0.25 0.25 0.25','']
        offset+=len(p.vertices)
    path.write_text('\n'.join(lines)+'\n');mtl.write_text('\n'.join(materials))


def render(parts, path, size=(1080,1920)):
    from PIL import Image,ImageDraw,ImageFilter
    w,h=size;eye=(62,-88,150);target=(0,0,19);forward=unit(sub(target,eye));right=unit(cross(forward,(0,0,1)));up=cross(right,forward)
    def camera(p):
        q=sub(p,eye);z=dot(q,forward)
        return (dot(q,right)/z,-dot(q,up)/z,z)
    points=[camera(v) for p in parts for v in p.vertices];xs=[p[0] for p in points];ys=[p[1] for p in points]
    scale=min((w-160)/(max(xs)-min(xs)),(h-480)/(max(ys)-min(ys)))
    cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
    def project(v):
        x,y,z=camera(v);return (w/2+(x-cx)*scale,h/2+(y-cy)*scale)
    im=Image.new('RGB',size,(238,242,244));shadow=Image.new('RGBA',size,(0,0,0,0));sd=ImageDraw.Draw(shadow)
    for part in parts:
        if part.name=='report_position':continue
        for face in part.faces:
            polygon=[]
            for i in face:
                x,y,z=part.vertices[i];polygon.append(project((x-z*0.24,y+z*0.15,-0.02)))
            sd.polygon(polygon,fill=(34,47,58,20))
    im=Image.alpha_composite(im.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(17))).convert('RGB');draw=ImageDraw.Draw(im)
    faces=[];light=unit((-0.65,-0.7,1.4))
    for part in parts:
        for face in part.faces:
            vs=[part.vertices[i] for i in face];normal=unit(cross(sub(vs[1],vs[0]),sub(vs[2],vs[0])));center=tuple(sum(v[i] for v in vs)/len(vs) for i in range(3))
            if dot(normal,sub(eye,center))<=0:continue
            shade=0.47+0.53*max(0,dot(normal,light));color=tuple(round(c*shade) for c in part.color)
            faces.append((camera(center)[2],[project(v) for v in vs],color))
    for _,polygon,color in sorted(faces,key=lambda x:x[0],reverse=True):
        draw.polygon(polygon,fill=color);draw.line(polygon+[polygon[0]],fill=tuple(max(0,c-25) for c in color),width=2)
    im.save(path)


def review_sheet(clean_path, path, opening_degrees):
    from PIL import Image,ImageDraw,ImageFont,ImageChops
    W,H=1600,1200;im=Image.new('RGB',(W,H),'#f2f4f5');d=ImageDraw.Draw(im)
    font_path='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    title=ImageFont.truetype(font_path,38);text=ImageFont.truetype(font_path,25);small=ImageFont.truetype(font_path,21)
    d.text((55,32),'P01 箱盖结构修正 · 3D 灰模',font=title,fill='#1b2a35')
    d.text((55,89),f'后上沿固定铰链轴旋转；参考开角约 {opening_degrees:g}°。此图用于约束几何，尚未替换写实素材。',font=text,fill='#526573')
    photo=Image.open(clean_path).convert('RGB')
    mask=ImageChops.difference(photo,Image.new('RGB',photo.size,(238,242,244))).convert('L').point(lambda v:255 if v>10 else 0)
    bounds=mask.getbbox()
    if bounds:photo=photo.crop((max(0,bounds[0]-25),max(0,bounds[1]-25),min(photo.width,bounds[2]+25),min(photo.height,bounds[3]+25)))
    photo.thumbnail((760,880),Image.Resampling.LANCZOS);im.paste(photo,(35,180))
    x0,y0=1090,870;s=10.5
    def side(y,z):return(x0-y*s,y0-z*s)
    # Side view looks along the hinge axis. Front of the box is right on this diagram.
    d.polygon([side(-12,0),side(12,0),side(12,18),side(-12,18)],fill='#bac6cf',outline='#435a6b',width=3)
    hinge=side(12,HINGE_Z);a=math.radians(opening_degrees)
    tip=side(12-DEPTH*math.cos(a),HINGE_Z+DEPTH*math.sin(a))
    d.line([hinge,side(-12,HINGE_Z)],fill='#9daab4',width=5)
    d.line([hinge,tip],fill='#147b8b',width=12)
    d.ellipse((hinge[0]-9,hinge[1]-9,hinge[0]+9,hinge[1]+9),fill='#bf8e35')
    d.text((850,180),'侧视机械关系',font=title,fill='#253d4c')
    d.text((850,245),'青色：修正后盖板',font=text,fill='#147b8b')
    d.text((850,290),'灰色：关闭时的水平位置',font=text,fill='#647580')
    d.text((850,335),'金色点：固定后沿转轴',font=text,fill='#8b6326')
    d.arc((hinge[0]-85,hinge[1]-85,hinge[0]+85,hinge[1]+85),start=360-opening_degrees,end=360,fill='#bf8e35',width=3)
    d.text((hinge[0]+75,hinge[1]-112),f'{opening_degrees:g}°',font=text,fill='#8b6326')
    d.text((850,940),f'盖板前沿随旋转抬高约 {DEPTH*math.sin(math.radians(opening_degrees)):.1f} cm',font=text,fill='#253d4c')
    d.text((850,985),'后沿不移动；盖子不能水平悬浮',font=text,fill='#253d4c')
    d.text((850,1030),'箱体、内腔、盖厚、合页分别建模',font=text,fill='#253d4c')
    d.text((55,1130),'建模比例用于修图参考：36 × 24 × 18 cm；尺寸是本次灰模设定，原图材质与军报/旧令由原素材保留。',font=small,fill='#526573')
    im.save(path)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path('production/p01-lid-repair-v2'));parser.add_argument('--angle',type=float,default=100);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    parts=model(args.angle);clean=args.out/'p01-lid-geometry-guide-v2.png';render(parts,clean);write_obj(parts,args.out/'p01-open-lid-v2.obj');review_sheet(clean,args.out/'p01-lid-geometry-review-v2.png',args.angle)
    corners=lid_corners(args.angle);metrics={'units':'cm','dimensions':{'width':WIDTH,'depth':DEPTH,'height':HEIGHT,'wall':WALL,'lid_thickness':LID_THICKNESS},'opening_degrees':args.angle,'hinge_axis':hinge_axis(),'lid_corners':corners,'inner_normal':lid_inner_normal(args.angle),'front_edge_rise':corners[2][2]-corners[1][2],'lid_is_rigid':True,'photo_replacement_generated':False}
    (args.out/'geometry.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'opening_degrees':args.angle,'front_edge_rise_cm':round(metrics['front_edge_rise'],4),'parts':len(parts),'photo_replacement_generated':False},ensure_ascii=False))


if __name__=='__main__':
    main()
