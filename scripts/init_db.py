#!/usr/bin/env python3
from pathlib import Path
import sqlite3

root = Path(__file__).resolve().parents[1]
db = root / 'xiaoguaishou.db'
skill = root
if db.exists():
    db.unlink()
con = sqlite3.connect(db)
con.executescript((skill / 'db_schema.sql').read_text(encoding='utf-8'))
con.executescript((skill / 'seed_rarity.sql').read_text(encoding='utf-8'))
con.executescript((skill / 'seed_monsters.sql').read_text(encoding='utf-8'))
con.commit()
print('initialized', db)
print('monster_species', con.execute('select count(*) from monster_species').fetchone()[0])
con.close()
