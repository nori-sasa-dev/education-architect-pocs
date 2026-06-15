"""
🎾 テニス・クイックコーチ — コーチエージェント

試合・練習中の状況テキストを受け取り、
「今すぐ使える戦術アドバイス」を構造化して返す。

抽出マーカーパターン: [ADVICE] + ```json``` ブロック
デモモードパターン: APIキー未設定時は DEMO_RESPONSES から固定応答を返す
"""

import json

MODEL = "claude-sonnet-4-6"


class CoachError(Exception):
    """アドバイス取得時のエラー（ネットワーク断・認証・レート超過など）を表す例外。

    app.py 側でこの例外を捕捉し、ユーザーに穏やかなメッセージを表示する。
    """
    pass

# システムプロンプト：今すぐ使える戦術アドバイスを構造化して返す
SYSTEM_PROMPT = """あなたは試合・練習中のプレイヤーをサポートする、実戦特化のテニスコーチです。
プレイヤーが今いるコート上の状況を受け取り、「次のポイントですぐ使える」具体的な戦術を返します。

## 役割
- 状況を素早く読み解き、実戦的で具体的なアドバイスを返す
- 抽象論（「集中しよう」など）ではなく、すぐ実行できる行動を示す
- プレイヤーのプレースタイル（攻撃型/守備型/オールラウンド）に合わせて調整する

## アドバイスの方針
- summary: 状況を1〜2文で簡潔に要約する
- tactics: 優先順位の高い順に3つの戦術を示す。それぞれ短く具体的に
- next_action: 次の1ポイントで必ず試す「1つだけ」の行動を示す
- mental: プレッシャー下でも実行しやすくする、メンタル面の一言

## 出力形式（マーカーとJSONのみ。前置き・後置き不要）
[ADVICE]
```json
{
  "summary": "状況の要約",
  "tactics": ["最優先の戦術", "2番目の戦術", "3番目の戦術"],
  "next_action": "次のポイントで試す1アクション",
  "mental": "メンタル面の一言"
}
```
"""

# プレースタイルごとの補足（システムプロンプトに付与する）
STYLE_NOTES = {
    "攻撃型": "プレイヤーは攻撃型です。先手を取り、主導権を握る戦術を優先してください。",
    "守備型": "プレイヤーは守備型です。粘り強くつなぎ、相手のミスを誘う戦術を優先してください。",
    "オールラウンド": "プレイヤーはオールラウンドです。状況に応じて攻守を切り替える柔軟な戦術を示してください。",
}

# デモ用の固定応答（APIキー未設定時に使用）
# プレースタイル別に用意し、未設定キーは「オールラウンド」にフォールバックする
DEMO_RESPONSES = {
    "攻撃型": {
        "summary": "相手のバックが弱く、2-3でリードされている展開。風が強い条件。",
        "tactics": [
            "相手バック側へ深いボールを集め、甘い返球を強打で仕留める",
            "風上ではスピンを多めにかけ、ボールを確実にコート内へ収める",
            "リターンから早めに前へ詰め、ポイントを短くしてリスクを減らす",
        ],
        "next_action": "1stサーブを相手バック側に集中させ、浮いた返球を即攻撃する。",
        "mental": "ビハインドこそ攻めの好機。1ポイントずつ取り返す意識でいこう。",
    },
    "守備型": {
        "summary": "相手のバックが弱く、2-3でリードされている展開。風が強い条件。",
        "tactics": [
            "相手バック側へ深く高い軌道で返し、攻め急がせてミスを誘う",
            "風下では低く速いボールで、相手の振り遅れを引き出す",
            "ラリーを長くして、リードしている相手に焦りを生ませる",
        ],
        "next_action": "相手バックへ高く深いボールを1本、まず確実につなぐ。",
        "mental": "今は耐える局面。1本多く返す気持ちで相手のミスを待とう。",
    },
    "オールラウンド": {
        "summary": "相手のバックが弱く、2-3でリードされている展開。風が強い条件。",
        "tactics": [
            "相手バック側を起点に組み立て、甘い球が来たら攻めに転じる",
            "風向きを見て、風上はスピン・風下はフラット気味と打ち分ける",
            "攻守の切り替えを早くし、相手にリズムを読ませない",
        ],
        "next_action": "相手バックへ1本深く打ち、返球の質を見てから攻守を決める。",
        "mental": "状況は悪くない。落ち着いて選択肢を持ち続けよう。",
    },
}


class CoachAgent:
    """状況テキストから戦術アドバイスを生成するエージェント"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        """APIキー未設定（クライアント未生成）ならデモモード"""
        return self.client is None

    def respond(self, situation: str, play_style: str) -> dict:
        """
        状況テキストとプレースタイルから戦術アドバイス（辞書）を返す。

        situation: 試合・練習中の状況テキスト
        play_style: "攻撃型" / "守備型" / "オールラウンド"
        """
        if self.is_demo_mode:
            # デモモード：プレースタイル別の固定応答を返す
            return DEMO_RESPONSES.get(play_style, DEMO_RESPONSES["オールラウンド"])

        # プレースタイルの補足をシステムプロンプトに付け足す
        style_note = STYLE_NOTES.get(play_style, STYLE_NOTES["オールラウンド"])
        system = SYSTEM_PROMPT + "\n\n## このプレイヤーについて\n" + style_note

        user_message = (
            f"今の状況です。次のポイントで使える戦術アドバイスをください。\n\n"
            f"【プレースタイル】{play_style}\n"
            f"【状況】{situation}"
        )

        # 実API呼び出し。ネットワーク断・認証エラー・レート超過などで
        # 例外が出ても生のトレースバックを表示せず、CoachError に包んで返す。
        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
        except Exception as e:
            raise CoachError(str(e)) from e

        return extract_advice(response.content[0].text)


def extract_advice(text: str) -> dict:
    """
    レスポンステキストから [ADVICE] + ```json``` ブロックを抽出し、辞書化する。
    パース失敗時は summary にテキスト全体を入れた辞書を返す（画面が壊れないように）。
    """
    try:
        json_start = text.index("```json") + len("```json")
        json_end = text.index("```", json_start)
        data = json.loads(text[json_start:json_end].strip())
    except (ValueError, json.JSONDecodeError):
        # マーカーが無い・JSONが壊れている場合のフォールバック
        return {
            "summary": text.strip(),
            "tactics": [],
            "next_action": "",
            "mental": "",
        }

    # 必要なキーが欠けていても落ちないよう、デフォルト値で補完する
    return {
        "summary": data.get("summary", ""),
        "tactics": data.get("tactics", []),
        "next_action": data.get("next_action", ""),
        "mental": data.get("mental", ""),
    }
