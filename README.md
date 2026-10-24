# 《云令入局》

七牛云内部测试样片：三集竖屏古装品牌短剧，关联《琅琊榜》世界观，以“琅琊云令”转译一站式 AI Infra 的产品价值。

## 项目状态

- 当前阶段：创作规格确认完成，准备进入镜头级剧本与 3D 灰模
- 画幅：9:16
- 单集时长：135–155 秒，硬上限 180 秒
- 集数：3 集
- 视觉方向：写实古装、史诗正剧为骨、轻喜剧为针
- 制作策略：先角色与场景设计，再 3D 导演台和灰模预演，确认流程后进入最终渲染
- 用途：七牛云内部品牌叙事和 AI Infra 产品隐喻测试

## 故事主线

十二年前，赤焰旧案留下残缺军令；十二年后，琅琊阁放出“麒麟才子”的锦囊；梅长苏携带旧案线索入京，残缺军令、北燕六皇子和金陵权局逐渐汇成同一盘棋。

每集围绕一个主任务展开：辅助人员或支持链路出现故障，主人公暂时暂停主任务完成救火，再回到主线。古风世界中的“云令中枢”对应七牛云一站式 AI Infra 对模型、数据、鉴权、调度和协作底层的整合能力。

## 目录

- [创作规格书](docs/superpowers/specs/2026-10-23-qiniu-langya-cloud-order-design.md)
- [项目过程记录](docs/PROJECT-LOG.md)
- [内部评审清单](docs/INTERNAL-REVIEW.md)
- [数据证据与决策依据](docs/DATA-EVIDENCE.md)
- [三集镜头节奏方案](docs/SHOT-PLAN.md)
- [本轮评审结论](docs/REVIEW-DECISION.md)
- [下一阶段制作计划](docs/superpowers/plans/2026-10-23-qiniu-langya-production-plan.md)
- [三集镜头级剧本](docs/scripts/)
- [角色一致性锚点](docs/CHARACTER-ANCHORS.md)
- [场景与道具锚点](docs/SCENE-PROP-ANCHORS.md)
- [第一人称摄影协议](docs/FIRST-PERSON-CAMERA-PROTOCOL.md)
- [3D 导演台规格](docs/3D-DIRECTOR-TABLE.md)
- [灰模评审表](docs/GRAYBOX-REVIEW.md)
- [基准提示词优化报告](docs/PROMPT-OPTIMIZATION-REPORT.md)
- [模型基准测试方案](docs/MODEL-BENCHMARK.md)
- [模型基准测试结果](docs/MODEL-BENCHMARK-RESULTS.md)
- [制作模型优先组合](docs/MODEL-SELECTION.md)
- [AI Canvas 三集制作工作包](production/README.md)
- [首批八图审阅与人工检查](production/REFERENCE-REVIEW.md)
- [P01 箱盖几何修正](production/p01-lid-repair-v2/README.md)

## 强制3D前置

所有图片、修图及视频运镜生成前必须完成对应3D建模与审核，见 [制作规范](docs/MANDATORY-3D-PRODUCTION.md) 和 [覆盖清单](production/geometry/COVERAGE.md)。当前已关闭所有待生成条件，先进行实际建模。

## 评审重点

1. 三集是否形成清晰连续的故事链；
2. 每集主任务是否在前 15 秒内成立；
3. 支线故障是否具体并能对应开发协作中的真实痛点；
4. “云令”是否通过行动体现，而不是依赖产品说明台词；
5. 七牛云品牌口播是否自然、清晰、容易记住；
6. 人物、服饰、场景和道具是否具备可持续生成的一致性。

## 当前边界

本仓库用于内部测试。当前版本可以保留《琅琊榜》相关人物和世界观符号，以便验证创意方向；若转为公开发布，需要另行处理版权、原创化和内容合规问题。
