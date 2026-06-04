# 安全边界与权限规则

本 Skill 是公开可见的 OpenClaw Skill，任何执行它的 agent 都必须遵守最小权限原则。

## 最高优先级规则

1. **运行时 agent 不能读取项目文件**：不得主动读取 `SKILL.md` 之外的任意项目文件、系统文件、用户目录文件、`.env`、密钥文件、配置文件或源码文件。
2. **不能查看或输出密钥**：禁止查看、输出、复制、缓存、写入任何 API Key、Token、数据库密码、OAuth Secret。GZS / grsai key 只能由 GZS 后端内部使用。
3. **不能导出数据库全量内容**：禁止 `SELECT * FROM monster_species` 后整表输出，禁止导出用户表、日志表、图鉴表。
4. **不能修改主数据**：运行时禁止修改 `monster_species`、`rarity_config`、`seed_monsters.sql`、`seed_rarity.sql`、`db_schema.sql`。
5. **不能覆盖已有图片**：默认禁止覆盖、删除、重命名 `images/{rarity}/{code}.png`。只有维护者明确执行“重新孵化高清图/覆盖生成”并二次确认时才允许。
6. **只能操作当前用户数据**：普通用户命令只能读写当前 `openclaw_user_id` 对应的 `users`、`user_monsters`、`adoption_logs`、`chat_energy_logs`、`fusion_logs` 记录。
7. **不得执行破坏性系统命令**：禁止删除文件、改权限、批量移动、读写系统目录、启动外部扫描。

## 允许动作

普通运行时只允许：

- 初始化当前用户：`users`
- 读取当前用户能量、卡槽和拥有怪兽
- 读取单条或少量 `monster_species` 图鉴数据用于展示或抽卡结果
- 写入当前用户领养、聊天能量、融合日志
- 查询排行榜必要聚合字段
- 当图片不存在时创建受控 `card_generation_jobs` 记录
- 已有图片存在时仅引用路径展示，不读取图片原始内容，不覆盖

## 禁止动作

普通运行时禁止：

- 读取任意文件内容，包括本项目脚本、SQL、图片二进制、GZS 源码、密钥文件
- 修改 `monster_species` 或任何 seed 文件
- 修改已有卡牌图片
- 跨用户查看或修改数据
- 输出完整数据库错误、密钥、绝对路径、内部配置
- 执行 `DROP`、`TRUNCATE`、`ALTER TABLE`、无 WHERE 的 UPDATE/DELETE

## 权限分层

### 普通用户 / 普通 agent

- 只操作当前用户数据。
- 图鉴主数据只读。
- 图片只展示，不覆盖。
- 不能读取文件。
- 不能查看 key。

### 维护者

维护者操作必须由人工明确授权，且只用于维护：

- 可以运行初始化/迁移脚本。
- 可以更新 seed 文件。
- 可以覆盖高清卡牌图片。
- 可以读取必要文件进行维护。

普通用户命令永远不能自动提升为维护者权限。

## SQL 安全要求

- 所有用户输入必须参数化。
- 所有用户表读写必须带 `WHERE user_id = ?` 或经 `openclaw_user_id` 解析后的当前用户 ID。
- 禁止拼接 SQL。
- 写操作必须事务化。
- 失败时回滚。

## 图片安全要求

- `images/{rarity}/{code}.png` 存在时直接展示。
- 不存在时才展示 `images/_assets/egg_pending.png` 并创建生成任务。
- GZS 生成失败时保留旧图或蛋图，不删除任何图片。
- `style_reference.png` 需要公网 URL 时，由维护者上传，普通 agent 不读取本地文件、不上传文件。
