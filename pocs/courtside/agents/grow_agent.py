import json

# ─── GROWステップ定義 ─────────────────────────────────
# 0=G(Goal), 1=R(Reality), 2=O(Options), 3=W(Will)
# 各ステップで「投げる問いの狙い」だけをsystem promptに注入する。
# 具体的な問い文はAIに生成させる（デモモードでは固定文を返す）。
GROW_STEPS = [
    {
        "key": "G",
        "label": "Goal（今日のゴール）",
        "focus": (
            "今日の練習が終わったときに「これができた」と言えたら最高なこと、"
            "つまり本人が望む今日のゴールを引き出す問いを1つ投げる。"
        ),
    },
    {
        "key": "R",
        "label": "Reality（いまの現実）",
        "focus": (
            "最近モヤッとした場面・うまくいかなかった場面など、"
            "本人がいま立っている現実を本人の言葉で語ってもらう問いを1つ投げる。"
        ),
    },
    {
        "key": "O",
        "label": "Options（試せそうなこと）",
        "focus": (
            "ゴールに近づくとしたら今日どんな打ち方・意識を試せそうか、"
            "本人の中にある選択肢を引き出す問いを1つ投げる（複数出てよい）。"
            "ただしAIから具体的なドリルやメニューを提案してはいけない。"
        ),
    },
    {
        "key": "W",
        "label": "Will（今日やる1つ）",
        "focus": (
            "出てきた選択肢の中から、今日まず1つだけやるとしたら何かを"
            "本人に選んでもらう問いを1つ投げる。"
        ),
    },
]

# ─── 共通の禁止事項（最重要・厳格）──────────────────────
# AIは「コーチ」ではなく「鏡」。問いを投げ、本人の言葉を映し返すだけ。
SYSTEM_PROMPT_BASE = """あなたはテニスの練習"前"に、プレイヤー自身が「今日の自分のテーマ」を
自分で決めるのを手伝う対話パートナーです。
ティモシー・ガルウェイのインナーゲームとGROWモデルの思想に基づきます。

## あなたの唯一の役割
- 本人に「問い」を投げること
- 本人が言った言葉を、短く映し返すこと（鏡のように）

## 絶対に行わないこと（厳守）
- 練習ドリル・練習メニュー・具体的な技術指導を出さない
- 「こう打つといい」「○○を意識して」などの処方・アドバイスをしない
- 上手い／下手、正しい／間違い といった評価をしない
- 答えや正解を与えない

## 話し方
- 1メッセージにつき、問いは1つだけ
- 出力は短く、2〜3文以内
- 共感を一言そえてから問いを返してよいが、長い説明はしない
- あなたはコーチではなく「鏡」です

## 出力形式（マーカーとJSONのみ。前置き不要）
[QUESTION]
```json
{"question": "本人への問いの文章"}
```
"""

# ─── デモモード用の固定の問い（G→R→O→W）──────────────
DEMO_QUESTIONS = [
    # G Goal
    "今日の練習、終わったときに「これができた」と言えたら最高なのは、どんなことですか？",
    # R Reality
    "なるほど。最近の練習で、どこで一番モヤッとしましたか？うまくいかなかったのはどんな場面でしょう。",
    # O Options
    "そのゴールに近づくとしたら、今日はどんな打ち方や意識を試せそうですか？（いくつ出してもOKです）",
    # W Will
    "いいですね。そのなかで、今日まず1つだけやるとしたら、どれにしますか？",
]

# ─── デモモード用の固定テーマカード ───────────────────
# 本人の入力語を引用する設計だが、デモでは固定文を返す。
DEMO_THEME_CARD = {
    "theme": "フォアハンドで「振り遅れ」をなくすために、早めの準備を1つだけ試す",
    "quote": "フォアの振り遅れが気になる",
    "reason": "あなた自身が「振り遅れが気になる」と話し、今日はその準備に集中すると決めたから。",
}

