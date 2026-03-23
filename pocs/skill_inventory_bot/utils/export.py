import csv
import io
import json
from datetime import datetime


def discovery_to_json(discovery: dict) -> str:
    """自己探索サマリーをJSON形式でエクスポートする"""
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "discovery": discovery,
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)


def discovery_to_csv(discovery: dict) -> str:
    """自己探索サマリーをCSV形式でエクスポートする"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["カテゴリ", "項目"])

    # 価値観
    for v in discovery.get("values", []):
        writer.writerow(["価値観", v])

    # 強み
    for s in discovery.get("strengths", []):
        writer.writerow(["強み", s])

    # スキル
    skills = discovery.get("skills", {})
    label_map = {"technical": "技術スキル", "human": "ヒューマンスキル", "tacit": "暗黙知"}
    for key, items in skills.items():
        label = label_map.get(key, key)
        for item in items:
            writer.writerow([label, item])

    # 方向性
    if discovery.get("direction"):
        writer.writerow(["方向性", discovery["direction"]])

    # サマリー
    if discovery.get("discovery_summary"):
        writer.writerow(["自己探索サマリー", discovery["discovery_summary"]])

    return output.getvalue()
