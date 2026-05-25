import anthropic
from database.db import get_feature_tickets, get_features


class FeatureProfileService:
    def get_profile(self, feature: str) -> dict:
        """指定機能のチケットを集約してカルテデータを返す"""
        tickets = get_feature_tickets(feature)
        if not tickets:
            return {}

        defects = [t for t in tickets if t["ticket_type"] == "故障管理"]
        issues = [t for t in tickets if t["ticket_type"] == "課題管理"]
        reviews = [t for t in tickets if t["ticket_type"] == "レビュー指摘"]

        root_causes = [
            t["root_cause"] for t in defects if t.get("root_cause")
        ]
        review_comments = [
            t["review_comment"] for t in reviews if t.get("review_comment")
        ]
        resolutions = [
            {"title": t["title"], "resolution": t["resolution"]}
            for t in tickets if t.get("resolution")
        ]

        return {
            "feature": feature,
            "total": len(tickets),
            "defects": defects,
            "issues": issues,
            "reviews": reviews,
            "root_causes": root_causes,
            "review_comments": review_comments,
            "resolutions": resolutions,
        }

    def generate_summary(self, profile: dict, api_key: str) -> str:
        """機能カルテをClaudeで要約し、AIツール注入用のコンテキストを生成する"""
        feature = profile["feature"]
        defects = profile["defects"]
        reviews = profile["reviews"]
        root_causes = profile["root_causes"]
        review_comments = profile["review_comments"]

        defect_lines = "\n".join(
            f"- {t['title']}（原因: {t.get('root_cause', 'なし')}）"
            for t in defects[:10]
        )
        review_lines = "\n".join(f"- {c}" for c in review_comments[:10])

        prompt = f"""以下は「{feature}」機能の品質情報です。

【故障一覧（{len(defects)}件）】
{defect_lines or 'なし'}

【レビュー指摘コメント（{len(reviews)}件）】
{review_lines or 'なし'}

---
上記をもとに、以下の3点を簡潔にまとめてください。

1. **この機能で繰り返し起きやすい故障パターン**（2〜3点）
2. **真の原因に共通する傾向**（1〜2点）
3. **開発・レビュー時に特に注意すべきポイント**（2〜3点）

AIコーディングアシスタント（Copilot等）へのコンテキスト注入を想定した、簡潔で実用的な文章にしてください。"""

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def export_context(self, profile: dict, summary: str | None = None) -> str:
        """AIツールへのコンテキスト注入用テキストを生成する"""
        feature = profile["feature"]
        lines = [
            f"# 機能カルテ: {feature}",
            f"総チケット数: {profile['total']}件"
            f"（故障{len(profile['defects'])}件 / 課題{len(profile['issues'])}件 / レビュー指摘{len(profile['reviews'])}件）",
            "",
        ]

        if profile["root_causes"]:
            lines.append("## 主な真の原因")
            for rc in profile["root_causes"][:5]:
                lines.append(f"- {rc}")
            lines.append("")

        if profile["review_comments"]:
            lines.append("## レビュー指摘傾向")
            for rc in profile["review_comments"][:5]:
                lines.append(f"- {rc}")
            lines.append("")

        if summary:
            lines.append("## AIによる品質サマリー")
            lines.append(summary)

        return "\n".join(lines)
