# 三集无字幕统一男声交付 v3

本版本按 2026-10-26 的修订要求移除旧装配字幕，采用同一中文男性神经语音逐场叙述，三集结尾复用同一条七牛云广告录音，并单独保存旁白、音乐和口播。

## 交付范围

- 第一集采用 `ep01-revision-v2/media` 的最新修订画面，避免回退到第一集旧素材。
- 第二、三集采用现有无后期字幕原片。本版本调整声音与字幕，**不宣称已经修复用户提出的道具、重复人脸、物理与运镜缺陷**。
- 不添加烧录字幕或文字卡。可选 SRT 文件由实际语音时间表生成，仅供后续审校。
- 旁白使用 `zh-CN-YunyangNeural`，语速 `-4%`，音高 `-5Hz`，为合成男声；沉稳叙事是制作方向，感情和年龄观感仍需听审。
- 逐场语音按画面视频流时长排布，不用文件容器时长累加。不得用剪断句尾的方式适配镜头。
- 音乐为本项目程序合成的五声音阶弦乐主题，三集共用同一源文件。配乐在旁白期间自动降低。
- 结尾固定音频：`audio/unified-brand-tagline.wav`，三集使用相同采样。

## 文件

- `EP01-no-subtitles-male-narration-v3.mp4`：第一集无字幕男声版。
- `EP02-no-subtitles-male-narration-v3.mp4`：第二集声音修订版，画面仍有待修项。
- `EP03-no-subtitles-male-narration-v3.mp4`：第三集声音修订版，画面仍有待修项。
- `three-episodes-no-subtitles-v3.mp4`：三集合片。
- `audio/EP01-narration.wav`、`EP02-narration.wav`、`EP03-narration.wav`：完整独立旁白轨。
- `audio/unified-brand-tagline.wav`：统一品牌口播。
- `audio/unified-original-music.wav`：统一原创合成音乐源。
- `delivery-manifest.json`：实际时长、画面来源与语音时间表。
- `qc/`：FFmpeg skill 的计划、导出与技术检查回执。

## 重建

```sh
python3 -m venv /tmp/langya-audio-runtime
/tmp/langya-audio-runtime/bin/pip install -r production/audio-delivery-v3/requirements.txt
/tmp/langya-audio-runtime/bin/python tools/build_voice_delivery_v3.py
```

`requirements.txt` 位于本目录。重建命令中的安装参数应使用该文件的实际路径。FFmpeg skill 脚本目录由构建脚本常量指向本机已安装技能。
