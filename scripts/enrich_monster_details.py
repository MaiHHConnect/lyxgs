#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich all monster descriptions and image prompts without regenerating images."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "xiaoguaishou.db"
SKILL = ROOT

CATEGORY_LABEL = {
    "fluffy": "毛绒系",
    "dragon": "龙兽系",
    "mecha": "机械系",
    "slime": "史莱姆系",
    "plant": "植物系",
    "ghost": "幽灵系",
    "planet": "星球系",
    "food": "食物系",
    "bug": "昆虫系",
    "beast": "神兽系",
}

ANIMAL_BY_CATEGORY = {
    "fluffy": ["兔狐", "雪貂", "龙猫", "小熊", "云羊", "猫鼬", "飞鼠", "绒鹿", "团雀", "梦貘"],
    "dragon": ["幼龙", "飞龙", "角龙", "海龙", "岩龙", "影龙", "彩龙", "翼龙", "晶龙", "梦龙"],
    "mecha": ["机械鹰", "齿轮熊", "机甲蝎", "量子鱼", "合金狼", "圣骑狮", "磁暴犀", "涡轮隼", "声波龟", "星核狮"],
    "slime": ["凝胶兔", "熔岩蛙", "叶冠蜗", "雷泡猫", "水滴鲸", "沙丘龟", "暗影蝠", "棱镜蝶", "星云狐", "黑洞章"],
    "plant": ["向日葵兔", "橡树熊", "樱花鹿", "食人花猫", "水晶兰狐", "珊瑚海马", "南瓜犬", "黑蔷薇鸦", "彩虹多肉龟", "孢子蘑菇龙"],
    "ghost": ["幽灵猫", "骷髅蝠", "灵蝶", "雾鸦", "魂蛇", "月蝠", "深海魂章", "九尾灵狐", "月光灵鹿", "灯笼魂鲸"],
    "planet": ["星狐", "月蝶", "彗星龙", "虚空鸦", "森林巨人", "环星鲸", "陨石犀", "极光马", "黑洞猫", "星盘鹿"],
    "food": ["焦糖熊", "辣椒龙", "抹茶兔", "芝士狮", "冰淇淋猫", "寿司鲸", "咖啡狐", "蜂蜜蜂", "齿轮饼干龟", "梦糕羊"],
    "bug": ["瓢虫", "晶翅蜻蜓", "雷须蜂", "草甲虫", "光蝶", "暗蛾", "土壳甲", "风蜻蜓", "机械甲虫", "梦茧蚕"],
    "beast": ["麒麟", "玄龟", "白虎", "灵鹿", "凤凰", "貔貅", "狻猊", "天马", "烛龙", "饕餮"],
}

PALETTES = [
    "珍珠白、樱花粉、琥珀金",
    "冰蓝、翡翠绿、月光银",
    "电光紫、亮金、深靛蓝",
    "珊瑚红、奶油黄、暖橙",
    "森林绿、松石蓝、萤火黄",
    "幽黑、暗紫、玫瑰金",
    "陶棕、古铜、苔藓绿",
    "天青、云白、虹彩边光",
    "铬银、蓝白电弧、黑曜石",
    "梦粉、星紫、糖霜白",
]

MATERIALS = ["绒毛", "鳞片", "金属", "果冻凝胶", "叶脉", "雾纱", "星尘", "奶油糖霜", "甲壳", "玉石晶体"]
EYES = ["琥珀圆眼", "冰蓝竖瞳", "电紫星眼", "月牙笑眼", "翠绿杏仁眼", "玫瑰金泪光眼", "古铜镜片眼", "天青猫瞳", "蓝白齿轮眼", "梦粉圆镜眼"]
POSES = ["捧着发光能量核", "展开半透明小翼", "踩在元素法阵中央", "尾巴卷成守护符号", "抱着专属小道具", "侧身回望并扬起光尘", "蜷卧在装饰巢穴里", "跃起穿过花纹圆环", "站在迷你祭坛上", "漂浮在星尘云团前"]

RARITY_FRAME = {
    "N": "木质边框，柔和自然光，适合基础陪伴感",
    "R": "银色边框，轻微光晕，突出明显特征",
    "SR": "蓝紫边框，星点粒子，中级收藏质感",
    "SSR": "金色边框，强烈光效，传说级成长感",
    "UR": "彩虹边框，高级粒子，神话般稀有气场",
    "LR": "红金限定框，限定标识，活动珍藏感",
    "MR": "黑金神话框，压迫感与王者气场，顶级稀有",
}


def category_from_code(code: str) -> tuple[str, int]:
    parts = code.split("_")
    return parts[1], int(parts[2])


