from state import SessionState, Phase
from agents.interview_agent import respond, extract_profile


class Orchestrator:
    """
    会話フローを管理し、各エージェントへのルーティングを担う。
    現在はInterview Agentのみ。Analysis / Planning Agentは今後追加予定。
    """

    def __init__(self):
        self.state = SessionState()

    def start(self) -> str:
        """セッションを開始し、最初のAI発話を返す。"""
        opening_user_msg = "キャリアチェンジについて相談したいです。"
        self.state.messages.append({"role": "user", "content": opening_user_msg})

        response, _ = respond(self.state.messages)
        self.state.messages.append({"role": "assistant", "content": response})
        return response

    def process(self, user_input: str) -> tuple[str, bool]:
        """
        ユーザー入力を受け取り、適切なエージェントで処理する。
        Returns: (AIの返答, セッション完了フラグ)
        """
        self.state.messages.append({"role": "user", "content": user_input})
        self.state.turn_count += 1

        if self.state.phase == Phase.INTERVIEW:
            response, is_complete = respond(self.state.messages)
            self.state.messages.append({"role": "assistant", "content": response})

            if is_complete:
                self.state.interview_complete = True
                self.state.phase = Phase.COMPLETE
                self.state.profile = extract_profile(self.state.messages)

            return response, is_complete

        return "インタビューはすでに完了しています。", True

    def get_profile_summary(self) -> str:
        return self.state.profile.summary()
