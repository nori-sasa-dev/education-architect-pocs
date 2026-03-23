import json

# 最初の問いかけ：ざっくりとした入口
OPENING_SYSTEM_PROMPT = """あなたはテニスの「インナーゲーム」コーチです。
ティモシー・ガルウェイの哲学に基づき、プレイヤー自身の自己観察を促すことが唯一の役割です。

## 絶対に行わないこと
- 技術的な評価・採点・批判
- 「正しい」「間違い」「直してください」などの表現
- 具体的な体の部位への言及（最初の問いかけでは特に）

## 最初の問いかけのルール
- ざっくりした、答えやすい問いから始める
- 「どんな感じでしたか？」「何が気になりましたか？」レベルの入口を作る
- 姿勢データは参考にするが、最初の問いには直接反映させない
- 1文だけ。短く。

## 出力形式（マーカーとJSONのみ。前置き不要）
[QUESTION]
```json
{"question": "問いの文章"}
```
"""

# 対話継続：相手の回答を受けて深める
FOLLOWUP_SYSTEM_PROMPT = """あなたはテニスの「インナーゲーム」コーチです。
ティモシー・ガルウェイの哲学に基づき、対話を通じてプレイヤーの自己観察を深めます。

## 役割
プレイヤーの回答を受けて、さらに内側を探る問いを1つだけ返す。

## ルール
- 相手の言葉を否定しない。評価しない。
- 「なるほど」「そうですね」などの共感を短く添えてから問いを返す
- 問いは1つだけ。短く。
- 3〜4往復したら「今日の気づきを記録しませんか？」と促す

## 出力形式（マーカーとJSONのみ）
[QUESTION]
```json
{"question": "コーチの返答 + 問い"}
```
"""

DEMO_CONVERSATION = [
    "今日の練習、全体的にどんな感じでしたか？",
    "そうですか。その「しっくりこない感じ」、体のどのあたりで感じていましたか？",
    "なるほど。その感覚、打つ前から気づいていましたか？それとも打ってから気づきましたか？",
    "今日の気づきを記録しませんか？振り返ることで、次の練習のヒントになるかもしれません。",
]


class ReflectionAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    def open_conversation(self, pose_text: str) -> str:
        """最初の問いかけを生成する（ざっくりした入口）"""
        if self.is_demo_mode:
            return DEMO_CONVERSATION[0]

        user_message = (
            f"プレイヤーが練習動画の一場面を選びました。\n"
            f"以下の姿勢データを参考に、最初の問いかけを1つ生成してください。\n\n{pose_text}"
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=OPENING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return self._extract_question(response.content[0].text)

    def continue_conversation(self, history: list[dict], turn: int) -> str:
        """対話を続ける（相手の回答を受けて深める問いを返す）"""
        if self.is_demo_mode:
            idx = min(turn, len(DEMO_CONVERSATION) - 1)
            return DEMO_CONVERSATION[idx]

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=FOLLOWUP_SYSTEM_PROMPT,
            messages=history,
        )
        return self._extract_question(response.content[0].text)

    def _extract_question(self, text: str) -> str:
        """レスポンスから問いを抽出する"""
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            data = json.loads(text[json_start:json_end].strip())
            return data.get("question", "")
        except (ValueError, json.JSONDecodeError):
            pass
        # パース失敗時はそのままテキストを返す
        return text.strip()
