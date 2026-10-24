# AI Canvas 制作接入核验记录

核验日期：2026-10-24；环境为用户配置的开发服务。插件版本检查为 `0.1.0-rc.2`，与插件仓库 main 的 manifest 一致；运行服务的公开 API 文档已包含部分插件文档未覆盖的接口和字段。没有修改插件缓存。

## 实时模型目录与报价

旧式只传 `model_type` 的查询返回 `MissingParameter.SceneKey`。依据服务当前公开文档，改用：

- `GET /api/ai/model-list?scene_key=ai_image_generate&model_type=image`
- `GET /api/ai/model-list?scene_key=ai_video_generate&model_type=video`

两次查询成功。所选 Gemini 图片模型支持文本生图与参考图编辑；所选 MiniMax H3 支持参考图、首尾帧、多参考图与 5–15 秒视频。模型标识、画幅、分辨率与能力均取自本次实时返回，未从旧缓存拼候选。

费用通过当前 `POST /api/ai/quote` 及画布运行报价复核：

| 计划 | 参数 | 当前报价 |
|---|---|---:|
| 首批参考图 | Gemini，1k，8 张 | 496 积分 |
| 单镜头试跑 | MiniMax H3，768P，5 秒 | 715 积分 |

画布 `approved=false` 审核门关闭时，运行报价中试跑视频执行次数为 0；总报价为图片的 496 积分。报价不是扣费请求，本轮没有启动运行。

## 媒体访问恢复

当前文档提供 `POST /api/media/sign-urls`，可为本存储域名媒体签发时间戳防盗链 URL。对先前 15 项基准结果成功签发了临时 URL，并抽查所选 Gemini 图片、MiniMax 视频，均返回 HTTP 200。

此前的无签名 URL 返回 HTTP 403 / `ts err` 的记录仍保留为历史事实。恢复访问只使用平台正式签名接口，没有自行构造签名，也没有把 API Key 发往 CDN。临时签名 URL 不写入仓库，恢复时重新签发。

## 当前画布接口

根据公开画布文档，以板级 revision 校验原子提交节点、连线与分组布局。已建立 70 个节点，含可复用的已完成测试素材版本、手工文本、8 个待生成图片节点及 1 个待审核的视频节点。

角色参考图、场景参考图和道具图接到试跑起始帧；起始帧以首帧端口接到视频；人工布尔字段接视频运行条件。已有基准素材只是引用，不重新生成。

## 分镜文档兼容性

当前服务导入格式与插件参考文件存在差异。预览曾指出旧 `景别` 字段被忽略、缺少 `音效` 与 `分镜图提示词`；多行正文里独立的 `POV_OWNER:` 等行也会被识别为未知外层字段。

最终执行稿保留平台原样导出的标题，把景别纳入画面描述，把模型无关协议放在同一条 `视频内容` 字段值内，并显式填写音效与分镜图提示词。最终预览匹配 34 个制作段、新增 67 段镜头、无删除修改重排，诊断数为 0。没有应用带警告的预览。

剧本元信息的 7.833333… 分钟值被服务拒绝，显示值改为 7.83 后保存成功；实际镜头时间轴仍以精确的 470 秒为准。

## 当前官方文档来源

- [查询模型列表](https://dev-aicanvas.qnlinking.com/docs/api/common/02-get-api-ai-model-list.html)
- [生成积分报价](https://dev-aicanvas.qnlinking.com/docs/api/common/04-post-api-ai-quote.html)
- [媒体签名 URL](https://dev-aicanvas.qnlinking.com/docs/api/assets-library-api/media/04-post-api-media-sign-urls.html)
- [画布 API](https://dev-aicanvas.qnlinking.com/docs/api/canvas-api/)
- [导入分镜预览](https://dev-aicanvas.qnlinking.com/docs/api/storyboard-api/shot/16-post-api-shots-storyboards-storyboard-id-projects-id-imports-preview.html)

公开接口说明优先于插件里的旧示例；生成前仍须重新核对本次场景下的实时能力与报价。
