# 人工审阅声明

## 声明时间

2026-10-26（Asia/Shanghai）。

## 用户声明

用户已人工查看当前项目中的全部审核材料，并声明当前范围全部批准。该声明覆盖：

- 100 项可复用三维代理资产；
- 23 项角色/场景/道具语义资产；
- 67 个正式视频片段的当前规划与已提供证据；
- 1 个视频试跑范围；
- 1 个 P01 修图范围。

## 状态边界

这份声明记录用户的人工查看结论，不自动替代每个范围的正式 3D report、证据文件哈希、revision、命名审核人和 `artifact_set_sha256`。因此：

- `user_review` 可以记录为已人工查看；
- `production/geometry/coverage-v1.json` 的正式 `approved_count` 继续为 0，直到每个范围完成正式审核包；
- `python3 tools/geometry_preflight.py` 仍必须对每个 exact scope 返回 0，才能进入对应生成流程；
- AI Canvas 的生成条件继续关闭；
- 不把“全部批准”解释为自动批准图片、视频、P01 修图或费用执行。

## 正式签核需要补齐

每个范围仍需有：

1. 当前模型、场景、相机、预览、深度和物体 ID 文件；
2. 实际 report 和视频逐帧 samples；
3. 当前 `source_sha256` 和 `revision`；
4. 真实审核人、审核时间和 `artifact_set_sha256`；
5. 对应 exact scope 的预检返回码 0。
