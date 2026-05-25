import json
import re
import random
import anthropic

# ─── デモデータ ───────────────────────────────────────────

DEMO_TASKS_INPUT = [
    {"name": "週次レポートの作成", "description": "ExcelでKPIデータを集計しWord報告書を作成する", "monthly_count": 4, "minutes_per_task": 60, "frequency": "週次"},
    {"name": "会議の議事録作成", "description": "定例会議後にメモから議事録を整形してメール送付", "monthly_count": 8, "minutes_per_task": 45, "frequency": "週次"},
    {"name": "メール返信（問い合わせ対応）", "description": "社内外からの問い合わせメールへの返信", "monthly_count": 80, "minutes_per_task": 10, "frequency": "毎日"},
    {"name": "Redmineチケットの進捗確認・更新", "description": "担当チケットのステータス確認と進捗コメント記入", "monthly_count": 20, "minutes_per_task": 15, "frequency": "週次"},
    {"name": "協力会社との定例MTG", "description": "月次の進捗報告・課題共有・関係構築", "monthly_count": 2, "minutes_per_task": 90, "frequency": "月次"},
    {"name": "新機能の仕様書レビュー", "description": "開発チームが作成した仕様書の論理矛盾・抜け漏れ確認", "monthly_count": 4, "minutes_per_task": 60, "frequency": "週次"},
    {"name": "チームメンバーの相談対応", "description": "業務・キャリア・人間関係に関する1on1相談", "monthly_count": 8, "minutes_per_task": 30, "frequency": "週次"},
    {"name": "請求書・稟議書の確認・承認", "description": "経費申請・外注発注の内容確認と承認", "monthly_count": 10, "minutes_per_task": 15, "frequency": "月次"},
]

DEMO_DIAGNOSIS_TASKS = [
    {"name": "週次レポートの作成", "category": "AI_AUTOMATE", "time_reduction_pct": 85,
     "reduction_reason": "データ収集90%・集計85%・文書化80%が自動化可能。人間はレビューのみ",
     "priority": "HIGH", "suggested_tool": "Claude API + Python",
     "monthly_count": 4, "minutes_per_task": 60},
    {"name": "会議の議事録作成", "category": "AI_AUTOMATE", "time_reduction_pct": 90,
     "reduction_reason": "音声認識で文字起こし→Claude要約で完全自動化。整形・送付も自動化可",
     "priority": "HIGH", "suggested_tool": "Whisper + Claude API",
     "monthly_count": 8, "minutes_per_task": 45},
    {"name": "メール返信（問い合わせ対応）", "category": "AI_AUGMENT", "time_reduction_pct": 60,
     "reduction_reason": "ドラフト生成70%削減・文章確認は人間が担う。定型問い合わせは完全自動化も可",
     "priority": "HIGH", "suggested_tool": "Claude API",
     "monthly_count": 80, "minutes_per_task": 10},
    {"name": "Redmineチケットの進捗確認・更新", "category": "AI_AUGMENT", "time_reduction_pct": 50,
     "reduction_reason": "サマリー生成・ステータス把握はAI、優先度判断・コメント内容は人間",
     "priority": "MEDIUM", "suggested_tool": "Redmine Ticket AI（社内POC）",
     "monthly_count": 20, "minutes_per_task": 15},
    {"name": "協力会社との定例MTG", "category": "HUMAN_ONLY", "time_reduction_pct": 10,
     "reduction_reason": "関係構築・信頼形成・交渉は人間固有の能力。議事録生成でサポートのみ可能",
     "priority": "LOW", "suggested_tool": "議事録自動生成AIでサポート",
     "monthly_count": 2, "minutes_per_task": 90},
    {"name": "新機能の仕様書レビュー", "category": "AI_AUGMENT", "time_reduction_pct": 40,
     "reduction_reason": "矛盾検出・抜け漏れ指摘はAI補助40%削減可能、最終判断・承認は人間",
     "priority": "MEDIUM", "suggested_tool": "Claude API",
     "monthly_count": 4, "minutes_per_task": 60},
    {"name": "チームメンバーの相談対応", "category": "HUMAN_ONLY", "time_reduction_pct": 0,
     "reduction_reason": "感情支援・キャリア相談・信頼関係が核心。AIに代替できない",
     "priority": "LOW", "suggested_tool": "—",
     "monthly_count": 8, "minutes_per_task": 30},
    {"name": "請求書・稟議書の確認・承認", "category": "AI_AUGMENT", "time_reduction_pct": 50,
     "reduction_reason": "チェックリスト確認・不備検出はAIが50%削減、最終承認は人間",
     "priority": "MEDIUM", "suggested_tool": "Claude API + RPA",
     "monthly_count": 10, "minutes_per_task": 15},
]

