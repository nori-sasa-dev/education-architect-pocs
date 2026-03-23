import json
import anthropic
from models import UserProfile

client = anthropic.Anthropic()

INTERVIEW_SYSTEM_PROMPT = """あなたはキャリアチェンジ支援の専門インタビュアーです。
ユーザーが次のキャリアステップを見つけられるよう、温かく共感的な対話を通じて情報を引き出してください。

【引き出すべき情報】
1. 現在の仕事・業界・転職を考えた理由
2. 仕事で大切にしたい価値観（成長・安定・創造性・社会貢献・収入など）
3. 熱中できること・興味関心（仕事外も含む）
4. これまで培ったスキル・得意なこと
5. 避けたい働き方・環境・仕事の種類

【進め方】
- 一度に質問するのは1〜2個まで
- ユーザーの言葉を拾って深掘りする
- 共感・承認を言葉で示す
- 4〜8往復で必要な情報が集まったら、インタビューを締めくくる

インタビューが十分に完了したと判断したら、最後のメッセージに必ず「[INTERVIEW_COMPLETE]」を含めること。
"""

EXTRACTION_SYSTEM_PROMPT = """会話履歴を分析し、ユーザーのキャリアプロフィールを抽出してください。
必ず以下のJSON形式のみで返してください（余計なテキスト・コードブロックは一切不要）:
{
  "name": "名前（不明なら空文字）",
  "current_job": "現職・職種・業界",
  "career_change_reason": "転職・キャリアチェンジを考えている理由",
  "values": ["価値観1", "価値観2"],
  "interests": ["興味・関心1", "興味・関心2"],
  "skills": ["スキル1", "スキル2"],
  "things_to_avoid": ["避けたいこと1", "避けたいこと2"]
}
"""


def respond(messages: list[dict]) -> tuple[str, bool]:
    """
    インタビューの返答を生成する。
    Returns: (表示用テキスト, インタビュー完了フラグ)
    """
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=INTERVIEW_SYSTEM_PROMPT,
        messages=messages,
    )
    text = response.content[0].text
    is_complete = "[INTERVIEW_COMPLETE]" in text
    clean_text = text.replace("[INTERVIEW_COMPLETE]", "").strip()
    return clean_text, is_complete


def extract_profile(messages: list[dict]) -> UserProfile:
    """
    会話履歴からプロフィール情報を抽出する。
    """
    conversation_text = "\n".join(
        f"{'ユーザー' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in messages
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"会話履歴:\n{conversation_text}"}],
    )

    try:
        data = json.loads(response.content[0].text)
        return UserProfile(**data)
    except Exception:
        return UserProfile()
