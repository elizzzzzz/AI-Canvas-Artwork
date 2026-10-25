# 192 个生成前范围的正式 3D 审核操作手册

这份手册说明如何把当前 192 个阻塞范围逐个变成可生成范围。内部测试模式允许人工查看确认后进入生成流程；正式证据审计仍可单独执行，不能把两种状态混为一谈。

## 1. 192 个范围怎么拆

| 批次 | 数量 | 审核对象 | 审核类型 |
|---|---:|---|---|
| 可复用代理资产 | 100 | 人物、手部、马匹、装备、道具、建筑、道路 | 静态资产几何 + 尺度/朝向/机构 |
| 语义资产/主场景范围 | 23 | 角色、场景、关键道具和代表性场景 | 场景装配 + 主观相机 + 遮挡 |
| 正式视频片段 | 67 | 34 个逻辑镜头拆出的 67 段 | 24fps 全帧运动审核 |
| 视频试跑 | 1 | `PILOT:EP01S08-5S` | 5 秒完整试跑包 |
| P01 修图 | 1 | `REPAIR:P01-v2` | 修图前完整药箱场景包 |
| **合计** | **192** |  |  |

建议按这个顺序推进：

1. 先冻结 100 个代理资产的版本和哈希；
2. 完成七个主场景和 23 个语义资产的装配；
3. 优先审核高风险动作片段，再扩展到其余 67 段；
4. 最后再做 5 秒试跑和 P01 修图。

视频片段不能只依赖“场景已审核”。每一段仍然要有自己的相机路径、起止状态、运动实体和全帧证据。

## 2. 每个范围必须交什么

每个范围都要在 `production/geometry/coverage-v1.json` 中形成一条完整记录，并具备以下文件：

| 字段 | 文件内容 | 人工要看什么 |
|---|---|---|
| `model` | GLB/OBJ 等实际模型 | 结构、厚度、关节、人物体块、道具机构 |
| `scene` | 单位、实体 ID、变换、父子关系、支撑/接触、时间轴 | 比例、位置、朝向、接触、任务关系 |
| `camera` | 主观眼位、视场角、画幅、近远裁面、完整路径 | 第一人称、净空、安全区、视线方向 |
| `preview` | 主观灰模预览和诊断预览 | 遮挡、可见性、构图、动作目的 |
| `depth` | 同一相机的深度图/逐帧深度 | 前后关系、遮挡、近裁面、物体间距 |
| `object_ids` | 同一相机的物体 ID 图和标签 | 关键物体是否在正确位置、被谁遮挡 |
| `report` | 实际检查结果 | 检查项、帧覆盖、失败项、当前版本 |
| `approval` | 命名人工签核 | 审核人、时间、源码哈希、证据哈希 |

所有文件路径都必须在仓库内，且写入 SHA-256。临时签名 URL、口头确认和截图上的“看起来没问题”不能替代这些文件。

## 3. 人工审核的实际步骤

### 第一步：冻结当前版本

先停止修改当前范围的模型、实例变换、相机和动作时间。记录范围 key、revision、`source_sha256`、相关资产 ID、审核人和审核时间。只要模型、比例、姿态、相机、运动时间、提示词或依赖资产发生变化，旧签核就失效。

### 第二步：打开证据

静态资产/场景：

```bash
python3 -m http.server 8767 --bind 127.0.0.1 --directory production/asset-library
```

打开 `http://127.0.0.1:8767/viewer.html`。场景文件在 `production/scene-blockouts/SC01/` 至 `SC07/`，重点查看同一范围的 `*-pov.png`、`*-diagnostic.png`、`*-pov-depth-mm.png`、`*-pov-object-ids.png`、`*-pov-object-ids.json`、`*-scene.json` 和 `*-camera.json`。

GLB 可以用资产查看器或 CAD Viewer 打开。诊断图允许侧视、顶视和透视，成片机位仍必须是第一人称。

视频范围要打开 24fps 运动草稿，检查每一帧和结尾边界；手部交接、药箱铰链、纸张接触、车轮接地、马匹支撑和门洞净空要增加检查点，不能只看首帧和末帧。

### 第三步：按清单做人工判断

基础检查项必须全部通过：`scale_units`、`entity_transforms`、`facing_direction`、`joint_limits`、`contact_support`、`no_unintended_intersections`、`critical_visibility`、`safe_frame`、`subjective_pov`、`prop_state_continuity`。

视频/试跑还必须通过：`camera_clearance`、`temporal_continuity`、`motion_path`、`full_frame_review`。

发现问题时记录“帧号 + 实体 ID + 问题 + 修复动作”。例如：

```text
EP01-S07-01 / frame 71 / wheel_left
问题：车轮下缘离雪路 3 cm，出现悬浮。
修复：调整车轴与车体共同位移，重新渲染 frame 0–193。
```

### 第四步：生成实际 report

报告不能由预检脚本凭空生成，必须来自真实人工检查。报告至少包含 `scope`、`revision`、`source_sha256`、完整 `files` 哈希、基础检查 `checks`、视频的 `sample_fps`、`sample_count` 和逐帧 `samples`。

视频 `sample_count` 必须是：