DEMO_ROADMAP = {
    "phases": [
        {
            "name": "今すぐ着手",
            "period": "〜1ヶ月",
            "month_start": 0,
            "month_end": 1,
            "actions": [
                {"task_name": "週次レポートの作成", "action": "Python + Claude APIでデータ集計・報告書生成を自動化", "tool": "Claude API + Python"},
                {"task_name": "会議の議事録作成", "action": "Whisper音声認識 + Claude要約パイプラインを構築", "tool": "Whisper + Claude API"},
            ],
        },
        {
            "name": "次のステップ",
            "period": "1〜3ヶ月",
            "month_start": 1,
            "month_end": 3,
            "actions": [
                {"task_name": "メール返信（問い合わせ対応）", "action": "Claude APIでメールドラフト生成ツールを導入", "tool": "Claude API"},
                {"task_name": "Redmineチケットの進捗確認・更新", "action": "社内Redmine Ticket AI POCを業務適用", "tool": "Redmine Ticket AI"},
                {"task_name": "請求書・稟議書の確認・承認", "action": "チェックリストAI化で確認工数を半減", "tool": "Claude API + RPA"},
            ],
        },
        {
            "name": "中長期",
            "period": "3〜6ヶ月",
            "month_start": 3,
            "month_end": 6,
            "actions": [
                {"task_name": "新機能の仕様書レビュー", "action": "Claude APIで仕様書の矛盾・抜け漏れを自動検出", "tool": "Claude API"},
                {"task_name": "業務フロー全体", "action": "個別AI化を統合し「AIが先に動く」ワークフローに再設計", "tool": "複合AI"},
            ],
        },
    ],
    "human_tasks": ["協力会社との定例MTG", "チームメンバーの相談対応"],
    "summary_message": "AIを活用することで月約12時間を創出できます。その時間を、協力会社との信頼構築やチームメンバーへの深い関与に充てましょう。",
}

# ─── プロンプト ───────────────────────────────────────────

DIAGNOSIS_SYSTEM = """あなたは業務のAI化可能性を診断する専門AIです。
ユーザーが入力した業務リストを分析し、各業務を以下の3カテゴリに分類してください。

【分類基準（境界線の判定ルール）】
- AI_AUTOMATE（完全自動化）: 定型・反復・データ処理が中心で、人間の判断なしにAIが完全実行できる
  → 例: 集計・レポート生成・音声→テキスト変換・定型メール送信
- AI_AUGMENT（AI増強）: AIがドラフト・分析・要約を行い、人間が最終判断・承認・コミュニケーションを担う
  → 例: メール返信案生成・仕様書レビュー支援・チケット優先度サジェスト
- HUMAN_ONLY（人間必須）: 感情・倫理・信頼関係・戦略的判断が核心で、AIは補助役にとどまる
  → 例: 1on1相談・交渉・組織設計・創造的な意思決定

【出力形式】
各業務について以下を判定してください:
- name: 業務名
- category: AI_AUTOMATE / AI_AUGMENT / HUMAN_ONLY
- time_reduction_pct: 削減できる時間の割合（0〜100の整数）
- reduction_reason: 削減率の根拠を工程レベルで説明（例:「データ収集90%削減・文書化80%削減の平均」）
- priority: 優先度（HIGH / MEDIUM / LOW）
- suggested_tool: 推奨ツール・手法（1〜2例）

※ 重要: 各業務の name フィールドは、入力された業務名と一字一句完全に一致させること。要約・省略・変更は禁止。

必ず以下の形式で返してください:
[DIAGNOSIS_RESULT]
```json
{
  "tasks": [
    {
      "name": "業務名",
      "category": "AI_AUTOMATE",
      "time_reduction_pct": 85,
      "reduction_reason": "根拠の説明",
      "priority": "HIGH",
      "suggested_tool": "推奨ツール"
    }
  ]
}
```"""

