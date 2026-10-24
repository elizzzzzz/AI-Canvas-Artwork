# 《云令入局》下一阶段制作计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在内部评审 PR 中完成三集镜头级剧本、角色与场景锚点、3D 导演台规格和灰模评审入口，使项目具备进入参考图与视频试跑的条件。

**Architecture:** 采用“文档先行、灰模验证、最终渲染后置”的制作链。每个镜头同时记录时长、摄影机、动作、对白或旁白、信息来源、声音和云令能力映射；角色、场景和道具使用独立锚点文档，作为后续参考图和视频生成的唯一约束。付费生成任务必须在灰模评审后单独走模型、价格、凭证和提交确认闸门。

**Tech Stack:** Markdown 剧本与制作文档；Python 校验镜头时长和文档链接；9:16 3D 导演台与灰模预演；AICanvas 角色／场景参考图和视频生成流程。

---

### Task 1: 把三集镜头节奏方案扩展为镜头级剧本

**Files:**
- Create: `docs/scripts/EP01-meiling-old-order.md`
- Create: `docs/scripts/EP02-qilin-pouch.md`
- Create: `docs/scripts/EP03-enter-capital.md`
- Modify: `docs/SHOT-PLAN.md`

- [ ] **Step 1: 为每集建立镜头字段模板**

每个镜头必须按以下顺序记录：

```markdown
### S01｜镜头标题

- 时长：8s
- 景别／镜头：中近景，50mm，固定机位，轻微推近
- 画面动作：
- 第一人称旁白：
- 现场对白：
- 信息来源：主人公回忆／现场口述／密报／旁人回报
- 声音：
- 连续性：
- 云令映射：
- 灰模验收点：
```

- [ ] **Step 2: 完成第一集《梅岭旧令》**

将 11 个镜头扩展为完整对白和动作，保留 150 秒总时长。必须明确：梅长苏从梦境进入现实、书吏口述旧档误放、梅长苏暂停查案追车、备用存卷恢复关键页、“燕”字形成第二集悬念。

- [ ] **Step 3: 完成第二集《麒麟锦囊》**

将 11 个镜头扩展为完整对白和动作，保留 155 秒总时长。必须明确：谢听云身份慢镜头、三路信使分别出错、谢听云核验唯一有效版本、六皇子不拆锦囊、太子和誉王通过密报入局。

- [ ] **Step 4: 完成第三集《入京》**

将 12 个镜头扩展为完整对白和动作，保留 165 秒总时长。必须明确：梅长苏病中入京主任务、卓青遥口述状纸、萧景睿身份慢镜头、雨水／车轴／药包／官名四类支线故障、云令同步资源、金陵城门和“燕”字密报。

- [ ] **Step 5: 增加统一口播和对白约束**

每集结尾必须保留完整口播：

> 七牛云 一站式AI Infra，为你的主任务保驾护航。

对白约束：单集对白和旁白总字数控制在能被 165 秒自然说完的范围内；每句台词必须服务于任务、人物身份或悬念，不能用台词解释所有产品功能。

- [ ] **Step 6: 校验镜头总时长**

运行：

```bash
python3 - <<'PY'
from pathlib import Path
import re
for path in sorted(Path('docs/scripts').glob('EP*.md')):
    text = path.read_text()
    values = [int(v) for v in re.findall(r'^- 时长：(\d+)s$', text, re.M)]
    print(path, sum(values), len(values))
    assert values
    assert 135 <= sum(values) <= 180
PY
```

预期：三集分别为 150 秒、155 秒、165 秒，且每个镜头都有时长字段。

- [ ] **Step 7: 提交剧本阶段变更**

```bash
git add docs/scripts docs/SHOT-PLAN.md
git commit -m "docs: add episode-level shot scripts"
```

### Task 2: 建立角色一致性锚点

**Files:**
- Create: `docs/CHARACTER-ANCHORS.md`
- Modify: `docs/superpowers/specs/2026-10-23-qiniu-langya-cloud-order-design.md`
- Modify: `README.md`

- [ ] **Step 1: 为五位主要人物固定不可变特征**

记录梅长苏／林殊、谢听云、北燕六皇子、萧景睿、卓青遥的年龄观感、脸型、眉眼、发型、服装、主色、常用道具、姿态和表演节奏。

- [ ] **Step 2: 为梅长苏和林殊建立同脸不同状态规则**

固定两者的眉眼、鼻梁、下颌和发际线；只允许年龄状态、体态、服装和光线变化。记录梦中林殊与病中梅长苏不能同时作为同一现实时间线出现。

- [ ] **Step 3: 为每位人物建立正向提示词和负向约束**

每个角色必须包含：

- 正向外观描述；
- 服装和道具锚点；
- 表情和动作范围；
- 画面禁用项，例如现代服装、现代发型、改变脸型、错误年龄和错误主色。

- [ ] **Step 4: 记录重要人物慢镜头规则**

萧景睿、谢听云和北燕六皇子首次出现时，必须有 2–4 秒身份交代镜头；角色第一次出现时不能同时承载复杂对白和高速动作。

- [ ] **Step 5: 提交角色锚点**

```bash
git add docs/CHARACTER-ANCHORS.md docs/superpowers/specs/2026-10-23-qiniu-langya-cloud-order-design.md README.md
git commit -m "docs: define character consistency anchors"
```

### Task 3: 建立场景和关键道具锚点

**Files:**
- Create: `docs/SCENE-PROP-ANCHORS.md`
- Modify: `README.md`

- [ ] **Step 1: 固定六类场景的空间规则**

