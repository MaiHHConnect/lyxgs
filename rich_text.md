# 富文本展示规范

## 领养成功

## 抽中后先展示蛋

╭━━━━━━━━━━━━━━━━╮
┃ 小怪兽蛋出现了！
┃ 稀有度：{rarity}
┃ 槽位：{slot_index} / 3
┃ 状态：正在孵化高清卡牌
╰━━━━━━━━━━━━━━━━╯

你消耗了 {cost_energy} 能量。
当前剩余：{remaining_energy} 能量。

[孵化蛋图片]
images/_assets/egg_pending.png

小怪兽已经抽中，正在使用统一风格参考图生成专属卡牌。
生成完成后将展示真正卡面。

## 高清卡牌生成完成

╭━━━━━━━━━━━━━━━━╮
┃ {rarity} · {name}
┃ 元素：{element}
┃ 性格：{personality}
┃ 技能：{skill_name}
┃ 初始能量：{base_power}
┃ 槽位：{slot_index} / 3
╰━━━━━━━━━━━━━━━━╯

你消耗了 {cost_energy} 能量。
当前剩余：{remaining_energy} 能量。

[卡牌图片]
{image_path}

## 能量增加

小怪兽吸收了今天的认真聊天。

+{energy_delta} 能量
原因：{reason}

当前账户能量：{account_energy}
主战怪兽：{main_monster} Lv.{level} / {monster_energy} 能量

## 废话扣能量

小怪兽困惑地看着你。

{energy_delta} 能量
原因：{reason}

当前账户能量：{account_energy}

## 卡槽已满

你的 3 个小怪兽卡槽已经满了。

当前怪兽：
1. {monster_1}
2. {monster_2}
3. {monster_3}

需要先融合，才能继续领养。

## 融合确认

融合请求

发起人：{initiator}
继承怪兽：{inherited_monster}
消耗怪兽：{consumed_monster}

融合后：
- {inherited_name} 继承 {inherit_percent}% 能量
- 有 {mutation_percent}% 概率发生外观变异
- 有 {dual_skill_percent}% 概率获得双魂技能

是否确认？

## 排行榜

小怪兽能量榜 TOP 10

{rank_lines}
