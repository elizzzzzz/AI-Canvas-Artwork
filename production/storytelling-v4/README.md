# 娓娓讲述版 v4

本轮修改三集旁白的口吻，采用当事人回忆往事的方式，说清人、物和事情的前后缘由。

- 故事正文共 34 段，唯一文字源为 `narration.json`。
- 正文禁止出现“主线、支线、任务、版本、调度、模型、开发者、制片”等工作术语。
- 正文不讲相机、视角、道具摆放规范，不把制作提示词读给观众。
- 保留既定七牛云广告末句“为你的主任务保驾护航”，单独存放在品牌口播音轨中，不纳入故事正文。
- 三集同一中文男性合成声音：`zh-CN-YunyangNeural`；语速 -4%，音高 -5Hz。
- 每场按实际画面时间放置完整句子；旁白过长就改短句子，不变调加速、不裁掉句尾。
- 同一配乐主题、同一品牌口播音频。单独保存三集旁白、音乐和广告录音。
- 沿用上一轮去掉后期字幕的画面，不添加烧录字幕或章节卡；可选 SRT 仅供审校。

## 文件与状态

- `EP01-no-subtitles-male-narration-v4.mp4`：第一集使用 EP01 v2 修订原片。
- `EP02-no-subtitles-male-narration-v4.mp4`、`EP03-no-subtitles-male-narration-v4.mp4`：第二、三集仅修订声音，仍待道具、人脸及运镜画面修复。
- `three-episodes-storytelling-v4.mp4`：三集合片。
- `audio/EP01-narration.wav`、`EP02-narration.wav`、`EP03-narration.wav`：独立完整旁白。
- `audio/unified-brand-tagline.wav`：三集共用品牌口播。
- `audio/unified-original-music.wav`：三集共用原创合成配乐主题。
- `delivery-manifest.json`：声画时间安排及来源。

本轮仅完成叙述口吻和音频修订，不等同于后两集的画面重绘，也不宣称模型生成的画内文字、脸部和物理问题已全部消除。

## 重建

使用 v3 的 `requirements.txt` 创建运行环境后执行：

```sh
/tmp/langya-audio-runtime/bin/python tools/build_storytelling_v4.py
```

合成缓存校验包含正文、声音、语速和音高的哈希，改文案后不会误用旧录音。