```text
ceil(duration_seconds × target_fps) + 1
```

例如 8 秒、24fps 必须是 193 个样本，最后一个样本是结束边界。

### 第五步：由真人签核

人工签核必须记录：

```json
{
  "reviewer": "真实姓名或公司账号",
  "approved_at": "2026-10-25T21:30:00+08:00",
  "revision": "motion-review-v1",
  "source_sha256": "<与当前条目一致>",
  "artifact_set_sha256": "<evidence + report 规范化摘要>",
  "notes": "明确记录关键接触、遮挡和 POV 检查结果"
}
```

内部测试模式可由用户人工查看直接确认；正式证据审计仍需要真实审核人和完整证据。助手不能伪造正式 report 或把内部确认写成正式几何事实。

## 4. 每个范围如何放行

完成 report 和人工签核后，在仓库根目录运行：

```bash
python3 tools/geometry_preflight.py --scope <exact_scope>
```

内部测试生成门使用 `python3 tools/geometry_preflight.py --internal-review --scope <exact_scope>`，用户人工查看和 source hash 匹配即可。默认命令 `python3 tools/geometry_preflight.py --scope <exact_scope>` 是可选正式证据审计。

## 5. 推荐审核队列

### 阶段 A：资产静态审核

先审 100 个 `LIB:<ID>`：人物和手部、马匹和车马组件、药箱/军报/旧令/封泥/云令匣、建筑/道路/家具、装备和替代组件。每项确认尺寸、朝向、结构、厚度和局部机构。组件不等于成片场景批准。

### 阶段 B：场景与语义资产审核

再审 23 个 `ASSET:<key>`，尤其是 `ASSET:SC01`–`ASSET:SC07`、P01 完整案面—药箱—军报—旧令—双手—相机，以及角色和关键道具参考。确认画外信息没有被错误做成异地镜头，主任务和支线动作在空间上可读。

### 阶段 C：动作片段审核

按集、按场景、按风险排序：追车/战争/雨棚救援/车轴失控/城门冲入；手部交接/药箱开合/纸张抢救/封泥转移；雨廊多人调度和路线冲突；其余稳定观察和口播片段。

### 阶段 D：试跑与修图

`PILOT:EP01S08-5S` 和 `REPAIR:P01-v2` 必须在依赖场景通过后单独审核。P01 v1 的水平箱盖错误已经被拒绝，不能用旧图或局部铰链模型替代完整场景包。

## 6. 审核完成后的生成顺序

先用一个已批准片段做低成本试跑，检查实际 AI 帧是否偏离批准的 3D 比例、遮挡、机构和 POV；通过后按 EP01 → EP02 → EP03 分集生成、复核、配音/字幕/口型同步和导出。发生模型、姿态、机位、动作时长或提示词变化，回到对应范围重新审核。

当前结论：内部测试审核是“用户人工查看 + internal_review preflight”；正式证据审计才是“证据包 + report + 签核 + formal preflight”。两种状态分开记录。

## 7. 一键审核台

为减少手工编辑 JSON，项目提供本地网页审核台：

```bash
python3 tools/review_console.py --port 8791
```

打开：

```text
http://127.0.0.1:8791
```

页面支持：

- 按范围 key、名称、场景和类型筛选；
- 批量记录“已人工查看”；
- 显示正式批准数、阻塞数和证据是否齐全；
- 记录审核人和时间；
- 保持“人工查看通过”和“正式生成批准”两种状态分离。

“记录已查看”只会写入 `human_review` 字段，不会把范围改成 `approved`，也不会打开 AI Canvas 生成门。正式批准仍需 report、证据哈希、命名签核和 exact-scope preflight 返回 0。

## 8. 最新内部测试模式

根据 2026-10-26 用户决定，内部测试生成流程采用双层审核：

### 内部测试生成门

人工查看确认即可进入内部生成流程，不强制要求完整 report、逐帧 evidence 或 artifact hash。执行：

```bash
python3 tools/geometry_preflight.py --internal-review
```

单个范围：

```bash
python3 tools/geometry_preflight.py --internal-review --scope EP01-S07-01
```

该模式要求：

- 当前 `source_sha256` 仍匹配；
- 存在真实用户人工查看记录；
- 不要求正式 `status: approved`；
- 不要求 report、深度、物体 ID 或逐帧报告；
- 不代表已经证明几何正确。

当前项目的内部模式结果应为：

```text
allowed: true
checked: 192
blocked: 0
mode: internal_review
```

### 正式证据审计

如需形成可追溯的正式制作包，仍可执行默认模式：

```bash
python3 tools/geometry_preflight.py --scope <exact_scope>
```

默认模式仍检查完整 evidence、report、逐帧 samples、artifact hash 和命名签核。它是审计层，不再阻塞内部测试模式。

两种状态必须分开记录：

- `internal_approval`：用户人工确认，可以进入内部测试生成流程；
- `status: approved`：正式证据审计完成，可作为严格制作审计结果。

内部测试模式允许继续验证模型选择、提示词、剪辑和故事效果；生成后仍要检查 AI 实际帧，不得把内部测试结果直接写成正式质量批准。
