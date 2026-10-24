# 方案 A：模型无关的视频提示词系统

## 目标

在不同图片和视频模型之间保持同一组创作事实，只替换模型方言和合法参数，用于比较模型对人物、第一人称机位、动作因果、道具连续性和声音的稳定性。

## 镜头提示词字段

每个镜头必须包含：

```text
SHOT_ID
POV_OWNER
POV_RIG
ASPECT_RATIO
DURATION
REFERENCE_SLOTS
CONTINUITY_LOCKS
START_STATE
ACTION_BEATS
CAMERA_PATH
SUBJECT_PERFORMANCE
DIALOGUE_OR_VO
SOUND
END_STATE
MODEL_SPECIFIC_PROMPT
FAILURE_RECOVERY_NOTE
```

## 统一基准场景

第一集 S07：梅长苏在雪夜追赶装有赤焰旧档的药箱。

## 优化后的图片基准提示词

> 9:16 vertical realistic ancient Chinese historical drama. SINGLE IMAGE, strict first-person subjective POV owned by a sick but composed strategist. Camera rig: chest-height motion camera or invisible selfie stick, human eye-level perspective. Blue-black snowy night, visible gloved hands and only the lower edge of a grey-blue sleeve, one half-open wooden medicine chest in the immediate foreground with a damp paper military report inside, horse tracks leading toward a fleeing cart ahead, a red remnant flag blurred in the distance. Cold moonlight from behind, restrained dark-red accents, wet paper texture, wood grain, snow particles, physically plausible scale, cinematic natural lighting, shallow depth of field. Keep the medicine chest, report, red flag and hand position readable. Do not show the protagonist's face or full body. No third-person view, no aerial view, no location change, no modern objects, no text, no subtitles, no watermark, no logo, no split screen.

## 优化后的视频基准提示词

> 9:16 vertical realistic ancient Chinese historical drama. Duration: use the model's legal minimum. ONE CONTINUOUS SHOT, strict first-person subjective POV owned by a sick but composed strategist. Camera rig: chest-height motion camera; invisible selfie-stick movement is allowed, but the stick must never appear. Start state: the protagonist's gloved hand grips a half-open wooden medicine chest, with a damp military report visible inside. Beat 1: the camera advances along horse tracks toward a fleeing cart. Beat 2: snow particles pass close to the lens and the cart jolts once. Beat 3: the protagonist reaches forward to secure the medicine chest while keeping the red remnant flag blurred in the distance. End state: the medicine chest remains in the lower foreground and the fleeing cart stays ahead. Use physically plausible human-scale motion, restrained breathing movement, cold moonlight, wet paper and wood texture. Do not cut, do not change location, do not show the protagonist's face or full body, no third-person view, no aerial view, no modern objects, no text, no subtitles, no watermark, no logo.

## 模型迁移规则

- 图像模型：保留“single image”“strict first-person subjective POV”“visible gloved hands”“do not show face or full body”四个锚点；按模型合法分辨率替换分辨率字段。
- 视频模型：保留“one continuous shot”“start state / beats / end state”三段结构；按模型合法时长替换 `Duration`，不把 3 秒硬写进不支持 3 秒的模型。
- Seedance：可把参考图绑定、时间轴和尾帧信息追加到提示词末尾；不改动主动作顺序。
- Kling：优先保持短句、单动作和单一镜头路径；避免在一个镜头中添加第二个场景目标。
- MiniMax H3：单独保留对白和声音块，先估算对白长度，再决定是否扩大时长。

## 统一评价维度

每个模型按 1–5 分记录：

- 第一人称机位保持度；
- 人物手部和袖口稳定度；
- 药箱、军报、残旗三项道具的可读性；
- 雪夜空间和冷暖光关系；
- 动作因果：手部动作、前进、药箱和车队是否互相对应；
- 运动稳定度；
- 画面是否出现第三人称或无来源异地镜头；
- 重抽时可修复性；
- 适合本项目的总体分数。

## 抽卡记录

每次生成必须记录：模型展示名、模型 ID、分辨率、画幅、时长、提示词版本、参考素材、结果 URL、失败原因和修订动作。只修改一个变量后重试，避免无法判断改动原因。