GUIDE_SYSTEM = """あなたは業務AI化の実装コーチです。
指定された1業務について、初心者でも実践できる導入ガイドをMarkdown形式で作成してください。

構成:
## 実装ガイド：{業務名}
### なぜこの分類なのか（1〜2段落）
### 具体的な実装ステップ（5〜7ステップ。各ステップに所要時間の目安を付ける）
### 必要なスキル・前提知識
### 初期コスト概算
### リスク・注意点

トーン: 前向き・具体的・日本語。初心者に寄り添う。"""

CHAT_SYSTEM_TEMPLATE = """あなたは業務AI化の実装支援コーチです。
以下の業務についてユーザーの質問に答えてください。

【対象業務】
業務名: {name}
分類: {category_label}
推奨ツール: {suggested_tool}
削減率: {time_reduction_pct}%（根拠: {reduction_reason}）
月間工数: {monthly_hours}h → 削減見込み: {monthly_reduction_hours}h/月

ユーザーの状況に合わせて実践的・前向きに日本語で回答してください。
コード例が必要な場合は提示してください。"""

DEMO_GUIDE_TEMPLATE = {
    "AI_AUTOMATE": """\
## 実装ガイド：{name}

### なぜ「完全自動化可能」なのか
{name}は定型・反復・データ処理が中心の業務です。
毎回ほぼ同じ手順で処理でき、判断基準が明確なため、AIが人間と同等以上の品質で実行できます。
月間工数 **{monthly_hours}時間** のうち **{monthly_reduction_hours}時間** をAIに任せられます。

### 具体的な実装ステップ
1. **現状の業務フローを書き出す**（30分）
   - 入力データ・処理手順・出力形式を紙に整理する
2. **Pythonで処理を自動化**（2〜4時間）
   - `pandas` でデータ読み込み・集計
   - Claude API で文書・メール・レポートを生成
3. **出力テンプレートを作る**（1時間）
   - 報告書・メールのひな型を用意し、プロンプトに埋め込む
4. **テスト実行・精度確認**（1時間）
   - 実データで動かして出力を確認・調整
5. **定期実行を設定**（30分）
   - macOS の `cron` または `launchd` でスケジュール実行
6. **運用開始・改善ループ**
   - 月1回アウトプットを確認し、プロンプトを微調整

### 必要なスキル・前提知識
- Python 基礎（変数・関数・ファイル操作）
- Claude API の基本的な使い方（既存POCが参考になります）

### 初期コスト概算
- 開発時間: 4〜8時間
- API コスト: 月数百円〜（処理量による）

### リスク・注意点
- 自動化後も月1回は出力を確認する（自動化 ≠ 放置）
- 社内の情報セキュリティポリシーを事前確認する
""",
    "AI_AUGMENT": """\
## 実装ガイド：{name}

### なぜ「AI増強」なのか
{name}は最終判断・コミュニケーション・文脈理解が必要な業務です。
AIが下書き・分析・要約を担い、あなたが確認・判断することで大幅な効率化が実現します。
月間 **{monthly_reduction_hours}時間** の削減が見込めます。

### 具体的な実装ステップ
1. **AIに任せる部分と自分が判断する部分を分ける**（30分）
   - 「ドラフト生成 → 自分がレビュー → 送信/承認」の分担を設計
2. **Claude API でドラフト生成ツールを作る**（2〜4時間）
   - Streamlit で「入力フォーム → Claude → 出力表示」の画面を作成
3. **自分の判断基準をプロンプトに反映**（1時間）
   - よく修正する箇所・重視するポイントをシステムプロンプトに書き込む
4. **実業務でテスト**（1時間）
   - 実際の業務で試し、気になる点をプロンプトに反映
5. **習慣化・チームへの展開**
   - 自分が慣れたらチームに共有し、組織全体の効率化へ

### 必要なスキル・前提知識
- Streamlit の基礎（既存POCが参考になります）
- Claude API の基本的な使い方

### 初期コスト概算
- 開発時間: 3〜6時間
- API コスト: 月数百円〜

### リスク・注意点
- 最終承認は必ず人間が行う設計を維持する
- 社内データを扱う場合は情報セキュリティポリシーを事前確認する
""",
    "HUMAN_ONLY": """\
## 実装ガイド：{name}

### なぜ「人間必須」なのか
{name}は感情・信頼関係・倫理的判断・戦略的思考が核心です。
AIに完全に任せることはできませんが、「周辺業務」をAI化することで本質的な部分に集中できます。

### AIでサポートできること
1. **事前準備の自動化**（30分で実装）
   - アジェンダ・資料のドラフト生成
   - 過去の会話履歴・課題のサマリー生成
2. **記録の自動化**（1〜2時間で実装）
   - 会話後の議事録・メモをClaudeに整形させる
3. **フォローアップの効率化**（1時間で実装）
   - アクションアイテムの整理・リマインダー設定

### 大切にしてほしいこと
この業務こそが、あなたが人間として価値を発揮できる場所です。
AIが周辺業務を担うことで、ここに集中できる時間と余裕が生まれます。

### リスク・注意点
- AIの意見を参考にすることは有益だが、最終判断は必ず人間が行う
- 人間関係・感情への配慮はAIでは判断できない
""",
}

