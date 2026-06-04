#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime skeleton for the 领养小怪兽 Skill.

This file is a guarded reference implementation. Normal Skill agents must not
read arbitrary files or mutate monster master data. All DB access must go
through the functions in this file or an equivalent trusted runtime layer.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "xiaoguaishou.db"
MAX_SLOTS = 3
FIRST_ADOPTION_COST = 100
NORMAL_ADOPTION_COST = 300
RARITY_WEIGHTS = (
    ("N", 45.0),
    ("R", 28.0),
    ("SR", 15.0),
    ("SSR", 8.0),
    ("UR", 3.0),
    ("LR", 0.9),
    ("MR", 0.1),
)

PROHIBITED_SQL = ("DROP ", "TRUNCATE ", "ALTER ", "ATTACH ", "DETACH ")
READ_ONLY_TABLES = ("monster_species", "rarity_config")


class SkillSecurityError(RuntimeError):
    pass


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def guard_sql(sql: str) -> None:
    normalized = " ".join((sql or "").upper().split()) + " "
    if any(word in normalized for word in PROHIBITED_SQL):
        raise SkillSecurityError("prohibited SQL operation")
    for table in READ_ONLY_TABLES:
        upper_table = table.upper()
        if f"UPDATE {upper_table}" in normalized or f"DELETE FROM {upper_table}" in normalized or f"INSERT INTO {upper_table}" in normalized:
            raise SkillSecurityError(f"{table} is read-only during runtime")