# ─── テーマカード生成用 system prompt ─────────────────
# AIの創作テーマにせず、本人が実際に使った言葉を引用させる。
THEME_SYSTEM_PROMPT = """あなたは、これまでの対話から「今日の練習テーマ」を1文にまとめる役割です。

## 最重要ルール
- テーマは必ず、本人（user）が実際に使った言葉を引用して作ること
- あなたが勝手に新しい技術用語や目標を創作してはいけない
- 本人が言っていないドリル・メニュー・技術指導を足してはいけない

## まとめ方
- theme: 本人の言葉を活かした「今日のテーマ」を1文で
- quote: テーマの根拠になった、本人の発言からの短い引用（本人の言葉そのまま）
- reason: なぜこれが今日のテーマなのかを、本人の言葉に沿って1〜2文で

## 出力形式（マーカーとJSONのみ。前置き不要）
[THEME]
```json
{"theme": "今日のテーマ（1文）", "quote": "本人の発言からの引用", "reason": "理由（1〜2文）"}
```
"""


class GrowAgent:
    """GROWモデルに沿って、練習前の「今日のテーマ」決めを問いで引き出すエージェント。"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    def respond(self, messages: list[dict], step: int) -> str:
        """現在のGROWステップに対応する「1問だけ」を返す。

        messages: これまでの対話履歴（role: user/assistant）
        step: 現在のGROWステップ（0=G, 1=R, 2=O, 3=W）
        """
        # ステップ範囲を安全に丸める
        safe_step = max(0, min(step, len(GROW_STEPS) - 1))

        if self.is_demo_mode:
            return DEMO_QUESTIONS[safe_step]

        # 現在ステップの狙いをsystem promptに注入
        current = GROW_STEPS[safe_step]
        system_prompt = (
            SYSTEM_PROMPT_BASE
            + f"\n\n## いまのステップ：{current['label']}\n{current['focus']}\n"
            + "このステップの問いを1つだけ投げてください。"
        )

        # 初回（履歴が空）はAPIにダミーのuser発話を与えて問いを生成させる
        api_messages = messages if messages else [
            {"role": "user", "content": "（練習前です。最初の問いをお願いします）"}
        ]

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=system_prompt,
            messages=api_messages,
        )
        return self._extract_question(response.content[0].text)

    def build_theme_card(self, messages: list[dict]) -> dict:
        """会話全体から「今日のテーマカード」を生成する。

        本人が実際に使った言葉を引用してテーマを1文に圧縮する。
        戻り値: {"theme": str, "quote": str, "reason": str}
        """
        if self.is_demo_mode:
            return DEMO_THEME_CARD

        # 本人の発言のみを抜き出してプロンプトに渡す
        user_words = "\n".join(
            f"- {m['content']}" for m in messages if m["role"] == "user"
        )
        user_message = (
            "これまでの対話から、今日の練習テーマを1文にまとめてください。\n"
            "必ず本人の発言の言葉を引用してください。\n\n"
            f"【本人の発言】\n{user_words}"
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=THEME_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return self._extract_theme(response.content[0].text)

    def _extract_question(self, text: str) -> str:
        """レスポンスから問い（question）を抽出する。"""
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            data = json.loads(text[json_start:json_end].strip())
            return data.get("question", "").strip()
        except (ValueError, json.JSONDecodeError):
            pass
        # パース失敗時はそのままテキストを返す
        return text.strip()

    def _extract_theme(self, text: str) -> dict:
        """レスポンスからテーマカード（theme/quote/reason）を抽出する。"""
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            data = json.loads(text[json_start:json_end].strip())
            return {
                "theme": data.get("theme", "").strip(),
                "quote": data.get("quote", "").strip(),
                "reason": data.get("reason", "").strip(),
            }
        except (ValueError, json.JSONDecodeError):
            pass
        # パース失敗時は最低限テキストをテーマに入れて返す
        return {"theme": text.strip(), "quote": "", "reason": ""}
