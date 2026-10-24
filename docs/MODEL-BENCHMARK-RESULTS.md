# 模型基准测试结果

- 执行日期：2026-10-24
- 测试场景：第一人称雪夜追车，药箱内有湿损军报，远处有赤焰残旗
- 提示词：见 `docs/PROMPT-SYSTEM.md`
- 请求画幅：9:16；服务端尺寸记录发现偏差，见下方“结果恢复核验”
- 结果状态：12 张图片、3 条视频均完成
- 视觉评分：尚无代理侧评分；用户已手动查看素材并选定优先组合
- 制作优先组合：MiniMax H3 视频 + Gemini 3.1 Flash Image 图片，详见 [模型选择记录](MODEL-SELECTION.md)

## 图片结果

| 模型 | 参数 | 试验 | 状态 | 结果 |
|---|---|---:|---|---|
| GPT Image 2.5 Flare | 1K | 1 | completed | [查看结果](https://canvas-test.ifsdc.com/images/ai_gen_ec18270b_1792821295.png) |
| GPT Image 2.5 Flare | 1K | 2 | completed | [查看结果](https://canvas-test.ifsdc.com/images/ai_gen_96186db0_1792821288.png) |
| GPT Image 2.5 Flare | 1K | 3 | completed | [查看结果](https://canvas-test.ifsdc.com/images/ai_gen_03ee2b27_1792821289.png) |
| Seedream 5.0 Pro | 2K | 1 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/images/04a4b7fc-0819-4d88-ac57-e03c84419bee_0.jpeg) |
| Seedream 5.0 Pro | 2K | 2 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/images/69a8bd88-d418-4ef2-b91c-8d4e831cd19d_0.jpeg) |
| Seedream 5.0 Pro | 2K | 3 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/images/be1e1dcc-9f26-4f0d-aece-0c9cb31a6b6e_0.jpeg) |
| Gemini 3.1 Flash Image | 1K | 1 | completed | [查看结果](https://canvas-test.ifsdc.com/images/ai_gen_f202d378_1792821350.png) |
| Gemini 3.1 Flash Image | 1K | 2 | completed | [查看结果](https://canvas-test.ifsdc.com/images/ai_gen_14f17f7e_1792821350.png) |
| Gemini 3.1 Flash Image | 1K | 3 | completed | [查看结果](https://canvas-test.ifsdc.com/images/ai_gen_61fb2427_1792821351.png) |
| Kling Image O1 | 2K | 1 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/images/7b285a83-f117-4e37-be76-b88f4068a3ab_0.png) |
| Kling Image O1 | 2K | 2 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/images/a909f670-041b-41ce-b410-48bd521f0690_0.png) |
| Kling Image O1 | 2K | 3 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/images/434014eb-ed79-4080-9b9b-54459064ac22_0.png) |

## 视频结果

