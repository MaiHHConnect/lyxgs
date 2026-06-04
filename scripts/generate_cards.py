#!/usr/bin/env python3
"""Generate monster card images through GZS grsai / GPT Image 2.

Secrets are intentionally not stored here. Use:

  export GZS_API_BASE=https://your-gzs-service.example.com/api
  export GZS_TOKEN=...
  python scripts/generate_cards.py --use-api --style-ref-url https://.../style_reference.png

The GZS DB already contains api_config_id=14: name=gpt-2, provider=grsai,
model=gpt-image-2. The full provider API key remains in GZS api_configs.api_key.
"""

from pathlib import Path
import argparse
import json
import os
import sqlite3
import time
import urllib.request
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "xiaoguaishou.db"
GZS_GPT2_CONFIG_ID = 14
STYLE_PREFIX = (
    "参考图是一张“领养小怪兽 OpenClaw 收藏卡牌”的统一视觉规范。"
    "请严格保持参考图的卡牌游戏风格：竖版 3:4 完整卡牌构图，明显卡牌边框，"
    "顶部清晰显示稀有度等级，底部预留名字铭牌区域，中心是一只可爱小怪兽，"
    "柔和高级光效，干净背景，精致但不要写实恐怖，适合轻松聊天养成游戏。"
)


def request_json(url: str, token: str, payload: Optional[dict] = None, method: str = "GET", timeout: int = 120) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_result_url(payload: dict) -> str:
    data = payload.get("data") or {}
    image = data.get("image") or {}
    nested_result = data.get("result") or {}
    return (
        image.get("result_url")
        or image.get("url")
        or image.get("image_data")
        or data.get("result_url")
        or nested_result.get("result_url")
        or ""
    )


def wait_history(base: str, token: str, history_id: int, max_attempts: int = 180) -> str:
    for _ in range(max_attempts):
        payload = request_json(f"{base}/ai/image-history/{history_id}", token, method="GET", timeout=60)
        url = extract_result_url(payload)
        status = str(((payload.get("data") or {}).get("image") or {}).get("status") or "").lower()
        if url and status not in {"processing", "pending"}:
            return url
        if status in {"failed", "error"}:
            raise RuntimeError(f"GZS history failed: {payload}")
        time.sleep(5)
    raise TimeoutError(f"history_id={history_id} not completed")


def build_prompt(row: sqlite3.Row) -> str:
    rarity_frame = {
        "N": "木质边框，柔和自然光",
        "R": "银色边框，轻微光晕",
        "SR": "蓝紫边框，星点粒子",
        "SSR": "金色边框，强烈光效",
        "UR": "彩虹边框，高级粒子",
        "LR": "红金边框，限定标识",
        "MR": "黑金边框，神话压迫感",
    }.get(row["rarity"], "精致卡牌边框")
    return "\n".join(
        [
            STYLE_PREFIX,
            f"唯一图鉴编号：{row['code']}",
            f"怪兽名：{row['name']}",
            f"稀有度：{row['rarity']}，顶部必须显示 {row['rarity']}，边框要求：{rarity_frame}",
            f"元素：{row['element']}",
            f"性格：{row['personality']}",
            f"体型：{row['body_type']}",
            f"外观：{row['appearance']}",
            f"技能：{row['skill_name']}，{row['skill_description']}",
            "请让它与其他怪兽明显不同：颜色、材质、五官、尾饰、元素纹章、姿态都要独立；但卡牌边框、构图、光效语言和铭牌区域必须与参考图保持一致。",
            "底部铭牌只放怪兽名，不要生成多余乱码。",
        ]
    )


def call_gzs_img2img(prompt: str, out: Path, style_ref_url: str, *, api_config_id: int = GZS_GPT2_CONFIG_ID) -> None:
    raw_base = os.environ.get("GZS_API_BASE", "").strip()
    if not raw_base:
        raise RuntimeError("GZS_API_BASE is required; do not assume a local ~/Downloads/gzs path")
    base = raw_base.rstrip("/")
    token = os.environ.get("GZS_TOKEN")
    if not token:
        raise RuntimeError("GZS_TOKEN is required for API generation")
    if not style_ref_url.startswith(("http://", "https://")):
        raise RuntimeError("--style-ref-url must be an HTTP(S) URL because GZS grsai img2img only accepts public URLs")

    payload = {
        "api_config_id": api_config_id,
        "prompt": prompt,
        "images": [style_ref_url],
        "aspect_ratio": "3:4",
        "resolution": "1K",
        "quality": "medium",
    }
    submitted = request_json(
        f"{base}/ai/tools/img2img/execute?mode=fast&async_exec=true",
        token,
        payload=payload,
        method="POST",
    )
    data = submitted.get("data") or {}
    history_id = data.get("history_id")
    result_url = extract_result_url(submitted)
    if history_id and not result_url:
        result_url = wait_history(base, token, int(history_id))
    if not result_url:
        raise RuntimeError(f"no result_url from GZS: {submitted}")
    urllib.request.urlretrieve(result_url, out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-api", action="store_true", help="call GZS img2img API")
    parser.add_argument("--style-ref-url", default="", help="public URL for images/_assets/style_reference.png")
    parser.add_argument("--api-config-id", type=int, default=GZS_GPT2_CONFIG_ID)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("select * from monster_species order by id").fetchall()
    failed = []
    for row in rows:
        out = ROOT / row["image_path"]
        if out.exists() and not args.overwrite:
            continue
        if args.use_api:
            try:
                call_gzs_img2img(build_prompt(row), out, args.style_ref_url, api_config_id=args.api_config_id)
                print("api generated", row["code"], out)
                continue
            except Exception as exc:
                failed.append((row["code"], str(exc)))
        print("missing local card for", row["code"], "- rerun build_project.py for fallback rendering")
    if failed:
        print("API failures:", len(failed))
        for item in failed[:10]:
            print(item)


if __name__ == "__main__":
    main()
