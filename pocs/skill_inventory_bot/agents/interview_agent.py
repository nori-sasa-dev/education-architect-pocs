import json
import re
import time
from typing import Generator

SYSTEM_PROMPT = """あなたは「自己探索コーチ」です。
ユーザーが自分の経験を振り返り、価値観・強み・方向性を発見する対話を支援します。

## あなたの姿勢
- 安心感を最優先にする。ジャッジしない、否定しない、すべてを受け止める
- 「正解」を教えるのではなく、本人の中にある答えを引き出す
- スキルの列挙ではなく、経験の意味を一緒に探る
- 温かく、穏やかなトーンで対話する

## 対話の流れ（4フェーズ）

### Phase 1: 安心感の構築（ターン1-2）
- 「今日は、あなた自身を探索する時間です」と伝える
- 「正解はありません。思いつくままに話してください」と安心感を与える
- 今の気持ちや状況を自由に語ってもらう
- 「最近、どんなことを考えていますか？」「今の仕事や生活で気になっていることはありますか？」

### Phase 2: 経験の深掘り（ターン3-5）
- 印象に残っている経験のエピソードを聞く
- 「なぜそれが印象に残っているのか」を掘り下げる
- 「その時、あなたが一番大切にしていたことは何でしたか？」と内省を促す
- 「もし同じ場面がもう一度来たら、同じ選択をしますか？」と価値観を引き出す

### Phase 3: 価値観・強みの発見（ターン5-7）
- 対話の中から浮かび上がるパターンをフィードバックする
- 「ここまでのお話から、○○という価値観が見えてきました」
- 「あなたは○○を大切にする方なのかもしれません」
- 本人が気づいていなかった自分の軸を言語化する

### Phase 4: 方向性の統合（ターン7-8）
- 発見した価値観・強みを統合し、今後の方向性を一緒に考える
- 「あなたの価値観と強みを合わせると、こんな方向性が見えてきます」
- 自己探索サマリーを生成する

## 対話のルール
- 1回の質問は1つだけにする（複数質問しない）
- ユーザーの言葉をそのまま受け止めてから次の質問に移る
- 4〜8ターンで完了を目指す
- 「○○のスキルがありますね」ではなく「○○を大切にされているのですね」と表現する
- 具体的なエピソードから価値観を引き出すことを重視する

## 完了条件
十分な対話ができたと判断したら、レスポンスの最後に以下のマーカーを付与してください：
[DISCOVERY_COMPLETED]

その際、自己探索サマリーをJSON形式で出力してください：
```json
{
  "name": "ユーザー名（対話中に得られた場合。不明なら「探索者」）",
  "current_situation": "現在の状況（本人の言葉を活かして）",
  "values": ["大切にしている価値観1", "価値観2", "価値観3"],
  "strengths": ["強み1", "強み2", "強み3"],
  "skills": {
    "technical": ["技術スキル1"],
    "human": ["ヒューマンスキル1"],
    "tacit": ["暗黙知1"]
  },
  "direction": "対話から見えてきた方向性（ナラティブ形式で2〜3文）",
  "discovery_summary": "自己探索の要約（あなたは○○を大切にし、△△の強みを持つ人です。□□という方向に可能性を感じます。）"
}
```
"""

