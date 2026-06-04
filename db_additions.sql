PRAGMA foreign_keys = ON;

-- 图片生成任务：记录“先蛋后卡”的异步状态，不修改 monster_species。
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
);

CREATE INDEX IF NOT EXISTS idx_card_generation_jobs_user_status ON card_generation_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_card_generation_jobs_monster ON card_generation_jobs(monster_id);
CREATE INDEX IF NOT EXISTS idx_card_generation_jobs_status_created ON card_generation_jobs(status, created_at);

-- 融合确认状态机：pending 阶段不改拥有数据。
CREATE TABLE IF NOT EXISTS fusion_confirmations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fusion_log_id INTEGER NOT NULL UNIQUE,
  initiator_user_id INTEGER NOT NULL,
  target_user_id INTEGER,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','initiator_confirmed','target_confirmed','completed','rejected_by_initiator','rejected_by_target','expired','cancelled')),
  expire_at TEXT,
  initiator_confirmed_at TEXT,
  target_confirmed_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fusion_log_id) REFERENCES fusion_logs(id),
  FOREIGN KEY (initiator_user_id) REFERENCES users(id),
  FOREIGN KEY (target_user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_fusion_confirmations_status ON fusion_confirmations(status, target_user_id);

-- 每日能量状态：与 users 表兼容，便于审计每日上限与冻结。
CREATE TABLE IF NOT EXISTS user_daily_energy_state (
  user_id INTEGER PRIMARY KEY,
  reset_date TEXT NOT NULL,
  daily_normal_gained INTEGER NOT NULL DEFAULT 0,
  daily_deep_gained INTEGER NOT NULL DEFAULT 0,
  daily_total_gained INTEGER NOT NULL DEFAULT 0,
  frozen_until TEXT,
  freeze_reason TEXT,
  last_event_type TEXT,
  last_event_at TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_user_daily_energy_state_frozen ON user_daily_energy_state(frozen_until);

-- 防护触发器：运行时保护图鉴主数据。维护者如需重建 DB，应先不要安装这些触发器或在维护事务中显式移除。
CREATE TRIGGER IF NOT EXISTS protect_monster_species_update
BEFORE UPDATE ON monster_species
BEGIN
  SELECT RAISE(ABORT, 'monster_species is read-only during skill runtime');
END;

CREATE TRIGGER IF NOT EXISTS protect_monster_species_delete
BEFORE DELETE ON monster_species
BEGIN
  SELECT RAISE(ABORT, 'monster_species is read-only during skill runtime');
END;
