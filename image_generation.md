# 图片生成说明

图片保存为 `images/{rarity}/{monster_code}.png`。

本 Skill 的图片生成使用外部 **GZS 服务**里的 **grsai / GPT Image 2** 配置。GZS 不是本 Skill 的固定本地目录，不能假设 agent 所在机器有 `~/Downloads/gzs`。不要把完整 API Key 写入本 Skill；Key 由 GZS 后台 `api_configs.api_key` 管理。

运行时通过环境变量或宿主配置定位 GZS：

```bash
export GZS_API_BASE=https://你的-gzs-服务域名/api
export GZS_TOKEN=宿主注入的登录JWT
```

如果没有这两个配置，本 Skill 只展示已有图片，不生成新图。

## 已确认的 GZS 配置

来自 GZS MySQL `api_configs` 表，安全记录如下：

| 字段 | 值 |
|---|---|
| name | gpt-2 |
| api_config_id | 14 |
| provider | grsai |
| model | gpt-image-2 |
| url | https://your-gzs-service.example.com/v1/draw/completions |
| enabled | 1 |
| weight | 0 |
| is_fast | 1 |
| api_key | 存在，保存在 GZS DB，不在 Skill 中明文保存；不在 Skill 中记录任何明文或掩码 |

GZS Provider 内部实际会：

1. 提交任务：`POST /v1/draw/completions`
2. Header：`Authorization: Bearer {api_configs.api_key}`
3. 文生图 payload：`model/prompt/size/webHook/shutProgress/quality`
4. 图生图 payload：`model/prompt/size/urls/webHook/shutProgress/quality`
5. 轮询结果：`POST /v1/draw/result`，payload：`{"id": provider_task_id}`

Skill 不直接碰 grsai Key，统一通过 GZS 的工具 API 调用。

## 推荐调用：图生图 + 统一风格参考图

统一风格参考图：

```text
images/_assets/style_reference.png
```

抽卡等待蛋图：

```text
images/_assets/egg_pending.png
```

推荐使用 `img2img`，把风格参考图作为 `images` 传入，这样所有卡牌更容易保持统一风格：

```bash
export GZS_API_BASE=https://你的-gzs-服务域名/api
export GZS_TOKEN=你的登录JWT
python scripts/generate_cards.py --use-api --style-ref-url 'https://你的OSS/style_reference.png'
```

调用接口：

```http
POST {GZS_API_BASE}/ai/tools/img2img/execute?mode=fast&async_exec=true
Authorization: Bearer {GZS_TOKEN}
Content-Type: application/json
```

请求体：

```json
{
  "api_config_id": 14,
  "prompt": "统一卡牌提示词 + 当前怪兽唯一设定",
  "images": ["https://你的OSS/style_reference.png"],
  "aspect_ratio": "3:4",
  "resolution": "1K",
  "quality": "medium"
}
```

返回异步任务后，轮询：

```http
GET {GZS_API_BASE}/ai/image-history/{history_id}
```

## 统一风格 Prompt 模板

必须把以下风格段落固定放在每张卡牌 prompt 前部：

```text
参考图是一张“领养小怪兽 OpenClaw 收藏卡牌”的统一视觉规范。请严格保持参考图的卡牌游戏风格：竖版 3:4 完整卡牌构图，明显卡牌边框，顶部清晰显示稀有度等级，底部预留名字铭牌区域，中心是一只可爱小怪兽，柔和高级光效，干净背景，精致但不要写实恐怖，适合轻松聊天养成游戏。

画面风格：将穆夏风格的华丽装饰背景与天野喜孝风格的飘逸线条、梦幻动物气质进行融合，杰作；文字清晰中大，任务标题醒目；根据不同任务/元素刻画不同动物代表任务属性；极繁主义，扁平插画，线绘插画，工笔素描风格，色彩艳丽，梦幻感，高级审美，高品质细节，超高清分辨率，最佳品质。
```

每张怪兽追加唯一设定：

```text
唯一图鉴编号：{code}
怪兽名：{name}
稀有度：{rarity}
元素：{element}
性格：{personality}
体型：{body_type}
外观：{appearance}
技能：{skill_name}，{skill_description}
请让它与其他怪兽明显不同：颜色、材质、五官、尾饰、元素纹章、姿态都要独立；但卡牌边框、构图、光效语言和铭牌区域必须与参考图保持一致。
```

不同稀有度边框要求：

- N：木质边框，柔和自然光
- R：银色边框，轻微光晕
- SR：蓝紫边框，星点粒子
- SSR：金色边框，强烈光效
- UR：彩虹边框，高级粒子
- LR：红金边框，限定标识
- MR：黑金边框，神话压迫感

## 抽卡展示流程

1. 抽中后立即展示 `images/_assets/egg_pending.png`。
2. 富文本提示：“小怪兽蛋正在孵化，卡牌高清图生成中。”
3. 后台异步调用 GZS `img2img`。
4. 生成完成后保存到 `images/{rarity}/{monster_code}.png`。
5. 再发送真正卡牌图和怪兽属性。

若 GZS API 不可用，脚本会用本地卡牌渲染兜底，仍保留卡牌边框、稀有度标识和独立图形。

## 已有图片不重复生成

- 当前 `images/{rarity}/{monster_code}.png` 已存在的卡牌，不要自动重复生成。
- `scripts/generate_cards.py` 默认跳过已有图片。
- 只有用户明确要求“重新孵化/重画/覆盖生成”时，才允许使用 `--overwrite`。
- 更新怪兽介绍、技能说明、prompt 时，不触碰已有图片文件。
