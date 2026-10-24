# 三集动作版分镜与审核入口

本次修订把动作场面按**实际镜头时长**计入，不按镜头数量估算。每集保留原定总时长，并增加战争、冲突、追逐、拦截、失控抢救和高压调度等动作段落。

| 集数 | 总时长 | 动作时长 | 动作比例 | 主要动作场面 |
|---|---:|---:|---:|---|
| 第一集 | 150 秒 | 84 秒 | 56.00% | 梅岭战争冲突、火线撤退、档室争执、雪夜追车、车厢抢救、封泥对峙 |
| 第二集 | 155 秒 | 101 秒 | 65.16% | 锦囊拦截、三路派发、信使争执、路线拉扯、雨廊追截、灯号调度、急报冲入 |
| 第三集 | 165 秒 | 114 秒 | 69.09% | 雨棚救援、萧景睿拦截追兵、失控车轴、资源冲突、雨路封锁、高压同步、封存抢救、冲入城门 |

动作修订仍遵守第一人称摄影：动作主体只能在主人公眼高、手边或近距离跟随装置可见范围内发生；不反拍主人公、不切全知战争全景、不把动作场面改成第三人称武打镜头。每个动作镜头还必须在 3D 中核对手部、人物、道路、车辆、马匹、门洞、障碍物与道具关系。

## 审核入口

### 1. GitHub Draft PR：用于文字、分镜、文件和差异评审

打开 [PR #4：assemble canonical scene blockouts](https://github.com/elizzzzzz/AI-Canvas-Artwork/pull/4)。动作版分镜与比例记录会随当前制作分支更新。重点查看：

- `docs/ACTION-BLOCKING-PLAN.md`：动作比例和动作类型；
- `production/action-coverage-v1.json`：机器可读的逐集比例；
- `docs/scripts/`：三集动作版镜头级剧本；
- `production/scene-blockouts/README.md`：七个主场景和每个场景的预览入口。

### 2. 本地场景预览：用于人工检查画面几何

在仓库根目录运行：

```bash
python3 -m http.server 8767 --bind 127.0.0.1 --directory production/asset-library
```

然后打开资产查看器：`http://127.0.0.1:8767/viewer.html`。它用于查看人物、手部、马匹、车马组件和药箱开合。

七个主场景的静态预览直接打开：

- `production/scene-blockouts/scene-overview-v1.jpg`
- `production/scene-blockouts/SC01/SC01-pov.png` 至 `SC07/SC07-pov.png`
- 对应的 `*-diagnostic.png`、`*-pov-depth-mm.png` 和 `*-pov-object-ids.png`

场景工作包入口为 [production/scene-blockouts/README.md](../production/scene-blockouts/README.md)。

### 3. AI Canvas：用于查看已登记的制作工作流

打开 [AI Canvas 制作画布](https://dev-aicanvas.qnlinking.com/canvas/6851506d-6617-46f5-a06e-a2e9954f2ea0)，查看“三维资产库 100项草模 待验收”分组和强制 3D 审核门。动作版分镜在生成前仍只作为项目文件和待审核工作流使用；10 个原有生成节点的条件继续关闭，不会因为动作比例达标而自动生成。

## 审核顺序

1. 先在 GitHub PR 中审阅动作比例、动作因果和第一人称约束。
2. 再看七个场景的 `pov`、诊断、深度和物体 ID 图，检查动作主体是否有足够空间。
3. 对需要正式视频的镜头建立逐段运动包，按 24fps 检查完整帧、结尾边界、车轮接地、手部交接、铰链和人物接触。
4. 只有场景、相机、深度、物体 ID、报告和人工签核都完成后，才运行对应范围的 `geometry_preflight.py`。
5. 当前动作比例通过的是**分镜规划检查**，不是几何或视频生成批准。动作版三集仍处于 `pending_3d_motion_review`。
