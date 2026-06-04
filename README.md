# 领养小怪兽 / Adopt Little Monsters

`lyxgs` is a portable OpenClaw Skill package for a chat-driven collectible monster game. Users earn energy through meaningful conversations, spend energy to adopt monster cards, and manage up to three monster slots with upgrading, fusion, leaderboards, egg-hatching UX, and optional AI card image generation.

`lyxgs` 是一个可搬运的 OpenClaw Skill 包，用于实现「领养小怪兽」聊天养成玩法。用户通过认真聊天积累能量，消耗能量领养小怪兽，每人最多 3 个卡槽，并支持升级、融合、排行榜、先出蛋再孵化卡牌，以及可选的 AI 高清卡牌生成。

---

## Features / 功能

- SQLite-based storage, no JSON as primary data structure.
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
