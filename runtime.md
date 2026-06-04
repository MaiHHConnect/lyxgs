# 运行时动作设计

运行时代码只能通过受控函数访问数据库，不能让普通 agent 读取文件或直接执行任意 SQL。

## ensure_user(openclaw_user_id, nickname=None)

- 若用户不存在则创建。
- 返回当前用户 ID、能量、冻结状态。
- 不读取文件，不修改主数据。

## grant_chat_energy(user_id, message_id, quality_type, reason)

- 根据聊天质量规则增加/扣除能量。
- 写入 `chat_energy_logs`。
- 每日普通 +300、深度额外 +500、总 +800。
- 账户能量最低 0。

## adopt_one(user_id, pool_type='normal', element=None)

- 检查能量、冻结、卡槽。
- 按概率和保底从 `monster_species` 只读抽取。
- 写入 `user_monsters` 和 `adoption_logs`。
- 更新用户能量和保底计数。
- 图片存在则直接展示；不存在则显示蛋并写 `card_generation_jobs`。

## adopt_ten(user_id)

- 十连领养。
- 不能超过 3 个卡槽。
- 每抽逐次更新保底。

## show_my_monsters(user_id)

- 查询当前用户怪兽。
- 关联图鉴信息。
- 图片仅返回相对路径。

## feed_monster(user_id, slot_index, feed_energy)

- 检查怪兽归属。
- 扣账户能量。
- 增加怪兽能量并重算等级。

## start_fusion / confirm_fusion / execute_fusion

- 必须明确继承者、消耗者、归属。
- 自己融合需要二次确认。
- 他人融合必须双方确认。
- 只删除 `user_monsters` 中的消耗怪兽拥有记录，不删除图鉴，不删除图片。

## show_leaderboard(board_type)

- 能量榜：按单只怪兽能量排序。
- 收藏榜：稀有度分 + 等级分 + 融合分 + 变异加成。
- 只输出 TOP 10 必要展示字段。

## render_rich_text(template_name, context)

- 根据 `rich_text.md` 的模板输出文本。
- 图片只输出相对路径。
- 缺失图片则显示蛋或提示“卡牌孵化中”。
