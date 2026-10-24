# 模型基准测试结果

- 执行日期：2026-10-24
- 测试场景：第一人称雪夜追车，药箱内有湿损军报，远处有赤焰残旗
- 提示词：见 `docs/PROMPT-SYSTEM.md`
- 画幅：9:16
- 结果状态：12 张图片、3 条视频均完成
- 视觉评分：待结果链接可访问后进行

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
