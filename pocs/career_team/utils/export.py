import json
import csv
import io
from datetime import datetime


def report_to_json(report: dict) -> str:
    """キャリアレポートをJSON文字列に変換"""
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "report": report,
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)


def report_to_csv(report: dict) -> str:
    """キャリアレポートをCSV文字列に変換"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["カテゴリ", "サブカテゴリ", "項目"])

    # セッションサマリー
    if report.get("session_summary"):
        writer.writerow(["セッションサマリー", "", report["session_summary"]])

    # 自己探索
    se = report.get("self_exploration", {})
    for v in se.get("values", []):
        writer.writerow(["自己探索", "価値観", v])
    for s in se.get("strengths", []):
        writer.writerow(["自己探索", "強み", s])
    for k in se.get("keywords", []):
        writer.writerow(["自己探索", "キーワード", k])

    # 市場分析
    mc = report.get("market_context", {})
    for t in mc.get("trends", []):
        writer.writerow(["市場分析", "トレンド", t])
    for o in mc.get("opportunities", []):
        writer.writerow(["市場分析", "機会", o])
    for d in mc.get("directions", []):
        writer.writerow(["市場分析", "方向性", d])

    # キャリア戦略
    cs = report.get("career_strategy", {})
    for d in cs.get("directions", []):
        writer.writerow([
            "キャリア戦略",
            f"方向性（{d.get('fit_score', '')}）",
            f"{d.get('name', '')} - {d.get('rationale', '')}",
        ])
    if cs.get("recommended"):
        writer.writerow(["キャリア戦略", "推奨", cs["recommended"]])

    # アクションプラン
    ap = report.get("action_plan", {})
    for a in ap.get("immediate_actions", []):
        writer.writerow([
            "アクションプラン",
            f"即時（{a.get('deadline', '')}）",
            a.get("action", ""),
        ])
    for g in ap.get("medium_term_goals", []):
        writer.writerow([
            "アクションプラン",
            "中期目標",
            f"{g.get('goal', '')} - {g.get('milestone', '')}",
        ])

    # チームメッセージ
    if report.get("team_message"):
        writer.writerow(["チームメッセージ", "", report["team_message"]])

    return output.getvalue()