| 模型 | 参数 | 状态 | 结果 |
|---|---|---|---|
| Kling V3 Omni | 1080p，3 秒 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/videos/5176511e-b8ac-4f15-a12c-f4140331ee5e_0.mp4) |
| Seedance 2.5 | 720p，4 秒 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/videos/a2a05526-b15f-4072-8eb3-48f3f535f44d_0.mp4) |
| MiniMax-H3 | 768P，5 秒 | completed | [查看结果](https://canvas-test.ifsdc.com/ai_gen/videos/def65f16-3d87-4cc7-acb1-45b6a52e7a80_0.mp4) |

## 实际执行记录

- 首轮图片提交：12 个任务；
- 首轮视频提交：3 个任务；
- 图片任务成功：12 个；
- 视频任务成功：3 个；
- Gemini `2l` 参数被服务端拒绝，改用同一实时模型列表中的 `1k` 重新提交；
- Kling 视频显式 `video_mode` 被服务端拒绝，按接口默认模式重新提交成功；
- 实际预估成本：约 2492 积分；
- 结果链接在当前会话中访问时返回 `403 Forbidden / ts err`，因此尚未给出视觉质量排名。

## 下一步评分

结果可访问后，按以下指标逐模型评分：

- 第一人称机位保持度；
- 手部、袖口和道具稳定度；
- 药箱、军报、残旗可读度；
- 动作顺序完成度；
- 是否出现第三人称切镜或异地跳转；
- 运动稳定度；
- 失败后单变量修复能力；
- 成本与画质平衡。

## 结果恢复核验

核验日期：2026-10-24（Asia/Shanghai）。本轮仅恢复和检查已完成任务，新增生成请求 **0**，新增生成积分 **0**。

- 重置后从 `launchctl` 读取配置，`GET /api/auth/me` 返回 `code: 0`；鉴权通过。
- 重新读取全部 15 个任务，均为 `completed`。这只证明服务端报告生成完成，不证明结果文件可访问或画面合格。
- 对全部 15 个结果 URL 发起不带凭证的 Range GET 探测，均返回 **HTTP 403**、`Content-Type: text/html`、`X-Error-Detail: ts err`。
- 另查一张代表图片的素材详情及团队素材时间线，返回的仍是同一批无查询参数的结果 URL，未取得新的签名下载地址。没有构造签名或把 API Key 发往 CDN。
- `ts err` 的具体服务端含义尚未确认；不能据此断言密钥错误、文件损坏、文件不存在或某个模型生成失败。
- 当前浏览器的 AI Canvas 控制台停留在登录页，尚未在已登录的控制台验证预览是否可用。
- 15 项素材已归档至 **琅琊云令 模型基准测试 20261024**；通过目录查询核对为 12 张图片、3 条视频，素材集合与本轮任务一致。此次归档不创建副本、不重新生成。

### 服务端记录的图片尺寸

下表来自任务接口的 `metadata`，尚未下载并解码原文件。画幅误差计算为 `abs((宽/高)/(9/16)-1)`。

| 模型 | 样本数 | 服务端记录尺寸 | 与 9:16 的相对误差 | 处理意见 |
|---|---:|---|---:|---|
| GPT Image 2.5 Flare | 3 | 1024×1536 | 18.519% | 2:3，画幅检查不通过；保留原结果，先调查参数映射 |
| Seedream 5.0 Pro | 3 | 1584×2816 | 0% | 元数据为精确 9:16，仍待视觉检查 |
| Gemini 3.1 Flash Image | 3 | 768×1376 | 0.775% | 接近 9:16，不能写作精确 9:16；成片需统一画幅 |
| Kling Image O1 | 3 | 1536×2720 | 0.392% | 接近 9:16，不能写作精确 9:16；成片需统一画幅 |

GPT Image 任务返回的 `request_params` 同时记录 `aspect_ratio: 9:16` 和 `size: 1024x1536`。参数记录本身存在画幅不一致，应先核对平台到供应商的尺寸映射；当前证据不足以把问题归因于提示词。未因此重跑任何付费任务。

### 服务端记录的视频时长

| 模型 | 计划生成时长 | 服务端记录时长 | 记录来源 |
|---|---:|---:|---|
| Kling V3 Omni | 3 秒 | 3.041667 秒 | 任务 `metadata`，`duration_source=ffprobe` |
| Seedance 2.5 | 4 秒 | 4.064 秒 | 同上 |
| MiniMax-H3 | 5 秒 | 5.175 秒 | 同上 |

视频时长尚未由本地解码复核。可访问后先比较各片前 3 秒的共同观察窗，再另评完整片段动作闭环；3/4/5 秒、不同分辨率仍是比较中的混杂因素。每个视频模型仅 1 个样本，只能用于初筛，不能估计稳定成功率或宣称模型胜出。

### 提示词与成本复核

- 12 张图片的任务 `prompt` SHA-256 一致；3 条视频的任务 `prompt` SHA-256 一致。图片与视频各使用自己的统一提示词，二者并非同一段文本。哈希一致只验证正向提示词，不能代表各供应商内部参数完全相同。
- 已提交任务状态记录的预估积分合计 **2492**；尚未对账，不应写成最终实际扣费。
- 本轮没有提交新的生成任务，没有选择主模型或备选模型，没有给不可访问的素材补造视觉分数。
- 可复核的脱敏记录：[model-benchmark-20261024.json](evidence/model-benchmark-20261024.json)。记录不包含凭证、账户联系方式或完整提示词。

### 恢复评审的条件

需要平台提供能正常访问的预览或签名下载地址，或在已登录的 AI Canvas 控制台确认预览可用。恢复后直接评审现有 15 项素材，不以重跑生成替代访问链路修复。任何新增付费补测都须重新核对实时模型参数、说明增量费用，并使用已经授权的范围或取得新的确认。


## 用户查看后的模型选择

2026-10-24，用户确认已手动下载并查看测试视频和图片，要求优先使用 **MiniMax H3 视频 + Gemini 3.1 Flash Image 图片**。以此作为后续制作的优先组合，不再把代理侧结果 URL 无法访问当作模型选择的前置阻塞。

上方“结果恢复核验”保留当次接口检查的历史事实；它不代表用户无法下载。代理尚未取得这些媒体进行独立评分，也没有对本轮 URL 做新的访问复测。下一步按 [制作模型优先组合](MODEL-SELECTION.md) 准备参考资产与代表镜头试跑。