def build_detail(row: sqlite3.Row) -> tuple[str, str, str]:
    code = row["code"]
    category, num = category_from_code(code)
    i = num - 1
    label = CATEGORY_LABEL.get(category, "怪兽系")
    animal = ANIMAL_BY_CATEGORY.get(category, ["小兽"] * 10)[i % 10]
    palette = PALETTES[(i + len(category)) % 10]
    material = MATERIALS[(i * 2 + len(category)) % 10]
    eyes = EYES[(i * 3 + len(category)) % 10]
    pose = POSES[(i * 4 + len(category)) % 10]
    frame = RARITY_FRAME.get(row["rarity"], "精致卡牌边框")
    category_motif = {
        "fluffy": "绒线花环、软云、蒲公英种子",
        "dragon": "火焰、鳞片、古代龙纹圆环",
        "mecha": "齿轮、线路、金属铆钉与能量核心",
        "slime": "半透明胶质、气泡、液态星光",
        "plant": "藤蔓、花冠、叶脉与花粉光尘",
        "ghost": "半透明雾气、鬼火、月轮与灵魂丝带",
        "planet": "星环、陨石、星座线与宇宙尘埃",
        "food": "糖霜、香气蒸汽、甜点纹样与烘焙光晕",
        "bug": "翅脉、甲壳、触须与复眼纹章",
        "beast": "神兽冠冕、祥云、圣印与传说光环",
    }.get(category, "元素纹章")

    appearance = (
        f"{row['name']}是一只{label}的{animal}代表怪兽，主色为{palette}，身体材质呈现{material}质感。"
        f"它拥有{eyes}，五官比例圆润可爱但带有{row['rarity']}级卡牌气场；体型为{row['body_type']}，"
        f"姿态是{pose}。身上保留唯一图鉴编号 {code} 的尾饰，尾饰与{row['element']}元素纹章相连，"
        f"周围漂浮{category_motif}。性格{row['personality']}，外观必须与其他小怪兽明显不同，"
        f"颜色、材质、五官、道具、尾饰和背景符号都独立。"
    )
    skill_desc = (
        f"{row['skill_name']}会释放{row['element']}元素的{animal}形光效，先在脚下展开专属纹章，"
        f"再把聊天积累的心情能量转化为守护、增幅或控制效果。技能发动时{category_motif}会被点亮，"
        f"融合后可继承部分能量并强化纹章亮度。"
    )
    prompt = (
        f"领养小怪兽 OpenClaw 收藏卡牌，竖版 3:4 完整卡牌构图。画面风格：将穆夏风格的华丽装饰背景"
        f"与天野喜孝风格的飘逸线条、梦幻人物/动物气质进行融合，杰作，极繁主义，扁平插画，线绘插画，"
        f"工笔素描风格，色彩艳丽，梦幻感，高级审美，高品质细节，超高清分辨率，最佳品质。"
        f"顶部文字清晰中大，任务标题醒目，清晰显示稀有度 {row['rarity']}；底部预留名字铭牌区域，"
        f"中文名字“{row['name']}”要清晰。卡面边框：{frame}。"
        f"主体根据不同任务/元素刻画不同动物代表任务属性：{animal}代表{row['element']}属性与{label}任务气质。"
        f"详细角色设定：{appearance} 技能视觉：{skill_desc}"
        f"背景包含{category_motif}，但中心怪兽轮廓必须清楚；可爱、收藏卡、游戏卡牌、高级装饰，"
        f"不要照片写实，不要恐怖，不要杂乱乱码，不要遮挡标题和铭牌。唯一图鉴编号：{code}。"
    )
    return appearance, skill_desc, prompt


def q(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def rebuild_seed(con: sqlite3.Connection) -> None:
    rows = con.execute(
        """
        SELECT code,name,rarity,element,personality,body_type,appearance,skill_name,
               skill_description,growth_rate,base_power,image_prompt,image_path
        FROM monster_species ORDER BY id
        """
    ).fetchall()
    values = []
    for row in rows:
        values.append(
            "(" + ",".join(
                [
                    q(row["code"]), q(row["name"]), q(row["rarity"]), q(row["element"]),
                    q(row["personality"]), q(row["body_type"]), q(row["appearance"]),
                    q(row["skill_name"]), q(row["skill_description"]), str(row["growth_rate"]),
                    str(row["base_power"]), q(row["image_prompt"]), q(row["image_path"]),
                ]
            ) + ")"
        )
    sql = (
        "INSERT OR REPLACE INTO monster_species "
        "(code,name,rarity,element,personality,body_type,appearance,skill_name,skill_description,growth_rate,base_power,image_prompt,image_path) VALUES\n"
        + ",\n".join(values)
        + ";\n"
    )
    (SKILL / "seed_monsters.sql").write_text(sql, encoding="utf-8")


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM monster_species ORDER BY id").fetchall()
    for row in rows:
        appearance, skill_desc, prompt = build_detail(row)
        con.execute(
            """
            UPDATE monster_species
            SET appearance=?, skill_description=?, image_prompt=?
            WHERE code=?
            """,
            (appearance, skill_desc, prompt, row["code"]),
        )
    con.commit()
    rebuild_seed(con)
    print(f"enriched {len(rows)} monsters; existing image files were not touched")


if __name__ == "__main__":
    main()
