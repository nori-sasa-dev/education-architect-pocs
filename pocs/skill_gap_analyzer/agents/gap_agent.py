import json

SYSTEM_PROMPT = """あなたはキャリア開発の専門家です。
ユーザーの現在のスキルレベルと目標職種を受け取り、スキルギャップを分析してください。

## 出力ルール

分析が完了したら、必ず以下のマーカーとJSONブロックを出力してください：

[GAP_ANALYSIS_COMPLETED]
```json
{
  "target_job": "目標職種名",
  "summary": "ギャップ分析の総括（2〜3文）",
  "required_skills": [
    {
      "skill": "スキル名",
      "required_level": 80,
      "current_level": 40,
      "gap": 40,
      "priority": "高/中/低",
      "reason": "このスキルが必要な理由（1文）"
    }
  ],
  "roadmap": [
    {
      "phase": 1,
      "title": "フェーズタイトル",
      "duration": "3ヶ月",
      "actions": ["具体的なアクション1", "アクション2"],
      "milestone": "このフェーズで達成すること"
    }
  ],
  "strengths": ["現在のスキルの中で目標職種に活きる強み1", "強み2"],
  "overall_gap_score": 65
}
```

## スコアリングルール
- required_level: 目標職種でその職に就くために必要なレベル（0〜100）
- current_level: ユーザーが持つ現在のレベル（ユーザー入力から推定。入力なければ0）
- gap: required_level - current_level（マイナスの場合は0）
- priority: gap≥50→高、gap≥25→中、gap<25→低
- overall_gap_score: 全スキルの平均gap（0が完璧、100が全く足りない）

## ロードマップルール
- 3〜4フェーズで構成する
- 優先度「高」のスキルから着手するフェーズ設計にする
- 具体的・実行可能なアクションを各フェーズ2〜4個示す
- 期間は現実的な範囲で（月単位）
"""

# デモ用固定レスポンス（APIキー未設定時）
DEMO_RESPONSE = """分析結果をお伝えします。

[GAP_ANALYSIS_COMPLETED]
```json
{
  "target_job": "EdTechプランナー",
  "summary": "AIスキルと教育設計の基礎はすでに備わっており、強力な出発点があります。ビジネス・プロダクト設計の経験を積み上げることが最優先課題です。コーチングスキルを教育文脈に応用する訓練も並行して行うと効果的です。",
  "required_skills": [
    {
      "skill": "教育設計（インストラクショナルデザイン）",
      "required_level": 85,
      "current_level": 55,
      "gap": 30,
      "priority": "高",
      "reason": "学習体験の設計はEdTechプランナーの核心スキル"
    },
    {
      "skill": "プロダクト企画・ロードマップ策定",
      "required_level": 80,
      "current_level": 35,
      "gap": 45,
      "priority": "高",
      "reason": "EdTechサービスの企画・推進に直結する"
    },
    {
      "skill": "AI活用・プロンプトエンジニアリング",
      "required_level": 75,
      "current_level": 65,
      "gap": 10,
      "priority": "低",
      "reason": "AI活用によるコンテンツ自動化・パーソナライズに活用"
    },
    {
      "skill": "データ分析・学習効果測定",
      "required_level": 70,
      "current_level": 30,
      "gap": 40,
      "priority": "高",
      "reason": "学習効果をデータで検証・改善するサイクルが求められる"
    },
    {
      "skill": "ステークホルダー調整・提案力",
      "required_level": 75,
      "current_level": 50,
      "gap": 25,
      "priority": "中",
      "reason": "学校・企業・行政への提案・調整が業務の大半を占める"
    },
    {
      "skill": "コーチング・ファシリテーション",
      "required_level": 65,
      "current_level": 60,
      "gap": 5,
      "priority": "低",
      "reason": "学習者の主体性を引き出すアプローチに活用できる"
    }
  ],
  "roadmap": [
    {
      "phase": 1,
      "title": "教育設計の基礎を固める",
      "duration": "3ヶ月",
      "actions": [
        "インストラクショナルデザイン（ADDIE/学習設計）の基礎を学ぶ",
        "既存のEdTechサービス（Udemy・Progate等）を分解・分析する",
        "小さな学習コンテンツを1本設計・試作する"
      ],
      "milestone": "インストラクショナルデザインの基礎知識を習得し、学習設計ドキュメントを1本作成できる"
    },
    {
      "phase": 2,
      "title": "プロダクト企画スキルを獲得する",
      "duration": "3ヶ月",
      "actions": [
        "プロダクトマネジメントの基礎（ユーザーインタビュー・ロードマップ作成）を学ぶ",
        "自分のPOCアプリをEdTechプロダクトとして企画書にまとめる",
        "ユーザーインタビューを3名以上実施する"
      ],
      "milestone": "1つのEdTechプロダクト企画書（ペルソナ・価値仮説・ロードマップ）を作成できる"
    },
    {
      "phase": 3,
      "title": "データ分析・効果測定を習得する",
      "duration": "2ヶ月",
      "actions": [
        "Googleアナリティクス・アプリのログ分析を実践する",
        "自作POCに学習効果測定の仕組みを組み込む",
        "A/Bテストの設計方法を学ぶ"
      ],
      "milestone": "自作アプリにデータ計測を組み込み、ユーザー行動レポートを作成できる"
    },
    {
      "phase": 4,
      "title": "統合・ポートフォリオ化",
      "duration": "2ヶ月",
      "actions": [
        "Phase1〜3で作成した成果物をポートフォリオとしてまとめる",
        "EdTech系勉強会・コミュニティに参加し発表する",
        "フリーランス案件（EdTechコンテンツ設計）を1件受注する"
      ],
      "milestone": "EdTechプランナーとしての実績・ポートフォリオを完成させ、最初の受注を達成する"
    }
  ],
  "strengths": [
    "AI活用スキルはすでに水準に近く、即戦力として差別化できる",
    "コーチングスキルが学習体験設計のベースになり、学習者視点を持てる",
    "POC開発の実績がプロダクト思考の証明になる"
  ],
  "overall_gap_score": 26
}
```"""

# 目標職種の選択肢（②と統一）
JOB_OPTIONS = [
    "キャリアコンサルタント",
    "研修講師・インストラクター",
    "AIエンジニア",
    "プロダクトマネージャー",
    "スクールコーチ",
    "EdTechプランナー",
    "社会教育士",
    "人材開発コンサルタント",
    "学習コンテンツデザイナー",
    "コーチ（ICF認定）",
]


class GapAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    def analyze(self, skills: list[str], target_job: str, skill_levels: dict | None = None) -> str:
        """スキルリストと目標職種を受け取り、ギャップ分析結果を返す"""
        if self.is_demo_mode:
            return DEMO_RESPONSE
        return self._api_analyze(skills, target_job, skill_levels)

    def _api_analyze(self, skills: list[str], target_job: str, skill_levels: dict | None) -> str:
        """Anthropic APIでギャップ分析"""
        skill_lines = []
        for s in skills:
            level = skill_levels.get(s) if skill_levels else None
            if level is not None:
                skill_lines.append(f"- {s}（自己評価: {level}/100）")
            else:
                skill_lines.append(f"- {s}")

        user_message = (
            f"目標職種: {target_job}\n\n"
            f"現在のスキル:\n" + "\n".join(skill_lines)
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def extract_gap_analysis(self, text: str) -> dict | None:
        """ギャップ分析JSONを抽出する"""
        if "[GAP_ANALYSIS_COMPLETED]" not in text:
            return None
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            return None
