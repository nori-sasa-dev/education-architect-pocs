import json


class SessionOrchestrator:
    """セッション進行を管理するオーケストレーター

    決定論的ステートマシンとして、フェーズ遷移を管理する。
    各フェーズには担当エージェントと最大ターン数が定義されている。
    """

    PHASES = [
        {
            "name": "opening",
            "agent_key": "coach",
            "max_turns": 1,
            "label": "チーム紹介",
            "description": "チームの紹介と最初の問いかけ",
        },
        {
            "name": "exploration",
            "agent_key": "mirror",
            "max_turns": 20,
            "label": "自己探索",
            "description": "価値観・強みの発見",
        },
        {
            "name": "market",
            "agent_key": "scout",
            "max_turns": 20,
            "label": "市場分析",
            "description": "キャリア市場の情報提供",
        },
        {
            "name": "strategy",
            "agent_key": "strategist",
            "max_turns": 20,
            "label": "戦略立案",
            "description": "キャリア方向性の提案",
        },
        {
            "name": "action",
            "agent_key": "coach",
            "max_turns": 20,
            "label": "アクションプラン",
            "description": "具体的な行動計画の策定",
        },
    ]

    def __init__(self):
        self.phase_index = 0
        self.phase_turn = 0
        self.insights = {}  # {"mirror": {...}, "scout": {...}, ...}
        self.completed = False

    def get_current_phase(self) -> dict:
        """現在のフェーズ情報を取得"""
        if self.completed:
            return self.PHASES[-1]
        return self.PHASES[self.phase_index]

    def get_current_agent_key(self) -> str:
        """現在のフェーズの担当エージェントキーを取得"""
        return self.get_current_phase()["agent_key"]

    def get_progress(self) -> tuple[int, int]:
        """進捗を返す (現在のフェーズ番号, 全フェーズ数)"""
        return self.phase_index + 1, len(self.PHASES)

    def get_agent_status(self, agent_key: str) -> str:
        """エージェントの状態を返す（待機中/発言中/完了）"""
        if self.completed:
            return "completed"

        current_key = self.get_current_agent_key()

        # 完了済みフェーズのエージェントを特定
        completed_agents = set()
        for i in range(self.phase_index):
            completed_agents.add(self.PHASES[i]["agent_key"])

        # 現在のエージェントの状態（coachは開始と終了の2フェーズあるので特別処理）
        if agent_key == current_key:
            return "active"
        elif agent_key in completed_agents:
            # coachは最初のフェーズで完了しても、最後のフェーズで再度activeになる
            if agent_key == "coach" and self.phase_index < len(self.PHASES) - 1:
                # まだactionフェーズに到達していない
                for future_phase in self.PHASES[self.phase_index:]:
                    if future_phase["agent_key"] == agent_key:
                        return "completed"  # 一旦完了扱い
            return "completed"
        else:
            return "waiting"

    def build_context(self) -> str | None:
        """前のエージェントの抽出結果をコンテキストとして構築"""
        if not self.insights:
            return None
        parts = []
        for agent_key, data in self.insights.items():
            parts.append(
                f"### {agent_key} の発見:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
            )
        return "\n\n".join(parts)

    def process_response(self, response: str, agent) -> bool:
        """レスポンスを処理し、フェーズ遷移が必要か判定する

        Returns:
            bool: フェーズが遷移した場合はTrue
        """
        if self.completed:
            return False

        # インサイト抽出を試みる
        insights = agent.extract_insights(response)
        if insights:
            self.insights[agent.AGENT_KEY] = insights

        # ハンドオフ判定（会話の深さに基づくHANDOFFマーカーのみで遷移）
        should_advance = False
        if agent.has_handoff(response):
            should_advance = True
        elif self.phase_turn >= self.get_current_phase()["max_turns"] - 1:
            # 安全弁：最大ターン数に達した場合のみ強制遷移
            should_advance = True

        # フェーズ遷移
        if should_advance:
            self.phase_index += 1
            self.phase_turn = 0
            if self.phase_index >= len(self.PHASES):
                self.phase_index = len(self.PHASES) - 1
                self.completed = True
        else:
            self.phase_turn += 1

        return should_advance

    def to_dict(self) -> dict:
        """session_state保存用にdict化"""
        return {
            "phase_index": self.phase_index,
            "phase_turn": self.phase_turn,
            "insights": self.insights,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionOrchestrator":
        """dictからオーケストレーターを復元"""
        orch = cls()
        orch.phase_index = data["phase_index"]
        orch.phase_turn = data["phase_turn"]
        orch.insights = data["insights"]
        orch.completed = data["completed"]
        return orch
