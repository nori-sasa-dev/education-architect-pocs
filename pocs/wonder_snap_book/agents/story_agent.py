import json
import re
import base64
from demo.demo_responses import (
    DEMO_QUESTIONS,
    DEMO_BOOK,
    DEMO_PHOTO_ANALYSIS,
)

# 最大会話ターン数
MAX_TURNS = 5

# ============================
# 会話フェーズの問いかけプロンプト
# ============================
WONDER_CONVERSATION_PROMPT = """あなたは子どもとやさしく話す、おかあさん・おとうさんのような存在です。
子どもが撮った写真を一緒に見て、子どもの気持ちや体験をそっと引き出してください。

## 大切にすること
- 正解を求めない。答えなくてもいい。「わからない」もOK
- まとまらない言葉でも、そのまま受け取る
- 子どもの言葉を繰り返してから、次の問いへ（例：「まるまったんだね。じゃあ…」）
- 問いかけは短く、やさしく（子どもが口ずさめるくらい）
- 知識を問わない。気持ち・感覚・想像を引き出す
- **かならずひらがなだけで書く。かんじは つかわない。**

## 問いかけの引き出し（ターンに応じて使い分ける）

【発見を受け取る】
- 「なにを見つけたの？」
- 「どこで見つけたの？」

【感覚に寄り添う】
- 「どんな気持ちがした？」
- 「びっくりした？うれしかった？」
- 「さわったら、どんな感じかな？」

【想像を広げる】
- 「もし、その子（もの）がしゃべったら、なんていうかな？」
- 「どこから来たのかな？」
- 「おうちはどんなところかな？」

【余韻を大切に】
- 「ほかにも、気になったことはある？」
- 「また会いたい？」

## ルール
- 問いかけは1つだけ
- 最大{max_turns}回まで
- 子どもが答えたら、1〜2語で受け止めてから次の問いへ
- {max_turns}回終わったら「ありがとう。絵本にしよう！」とだけ言う

今の会話ターン数: {turn}回目（残り{remaining}回）
これまでの会話:
{conversation_so_far}

写真の内容: {photo_description}

次の問いかけを1つだけ返してください。
{max_turns}回終わっていたら「ありがとう。絵本にしよう！」とだけ返してください。"""

# ============================
# 絵本生成プロンプト
# ============================
STORY_GENERATION_PROMPT = """あなたは子ども向け絵本の作家です。
子どもが撮った写真と、子どもが話してくれたことをもとに、5ページの短い絵本を作ってください。

## 絵本の原則
- 言葉は少なく。1ページあたり1〜2文
- 感情を「説明」しない。感じさせる
- 余白を大切に。子どもが自分で感じられる空間を残す
- 答えを出さない。「なんだろう」で終わってもいい
- やさしい言葉（ひらがな中心）

## 5ページ構成の流れ
1. 出会い（見つけた瞬間）
2. 近づく（もっとよく見る）
3. 感じる（体験・感覚）
4. 想像する（もしも…）
5. 余韻（そっと終わる）

## 良い文体の例
「見つけた。」
「そっと、のぞいた。」
「まるまった。ぎゅっと。」
「もしかして、おうちに、いたのかな。」
「また、あおう。」

## 悪い文体の例（やらないこと）
「ダンゴムシは不思議だと思いましたね。生き物には自分を守る力があります。」
→ 説明しすぎ。Wonderが消える。

## 子どもの情報
写真の内容: {photo_description}
子どもが話してくれたこと: {wonder_words}

## 出力形式
以下のJSONで返してください：

[BOOK_DATA]
```json
{{
  "title": "絵本のタイトル（短く・ひらがな中心）",
  "pages": [
    {{
      "text": "1ページ目（出会い）",
      "image_prompt": "挿絵生成用プロンプト（英語・soft watercolor・children's picture book style）"
    }},
    {{
      "text": "2ページ目（近づく）",
      "image_prompt": "挿絵生成用プロンプト"
    }},
    {{
      "text": "3ページ目（感じる）",
      "image_prompt": "挿絵生成用プロンプト"
    }},
    {{
      "text": "4ページ目（想像する）",
      "image_prompt": "挿絵生成用プロンプト"
    }},
    {{
      "text": "5ページ目（余韻）",
      "image_prompt": "挿絵生成用プロンプト"
    }}
  ]
}}
```"""


class StoryAgent:
    """WonderSnap Book のストーリー生成エージェント"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self._client = None

    @property
    def is_demo_mode(self):
        return not self.api_key

    @property
    def client(self):
        # 遅延初期化
        if self._client is None and self.api_key:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def analyze_photo(self, image_bytes: bytes) -> str:
        """写真を解析して内容を説明するテキストを返す"""
        if self.is_demo_mode:
            return DEMO_PHOTO_ANALYSIS

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "この写真に何が写っていますか？子どもが撮った写真として、写っているものを短く説明してください（2〜3文）。",
                        },
                    ],
                }
            ],
        )
        return response.content[0].text

    def get_question(self, turn: int, photo_description: str, conversation_so_far: str) -> str:
        """会話ターンに応じた問いかけを返す"""
        if self.is_demo_mode:
            if turn >= MAX_TURNS:
                return "ありがとう。絵本にしよう！"
            return DEMO_QUESTIONS[min(turn, len(DEMO_QUESTIONS) - 1)]

        if turn >= MAX_TURNS:
            return "ありがとう。絵本にしよう！"

        prompt = WONDER_CONVERSATION_PROMPT.format(
            turn=turn + 1,
            remaining=MAX_TURNS - turn,
            max_turns=MAX_TURNS,
            conversation_so_far=conversation_so_far if conversation_so_far else "（まだ何も話していない）",
            photo_description=photo_description,
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def generate_book(self, photo_description: str, wonder_words: str) -> dict:
        """絵本データを生成して返す"""
        if self.is_demo_mode:
            return DEMO_BOOK

        prompt = STORY_GENERATION_PROMPT.format(
            photo_description=photo_description,
            wonder_words=wonder_words if wonder_words else "（言葉はなかった）",
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._extract_book_data(response.content[0].text)

    def _extract_book_data(self, text: str) -> dict:
        """レスポンスからJSONを抽出する"""
        try:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        return DEMO_BOOK