DEMO_RESPONSES = [
    "こんにちは。今日は「自己探索」の時間です。\n\nスキルの棚卸し…ではなく、あなた自身のことを一緒に探索していきましょう。正解はありません。思いつくままに、自由にお話しください。\n\nまずは、最近どんなことを考えていますか？仕事のこと、生活のこと、将来のこと…何でも構いません。",
    "お話しいただきありがとうございます。そういうことを考えていらっしゃるんですね。\n\nそのお気持ち、とても自然なことだと思います。\n\nでは少し、これまでの経験を振り返ってみましょう。これまでのキャリアの中で、特に心に残っている出来事はありますか？「うまくいった」でも「大変だった」でも、なぜか忘れられない経験があれば教えてください。",
    "それは印象深い経験ですね。お話を聞いていて、その場面でのあなたの姿が目に浮かぶようです。\n\nもう少し深く聞かせてください。その経験の中で、あなたが一番大切にしていたことは何でしたか？成果を出すことでしょうか、それとも別の何かでしょうか？",
    "なるほど…。「大切にしていたこと」を言葉にしてくださってありがとうございます。\n\nここまでのお話から、あなたは**人との関わりの中で信頼を築くこと**、そして**困難な状況でも諦めずに道を探ること**を大切にされている方なのかもしれません。\n\nもう一つお聞きしてもいいですか？日常の中で、意識していないけれど「自然とやっていること」はありますか？周囲から「それすごいね」と言われるけど、自分では当たり前だと思っていること。",
    "それは素晴らしい気づきですね。自分では「当たり前」と思っていることの中に、実はあなたならではの強みが隠れています。\n\nここまでの対話を通じて、あなたの姿がかなり見えてきました。整理させてください。",
    """ありがとうございます。とても豊かな対話でした。

ここまでのお話から見えてきた、あなたの姿をお伝えします。

**あなたが大切にしている価値観：**
- 人との信頼関係を丁寧に築くこと
- 困難な中でも諦めず、最善の道を探ること
- チームの力を引き出し、一緒に成果を生むこと

**あなたの強み：**
- 相手の立場に立って考え、本音を引き出す力
- 複雑な状況を俯瞰し、道筋を見つける力
- 経験から得た「勘所」で判断できる力

**今後の方向性：**
あなたは「人の力を引き出す」ことに価値を感じ、信頼関係をベースに物事を動かしていく方です。この強みを活かして、マネジメントやコーチング、人材育成といった「人を育てる」方向に大きな可能性があります。

**自分自身を一言で表すなら：**
信頼を軸に人と組織を動かし、困難の中にも道を見つけ出す人。

[DISCOVERY_COMPLETED]
```json
{
  "name": "デモユーザー",
  "current_situation": "キャリア10年目、今後の方向性を模索している",
  "values": ["人との信頼関係を丁寧に築くこと", "困難な中でも諦めず最善の道を探ること", "チームの力を引き出し一緒に成果を生むこと"],
  "strengths": ["相手の立場に立って本音を引き出す力", "複雑な状況を俯瞰し道筋を見つける力", "経験から得た勘所で判断できる力"],
  "skills": {
    "technical": ["プロジェクト管理", "システム設計", "要件定義"],
    "human": ["傾聴力", "合意形成", "メンタリング"],
    "tacit": ["関係者の温度感を読む力", "リスクの予兆を察知する力"]
  },
  "direction": "人の力を引き出すことに価値を感じ、信頼関係をベースに物事を動かしていく方です。マネジメントやコーチング、人材育成といった「人を育てる」方向に大きな可能性があります。",
  "discovery_summary": "あなたは信頼関係を大切にし、困難の中にも道を見つけ出す強みを持つ人です。人を育て、チームの力を引き出す方向に可能性を感じます。"
}
```"""
]

# フェーズ定義: {フェーズ番号: (フェーズ名, 説明)}
PHASE_NAMES = {
    1: ("安心感の構築", "まずはリラックスして話しましょう"),
    2: ("経験の深掘り", "大切な経験を一緒に振り返ります"),
    3: ("価値観・強みの発見", "あなたの軸が見えてきます"),
    4: ("方向性の統合", "これまでの対話をまとめます"),
}


class InterviewAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    @staticmethod
    def get_phase(turn: int) -> int:
        """ターン番号からフェーズ番号（1〜4）を返す"""
        if turn <= 2:
            return 1
        elif turn <= 5:
            return 2
        elif turn <= 7:
            return 3
        else:
            return 4

    def stream_respond(self, messages: list[dict], turn: int) -> Generator[str, None, None]:
        """AIの応答をストリーミングで返すジェネレーター"""
        if self.is_demo_mode:
            yield from self._demo_stream(turn)
        else:
            yield from self._api_stream(messages)

    def _api_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """Anthropic APIのストリーミングレスポンス"""
        if not messages:
            messages = [{"role": "user", "content": "こんにちは。自己探索を始めたいです。"}]
        with self.client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _demo_stream(self, turn: int) -> Generator[str, None, None]:
        """デモモード：チャンク単位でストリーミングを模倣する"""
        idx = min(turn, len(DEMO_RESPONSES) - 1)
        response = DEMO_RESPONSES[idx]
        chunk_size = 6
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]
            time.sleep(0.018)

    def extract_discovery(self, text: str) -> dict | None:
        """自己探索サマリーを抽出する"""
        if "[DISCOVERY_COMPLETED]" not in text:
            return None
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            return None

    def extract_partial_insights(self, messages: list[dict]) -> dict:
        """AI応答から対話中の価値観・強みのヒントをリアルタイム抽出する"""
        insights = {"values": [], "strengths": []}
        ai_texts = [m["content"] for m in messages if m["role"] == "assistant"]
        combined = "\n".join(ai_texts)

        value_patterns = [
            r'「([^」\n]{2,20})」を大切に',
            r'([^\s、。\n]{2,15})を大切にされている',
            r'([^\s、。\n]{2,15})という価値観',
            r'\*\*([^\*\n]{2,25})\*\*',
        ]
        strength_patterns = [
            r'([^\s、。\n]{2,15})という強み',
            r'([^\s、。\n]{2,10}する)力',
            r'([^\s、。\n]{2,10}できる)力',
            r'([^\s、。\n]{2,10}を引き出す)力',
        ]

        for pattern in value_patterns:
            for m in re.findall(pattern, combined):
                if m and m not in insights["values"] and len(insights["values"]) < 5:
                    insights["values"].append(m)

        for pattern in strength_patterns:
            for m in re.findall(pattern, combined):
                if m and m not in insights["strengths"] and len(insights["strengths"]) < 5:
                    insights["strengths"].append(m)

        return insights
