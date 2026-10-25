#!/usr/bin/env python3
"""Queue all 67 formal video clips on the shared AICanvas board.
No title-card nodes are created; the clip prompt itself carries first-person and action constraints.
"""
from __future__ import annotations
import os, json, uuid, requests, datetime, pathlib, time, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
HOST=os.environ.get('AICANVAS_HOST','https://aicanvas.qnlinking.com').rstrip('/')
KEY=os.environ['AICANVAS_API_KEY']; BOARD='6851506d-6617-46f5-a06e-a2e9954f2ea0'
HEAD={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'}
GATE='b30832a0-61c3-428c-aaa2-bfc7381016cc'
STATE=ROOT/'production/full-generation-v2.json'

def api(method,path,**kwargs):
    r=requests.request(method,HOST+path,headers=HEAD,timeout=120,**kwargs)
    r.raise_for_status(); data=r.json()
    if data.get('code') not in (0,None): raise RuntimeError(data)
    return data

def get_graph(): return api('GET',f'/api/canvas/boards/{BOARD}/graph')['data']

def main():
    wf=json.loads((ROOT/'production/workflow-v1.json').read_text())
    clips=[(shot,c) for shot in wf['shots'] for c in shot['clips']]
    g=get_graph(); existing={n.get('title'):n for n in g['nodes'].values()}
    nodes=[]; records=[]; rev=g['revision']
    for shot,c in clips:
        key=c['key']; title=f'FULL {key} 正式片段'
        if title in existing:
            n=existing[title]; records.append({'key':key,'logical_shot':shot['key'],'node_id':n['id'],'title':title,'duration':c['duration'],'status':'existing'})
            continue
        nid=str(uuid.uuid4())
        # Prompt already contains the project visual contract; add a hard post-production rule.
        prompt=c['prompt']+'\n后期规则：不得插入章节卡、PPT式说明页或全屏图文卡；信息通过画外音或画面内书法字幕完成，字幕不改变空间几何。'
        nodes.append({'op':'add_node','id':nid,'kind':'video','title':title,'spec':{'model':'minimax/minimax-h3','aspect':'9:16','prompt':prompt,'duration':int(c['duration']),'resolution':'768P'},'inputs':{'condition':[{'mode':'each','node':GATE,'field':'pilot_ready','match':'any'}]},'pause_after':False})
        records.append({'key':key,'logical_shot':shot['key'],'node_id':nid,'title':title,'duration':c['duration'],'status':'queued'})
    # Apply in chunks to keep the graph request bounded.
    for i in range(0,len(nodes),20):
        chunk=nodes[i:i+20]
        layout={'nodes':{op['id']:{'x':7000+(j%5)*420,'y':-1600+(j//5)*300,'w':360,'h':0} for j,op in enumerate(chunk)}}
        result=api('POST',f'/api/canvas/boards/{BOARD}/ops',json={'expected_revision':rev,'ops':chunk,'layout_patch':layout})
        rev=result['data']['revision']
    out={'version':2,'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'board_id':BOARD,'canvas_revision':rev,'status':'nodes_queued_no_title_cards_text_to_video_inferred','model':'minimax/minimax-h3','resolution':'768P','aspect':'9:16','gate':'pilot_ready=true','clip_count':len(records),'clips':records}
    STATE.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':rev,'clip_count':len(records),'new_nodes':len(nodes),'state':str(STATE)},ensure_ascii=False))
if __name__=='__main__': main()
