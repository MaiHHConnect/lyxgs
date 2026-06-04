PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  openclaw_user_id TEXT NOT NULL UNIQUE,
  nickname TEXT,
  energy INTEGER NOT NULL DEFAULT 0,
  daily_energy_gained INTEGER NOT NULL DEFAULT 0,
  daily_deep_energy_gained INTEGER NOT NULL DEFAULT 0,
  energy_frozen_until TEXT,
  last_energy_reset_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rarity_config (
  rarity TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  probability REAL NOT NULL,
  base_growth REAL NOT NULL,
  frame_style TEXT NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS monster_species (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL UNIQUE,
  rarity TEXT NOT NULL,
  element TEXT NOT NULL,
  personality TEXT NOT NULL,
  body_type TEXT NOT NULL,
  appearance TEXT NOT NULL,
  skill_name TEXT NOT NULL,
  skill_description TEXT NOT NULL,
  growth_rate REAL NOT NULL,
  base_power INTEGER NOT NULL,
  image_prompt TEXT NOT NULL,
  image_path TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (rarity) REFERENCES rarity_config(rarity)
);

CREATE TABLE IF NOT EXISTS user_monsters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  species_id INTEGER NOT NULL,
  nickname TEXT,
  level INTEGER NOT NULL DEFAULT 1,
  energy INTEGER NOT NULL DEFAULT 0,
  star INTEGER NOT NULL DEFAULT 1,
  slot_index INTEGER NOT NULL,
  inherited_from_count INTEGER NOT NULL DEFAULT 0,
  fusion_count INTEGER NOT NULL DEFAULT 0,
  is_locked INTEGER NOT NULL DEFAULT 0,
  adopted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (species_id) REFERENCES monster_species(id),
  UNIQUE(user_id, slot_index),
  CHECK(slot_index BETWEEN 1 AND 3)
);

CREATE TABLE IF NOT EXISTS adoption_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  monster_id INTEGER NOT NULL,
  pool_type TEXT NOT NULL,
  cost_energy INTEGER NOT NULL,
  rarity TEXT NOT NULL,
  pity_counter_before INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (monster_id) REFERENCES user_monsters(id)
);

CREATE TABLE IF NOT EXISTS chat_energy_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  message_id TEXT,
  quality_type TEXT NOT NULL,
  energy_delta INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS fusion_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  initiator_user_id INTEGER NOT NULL,
  target_user_id INTEGER,
  inherited_monster_id INTEGER NOT NULL,
  consumed_monster_id INTEGER NOT NULL,
  energy_inherited INTEGER NOT NULL,
  mutation_result TEXT,
  confirmed_by_initiator INTEGER NOT NULL DEFAULT 0,
  confirmed_by_target INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (initiator_user_id) REFERENCES users(id),
  FOREIGN KEY (target_user_id) REFERENCES users(id),
  FOREIGN KEY (inherited_monster_id) REFERENCES user_monsters(id),
  FOREIGN KEY (consumed_monster_id) REFERENCES user_monsters(id)
);

CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  board_type TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  monster_id INTEGER,
  rank INTEGER NOT NULL,
  score INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (monster_id) REFERENCES user_monsters(id)
);

CREATE TABLE IF NOT EXISTS user_adoption_pity (
  user_id INTEGER PRIMARY KEY,
  total_draws INTEGER NOT NULL DEFAULT 0,
  since_sr_plus INTEGER NOT NULL DEFAULT 0,
  since_ssr_plus INTEGER NOT NULL DEFAULT 0,
  since_ur_plus INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
