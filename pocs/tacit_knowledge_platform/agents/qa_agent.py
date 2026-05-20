import json

SYSTEM_PROMPT_TEMPLATE = """あなたは「{author_name}」（{author_role}・{department}・経験{years_of_experience}）の代理として応答するAIです。

以下の知識ベースに基づき、{author_name}さん本人として自然な一人称で回答してください。

## 知識ベース
{knowledge_context}

## 応答のルール
- 「私は〜」「私の経験では〜」など一人称で話す
- 知識ベースにある内容は具体的に答える
- 知識ベースにない内容は「その点は記録が残っていないのですが…」と正直に伝える
- 後任者に語りかけるような温かいトーンで
- 回答は簡潔に（長くても300字程度）
"""

DEMO_RESPONSES = [
    "私の経験から言うと、障害が起きたときはまず「何が変わったか」を確認するのが鉄則です。直近1週間のデプロイや設定変更を確認してください。原因の8割はそこにあります。",
    "リリース判断に迷ったとき、私はいつも「このバグでユーザーの業務が止まるか？」を基準にしていました。止まらないなら、まず出してしまって後から直す判断も大事です。",
    "プロジェクトの雰囲気が変わったと感じたら要注意です。報告が減る、会議で目を合わせない、進捗が急に楽観的になる…これが重なったときは必ず1on1で直接聞いてください。",
    "技術は後から追いつけます。でも人間関係は時間がかかる。困ったときに頼れる人を平時から作っておくこと、これが私からの一番の教えです。",
]


def _build_knowledge_context(knowledge_items: list[dict]) -> str:
    if not knowledge_items:
        return "（知識ベースが空です）"
    lines = []
    for item in knowledge_items:
        lines.append(f"### [{item['category']}] {item['title']}")
        lines.append(item["content"])
        if item.get("context"):
            lines.append(f"活用場面: {item['context']}")
        lines.append("")
    return "\n".join(lines)


class QAAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        self._demo_turn = 0

    @property
    def is_demo_mode(self):
        return self.client is None

    def respond(self, messages: list[dict], author_info: dict, knowledge_items: list[dict]) -> str:
        if self.is_demo_mode:
            return self._demo_respond()
        return self._api_respond(messages, author_info, knowledge_items)

    def _api_respond(self, messages: list[dict], author_info: dict, knowledge_items: list[dict]) -> str:
        knowledge_context = _build_knowledge_context(knowledge_items)
        system = SYSTEM_PROMPT_TEMPLATE.format(
            author_name=author_info.get("author_name", "前任者"),
            author_role=author_info.get("author_role", ""),
            department=author_info.get("department", ""),
            years_of_experience=author_info.get("years_of_experience", ""),
            knowledge_context=knowledge_context,
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def _demo_respond(self) -> str:
        idx = self._demo_turn % len(DEMO_RESPONSES)
        self._demo_turn += 1
        return DEMO_RESPONSES[idx]
