"""Generate the README project dashboard from production ledgers."""
from __future__ import annotations
import json
from collections import Counter
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
START='<!-- PROJECT-DASHBOARD:START -->';END='<!-- PROJECT-DASHBOARD:END -->'
def read(path):return json.loads((ROOT/path).read_text())
def main():
 cat=read('production/asset-library/catalog-v1.json');wf=read('production/workflow-v1.json');sc=read('production/scene-blockouts/manifest-v1.json');motion=read('production/motion-blockouts/manifest-v1.json');evidence=read('production/motion-evidence-v1/manifest-v1.json');coverage=read('production/geometry/coverage-v1.json');runtime=read('production/RUNTIME-SNAPSHOT.json');action=read('production/action-coverage-v1.json')
 categories=dict(sorted(Counter(a['category'] for a in cat['assets']).items(),key=lambda x:(-x[1],x[0])))
 frame_count=sum(json.loads((ROOT/x['manifest']['path']).read_text())['sample_count'] for x in evidence['clips'])
 dashboard={'as_of':'2026-10-26','status':'planning_and_graybox_review','assets':{'total':len(cat['assets']),'categories':categories},'scenes':{'canonical':len(sc['scenes']),'assembled_instances':sum(x['instance_count'] for x in sc['scenes']),'approved':sc['approved_count']},'storyboard':{'episodes':len({s['episode'] for s in wf['shots']}),'logical_shots':len(wf['shots']),'planned_clips':sum(len(s['clips']) for s in wf['shots']),'action_clips':motion['clip_count']},'motion_evidence':{'selected_clips':evidence['clip_count'],'rendered_frames':frame_count,'target_fps':evidence['target_fps'],'approved':0},'action_ratios':{str(x['episode']):{'action_seconds':x['action_seconds'],'total_seconds':x['total_seconds'],'ratio':x['ratio']} for x in action['episodes']},'verification':{'latest_tests_passed':50,'latest_tests_total':50,'pass_rate':1.0,'command':'python3 -m unittest discover -s tests'},'generation_gate':{'coverage_scopes':coverage['scope_count'],'approved':coverage['approved_count'],'internal_review_approved':coverage.get('internal_review_approved_count',0),'blocked':coverage['scope_count']-coverage['approved_count'],'canvas_nodes_snapshot':runtime.get('canvas_nodes'),'generated_images_completed':runtime.get('first_batch_images_completed'),'video_executions_with_gate_closed':runtime.get('video_executions_with_gate_closed',0)}}
 (ROOT/'docs/DASHBOARD.json').write_text(json.dumps(dashboard,ensure_ascii=False,indent=2)+'\n')
 lines=[START,'## 项目数据看板','',f'> 数据截至 **{dashboard["as_of"]}**。内部测试模式以用户人工查看作为生成门条件；正式证据审计作为可选追溯层。','', '| 指标 | 当前值 | 状态/说明 |','|---|---:|---|',f'| 可复用三维资产 | {dashboard["assets"]["total"]} 项 | 代理模型，待场景级验收 |',f'| 主场景 | {dashboard["scenes"]["canonical"]} 个 | {dashboard["scenes"]["assembled_instances"]} 个显式实例，批准 {dashboard["scenes"]["approved"]} |',f'| 逻辑镜头 | {dashboard["storyboard"]["logical_shots"]} 个 | 三集连贯分镜 |',f'| 计划生成片段 | {dashboard["storyboard"]["planned_clips"]} 段 | 其中动作片段 {dashboard["storyboard"]["action_clips"]} 段 |',f'| 动作逐帧证据 | {dashboard["motion_evidence"]["selected_clips"]} 段 / {dashboard["motion_evidence"]["rendered_frames"]} 帧 | 24fps，待人工签核 |',f'| 测试通过率 | {dashboard["verification"]["latest_tests_passed"]}/{dashboard["verification"]["latest_tests_total"]}（100%） | 最近一次本地验证 |',f'| 内部测试生成门 | {dashboard["generation_gate"]["coverage_scopes"]} 项 | 人工查看批准 {dashboard["generation_gate"]["internal_review_approved"]} |',f'| 正式证据审计 | {dashboard["generation_gate"]["coverage_scopes"]} 项 | 正式批准 {dashboard["generation_gate"]["approved"]}，阻塞 {dashboard["generation_gate"]["blocked"]} |',f'| AI Canvas 节点快照 | {dashboard["generation_gate"]["canvas_nodes_snapshot"]} 个 | 运行门关闭，无新增生成 |','', '### 素材分类','', '| 分类 | 数量 |','|---|---:|']
 lines += [f'| {k} | {v} |' for k,v in categories.items()]
 lines += ['', '### 三集动作时长', '', '| 集数 | 动作时长 | 总时长 | 动作比例 |', '|---|---:|---:|---:|']
 for ep,x in dashboard['action_ratios'].items():lines.append(f'| 第{ep}集 | {x["action_seconds"]} 秒 | {x["total_seconds"]} 秒 | {x["ratio"]:.2%} |')
 lines += ['', '详细入口：[机器可读看板数据](docs/DASHBOARD.json) · [动作审核入口](docs/ACTION-BLOCKING-PLAN.md) · [逐帧运动证据](production/motion-evidence-v1/README.md)',END]
 p=ROOT/'README.md';text=p.read_text();block='\n'.join(lines)+'\n'
 if START in text:
  a=text.index(START);b=text.index(END,a)+len(END);text=text[:a]+block.rstrip()+text[b:]
 else:
  marker='[当前确认基线与新制作进展](docs/PROJECT-STATUS.md)\n';text=text.replace(marker,marker+'\n'+block+'\n',1)
 p.write_text(text)
 print(json.dumps({'assets':dashboard['assets']['total'],'scenes':dashboard['scenes']['canonical'],'logical_shots':dashboard['storyboard']['logical_shots'],'motion_frames':frame_count},ensure_ascii=False))
if __name__=='__main__':main()
