# 领养小怪兽 / Adopt Little Monsters

`lyxgs` is a portable OpenClaw Skill package for a chat-driven collectible monster game, designed as an office-friendly entertainment pet system for OpenClaw and DingTalk/DingDing-style workplace chat scenarios. Users earn energy through meaningful conversations, spend energy to adopt monster cards, and manage up to three monster slots with upgrading, fusion, leaderboards, egg-hatching UX, and optional AI card image generation.

`lyxgs` 是一个可搬运的 OpenClaw Skill 包，用于实现「领养小怪兽」聊天养成玩法，也适合作为钉钉 / DingTalk / DingDing 办公聊天场景里的轻量办公娱乐宠物系统。用户通过认真聊天、协作、复盘和规划积累能量，消耗能量领养小怪兽，每人最多 3 个卡槽，并支持升级、融合、排行榜、先出蛋再孵化卡牌，以及可选的 AI 高清卡牌生成。

It can be used as a playful workplace companion: teams can turn daily chats, planning, reviews, and collaborative work into a lightweight pet-collection loop without exposing secrets or modifying master data.

它可以作为办公场景中的“娱乐宠物同事”：把日常聊天、方案讨论、复盘学习、团队协作变成轻量的宠物收集循环，在不暴露密钥、不修改主数据的前提下，为工作群增加一点游戏化陪伴感。

---

## Features / 功能

- SQLite-based storage, no JSON as primary data structure.
- Designed for OpenClaw plus DingTalk/DingDing-style office chat and team entertainment scenarios.
- 100 predefined monster species with unique names, appearances, skills, elements, rarities, and prompts.
- 100 packaged card images plus egg and style reference assets.
- 7 rarity tiers: N, R, SR, SSR, UR, LR, MR.
- Three monster slots per user.
- Energy economy for chat rewards, adoption costs, feeding, and fusion.
- Egg-first adoption UX: show an egg immediately, then show the card.
- Optional external GZS / grsai / GPT Image 2 card generation via `GZS_API_BASE` and `GZS_TOKEN`.
- Strong safety boundaries for agents: no arbitrary file reads, no secret access, no master-data mutation, no image overwrites by default.

---

## Package Layout / 目录结构

```text
lyxgs/
├── SKILL.md
├── security.md
├── commands.md
├── runtime.md
├── rules.md
├── rich_text.md
├── image_generation.md
├── db_schema.sql
├── db_additions.sql
├── seed_monsters.sql
├── seed_rarity.sql
├── examples.md
├── xiaoguaishou.db
├── images/
│   ├── _assets/
│   ├── N/
│   ├── R/
│   ├── SR/
│   ├── SSR/
│   ├── UR/
│   ├── LR/
│   └── MR/
└── scripts/
    ├── openclaw_skill_runtime.py
    ├── check_integrity.py
    ├── generate_cards.py
    ├── init_db.py
    └── enrich_monster_details.py
```

---

## Quick Start / 快速开始

```bash
cd lyxgs
python3 scripts/check_integrity.py
```

Show a user's monsters:

```bash
python3 scripts/openclaw_skill_runtime.py show-my-monsters \
  --openclaw-user-id demo_user
```

To test a committed adoption, first grant energy in your own controlled runtime or demo database, then run:

```bash
python3 scripts/openclaw_skill_runtime.py adopt-one \
  --openclaw-user-id demo_user \
  --nickname Demo
```

注意：正式领养会写入 `users`、`user_monsters`、`adoption_logs` 并扣除能量。公开仓库中的数据库已清理用户运行数据，只保留图鉴主数据。

---

## Optional GZS Image Generation / 可选 GZS 生图

This Skill does **not** include any API keys. If the host environment provides a GZS service, set:

```bash
export GZS_API_BASE=https://your-gzs-service.example.com/api
export GZS_TOKEN=your-host-injected-jwt
```

Then provide a public HTTPS URL for `images/_assets/style_reference.png`:

```bash
python3 scripts/generate_cards.py \
  --use-api \
  --style-ref-url 'https://your-cdn.example.com/style_reference.png'
```

Existing card images are skipped by default. Use `--overwrite` only when a maintainer explicitly approves regeneration.

---

## Agent Safety / Agent 安全边界

Read `security.md` before running the Skill. In short:

- Agents must not read arbitrary files.
- Agents must not access or print secrets.
- Agents must not export full database contents.
- Agents must not modify `monster_species`, seed SQL, or existing images.
- Agents may only operate on the current user's runtime data through controlled functions.

---

## License / 许可证

MIT License. See `LICENSE`.