def execute(con: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    guard_sql(sql)
    return con.execute(sql, params)


def ensure_runtime_tables(con: sqlite3.Connection) -> None:
    """Create runtime-only tables without installing master-data triggers."""
    execute(
        con,
        """
        CREATE TABLE IF NOT EXISTS card_generation_jobs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          monster_id INTEGER NOT NULL,
          species_id INTEGER NOT NULL,
          species_code TEXT NOT NULL,
          gzs_history_id INTEGER,
          status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','processing','success','failed','cancelled','saved','skipped')),
          style_ref_url TEXT,
          prompt_used TEXT,
          result_url TEXT,
          local_image_path TEXT,
          overwrite_requested INTEGER NOT NULL DEFAULT 0,
          retry_count INTEGER NOT NULL DEFAULT 0,
          max_retries INTEGER NOT NULL DEFAULT 3,
          error_message TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          completed_at TEXT,
          FOREIGN KEY (user_id) REFERENCES users(id),
          FOREIGN KEY (monster_id) REFERENCES user_monsters(id),
          FOREIGN KEY (species_id) REFERENCES monster_species(id)
        )
        """,
    )


def choose_rarity(rng: random.Random) -> str:
    rarities = [item[0] for item in RARITY_WEIGHTS]
    weights = [item[1] for item in RARITY_WEIGHTS]
    return rng.choices(rarities, weights=weights, k=1)[0]


def render_egg_result(*, species: sqlite3.Row, slot_index: int, cost: int, remaining_energy: int, card_generation_job_id: Optional[int]) -> str:
    lines = [
        "╭━━━━━━━━━━━━━━━━╮",
        "┃ 🥚 小怪兽蛋出现了！",
        f"┃ 稀有度：{species['rarity']}",
        f"┃ 槽位：{slot_index} / 3",
        "┃ 状态：正在孵化高清卡牌",
        "╰━━━━━━━━━━━━━━━━╯",
        "",
        f"抽中物种：{species['name']}（{species['code']}）",
        f"元素：{species['element']} | 性格：{species['personality']}",
        f"消耗：{cost} 能量",
        f"剩余能量：{remaining_energy}",
        "",
        "[孵化蛋图片]",
        "images/_assets/egg_pending.png",
        "",
    ]
    image_path = species["image_path"]
    if (ROOT / image_path).exists():
        lines.extend([
            "[已有卡牌图]",
            image_path,
            "卡牌图已存在，正式运行时不会重复生成。",
        ])
    else:
        lines.extend([
            "[卡牌孵化任务]",
            f"card_generation_job_id={card_generation_job_id or '—'}",
        ])
    return "\n".join(lines)


def ensure_user(openclaw_user_id: str, nickname: Optional[str] = None) -> Dict[str, Any]:
    if not openclaw_user_id:
        raise ValueError("openclaw_user_id required")
    with connect() as con:
        execute(
            con,
            "INSERT OR IGNORE INTO users (openclaw_user_id, nickname) VALUES (?, ?)",
            (openclaw_user_id, nickname),
        )
        if nickname:
            execute(
                con,
                "UPDATE users SET nickname = COALESCE(nickname, ?), updated_at = CURRENT_TIMESTAMP WHERE openclaw_user_id = ?",
                (nickname, openclaw_user_id),
            )
        row = execute(con, "SELECT id, openclaw_user_id, nickname, energy, energy_frozen_until FROM users WHERE openclaw_user_id = ?", (openclaw_user_id,)).fetchone()
        return dict(row)


def get_user_monsters(user_id: int) -> List[Dict[str, Any]]:
    with connect() as con:
        rows = execute(
            con,
            """
            SELECT um.id AS monster_id, um.slot_index, um.level, um.energy, um.star,
                   ms.code, ms.name, ms.rarity, ms.element, ms.personality, ms.image_path
            FROM user_monsters um
            JOIN monster_species ms ON ms.id = um.species_id
            WHERE um.user_id = ?
            ORDER BY um.slot_index
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def find_empty_slot(con: sqlite3.Connection, user_id: int) -> Optional[int]:
    used = {
        row[0]
        for row in execute(con, "SELECT slot_index FROM user_monsters WHERE user_id = ?", (user_id,)).fetchall()
    }
    for slot in range(1, MAX_SLOTS + 1):
        if slot not in used:
            return slot
    return None


def show_my_monsters(openclaw_user_id: str) -> Dict[str, Any]:
    user = ensure_user(openclaw_user_id)
    monsters = get_user_monsters(user["id"])
    return {"user": user, "monsters": monsters, "slot_count": len(monsters), "max_slots": MAX_SLOTS}


def create_card_generation_job_if_missing_image(
    con: sqlite3.Connection,
    *,
    user_id: int,
    monster_id: int,
    species_id: int,
    species_code: str,
    image_path: str,
    prompt_used: str,
    style_ref_url: str = "",
) -> Optional[int]:
    # Existing images are never regenerated by default.
    if (ROOT / image_path).exists():
        return None
    cur = execute(
        con,
        """
        INSERT INTO card_generation_jobs
        (user_id, monster_id, species_id, species_code, status, style_ref_url, prompt_used, local_image_path)
        VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
        """,
        (user_id, monster_id, species_id, species_code, style_ref_url, prompt_used, image_path),
    )
    return int(cur.lastrowid)


def render_slot_full(monsters: List[Dict[str, Any]]) -> str:
    lines = ["你的 3 个小怪兽卡槽已经满了。", "", "当前怪兽："]
    for item in monsters:
        lines.append(f"{item['slot_index']}. {item['name']} {item['rarity']} Lv.{item['level']}")
    lines.append("")
    lines.append("需要先融合，才能继续领养。")
    return "\n".join(lines)


def adopt_one(
    openclaw_user_id: str,
    *,
    nickname: Optional[str] = None,
    pool_type: str = "first",
    cost_energy: Optional[int] = None,
    rng_seed: Optional[int] = None,
    style_ref_url: str = "",
) -> Dict[str, Any]:
    """Official COMMIT adoption action.

    This function mutates only current-user runtime tables. It never modifies
    monster_species, rarity_config, seed SQL files, or existing images.
    """
    cost = cost_energy if cost_energy is not None else (FIRST_ADOPTION_COST if pool_type == "first" else NORMAL_ADOPTION_COST)
    rng = random.Random(rng_seed)
    with connect() as con:
        ensure_runtime_tables(con)
        try:
            execute(con, "BEGIN")
            execute(
                con,
                "INSERT OR IGNORE INTO users (openclaw_user_id, nickname) VALUES (?, ?)",
                (openclaw_user_id, nickname),
            )
            if nickname:
                execute(
                    con,
                    "UPDATE users SET nickname = COALESCE(nickname, ?), updated_at = CURRENT_TIMESTAMP WHERE openclaw_user_id = ?",
                    (nickname, openclaw_user_id),
                )
            user = execute(
                con,
                "SELECT id, openclaw_user_id, nickname, energy, energy_frozen_until FROM users WHERE openclaw_user_id = ?",
                (openclaw_user_id,),
            ).fetchone()
            if not user:
                raise RuntimeError("用户初始化失败")
            if user["energy_frozen_until"]:
                raise RuntimeError(f"能量被冻结至 {user['energy_frozen_until']}，暂不能领养。")
            if int(user["energy"] or 0) < cost:
                raise RuntimeError(f"能量不够，还需要 {cost - int(user['energy'] or 0)} 能量。")

            slot_index = find_empty_slot(con, int(user["id"]))
            if slot_index is None:
                monsters = get_user_monsters(int(user["id"]))
                raise RuntimeError(render_slot_full(monsters))

            rarity = choose_rarity(rng)
            species = execute(
                con,
                "SELECT * FROM monster_species WHERE rarity = ? ORDER BY RANDOM() LIMIT 1",
                (rarity,),
            ).fetchone()
            if not species:
                raise RuntimeError(f"没有可领养的 {rarity} 怪兽。")

            execute(con, "UPDATE users SET energy = energy - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (cost, int(user["id"])))
            cur = execute(
                con,
                "INSERT INTO user_monsters (user_id, species_id, slot_index, energy) VALUES (?, ?, ?, 0)",
                (int(user["id"]), int(species["id"]), slot_index),
            )
            monster_id = int(cur.lastrowid)
            execute(
                con,
                "INSERT INTO adoption_logs (user_id, monster_id, pool_type, cost_energy, rarity) VALUES (?, ?, ?, ?, ?)",
                (int(user["id"]), monster_id, pool_type, cost, species["rarity"]),
            )
            job_id = create_card_generation_job_if_missing_image(
                con,
                user_id=int(user["id"]),
                monster_id=monster_id,
                species_id=int(species["id"]),
                species_code=species["code"],
                image_path=species["image_path"],
                prompt_used=species["image_prompt"],
                style_ref_url=style_ref_url,
            )
            remaining = int(user["energy"] or 0) - cost
            con.commit()
            text = render_egg_result(
                species=species,
                slot_index=slot_index,
                cost=cost,
                remaining_energy=remaining,
                card_generation_job_id=job_id,
            )
            return {
                "ok": True,
                "committed": True,
                "user_id": int(user["id"]),
                "monster_id": monster_id,
                "species_code": species["code"],
                "species_name": species["name"],
                "rarity": species["rarity"],
                "slot_index": slot_index,
                "cost_energy": cost,
                "remaining_energy": remaining,
                "image_path": species["image_path"],
                "card_generation_job_id": job_id,
                "text": text,
            }
        except Exception:
            con.rollback()
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description="领养小怪兽 runtime")
    sub = parser.add_subparsers(dest="command")

    adopt = sub.add_parser("adopt-one", help="officially adopt one monster and COMMIT")
    adopt.add_argument("--openclaw-user-id", required=True)
    adopt.add_argument("--nickname", default="")
    adopt.add_argument("--pool-type", default="first")
    adopt.add_argument("--cost-energy", type=int, default=None)
    adopt.add_argument("--rng-seed", type=int, default=None)
    adopt.add_argument("--style-ref-url", default="")
    adopt.add_argument("--json", action="store_true")

    show = sub.add_parser("show-my-monsters", help="show current user's monsters")
    show.add_argument("--openclaw-user-id", required=True)
    show.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "adopt-one":
        result = adopt_one(
            args.openclaw_user_id,
            nickname=args.nickname or None,
            pool_type=args.pool_type,
            cost_energy=args.cost_energy,
            rng_seed=args.rng_seed,
            style_ref_url=args.style_ref_url,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["text"])
        return
    if args.command == "show-my-monsters":
        result = show_my_monsters(args.openclaw_user_id)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            monsters = result["monsters"]
            if not monsters:
                print("你还没有小怪兽，快去领养一只吧！")
            else:
                for item in monsters:
                    print(f"{item['slot_index']}. {item['name']} {item['rarity']} Lv.{item['level']} / {item['energy']} 能量")
        return
    print("Runtime loaded. Use --help for commands. Do not run destructive operations from Skill agents.")


if __name__ == "__main__":
    main()
