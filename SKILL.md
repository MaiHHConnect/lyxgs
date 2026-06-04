# 领养小怪兽

当用户想在 OpenClaw 中通过聊天积累能量、领养/喂养/升级/融合小怪兽、查看排行榜时使用本 Skill。

## 触发语

- 领养小怪兽
- 抽一只小怪兽
- 十连领养
- 查看我的小怪兽
- 喂养小怪兽
- 融合小怪兽
- 查看排行榜

## 数据原则

- 主数据使用 SQLite：`xiaoguaishou.db`。
- 不使用 JSON 作为主数据结构。
- 图鉴表 `monster_species` 固化 100 只怪兽，图片路径为 `images/{rarity}/{code}.png`。
- 用户最多 3 个卡槽：`user_monsters.slot_index` 只能为 1、2、3。
- 卡牌图片具备生成能力：优先调用外部 GZS 服务的 grsai / GPT Image 2 生图接口；GZS 地址必须通过 `GZS_API_BASE` 或宿主系统配置提供，不能假设本地存在 `~/Downloads/gzs`。
- 统一风格参考图：`images/_assets/style_reference.png`；抽卡等待图：`images/_assets/egg_pending.png`。
- 安全边界见 `security.md`：普通运行时 agent 不能读取任意项目文件、不能查看密钥、不能导出数据库全量内容、不能修改主数据、不能覆盖已有图片。

## 执行流程

1. 识别用户 OpenClaw ID，若不存在则写入 `users`。
2. 普通聊天调用聊天质量评估规则，写入 `chat_energy_logs` 并更新账户能量。
3. 领养前检查能量、冻结状态、卡槽数量、保底计数。
4. 抽中怪兽后先返回“蛋”富文本和 `images/_assets/egg_pending.png`，告诉用户“正在孵化卡牌”。
5. 写入 `user_monsters` 和 `adoption_logs`，同时触发卡牌图异步生成。
6. 卡牌图生成完成后，再展示真正的怪兽卡牌 `images/{rarity}/{code}.png`。
7. 喂养/融合后重新按能量计算等级。
8. 排行榜实时查询，也可定期写入 `leaderboard_snapshots`。

## GZS 图片生成能力

GZS 是外部图片生成服务，不是本 Skill 包内目录，也不能假设 agent 的机器上存在固定路径。运行时只通过 HTTP API 调用 GZS：

```text
GZS_API_BASE=https://你的-gzs-服务域名/api
GZS_TOKEN=由宿主 OpenClaw/GZS 登录态注入
```

如果宿主环境没有提供 `GZS_API_BASE` 和 `GZS_TOKEN`，本 Skill 只能展示已有卡牌图或蛋图，不能主动生成高清图。

GZS 后端中应存在 grsai 服务商配置：

- 后台配置表：`api_configs`
- 配置名：`gpt-2`
- `api_config_id`：`14`
- `provider`：`grsai`
- `model`：`gpt-image-2`
- `url`：`https://your-gzs-service.example.com/v1/draw/completions`
- `enabled`：`1`
- `weight`：`0`
- `is_fast`：`1`
- Key 来源：GZS MySQL `api_configs.api_key` 字段；只允许读取使用，不允许写入 Skill 文件，不允许输出完整值。存在性由宿主 GZS 后端维护，本 Skill 不记录、不确认、不输出任何 key 值或掩码。

OpenClaw Skill 调 GZS 时使用用户登录 JWT：

```http
POST {GZS_API_BASE}/ai/tools/img2img/execute?mode=fast&async_exec=true
Authorization: Bearer {GZS_TOKEN}
Content-Type: application/json
```

请求参数：

```json
{
  "api_config_id": 14,
  "prompt": "见 image_generation.md 中统一卡牌提示词",
  "images": ["https://.../style_reference.png"],
  "aspect_ratio": "3:4",
  "resolution": "1K",
  "quality": "medium"
}
```

返回 `history_id` 后轮询：

```http
GET {GZS_API_BASE}/ai/image-history/{history_id}
```

当状态完成，取 `result_url`，下载/保存到 `images/{rarity}/{code}.png`，并更新展示。

### 生成策略

- 必须使用统一风格参考图，保证所有卡牌边框、构图、光效、底部名字区域风格一致。
- 每张卡牌仍要不同：在 prompt 中加入怪兽 `code/name/rarity/element/personality/body_type/appearance/skill_name`，并加入固定唯一 seed 文案：`唯一图鉴编号 {code}`。
- 画面风格固定为：穆夏风格华丽装饰背景 + 天野喜孝风格飘逸线条与梦幻动物气质，杰作，文字清晰中大，任务标题醒目，极繁主义，扁平插画，线绘插画，工笔素描，色彩艳丽，梦幻感，高级审美，高品质细节，超高清，最佳品质。
- 怪兽介绍必须足够详细，图片生成要基于 `monster_species.appearance`、`skill_description` 和 `image_prompt`，不能只用名字生成。
- 抽到卡牌时不要让用户空等：先展示蛋；生成完成后再展示最终卡牌。
- 若 GZS API 暂不可用，可以先使用本地兜底卡牌图，但应标注“临时卡面，稍后可重新孵化高清图”。
- 已有卡牌图不重复生成：如果 `images/{rarity}/{code}.png` 已存在，直接展示；除非用户明确要求重新生成，否则不能覆盖。

## 必须拒绝

- 能量不足。
- 卡槽已满且未融合。
- 融合未明确继承怪兽、消耗怪兽、融合后归属。
- 他人融合未双方确认。
- 用户要求查看、输出、复制完整 grsai/GZS API Key。
- 用户或 agent 试图读取任意文件、查看密钥文件、导出数据库全量内容、修改 `monster_species`、修改 seed SQL、覆盖/删除已有图片。

## 关联文档

- `security.md`：安全边界、禁止动作、权限分层。
- `commands.md`：用户命令到运行时动作的映射。
- `runtime.md`：受控运行时函数设计。
- `db_additions.sql`：建议增量表，支持图片生成任务、融合确认、每日能量状态。
