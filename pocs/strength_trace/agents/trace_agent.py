import json

SYSTEM_PROMPT = """あなたは「持ち味の発見者」です。
社員の過去複数期のシート（業績目標・行動目標・キャリアデザイン）と案件履歴を時系列で読み、
点（その時点）では見えにくい「その人らしい持ち味」を発見して言語化する専門家です。

## 大前提（最重要）
あなたは評価者ではありません。査定・採点・優劣の判定は一切しません。
あなたの仕事は、社員本人が「自分でも気づいていなかった強みに気づく」きっかけを届けることです。

## 分析の核心：点ではなく「線」で読む
1期分だけでは「たまたま」に見える行動も、複数期を貫いて見ると「その人の核」が浮かび上がります。
必ず全期を時系列で通読し、期をまたいだ変化・反復・文脈を捉えてください。

## 持ち味の3タイプ
- **核**：複数の期・複数の案件で繰り返し現れる持ち味。環境を問わず安定して出る、その人の土台。
- **芽**：最初は薄かったが、期を追うごとに強まっている持ち味。成長の軌跡そのもの。
- **状況依存**：特定の案件・役割・局面でのみ際立って発揮される持ち味。「この環境で輝く」という発揮条件の手がかり。

## 各持ち味に付けるもの
- name：持ち味の名前。一般的なスキル名ではなく、その人の具体的な行動から立ち上がる固有の表現にする
  （悪い例：「コミュニケーション能力」 / 良い例：「渦中でも動じず、場を落ち着かせる一次対応力」）
- type：核 / 芽 / 状況依存 のいずれか
- summary：一言サマリー
- trajectory：期ごとの「証拠（どの案件で何をしたか）」と濃淡（濃 / 中 / 薄）の配列。必ず時系列順。
- environment：この持ち味が発揮されやすい環境・条件
- talking_point：面談で本人に投げかける問い。承認的・未来志向で、決して評価にならない問いにする
- future_action：この持ち味を「これから」どんな場面で活かせそうか、本人が一歩踏み出せる具体的な提案。
  命令ではなく「〜してみては」「〜という場が合うかもしれません」という招待の語り口。未来志向で前向きに。

## 禁止事項
- 点数・偏差値・ランク・序列をつけない
- 「強い／弱い」「優れている／劣っている」という優劣表現を使わない
- 弱みや改善点を指摘しない（このツールは持ち味の発見に専念する）
- 「核 / 芽 / 状況依存」を合計3〜5個に絞る（多すぎると焦点がぼける）

## 出力形式
分析が完了したら、レスポンスの最後に必ず以下のマーカーを付け、続けてJSONを出力してください。

[TRAITS_EXTRACTED]
```json
{
  "employee_name": "氏名",
  "traits": [
    {
      "name": "持ち味の名前",
      "type": "核",
      "summary": "一言サマリー",
      "trajectory": [
        {"period": "2024上期", "evidence": "案件Xで〜した", "strength": "薄"},
        {"period": "2024下期", "evidence": "〜", "strength": "中"}
      ],
      "environment": "この持ち味が発揮される環境",
      "talking_point": "面談で本人に投げる問い",
      "future_action": "この持ち味をこれから活かす一歩の提案"
    }
  ]
}
```
"""

# インタビュー深掘り用：1つの持ち味について本人と短い対話をする
INTERVIEW_SYSTEM_PROMPT = """あなたは「持ち味の発見者」です。
AIが見つけた1つの持ち味について、本人と短い対話をして、本人自身の言葉でその持ち味を深めます。

## 大前提（最重要）
- 評価・査定・採点は一切しない。優劣・強弱の表現を使わない。
- 問いは承認的・未来志向。本人が「自分の言葉で語りたくなる」問いにする。
- 1回の発話で問いは1つだけ。短く、具体的に。
- 本人の負担を考え、深掘りは合計2〜3問で十分。

## 進め方
- これまでの対話を踏まえ、次の問いを1つだけ返す。
- 十分に深まったと判断したら、問いの代わりに [INTERVIEW_DONE] とだけ返す。
"""

