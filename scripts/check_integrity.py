#!/usr/bin/env python3
from pathlib import Path
import sqlite3

root = Path(__file__).resolve().parents[1]
db = root / 'xiaoguaishou.db'
assert db.exists(), 'missing xiaoguaishou.db'
con = sqlite3.connect(db)
species = con.execute('select code, rarity, image_path from monster_species').fetchall()
assert len(species) == 100, f'expected 100 monsters, got {len(species)}'
assert con.execute('select count(distinct name) from monster_species').fetchone()[0] == 100
assert con.execute('select count(distinct appearance) from monster_species').fetchone()[0] == 100
missing = [p for _, _, p in species if not (root / p).exists()]
assert not missing, f'missing images: {missing[:5]}'
for rarity in ['N','R','SR','SSR','UR','LR','MR']:
    assert (root / 'images' / rarity).is_dir(), f'missing images/{rarity}'
assert (root / 'images' / '_assets' / 'egg_pending.png').exists(), 'missing egg_pending.png'
assert (root / 'images' / '_assets' / 'style_reference.png').exists(), 'missing style_reference.png'
print('OK: schema, DB, 100 monsters, 100 images, egg asset, style reference, unique names/appearances')