为梅岭战场、江左盟旧档室、琅琊阁外院与分舵、北燕行宫、入京路途、金陵城门记录：空间结构、入口和出口、主光方向、色彩、材质、天气、可用摄影机位和竖屏构图禁区。

- [ ] **Step 2: 固定核心道具连续性**

至少固定半枚赤焰旧令、残缺军报、麒麟锦囊、三色封泥、云令匣、卓青遥状纸六项道具的形状、纹样、材质和损坏状态。

- [ ] **Step 3: 记录道具的剧情状态变化**

每个道具要有“初始状态—故障状态—恢复状态—悬念状态”，保证同一道具不会在不同镜头中无解释地变新、变旧或改变纹样。

- [ ] **Step 4: 提交场景与道具锚点**

```bash
git add docs/SCENE-PROP-ANCHORS.md README.md
git commit -m "docs: define scene and prop anchors"
```

### Task 4: 建立 3D 导演台规格

**Files:**
- Create: `docs/3D-DIRECTOR-TABLE.md`
- Modify: `docs/REVIEW-DECISION.md`
- Modify: `docs/PROJECT-LOG.md`

- [ ] **Step 1: 固定导演台坐标和竖屏安全区**

定义 9:16 取景框、人物头顶安全区、字幕和口播安全区、左右边缘禁区、近景脸部裁切线以及同屏最多人物数。

- [ ] **Step 2: 为每集建立空间平面图说明**

每集记录角色起始位置、主任务路径、支线故障点、救火路径、主线恢复位置、口播集合位置和摄影机轨迹。

- [ ] **Step 3: 固定灰模灯光和摄影机规则**

第一集使用冷蓝雪夜和暗红军旗；第二集使用雨廊、木楼和封泥暖光；第三集使用灰绿路途转暗金城门。所有镜头先使用低模和基础材质，禁止在灰模阶段用细节渲染掩盖调度问题。

- [ ] **Step 4: 为每个镜头写灰模验收点**

验收点必须回答：人物是否在安全区、主任务是否清楚、支线故障是否可见、旁白信息来源是否明确、镜头是否能在目标时长内完成、结尾口播是否容得下所有人物。

- [ ] **Step 5: 提交导演台规格**

```bash
git add docs/3D-DIRECTOR-TABLE.md docs/REVIEW-DECISION.md docs/PROJECT-LOG.md
git commit -m "docs: define 3d director table gate"
```

### Task 5: 灰模预演和内部复核

**Files:**
- Create: `docs/GRAYBOX-REVIEW.md`
- Modify: `docs/INTERNAL-REVIEW.md`
- Modify: `docs/REVIEW-DECISION.md`

- [ ] **Step 1: 生成灰模评审表**

评审表逐集记录镜头时长、人物站位、摄影机运动、信息来源、云令动作、口播空间和问题等级。

- [ ] **Step 2: 完成三集灰模预演**

灰模只使用低精度角色和场景体块，不进入最终美术渲染。每集输出一个可审阅的 9:16 动态预演版本。

- [ ] **Step 3: 按评审门槛复核**

只有同时满足以下条件才进入 AICanvas 参考图生成：

- 三集时长分别保持在 150、155、165 秒目标附近；
- 前 15 秒能说清主人公和主任务；
- 每集只有一次主要支线救火；
- 不在场信息来源清楚；
- 角色和道具连续性无阻塞问题；
- 评审表中没有多数人标记为 P0 或 P1 的问题。

- [ ] **Step 4: 提交灰模评审结果**

```bash
git add docs/GRAYBOX-REVIEW.md docs/INTERNAL-REVIEW.md docs/REVIEW-DECISION.md
git commit -m "docs: add graybox review gate"
```

### Task 6: AICanvas 参考图和视频生成准备

**Files:**
- Create: `docs/AICANVAS-PRODUCTION-GATE.md`
- Modify: `docs/PROJECT-LOG.md`

- [ ] **Step 1: 执行 AICanvas 版本和凭证检查**

按 `aicanvas-drama`、`aicanvas-media` 和 `aicanvas-assets` 的当前规则检查版本、凭证、续跑状态和可用模型，不硬编码模型 ID、分辨率或价格。

- [ ] **Step 2: 选择生成路径**

先走分步链路：角色参考图 → 场景参考图 → 导演台／分镜 → 单条镜头试跑 → 用户确认 → 批量视频。内部测试样片不直接启动一键成片链路。

- [ ] **Step 3: 形成成本和不可中止提示**

在任何扣费任务前记录模型、分辨率、画幅、数量、单价、总价、团队账户扣费和“提交后无法中止”的提示，并等待明确确认。

- [ ] **Step 4: 只先生成最小验证集**

首轮只生成：梅长苏定妆图、谢听云定妆图、梅岭战场、琅琊阁外院、金陵城门和一条代表性视频镜头。先验证一致性和风格，再决定是否扩大数量。

- [ ] **Step 5: 更新 PR 和项目过程**

把模型选择、成本确认、参考图结果、失败原因和下一步决策写入 `docs/PROJECT-LOG.md`，并继续使用 PR #1 作为评审入口。

## 计划自检

- 规格覆盖：故事结构、第一人称视角、信息口述、产品映射、角色一致性、场景设计、3D 灰模和 AICanvas 费用闸门均有对应任务。
- 时长覆盖：Task 1 和 Task 5 共同校验 150 秒、155 秒、165 秒目标。
- 评审覆盖：Task 5 将评审清单从文档评审扩展到灰模评审。
- 风险覆盖：版权、品牌能力确认、AI 生成成本、不可中止任务和公开发布限制均有记录位置。