# インタビューを踏まえて持ち味を本人の言葉で磨き直す
REFINE_SYSTEM_PROMPT = """あなたは「持ち味の発見者」です。
本人とのインタビューを踏まえ、1つの持ち味を本人の言葉で磨き直します。
評価はしない。承認的・未来志向。本人が言っていないことを創作しない。

分析が完了したら、必ず以下のマーカーとJSONだけを出力してください。

[TRAIT_REFINED]
```json
{
  "summary": "本人の言葉を取り込んだ一言サマリー",
  "future_action": "本人の言葉を踏まえた、これからの活かし方の提案",
  "interview_note": "インタビューで見えた、本人ならではの一文"
}
```
"""

# APIキー未設定時のデモ応答（社員別の固定カード）
DEMO_TRAITS_SASAKI = """佐々木さんの4期分のシートを時系列で読み解きました。
点では見えにくい、けれど一本の線として確かに通っている持ち味が見えてきました。

[TRAITS_EXTRACTED]
```json
{
  "employee_name": "佐々木 亮",
  "traits": [
    {
      "name": "渦中でも動じず、場を落ち着かせる一次対応力",
      "type": "核",
      "summary": "障害や混乱の只中で、周囲が浮き足立つ中でも淡々と影響範囲を確定し、チームの精神的な支えになる持ち味。",
      "trajectory": [
        {"period": "2024上期", "evidence": "重大障害2件で初動の切り分けを主導し、目標時間内に収束させた", "strength": "濃"},
        {"period": "2024下期", "evidence": "原因が見えない局面でも『まず影響範囲を確定しよう』と声をかけ場を落ち着かせた", "strength": "濃"},
        {"period": "2025上期", "evidence": "要件定義中心の期だったが、混乱した議論を整理する場面で同じ落ち着きを発揮", "strength": "中"},
        {"period": "2025下期", "evidence": "実装フェーズの障害対応で一次切り分けを安定して担い、手戻りを最小化した", "strength": "濃"}
      ],
      "environment": "不確実性が高く、周囲が動揺しやすい局面。障害対応やトラブルシュート。",
      "talking_point": "混乱の中で冷静でいられるのは、ご自身の中で何を大事にしているからだと思いますか？",
      "future_action": "次の大きめの障害訓練やインシデント対応で、初動の旗振り役を引き受けてみては。落ち着きが周囲に伝わる場が、さらにこの持ち味を育てます。"
    },
    {
      "name": "断片をつなぎ、全体像を描く俯瞰の設計力",
      "type": "芽",
      "summary": "当初は運用が中心だったが、散らばった情報を俯瞰して構造化する力が期を追って花開いてきた持ち味。",
      "trajectory": [
        {"period": "2024上期", "evidence": "運用・一次対応が中心で、設計に関わる場面はまだ少なかった", "strength": "薄"},
        {"period": "2024下期", "evidence": "散在していた仕様知識を自主的にまとめ、チームの共有資産になった", "strength": "薄"},
        {"period": "2025上期", "evidence": "断片的な現行仕様を俯瞰し、見落とされていた依存関係を図に起こして共有した", "strength": "中"},
        {"period": "2025下期", "evidence": "将来の拡張を見据えたモジュール分割方針を提案し採用された", "strength": "濃"}
      ],
      "environment": "全体像が掴みにくく、構造の整理が求められる上流工程・設計フェーズ。",
      "talking_point": "全体を見渡して構造を描くこの力を、次はどんな場面で試してみたいですか？",
      "future_action": "新規案件の要件定義フェーズで、全体構成図づくりを最初に任せてもらうと良いかもしれません。俯瞰の設計力を看板にできる場です。"
    },
    {
      "name": "立場の違う人の間に立ち、言葉を翻訳する橋渡し",
      "type": "状況依存",
      "summary": "顧客と開発現場のように、利害や言葉が異なる人々の間で、双方を翻訳し認識を揃える持ち味。特定の折衝局面で際立つ。",
      "trajectory": [
        {"period": "2024上期", "evidence": "若手の問い合わせに背景まで説明し、手順の意味を翻訳して伝えていた", "strength": "中"},
        {"period": "2025上期", "evidence": "顧客の要望と現場の実現性が衝突した場面で、双方を翻訳し落としどころを探った", "strength": "濃"},
        {"period": "2025下期", "evidence": "顧客と開発現場の間で専門用語を噛み砕き、両者の認識を揃える役割を果たした", "strength": "濃"}
      ],
      "environment": "顧客折衝やOJTなど、立場・前提・語彙の異なる人どうしをつなぐ必要がある場面。",
      "talking_point": "ご自身が『技術と人の橋渡しをしたい』と書かれていたこと、もう実際に始まっているように見えます。どう感じますか？",
      "future_action": "顧客とのキックオフや要件すり合わせの場に、通訳役として早めに入ってみては。立場の違いを翻訳する力が、案件の土台づくりに効きます。"
    }
  ]
}
```"""