DEMO_CHAT_RESPONSES = [
    "良い質問です！**{name}** の場合、まず「どのデータを使うか」を整理するところから始めると進めやすいです。具体的には、現在使っているファイル（Excel・PDFなど）をリストアップして、それぞれのデータ構造を確認してみてください。何か特定の部分で詰まっていますか？",
    "おっしゃる通りです。**{name}** では推奨ツールとして **{tool}** を提案しましたが、まずは既存のPOCコード（`02_development/pocs/`）を参考にするのが最短ルートです。似た処理のコードを流用できる部分が多いはずです。",
    "コスト面でいうと、Claude APIは従量課金なので最初は少額（月数百円程度）から試せます。本番運用前にデモモードで動作確認してから切り替えるのが安全です。何か他に気になる点はありますか？",
]

ROADMAP_SYSTEM = """あなたは業務AI化の実行支援コーチです。
診断結果をもとに、個人AIロードマップをJSON形式で生成してください。

出力形式:
[ROADMAP_RESULT]
```json
{
  "phases": [
    {
      "name": "フェーズ名",
      "period": "期間表記",
      "month_start": 0,
      "month_end": 1,
      "actions": [
        {"task_name": "業務名", "action": "具体的アクション（1文）", "tool": "推奨ツール"}
      ]
    }
  ],
  "human_tasks": ["人間必須タスク名のリスト"],
  "summary_message": "全体の前向きなメッセージ（2〜3文）"
}
```

フェーズ設計:
- 今すぐ着手（month_start:0, month_end:1）: HIGH優先度の自動化タスク
- 次のステップ（month_start:1, month_end:3）: MEDIUM優先度・AI増強タスク
- 中長期（month_start:3, month_end:6）: LOW優先度・フロー統合

トーン: 前向き・具体的・日本語。"""


# ─── エージェント ─────────────────────────────────────────

class DiagnosisAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.is_demo_mode = not bool(api_key)
        if not self.is_demo_mode:
            self.client = anthropic.Anthropic(api_key=api_key)

    def diagnose(self, tasks: list[dict]) -> list[dict]:
        """tasks: カード入力から収集した業務リスト"""
        if self.is_demo_mode:
            # 入力件数に合わせてデモデータをトリム（超過分を表示しない）
            demo = DEMO_DIAGNOSIS_TASKS[:len(tasks)]
            return self._attach_hours(demo, tasks)

        task_text = self._format_tasks_for_prompt(tasks)
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            system=DIAGNOSIS_SYSTEM,
            messages=[{"role": "user", "content": f"以下の業務を診断してください:\n\n{task_text}"}],
        )
        parsed = self._parse_json(response.content[0].text, "DIAGNOSIS_RESULT")
        if not parsed:
            raise RuntimeError("AIからの応答を解析できませんでした。再試行してください。")
        raw_tasks = parsed.get("tasks", [])
        if not raw_tasks:
            raise RuntimeError("診断結果が空でした。業務の説明を詳しくして再試行してください。")
        return self._attach_hours(raw_tasks, tasks)

    def generate_guide(self, task: dict) -> str:
        if self.is_demo_mode:
            cat = task.get("category", "AI_AUGMENT")
            template = DEMO_GUIDE_TEMPLATE.get(cat, DEMO_GUIDE_TEMPLATE["AI_AUGMENT"])
            return template.format(
                name=task.get("name", "業務"),
                monthly_hours=task.get("monthly_hours", 0),
                monthly_reduction_hours=task.get("monthly_reduction_hours", 0),
            )

        category_labels = {
            "AI_AUTOMATE": "完全自動化可能",
            "AI_AUGMENT": "AI増強",
            "HUMAN_ONLY": "人間必須",
        }
        context = (
            f"業務名: {task['name']}\n"
            f"詳細: {task.get('description', '—')}\n"
            f"分類: {category_labels.get(task['category'], task['category'])}\n"
            f"削減率: {task.get('time_reduction_pct', 0)}%（根拠: {task.get('reduction_reason', '—')}）\n"
            f"推奨ツール: {task.get('suggested_tool', '—')}\n"
            f"月間工数: {task.get('monthly_hours', 0)}h / 削減見込み: {task.get('monthly_reduction_hours', 0)}h"
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=GUIDE_SYSTEM,
            messages=[{"role": "user", "content": context}],
        )
        return response.content[0].text

    def chat(self, task: dict, history: list[dict]) -> str:
        if self.is_demo_mode:
            resp = random.choice(DEMO_CHAT_RESPONSES)
            return resp.format(
                name=task.get("name", "この業務"),
                tool=task.get("suggested_tool", "推奨ツール"),
            )

        category_labels = {
            "AI_AUTOMATE": "完全自動化可能",
            "AI_AUGMENT": "AI増強",
            "HUMAN_ONLY": "人間必須",
        }
        system = CHAT_SYSTEM_TEMPLATE.format(
            name=task.get("name", "—"),
            category_label=category_labels.get(task.get("category", ""), "—"),
            suggested_tool=task.get("suggested_tool", "—"),
            time_reduction_pct=task.get("time_reduction_pct", 0),
            reduction_reason=task.get("reduction_reason", "—"),
            monthly_hours=task.get("monthly_hours", 0),
            monthly_reduction_hours=task.get("monthly_reduction_hours", 0),
        )
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def generate_roadmap(self, diagnosis_tasks: list[dict]) -> dict:
        if self.is_demo_mode:
            return DEMO_ROADMAP

        context = json.dumps(
            [{"name": t["name"], "category": t["category"], "priority": t["priority"],
              "monthly_reduction_hours": t.get("monthly_reduction_hours", 0)}
             for t in diagnosis_tasks],
            ensure_ascii=False, indent=2
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=ROADMAP_SYSTEM,
            messages=[{"role": "user", "content": f"診断結果:\n{context}"}],
        )
        result = self._parse_json(response.content[0].text, "ROADMAP_RESULT")
        if not result:
            raise RuntimeError("ロードマップの生成に失敗しました。再試行してください。")
        return result

    # ─── ヘルパー ───

    def _format_tasks_for_prompt(self, tasks: list[dict]) -> str:
        lines = []
        for t in tasks:
            monthly_hours = t["monthly_count"] * t["minutes_per_task"] / 60
            lines.append(
                f"業務名: {t['name']}\n"
                f"詳細: {t.get('description', '（説明なし）')}\n"
                f"月間件数: {t['monthly_count']}回 / 1件あたり: {t['minutes_per_task']}分 / 月間工数: {monthly_hours:.1f}時間\n"
                f"頻度: {t.get('frequency', '—')}"
            )
        return "\n\n".join(lines)

    def _attach_hours(self, diagnosis_tasks: list[dict], input_tasks: list[dict]) -> list[dict]:
        """入力データから月間工数・削減時間を計算して付与する"""
        input_map = {t["name"]: t for t in input_tasks}
        result = []
        for i, dt in enumerate(diagnosis_tasks):
            # 名前で一致を試み、Claudeが名前を変えた場合はインデックス順でフォールバック
            inp = input_map.get(dt["name"])
            if inp is None and i < len(input_tasks):
                inp = input_tasks[i]
            inp = inp or {}
            monthly_count = inp.get("monthly_count", dt.get("monthly_count", 1))
            minutes_per_task = inp.get("minutes_per_task", dt.get("minutes_per_task", 30))
            monthly_hours = monthly_count * minutes_per_task / 60
            reduction_pct = dt.get("time_reduction_pct", 0)
            result.append({
                **dt,
                "monthly_count": monthly_count,
                "minutes_per_task": minutes_per_task,
                "monthly_hours": round(monthly_hours, 1),
                "monthly_reduction_hours": round(monthly_hours * reduction_pct / 100, 1),
            })
        return result

    def _parse_json(self, text: str, marker: str) -> dict | list | None:
        pattern = rf"\[{marker}\]\s*```json\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None
