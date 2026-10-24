"""Build scene/shot asset linkage and a review atlas from actual local GLB outputs."""
import collections, hashlib, json, math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'production/asset-library';catalog=json.loads((out/'catalog-v1.json').read_text());assets=catalog['assets'];ids={a['id'] for a in assets};blue=json.loads((ROOT/'production/workflow-v1.json').read_text())
    roles={
    1:[['MCS'],['LS'],['LS'],['LS','MCS'],['MCS','SCRIBE'],['MCS','SCRIBE'],['MCS','SCRIBE','GUARD','DRIVER'],['MCS','SCRIBE'],['MCS','SCRIBE'],['MCS','COURIER'],['MCS','SCRIBE','GUARD','DRIVER']],
    2:[['XTY'],['XTY','KEEPER'],['XTY','MSG-A'],['XTY','MSG-A','MSG-B','MSG-C'],['XTY','MSG-A','MSG-B'],['XTY','MSG-C'],['XTY','MSG-A','MSG-B','MSG-C'],['XTY','SCRIBE','MSG-A','MSG-B','MSG-C'],['XTY','MSG-A'],['XTY','RPT-A','RPT-B'],['XTY','MSG-A','MSG-B','MSG-C','SCRIBE']],
    3:[['MCS'],['MCS','ZQY'],['MCS','XJR','GUARD'],['MCS','SCRIBE','MEDBOY','DRIVER'],['MCS','DRIVER','GUARD'],['MCS','MEDBOY','COURIER'],['MCS','SCRIBE','MEDBOY','DRIVER','GUARD'],['MCS','SCRIBE','MEDBOY','DRIVER','GUARD'],['MCS','ZQY'],['MCS','XJR','DRIVER'],['MCS','RPT-A'],['MCS','ZQY','XJR','DRIVER','MEDBOY','GUARD']]}
    props={
    1:[['TOKEN','CANDLE','STAND'],['REPORT'],['REPORT','MAP-NEW','STAMP'],['CANDLE','STAND'],['ARCHIVEBOX','INDEX','STAMP','INK'],['INDEX','ARCHIVEBOX'],['CHEST','REPORT','MEDBUNDLE'],['CHEST','REPORT','BACKUP'],['TOKEN','REPORT'],['TOKEN','LETTERBOX','SEAL-R'],['TOKEN']],
    2:[['BADGE','CLOUDBOX'],['POUCH','LETTERBOX','SEAL-R','SEAL-G','SEAL-B'],['MAP-NEW','REPORT'],['MAP-NEW','SEAL-R','SEAL-G','SEAL-B','BADGE'],['SEAL-R','SEAL-G','SEAL-B','BADGE'],['MAP-OLD','MAP-NEW'],['BADGE','CLOUDBOX','MAP-NEW','SEAL-R','SEAL-G','SEAL-B'],['CLOUDBOX','MAP-NEW','SEAL-R','SEAL-G','SEAL-B'],['RECEIPT','SEAL-R','SEAL-G','SEAL-B'],['REPORT','RECEIPT'],['RECEIPT','CLOUDBOX']],
    3:[['MEDBUNDLE','FAN'],['COMPLAINT','MEDBUNDLE','TIE'],['PERMIT','BADGE'],['COMPLAINT','MEDBUNDLE','MAP-NEW'],['COMPLAINT','MAP-NEW'],['MEDBUNDLE','REPORT'],['COMPLAINT','MEDBUNDLE','MAP-NEW','REPORT'],['COMPLAINT','MEDBUNDLE','MAP-NEW','CLOUDBOX','TIE','STAMP'],['COMPLAINT','MEDBUNDLE','MAP-NEW','CHEST'],['PERMIT','LANTERN'],['REPORT','PERMIT'],['REPORT','COMPLAINT','TOKEN','PERMIT']]}
    env={
      'SC01':['AR-WALL','AR-FLOOR','AR-BEAM','AR-WINDOW','AR-DOOR','AR-BED','AR-DESK'],
      'SC02':['ENV-SNOWROAD','ENV-SNOWBANK','ENV-ROCK','ENV-BROKENWOOD','ENV-FLAG','ENV-BRAZIER','EQ-ARMOR','EQ-HELMET','EQ-SHIELD','EQ-SWORD'],
      'SC03':['AR-WALL','AR-FLOOR','AR-BEAM','AR-WINDOW','AR-DOOR','AR-DESK','AR-CABINET','AR-STEP','PR-BRUSH','PR-INKSTONE'],
      'SC04':['ENV-SNOWROAD','ENV-SNOWBANK','ENV-TREE','VH-CART','VH-CANOPY','VH-WHEEL','VH-AXLE','VH-BOARD','VH-DRAWBAR'],
      'SC05':['AR-FLOOR','AR-COLUMN','AR-BEAM','AR-ROOF','AR-DESK','AR-BRIDGE','PR-BRUSH','PR-INKSTONE'],
      'SC06':['ENV-DIRT','VH-CART','VH-WHEEL','VH-AXLE','AR-AWNING','AR-DESK','PR-BOTTLE','PR-JUG'],
      'SC07':['AR-GATEWALL','AR-GATE','AR-GATELEAF','AR-LIGHT','PR-LANTERN','ENV-PAVING']}
    shot_links=[]
    for s in blue['shots']:
        e,i=s['episode'],s['shot_index']-1;characters=['CH-'+x for x in roles[e][i]];asset_ids=set(characters+["PR-"+x for x in props[e][i]])
        for sc in set(c['scene_key'] for c in s['clips']):asset_ids.update(env[sc])
        for owner in set(c['pov_owner'] for c in s['clips']):
            who={'梅长苏':'MCS','林殊':'LS','谢听云':'XTY'}[owner];asset_ids.update(['HAND-'+who+'-L','HAND-'+who+'-R'])
        if s['key'] in ['EP01-S07','EP03-S03','EP03-S10','EP03-S12']:asset_ids.update(['AN-HORSE','EQ-SADDLE','EQ-BRIDLE','VH-REINS'])
        if s['key'] in ['EP03-S05','EP03-S08']:asset_ids.add('VH-AXLE-BROKEN')
        assert asset_ids<=ids,(s['key'],asset_ids-ids)
        shot_links.append({'logical_shot':s['key'],'title':s['title'],'clip_keys':[c['key'] for c in s['clips']],'asset_ids':sorted(asset_ids),'character_asset_ids':characters,'pov_visibility_rule':'主人公身体/头/肩背不在成片中出现；自己的手及袖口按当前姿态取景','status':'assembly_plan_not_visibility_approved','note':'含场景支撑组件；不是认定所有列出实体都在最终画面可见，逐机位检查时确定可见/遮挡/画外。'})
    reverse={a['id']:[s['logical_shot'] for s in shot_links if a['id'] in s['asset_ids']] for a in assets}
    for a in assets:a['logical_shot_candidates']=reverse[a['id']];a['source_files']=['docs/CHARACTER-ANCHORS.md','docs/SCENE-PROP-ANCHORS.md','production/workflow-v1.json'];a['deployment']='planned_shot_use' if reverse[a['id']] else 'reusable_component_or_alternative_not_yet_assigned'
    (out/'catalog-v1.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    (out/'shot-asset-map-v1.json').write_text(json.dumps({'version':1,'logical_shot_count':34,'clip_count':67,'mapping_status':'explicit_assembly_plan_pending_review','shots':shot_links},ensure_ascii=False,indent=2)+'\n')
    categories=collections.Counter(a['category'] for a in assets)
    fontpath='/System/Library/Fonts/Supplemental/Arial Unicode.ttf';font=ImageFont.truetype(fontpath,24);small=ImageFont.truetype(fontpath,17);title=ImageFont.truetype(fontpath,36)
    featured=['CH-MCS','HAND-MCS-R','AN-HORSE','PR-CHEST','PR-CLOUDBOX','EQ-SADDLE','VH-CART','VH-WHEEL','AR-CABINET','AR-WINDOW','AR-GATE','ENV-SNOWROAD'];by={a['id']:a for a in assets};w,h=1420,1290;im=Image.new('RGB',(w,h),'#172222');d=ImageDraw.Draw(im)
    d.text((34,24),'琅琊云令 / 可复用三维资产库 v1',font=title,fill='#edf0e9');d.text((34,77),f'{len(assets)} 个实际 GLB · 7 个主场景关联 · 34 个镜头组装计划 · 0 项已验收',font=small,fill='#afc3b9')
    cw,ch,gap=320,350,24
    for n,key in enumerate(featured):
        x=34+(n%4)*(cw+gap);y=130+(n//4)*(ch+gap);a=by[key];d.rounded_rectangle((x,y,x+cw,y+ch),6,fill='#253332');img=Image.open(out/a['preview']).convert('RGB');img=img.resize((cw,267),Image.Resampling.LANCZOS);im.paste(img,(x,y));d.text((x+12,y+276),a['name'],font=font,fill='#e9eee5');d.text((x+12,y+313),key+' · '+a['category'],font=small,fill='#a9c2b5')
    d.text((34,1250),'代理模型用于几何与布景；人物面容、动物步态、手部接触和逐镜头遮挡仍需细化与审核。',font=small,fill='#bfd0c5');im.save(out/'library-overview-v1.jpg',quality=92,optimize=True)
    # Full atlas includes every actual built asset, not merely a representative subset.
    cw,ch=190,290;columns=10;rows=math.ceil(len(assets)/columns);atlas=Image.new('RGB',(columns*cw+40,rows*ch+100),'#eef1ee');ad=ImageDraw.Draw(atlas);ad.text((20,18),'100 项三维代理资产 / 全量索引',font=font,fill='#243c35')
    for n,a in enumerate(assets):
        x=20+(n%columns)*cw;y=70+(n//columns)*ch;img=Image.open(out/a['preview']).convert('RGB');atlas.paste(img,(x,y));ad.text((x+4,y+242),a['name'],font=small,fill='#233e34');ad.text((x+4,y+266),a['id'],font=ImageFont.truetype(fontpath,13),fill='#61796c')
    atlas.save(out/'all-assets-atlas-v1.jpg',quality=88,optimize=True)
    rows=['# 三维代理资产目录','', '所有文件均已导出真实网格；状态仍是低精度、待细化/布景与验收。','', '| 类别 | 数量 |','|---|---:|']+[f'| {k} | {v} |' for k,v in categories.items()]+['','| ID | 名称 | 模型 | 对应主场景 |','|---|---|---|---|']
    for a in assets:rows.append(f'| {a["id"]} | {a["name"]} | [GLB]({a["file"]}) | '+', '.join(a['scene_keys'])+' |')
    (out/'CATALOG.md').write_text('\n'.join(rows)+'\n')
    print(json.dumps({'assets':len(assets),'categories':categories,'unassigned_components':[a['id'] for a in assets if not a['logical_shot_candidates']],'logical_shots':len(shot_links)},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
