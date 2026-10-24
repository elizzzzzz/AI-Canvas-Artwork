# 所有画面必须有 3D 依据

这是一份覆盖实际代理资产、七个代表性场景草稿及待审核分镜的台账；完整子空间和动态场景包仍待完成。用户的强制要求已写入 [制作规范](../../docs/MANDATORY-3D-PRODUCTION.md)及仓库 [AGENTS.md](../../AGENTS.md)。

- 7 个主场景，逐场列出子空间、人物、道具和空间动作关系：[scene-inventory-v1.json](scene-inventory-v1.json)。
- 192 个验收范围：100 个可复用三维代理资产、23 项原始语义资产、67 个正式片段、1 个 5 秒试跑、1 个 P01 修图：[coverage-v1.json](coverage-v1.json)。
- 当前 **0 个批准，192 个阻塞**；100 个 GLB 已实际导出但仍是代理模型，P01 箱盖是部分机构模型，尚无完整布景审批。
- [运行门核验](runtime-gate-verification.json)证明 10 个现有生成节点的运行条件关闭，逐节点重跑也不执行；它不证明场景几何正确。

## 执行检查

```bash
# 审计全部范围；未建模时应返回1（阻塞），不能把此结果改成通过
python3 tools/geometry_preflight.py

# 检查某一范围
python3 tools/geometry_preflight.py --scope ASSET:SC04
python3 tools/geometry_preflight.py --scope EP01-S08-01
python3 tools/geometry_preflight.py --scope REPAIR:P01-v2

# 运行检查器与已有铰链模型的单元测试
python3 -m unittest discover -s tests
```

预检只检查真实审核包的完整性、文件哈希、源码版本、检查字段与逐帧覆盖，不会替你创建模型、求解碰撞或伪造评审结论。

## 当前范围与未来画布关联

资产库登记见 [三维代理资产库](../asset-library/README.md)，目录和镜头装配图的哈希已写入 `production/workflow-v1.json`。

- 当前 8 个图片生成节点分别对应 `ASSET:C01`、`ASSET:C02`、`ASSET:C03`、`ASSET:C04`、`ASSET:SC03`、`ASSET:SC04`、`ASSET:P01`、`ASSET:KF01`。
- 当前视频试跑对应 `PILOT:EP01S08-5S`；P01 修图对应 `REPAIR:P01-v2`。
- 67 个正式片段仍是已导入分镜，不是 67 个已建立的视频生成节点；将来建节点时也必须接入各自关闭的条件，并以同名片段范围通过预检后才放行。
- 审批是“几何证据 + 艺术检查 + 当前费用范围”的交集；只确认费用不能打开 3D 门，只有局部铰链模型也不能放行完整画面。

## 三维包的实际数据约定

`scene` 至少描述单位、实体 ID、尺寸、变换、局部前向、骨架/关节、支撑/接触对象与时间轴；`camera` 描述主观眼位、镜头与路径。`report` 绑定同一组 `model/scene/camera/preview/depth/object_ids` 文件哈希，记录基础检查项。

视频报告按范围中的 `duration`、`target_fps` 提供逐帧 `samples`，包括 `frame`、`time_seconds`、该帧检查结果，最后额外保留结束边界；关键接触需要真实建模工具中的额外检查。每个报告绑定当前源码与版本，并由明确评审人签核。缺文件、缺帧、任一必要检查失败或哈希变化，均不放行。

单元测试中的临时“synthetic-test-only”文件只检验程序能正确拒绝不完整/过期证据，不会写入生产台账或被当作真实模型。


人工签核还必须记录 `artifact_set_sha256`（证据路径/哈希与报告路径/哈希的规范化摘要）；即使沿用旧版本号，任何模型、相机或报告内容变化也不能复用旧签核。

七个代表性静态组合草稿已导出，见 [场景工作包](../scene-blockouts/README.md)。`ASSET:SC01` 至 `ASSET:SC07` 已登记六类静态证据，仍无审核报告或人工批准。所有 67 段运镜及子空间继续待制作。
