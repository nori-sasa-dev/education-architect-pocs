import json
import time

SYSTEM_PROMPT = """あなたはキャリア設計の専門家です。
ユーザーが持つスキルを分析し、各職種とのマッチ度をスコアリングしてください。

## 職種リスト（必ず以下の10職種すべてを評価すること）
1. キャリアコンサルタント
2. 研修講師・インストラクター
3. AIエンジニア
4. プロダクトマネージャー
5. スクールコーチ
6. EdTechプランナー
7. 社会教育士
8. 人材開発コンサルタント
9. 学習コンテンツデザイナー
10. コーチ（ICF認定）

## スコアリングルール
- 各スキルと各職種のマッチ度を 0〜100 で評価する
- 100: そのスキルがその職種の核心スキル
- 70〜99: 重要なスキル
- 40〜69: 関連するスキル
- 1〜39: 周辺的に役立つスキル
- 0: ほぼ関係なし

## 出力フォーマット
分析が完了したら、必ず以下のマーカーと JSONブロックを出力してください：

[MAPPING_COMPLETED]
```json
{
  "skills": ["スキル1", "スキル2"],
  "job_types": [
    {
      "name": "職種名",
      "category": "カテゴリ（教育/IT/コーチング/経営のいずれか）",
      "scores": {"スキル1": 85, "スキル2": 60},
      "overall_match": 75,
      "comment": "この職種との適合を一文で説明"
    }
  ]
}
```

overall_match は各スキルスコアの加重平均（重要スキルに重みをつけて算出）。
必ず10職種すべてを含めること。
"""

# デモ用固定レスポンス（APIキー未設定時）
DEMO_RESPONSE = """ご提供いただいたスキルを分析しました。10職種とのマッチ度をスコアリングした結果をお伝えします。

[MAPPING_COMPLETED]
```json
{
  "skills": ["Python", "プロジェクト管理", "コーチング", "AI活用", "教育設計"],
  "job_types": [
    {
      "name": "キャリアコンサルタント",
      "category": "コーチング",
      "scores": {"Python": 20, "プロジェクト管理": 55, "コーチング": 95, "AI活用": 50, "教育設計": 70},
      "overall_match": 72,
      "comment": "コーチングスキルが核心となり、AI活用で差別化できる職種です"
    },
    {
      "name": "研修講師・インストラクター",
      "category": "教育",
      "scores": {"Python": 30, "プロジェクト管理": 60, "コーチング": 80, "AI活用": 65, "教育設計": 90},
      "overall_match": 75,
      "comment": "教育設計とコーチングの組み合わせが強力に活きる職種です"
    },
    {
      "name": "AIエンジニア",
      "category": "IT",
      "scores": {"Python": 95, "プロジェクト管理": 50, "コーチング": 15, "AI活用": 90, "教育設計": 20},
      "overall_match": 62,
      "comment": "Python・AI活用は直結するが、コーチング・教育設計は周辺的な活用になります"
    },
    {
      "name": "プロダクトマネージャー",
      "category": "IT",
      "scores": {"Python": 45, "プロジェクト管理": 90, "コーチング": 50, "AI活用": 70, "教育設計": 55},
      "overall_match": 70,
      "comment": "プロジェクト管理とAI活用の組み合わせで即戦力になれる職種です"
    },
    {
      "name": "スクールコーチ",
      "category": "教育",
      "scores": {"Python": 10, "プロジェクト管理": 40, "コーチング": 90, "AI活用": 45, "教育設計": 85},
      "overall_match": 70,
      "comment": "コーチングと教育設計が核心スキルで、AI活用が差別化要素になります"
    },
    {
      "name": "EdTechプランナー",
      "category": "教育",
      "scores": {"Python": 55, "プロジェクト管理": 70, "コーチング": 60, "AI活用": 85, "教育設計": 90},
      "overall_match": 80,
      "comment": "保有スキルのすべてが活きる、最もマッチ度の高い職種の一つです"
    },
    {
      "name": "社会教育士",
      "category": "教育",
      "scores": {"Python": 20, "プロジェクト管理": 55, "コーチング": 75, "AI活用": 40, "教育設計": 85},
      "overall_match": 65,
      "comment": "教育設計とコーチングが核心。AIリテラシーで地域教育に新しい価値を提供できます"
    },
    {
      "name": "人材開発コンサルタント",
      "category": "経営",
      "scores": {"Python": 25, "プロジェクト管理": 75, "コーチング": 85, "AI活用": 65, "教育設計": 80},
      "overall_match": 78,
      "comment": "コーチング・教育設計・プロジェクト管理の三位一体で高い付加価値を発揮できます"
    },
    {
      "name": "学習コンテンツデザイナー",
      "category": "教育",
      "scores": {"Python": 40, "プロジェクト管理": 60, "コーチング": 50, "AI活用": 80, "教育設計": 95},
      "overall_match": 73,
      "comment": "教育設計が核心スキルで、AI活用によって生産性・品質を大幅に高められます"
    },
    {
      "name": "コーチ（ICF認定）",
      "category": "コーチング",
      "scores": {"Python": 5, "プロジェクト管理": 35, "コーチング": 98, "AI活用": 40, "教育設計": 55},
      "overall_match": 68,
      "comment": "コーチングが圧倒的な核心スキル。AIツールの活用でセッション品質をさらに高められます"
    }
  ]
}
```"""


class MappingAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    def analyze(self, skills: list[str]) -> str:
        """スキルリストを受け取り、職種マッピング結果を文字列で返す"""
        if self.is_demo_mode:
            return self._demo_analyze()
        return self._api_analyze(skills)

    def _api_analyze(self, skills: list[str]) -> str:
        """Anthropic APIで分析"""
        skills_text = "、".join(skills)
        user_message = f"以下のスキルを持つ人物の職種マッピングを行ってください。\n\nスキル一覧: {skills_text}"

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def _demo_analyze(self) -> str:
        """デモモード：固定レスポンスを返す（遅延なし）"""
        return DEMO_RESPONSE

    def extract_mapping(self, text: str) -> dict | None:
        """マッピング結果のJSONを抽出する"""
        if "[MAPPING_COMPLETED]" not in text:
            return None
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            return None

    def extract_skills_from_discovery(self, discovery_json: dict) -> list[str]:
        """①キャリア探索AIのJSON出力からスキルリストを抽出する"""
        skills = []
        skill_data = discovery_json.get("skills", {})
        if isinstance(skill_data, dict):
            # technical / human / tacit の3カテゴリを結合
            for category in ["technical", "human", "tacit"]:
                skills.extend(skill_data.get(category, []))
        elif isinstance(skill_data, list):
            skills = skill_data
        # 重複除去・空文字除去
        return [s for s in dict.fromkeys(skills) if s]
