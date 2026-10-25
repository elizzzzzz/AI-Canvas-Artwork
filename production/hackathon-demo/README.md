# 正式生成修复链样片

本目录记录工作流节点修复后的正式生成结果。所有视频均由 AICanvas 工作流节点提交，使用独立图片输入节点将已完成关键帧注入视频节点，视频生成模式统一为 `reference`，不再使用旧的 `frames/first_frame` 链路。

## 样片

- `ep01s07-minimax-h3-formal-clip.mp4`：第一集雪夜追车，8 秒。
- `ep02s07-minimax-h3-formal-clip.mp4`：第二集雨廊追截，实际 9.425 秒。
- `ep03s05-minimax-h3-formal-clip.mp4`：第三集车轴失控，实际 13.667 秒。
- `formal-preview-v1/qiniu-langya-formal-pilot-preview-v1.mp4`：三条正式片段与章节卡的 39.124 秒拼接预演。

## 统一参数

- 画幅：9:16
- 视频模型：MiniMax-H3
- 分辨率：768P
- 参考图模型：Gemini 3.1 Flash Image，1k，9:16
- 生成门：内部测试门 `pilot_ready=true`
- 画面规则：所有叙事镜头保持指定主人公第一人称；3D 预检使用内部人工审核模式。

节点与媒体资产记录见 `formal-generation-v1.json`。该记录不包含临时签名 URL 或任何凭证。

## 缺陷修复版

- `ep01s07-repair-v2.mp4`：护卫与护送车同步运动，移除贴窗跟跑语义。
- `ep03s05a-repair-v2.mp4`：车轴回报，纸张停留在固定开放木板。
- `ep03s05b-repair-v2.mp4`：固定木板连续段，禁止盒子、盒盖和开合结构。
- `formal-preview-v2/qiniu-langya-formal-repair-preview-v2.mp4`：替换缺陷片段后的拼接预演。