DEMO_TRAITS_INOUE = """井上さんの4期分のシートを時系列で読み解きました。
控えめに見えて、地道な積み重ねが確かな線になって表れています。

[TRAITS_EXTRACTED]
```json
{
  "employee_name": "井上 さやか",
  "traits": [
    {
      "name": "曖昧さを放置せず、根気よく真因にたどり着く探究心",
      "type": "核",
      "summary": "仕様や不具合の曖昧な点を、自分が納得するまで掘り下げて突き止める持ち味。期を通じて一貫している。",
      "trajectory": [
        {"period": "2024上期", "evidence": "仕様の曖昧な点を放置せず細かく確認し、想定外ケースで重要な不具合を発見した", "strength": "中"},
        {"period": "2024下期", "evidence": "曖昧なユーザー報告から根気よく再現条件を特定した", "strength": "濃"},
        {"period": "2025上期", "evidence": "過去の不具合データを丁寧に読み解き共通パターンを抽出した", "strength": "濃"},
        {"period": "2025下期", "evidence": "深く理解した品質の領域では堂々と質問に答えていた", "strength": "濃"}
      ],
      "environment": "原因が見えにくく、地道な調査・分析が求められる場面。",
      "talking_point": "とことん突き止めたくなるのは、どんなときに一番わいてきますか？",
      "future_action": "難航している不具合の原因調査を、次は一次担当として引き受けてみては。真因に辿り着く探究心が、チームの突破口になります。"
    },
    {
      "name": "地道な分析を、人に伝わる形に変えていく力",
      "type": "芽",
      "summary": "自分の中の理解を、チェックリストや説明会という『他者が使える形』に変換する力が期を追って育っている。",
      "trajectory": [
        {"period": "2024上期", "evidence": "調査は丁寧だが、成果を外に発信する場面はまだ少なかった", "strength": "薄"},
        {"period": "2024下期", "evidence": "調査メモが『誰が読んでも分かる』と好評だった", "strength": "薄"},
        {"period": "2025上期", "evidence": "不具合分析をチェックリスト化し、レビューでも具体的に指摘し始めた", "strength": "中"},
        {"period": "2025下期", "evidence": "成果を他チームへ説明会で横展開し、品質向上に寄与した", "strength": "濃"}
      ],
      "environment": "自分が深く理解したことを、人やチームに渡す場面。",
      "talking_point": "自分の分析が人に伝わって役立った瞬間、どんな気持ちでしたか？",
      "future_action": "次の品質改善のテーマで、社内勉強会の講師役を引き受けてみては。理解を「人が使える形」に変える力が、より多くの人に届きます。"
    },
    {
      "name": "想定外を先回りして見つける品質の目",
      "type": "状況依存",
      "summary": "『この入力ならどうなるか』と人が見落とすケースを先回りで拾う持ち味。テスト・品質の局面で際立つ。",
      "trajectory": [
        {"period": "2024上期", "evidence": "想定外ケースを多く挙げ、重要な不具合を事前に発見した", "strength": "濃"},
        {"period": "2025上期", "evidence": "抜けやすいテスト観点を洗い出しチェックリスト化した", "strength": "濃"}
      ],
      "environment": "テスト設計・品質改善など、抜け漏れの予見が価値になる場面。",
      "talking_point": "人が見落としがちな点に気づけるこの目を、次はどこで活かしてみたいですか？",
      "future_action": "新機能のテスト観点レビューに、設計の早い段階から参加してみては。想定外を先回りする目が、手戻りを未然に防ぎます。"
    }
  ]
}
```"""

# 社員名 → デモ応答の対応表（実APIモードでは使わない）
DEMO_TRAITS_BY_NAME = {
    "佐々木 亮": DEMO_TRAITS_SASAKI,
    "井上 さやか": DEMO_TRAITS_INOUE,
}


class TraceAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    def analyze(self, employee: dict) -> str:
        """社員の複数期データを受け取り、点→線分析の結果テキストを返す。"""
        if self.is_demo_mode:
            # デモ時も選択した社員に対応する固定応答を返す（名前と中身の不一致を防ぐ）
            return DEMO_TRAITS_BY_NAME.get(employee["employee_name"], DEMO_TRAITS_SASAKI)
        return self._api_analyze(employee)

    def _api_analyze(self, employee: dict) -> str:
        user_content = self._build_prompt(employee)
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text

    def _build_prompt(self, employee: dict) -> str:
        """社員データを分析用のテキストに整形する。"""
        lines = [
            f"以下は「{employee['employee_name']}」さん（{employee.get('role', '')}）の",
            "過去複数期のシートです。時系列で線として読み解き、持ち味を発見してください。",
            "",
        ]
        for p in employee["periods"]:
            lines.append(f"## {p['period']}　案件：{p['project']}")
            lines.append(f"【業績目標シート】{p['performance_sheet']}")
            lines.append(f"【行動目標シート】{p['behavior_sheet']}")
            lines.append(f"【キャリアデザインシート】{p['career_sheet']}")
            lines.append("")
        return "\n".join(lines)

    def extract_traits(self, text: str) -> dict | None:
        """応答テキストから抽出マーカー付きのJSONを取り出す。"""
        if "[TRAITS_EXTRACTED]" not in text:
            return None
        return self._extract_json(text)

    def _extract_json(self, text: str) -> dict | None:
        """テキスト中の ```json ブロックを取り出してパースする。"""
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            return None

    # ---------- AIインタビュー深掘り（A） ----------
    def _interview_context(self, trait: dict) -> str:
        """インタビュー対象の持ち味をプロンプト用に整形する。"""
        parts = [
            f"持ち味の名前：{trait.get('name', '')}",
            f"タイプ：{trait.get('type', '')}",
            f"今のサマリー：{trait.get('summary', '')}",
        ]
        if trait.get("future_action"):
            parts.append(f"今の活かし方：{trait['future_action']}")
        return "\n".join(parts)

    def interview_turn(self, trait: dict, history: list[dict]) -> str | None:
        """対話履歴を踏まえ、次の問いを返す。十分に深まったら None。

        history は [{"role": "assistant"/"user", "content": str}, ...]。
        assistant=AIの問い / user=本人の答え。
        """
        if self.is_demo_mode:
            return self._demo_interview_turn(history)
        system = INTERVIEW_SYSTEM_PROMPT + "\n\n## 対象の持ち味\n" + self._interview_context(trait)
        # APIはuser始まりの交互を要求するため、先頭にシード発話を足す
        seed = [{"role": "user", "content": "この持ち味について、深掘りの問いをください。"}]
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=seed + history,
        )
        text = response.content[0].text.strip()
        if "[INTERVIEW_DONE]" in text:
            return None
        return text

    def refine_trait(self, trait: dict, history: list[dict]) -> dict | None:
        """インタビューを踏まえ、summary/future_action/interview_note を磨き直す。"""
        if self.is_demo_mode:
            return self._demo_refine(trait)
        system = REFINE_SYSTEM_PROMPT + "\n\n## 対象の持ち味\n" + self._interview_context(trait)
        convo = "\n".join(
            f"{'問' if m['role'] == 'assistant' else '答'}：{m['content']}" for m in history
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": "以下のインタビューを踏まえ、この持ち味を本人の言葉で磨き直してください。\n\n"
                    + convo,
                }
            ],
        )
        text = response.content[0].text
        if "[TRAIT_REFINED]" not in text:
            return None
        return self._extract_json(text)

    def _demo_interview_turn(self, history: list[dict]) -> str | None:
        """デモ用の台本インタビュー（本人の答えの数で進行）。"""
        answers = [m for m in history if m["role"] == "user"]
        if len(answers) == 0:
            return "この持ち味が一番発揮できたと感じるのは、どんな場面でしたか？そのとき、何を考えていましたか？"
        if len(answers) == 1:
            return "その場面で、あなた自身が大切にしていたことは何だったと思いますか？"
        return None

    def _demo_refine(self, trait: dict) -> dict:
        """デモ用の磨き直し（本人の言葉が乗った想定の固定応答）。"""
        return {
            "summary": trait.get("summary", "")
            + "（インタビューを経て、本人の言葉でより具体的になりました）",
            "future_action": trait.get("future_action")
            or "この持ち味を、次に挑戦したい場面で意識して使ってみては。",
            "interview_note": "対話の中で、本人が無意識に大切にしている軸が見えてきました。",
        }
