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

## 图片基准提示词

> 9:16 vertical realistic ancient Chinese historical drama, strict first-person subjective POV of a sick but composed strategist moving through a blue-black snowy night, visible gloved hands and the edge of a grey-blue sleeve in the lower frame, one half-open wooden medicine chest with a damp paper military report inside, a red remnant flag blurred in the distance, horse tracks and a fleeing cart ahead, cold moonlight from behind, restrained dark-red accents, wet paper texture, wood grain, snow particles, cinematic natural lighting, shallow depth of field, realistic human-scale perspective, no visible third-person body, no selfie stick, no modern objects, no text, no subtitles, no watermark, no logo, no split screen.

## 视频基准提示词

> Strict first-person subjective POV, 9:16 vertical realistic ancient Chinese historical drama. The camera is the protagonist's chest-height motion camera moving through a blue-black snowy night. Start with the protagonist's gloved hand tightening around a half-open wooden medicine chest; a damp military report is visible inside. The camera advances toward a fleeing cart along horse tracks, snow particles pass close to the lens, the red remnant flag stays blurred in the distance, the cart jolts once, and the protagonist reaches forward without cutting away from the subjective view. One continuous action, physically plausible movement, restrained handheld breathing motion, cold moonlight, wet paper and wood texture, no third-person cutaway, no aerial view, no location change, no modern objects, no text, no subtitles, no watermark, no logo.

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
