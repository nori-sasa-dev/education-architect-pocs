import json


class BaseCareerAgent:
    """キャリアチームAI共通エージェント基底クラス"""

    # サブクラスで定義する
    AGENT_NAME: str = ""
    AGENT_KEY: str = ""
    AGENT_ICON: str = ""
    AGENT_DESCRIPTION: str = ""
    SYSTEM_PROMPT: str = ""
    DEMO_RESPONSES: list = []
    MARKER: str = ""  # 抽出マーカー（例: [MIRROR_INSIGHT]）

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        """APIキー未設定時はデモモード"""
        return self.client is None

    def respond(self, messages: list[dict], turn: int, context: str | None = None) -> str:
        """メッセージに対する応答を生成する

        Args:
            messages: 会話履歴
            turn: 現在のフェーズ内ターン数
            context: 前のエージェントからの引き継ぎ情報
        """
        if self.is_demo_mode:
            return self._demo_respond(messages, turn)
        return self._api_respond(messages, context)

    def _api_respond(self, messages: list[dict], context: str | None = None) -> str:
        """Claude APIを使って応答を生成"""
        system = self.SYSTEM_PROMPT
        if context:
            system += f"\n\n## チームメンバーからの引き継ぎ情報\n{context}"

        # 初回挨拶時（メッセージ空）はダミーメッセージを送る
        if not messages:
            messages = [{"role": "user", "content": "こんにちは。キャリアについて相談したいです。"}]

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def _demo_respond(self, messages: list[dict], turn: int) -> str:
        """デモモード用の固定応答を返す"""
        idx = min(turn, len(self.DEMO_RESPONSES) - 1)
        return self.DEMO_RESPONSES[idx]

    def extract_insights(self, text: str) -> dict | None:
        """レスポンスから構造化データを抽出する

        [MARKER] + ```json``` ブロックのパターンで抽出
        """
        if self.MARKER not in text:
            return None
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            return None

    def has_handoff(self, text: str) -> bool:
        """レスポンスにハンドオフマーカーが含まれるか判定"""
        return "[HANDOFF]" in text

    @staticmethod
    def clean_response(text: str) -> str:
        """表示用にマーカーとJSONブロックを除去する"""
        # [HANDOFF] を除去
        text = text.replace("[HANDOFF]", "")

        # [MARKER] 以降のJSONブロックを除去
        markers = [
            "[MIRROR_INSIGHT]",
            "[SCOUT_INSIGHT]",
            "[STRATEGY_INSIGHT]",
            "[CAREER_REPORT]",
        ]
        for marker in markers:
            if marker in text:
                text = text.split(marker)[0]

        return text.strip()
