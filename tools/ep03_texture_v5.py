"""Embed one exact canonical raster per prop in existing EP03 GLBs.
No AI raster generation; map and complaint retain distinct semantic roles.
"""
import hashlib,json,pathlib,struct
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'production/ep03-repair-v5'
def patch(p):
 raw=p.read_bytes();n,tag=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);bn,btag=struct.unpack_from('<II',raw,20+n);binary=bytearray(raw[28+n:28+n+bn])
 parents={c:i for i,node in enumerate(doc['nodes']) for c in node.get('children',[])}
 texts={'PR-MAP-NEW':R/'production/ep02-repair-v5/textures/route-valid.png','PR-COMPLAINT':R/'production/ep02-repair-v5/textures/paper-substrate.png'}
 patched=[];texture_ids={};doc.setdefault('images',[]);doc.setdefault('textures',[]);doc.setdefault('samplers',[])
 def append(blob):
  while len(binary)%4:binary.append(0)
  off=len(binary);binary.extend(blob);i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(blob)});return i
 for idx,node in enumerate(doc['nodes']):
  if 'mesh' not in node or node.get('name')!='paper_sheet':continue
  ancestor=idx;aid=None
  while ancestor in parents:
   ancestor=parents[ancestor];aid=doc['nodes'][ancestor].get('extras',{}).get('asset_id')
   if aid:break
  if aid not in texts:continue
  tex=texts[aid];assert tex.is_file(),str(tex)
  if aid not in texture_ids:
   im=len(doc['images']);doc['images'].append({'name':tex.name,'bufferView':append(tex.read_bytes()),'mimeType':'image/png'})
   sampler=len(doc['samplers']);doc['samplers'].append({'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071})
   tid=len(doc['textures']);doc['textures'].append({'source':im,'sampler':sampler});texture_ids[aid]=tid
  for prim in doc['meshes'][node['mesh']]['primitives']:
   acc=doc['accessors'][prim['attributes']['POSITION']];view=doc['bufferViews'][acc['bufferView']];off=view.get('byteOffset',0)+acc.get('byteOffset',0);pos=np.frombuffer(binary,dtype='<f4',offset=off,count=acc['count']*3).copy().reshape(-1,3)
   # Source sheet lies in author XY plane; top orientation matches canonical manifest.
   lo=pos[:,:2].min(0);hi=pos[:,:2].max(0);uv=(pos[:,:2]-lo)/np.maximum(hi-lo,1e-9);uv[:,1]=1-uv[:,1]
   vi=append(uv.astype('<f4').tobytes());ai=len(doc['accessors']);doc['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(pos),'type':'VEC2'});prim['attributes']['TEXCOORD_0']=ai
   mi=len(doc['materials']);doc['materials'].append({'name':'canonical_'+aid,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':texture_ids[aid],'texCoord':0},'metallicFactor':0,'roughnessFactor':.95}});prim['material']=mi
  patched.append({'node':idx,'asset_id':aid,'texture_path':str(tex.relative_to(R)),'texture_sha256':hashlib.sha256(tex.read_bytes()).hexdigest()})
 while len(binary)%4:binary.append(0)
 doc['buffers']=[{'byteLength':len(binary)}];doc['extras']['canonical_texture_bindings']=patched;enc=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();enc+=b' '*((-len(enc))%4)
 out=p.with_name('scene-textured.glb');total=12+8+len(enc)+8+len(binary);out.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<II',len(enc),0x4e4f534a)+enc+struct.pack('<II',len(binary),0x004e4942)+binary)
 return {'path':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bindings':patched,'render_note':'graybox PNGs omit textures; this textured GLB contains explicit UV and embedded original canonical PNGs','human_review':None}
def main():
 rows=[patch(p) for p in sorted(OUT.glob('EP03R5-*/scene.glb'))]
 (OUT/'texture-bindings.json').write_text(json.dumps({'status':'textured_glb_pending_review','models':rows,'no_ai_generation':True,'complaint_not_military_report':'complaint uses same paper substrate, never military Yan seal'},ensure_ascii=False,indent=2)+'\n')
 print([(x['path'],len(x['bindings'])) for x in rows])
if __name__=='__main__':main()
