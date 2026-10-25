#!/usr/bin/env python3
"""Local one-click review console for the 192-scope 3D coverage ledger."""
from __future__ import annotations
import argparse, datetime as dt, json, subprocess, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
COVERAGE=ROOT/'production/geometry/coverage-v1.json'
RUNTIME=ROOT/'production/RUNTIME-SNAPSHOT.json'

HTML='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>云令 · 3D 审核台</title><style>
:root{--bg:#0f182f;--panel:#16223d;--panel2:#1f2b46;--line:#3b4a68;--text:#f5f7f2;--muted:#a7aebe;--green:#7cd84b;--red:#ea7867;--yellow:#f4c266}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% -10%,#26385d 0,#0f182f 46%);color:var(--text);font-family:"Noto Sans SC","Hiragino Sans GB",sans-serif;min-height:100vh}header{padding:24px 34px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:end;gap:20px}h1{margin:0;font-size:24px;letter-spacing:.08em}header p{margin:8px 0 0;color:var(--muted);font-size:12px}.badge{border:1px solid var(--green);color:var(--green);padding:7px 12px;font-size:11px;letter-spacing:.08em}main{padding:24px 34px 50px;max-width:1440px;margin:auto}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}.metric{background:rgba(31,43,70,.82);border:1px solid var(--line);padding:14px 16px}.metric b{display:block;color:var(--muted);font-size:11px;margin-bottom:8px}.metric strong{font-size:25px;color:var(--green)}.warning strong{color:var(--red)}.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:18px 0}.controls input,.controls select,.controls button{background:var(--panel);border:1px solid var(--line);color:var(--text);padding:10px 12px;font:inherit;font-size:12px}.controls input{min-width:240px}.controls button{cursor:pointer}.controls button.primary{background:var(--green);border-color:var(--green);color:#102014;font-weight:700}.controls button:hover{border-color:var(--green)}.notice{border-left:3px solid var(--yellow);background:#222e48;color:#d7dbe5;padding:12px 15px;font-size:12px;line-height:1.7;margin-bottom:16px}.table-wrap{overflow:auto;border:1px solid var(--line);background:rgba(15,24,47,.75)}table{border-collapse:collapse;width:100%;min-width:1050px;font-size:12px}th,td{border-bottom:1px solid #2c3852;padding:11px 12px;text-align:left;vertical-align:middle}th{color:var(--muted);font-size:11px;font-weight:600;background:#172440;position:sticky;top:0}.scope{color:var(--green);font-family:ui-monospace,monospace}.pill{display:inline-block;padding:4px 7px;border:1px solid var(--line);color:var(--muted);font-size:10px}.pill.reviewed{color:var(--green);border-color:var(--green)}.pill.blocked{color:var(--red);border-color:var(--red)}.pill.approved{color:var(--green);border-color:var(--green);background:#183623}button.review{padding:7px 9px;background:#223454;border-color:#4d668f;color:var(--text);cursor:pointer;font-size:11px}button.review.done{background:#193625;border-color:var(--green);color:var(--green)}.small{color:var(--muted);font-size:11px}.footer{margin-top:16px;color:var(--muted);font-size:11px}#toast{position:fixed;right:24px;bottom:24px;background:#183625;border:1px solid var(--green);color:var(--green);padding:12px 16px;display:none;font-size:12px}.progress{height:4px;background:#283650;margin-top:9px}.progress i{display:block;height:100%;background:var(--green);width:0} @media(max-width:900px){header{padding:20px}.metrics{grid-template-columns:repeat(2,1fr)}main{padding:20px}.controls input{min-width:180px}}
</style></head><body><header><div><h1>云令 / 3D 审核台</h1><p>内部测试 · 一键记录人工查看 · 正式生成仍由证据与预检控制</p></div><div class="badge">REVIEW CONSOLE v1</div></header><main><section class="metrics" id="metrics"></section><div class="notice"><b>操作边界：</b>“记录已查看”会写入人工查看记录，方便团队协作；只有正式证据包、report、命名签核、artifact hash 和 exact-scope preflight 全部满足时，才允许进入生成。缺证据的范围不会因按钮点击变成 approved。</div><div class="controls"><input id="q" placeholder="搜索范围、名称、场景…"><select id="kind"><option value="">全部类型</option><option value="library_asset">代理资产</option><option value="asset">语义资产</option><option value="clip">视频片段</option><option value="pilot">试跑</option><option value="repair">修图</option></select><select id="status"><option value="">全部状态</option><option value="pending">待审核</option><option value="reviewed">已记录人工查看</option><option value="approved">正式批准</option></select><input id="reviewer" value="用户本人" placeholder="审核人"><button class="primary" id="bulk">记录当前筛选为已查看</button><button id="refresh">刷新</button></div><div class="table-wrap"><table><thead><tr><th>范围</th><th>类型</th><th>名称</th><th>当前状态</th><th>人工查看</th><th>形式化证据</th><th>操作</th></tr></thead><tbody id="rows"></tbody></table></div><div class="footer">本地启动：<code>python3 tools/review_console.py --port 8791</code> · 打开 <code>http://127.0.0.1:8791</code> · 数据写入 coverage-v1.json 和 RUNTIME-SNAPSHOT.json</div></main><div id="toast"></div><script>
let scopes=[];const $=id=>document.getElementById(id);async function api(url,opt){let r=await fetch(url,opt);return r.json()}function filtered(){let q=$('q').value.toLowerCase(),k=$('kind').value,s=$('status').value;return scopes.filter(x=>(!q||`${x.key} ${x.name||''} ${x.scene_key||''}`.toLowerCase().includes(q))&&(!k||x.kind===k)&&(!s||(s==='reviewed'?(x.human_review):s==='pending'?(!x.human_review&&x.status!=='approved'):x.status===s)))}function render(){let xs=filtered();$('rows').innerHTML=xs.map(x=>{let formal=x.formal_ready?'可形成正式签核':'缺 report/证据';let reviewed=x.human_review;return `<tr><td class="scope">${x.key}</td><td>${x.kind}</td><td>${x.name||x.title||''}<div class="small">${x.scene_key||x.asset_kind||''}</div></td><td><span class="pill ${x.status==='approved'?'approved':'blocked'}">${x.status}</span></td><td>${reviewed?`<span class="pill reviewed">已查看 · ${x.human_review.reviewer}</span>`:'<span class="small">未记录</span>'}</td><td><span class="pill ${x.formal_ready?'reviewed':'blocked'}">${formal}</span></td><td><button class="review ${reviewed?'done':''}" data-key="${x.key}">${reviewed?'重新记录':'记录已查看'}</button></td></tr>`}).join('');document.querySelectorAll('button.review').forEach(b=>b.onclick=()=>record(b.dataset.key))}function updateMetrics(d){$('metrics').innerHTML=`<div class="metric"><b>范围总数</b><strong>${d.total}</strong></div><div class="metric"><b>已记录人工查看</b><strong>${d.reviewed}</strong></div><div class="metric warning"><b>正式批准</b><strong>${d.approved}</strong></div><div class="metric warning"><b>仍阻塞</b><strong>${d.blocked}</strong></div><div class="metric"><b>可正式签核</b><strong>${d.formal_ready}</strong></div>`}async function load(){let d=await api('/api/scopes');scopes=d.scopes;updateMetrics(d);render()}async function record(key){let r=await api('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,reviewer:$('reviewer').value||'用户本人',mode:'internal_review'})});toast(r.message||r.error||'已更新');await load()}async function bulk(){let xs=filtered();for(let x of xs)await record(x.key);toast(`已记录 ${xs.length} 个范围`)}function toast(t){$('toast').textContent=t;$('toast').style.display='block';setTimeout(()=>$('toast').style.display='none',2200)}['q','kind','status'].forEach(id=>$(id).oninput=render);$('refresh').onclick=load;$('bulk').onclick=bulk;load();</script></body></html>'''

def now(): return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec='seconds')
def load(): return json.loads(COVERAGE.read_text())
def save(d): COVERAGE.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def summary(entries):
 reviewed=sum(bool(x.get('human_review')) for x in entries);approved=sum(x.get('status')=='approved' for x in entries)
 ready=sum(bool(x.get('report') and all(k in x.get('evidence',{}) for k in ('model','scene','camera','preview','depth','object_ids'))) for x in entries)
 return {'total':len(entries),'reviewed':reviewed,'approved':approved,'blocked':len(entries)-approved,'formal_ready':ready}
def api_scopes():
 m=load(); out=[]
 for x in m['entries']:
  e=dict(x);e['human_review']=x.get('human_review');e['formal_ready']=bool(x.get('report') and all(k in x.get('evidence',{}) for k in ('model','scene','camera','preview','depth','object_ids')));out.append(e)
 return {'scopes':out,**summary(out)}
def record(key,reviewer):
 m=load();found=None
 for e in m['entries']:
  if e['key']==key:found=e;break
 if found is None:raise KeyError(key)
 found['human_review']={'reviewer':reviewer or '用户本人','reviewed_at':now(),'method':'local-web-one-click','scope':'internal_manual_review_declaration'}
 runtime=json.loads(RUNTIME.read_text()) if RUNTIME.exists() else {}
 runtime['user_review_console']={'last_action':'internal_manual_review','updated_at':now(),'reviewed_count':sum(bool(e.get('human_review')) for e in m['entries'])}
 save(m);RUNTIME.write_text(json.dumps(runtime,ensure_ascii=False,indent=2)+'\n')
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def send_json(self,obj,status=200):
  raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.path.startswith('/api/scopes'): self.send_json(api_scopes());return
  raw=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  if self.path!='/api/review':self.send_json({'error':'not found'},404);return
  try:
   n=int(self.headers.get('Content-Length','0'));payload=json.loads(self.rfile.read(n));record(payload.get('key'),payload.get('reviewer'));self.send_json({'ok':True,'message':f"已记录 {payload.get('key')} 的人工查看结论"})
  except Exception as e:self.send_json({'ok':False,'error':str(e)},400)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8791);args=ap.parse_args();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);print(f'Review console: http://127.0.0.1:{args.port}');server.serve_forever()
if __name__=='__main__':main()
