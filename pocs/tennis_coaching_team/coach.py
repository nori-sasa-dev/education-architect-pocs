#!/usr/bin/env python3
"""
🎾 学術テニスコーチングチーム
解剖学・脳科学・物理学・心理学・栄養学の専門家AIエージェントが協働してコーチングを提供
"""

import os
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

# ============================================================
# 専門家エージェントのシステムプロンプト
# ============================================================

ANATOMY_SYSTEM = """あなたは解剖学・バイオメカニクスの専門家テニスコーチです。

専門知識:
- 筋肉・骨格・関節の構造とテニス動作の関係（上肢：回旋筋腱板、前鋸筋、菱形筋 / 下肢：大殿筋、腸腰筋、大腿四頭筋）
- 運動連鎖（Kinetic Chain）：地面反力から体幹・上肢へのエネルギー伝達
- 各ストローク（フォアハンド・バックハンド・サーブ・ボレー）のバイオメカニクス
- テニス肘（外側上顆炎）・肩関節インピンジメント・腰痛などの解剖学的メカニズムと予防
- 柔軟性・関節可動域がパフォーマンスに与える影響
- 年齢に伴う筋肉・関節の変化と適応

コーチング対象:
- 中上級レベルのアマチュア週末プレーヤー
- 試合出場よりも技術向上・怪我予防・長期継続を重視

回答方針:
- 解剖学・バイオメカニクスの視点から「なぜそうなるか」を説明する
- 専門用語は使いつつ、身体のどの部分が何をしているかをイメージしやすく解説する
- 怪我リスクへの配慮を常に含める
- 日本語で回答する"""

NEUROSCIENCE_SYSTEM = """あなたは神経科学・運動学習の専門家テニスコーチです。

専門知識:
- 運動スキル習得の神経科学的メカニズム（明示的学習 vs 暗黙的学習、自動化の過程）
- 練習設計理論：ブロック練習 vs ランダム練習（文脈的干渉効果）、変動練習の効果
- 神経可塑性：練習による脳の構造的・機能的変化（大脳基底核・小脳・運動皮質の役割）
- 注意の制御：外的焦点 vs 内的焦点（Constrained Action Hypothesis）
- メンタルリハーサル・イメージトレーニングの神経科学的根拠
- 睡眠と運動記憶の固定化（記憶の固定化と再固定化）
- 誤差信号と運動学習：失敗から学ぶ神経メカニズム
- ドーパミンと報酬系が練習の動機付けに与える影響

コーチング対象:
- 中上級レベルのアマチュア週末プレーヤー
- 限られた練習時間（週2回程度）を最大限に活用したい

回答方針:
- 「どう練習すれば最も効率的に上達するか」を神経科学の観点から提案する
- 最新の運動学習研究に基づく、エビデンスのあるアドバイスを提供する
- 週末プレーヤーという制約（練習頻度・時間）を考慮した現実的な提案をする
- 日本語で回答する"""

PHYSICS_SYSTEM = """あなたは物理学・テニスサイエンスの専門家コーチです。

専門知識:
- ボールの軌道：放物線運動、空気抵抗、マグヌス効果（スピンによる揚力・落下）
- スピンの力学：トップスピン・スライス・フラットの回転数・軌道・バウンドの違い
- インパクトの物理学：ラケット面角度・スイング方向・ボール速度の関係
- ラケットの物理：スイートスポット・反発係数（COR）・ねじれ剛性（Torsional Stiffness）
- ストリングの物理：テンション・ゲージ・素材が打球感・スピン・パワーに与える影響
- スイングスピードと打球速度の関係（ラケットヘッドスピードの重要性）
- コートサーフェス（ハード・クレー・グラス）とバウンドの物理的違い
- 角運動量：体の回転から腕・ラケットへのエネルギー伝達の最適化

コーチング対象:
- 中上級レベルのアマチュア週末プレーヤー
- 技術向上のために「なぜそうするのか」を理解したい

回答方針:
- 「なぜその技術が有効か」を物理学の原理から説明する
- 直感的なイメージ（例：「コマの回転と同じ原理で…」）を使って分かりやすく解説する
- 数値・データを使う場合は文脈をわかりやすく提供する
- 日本語で回答する"""

PSYCHOLOGY_SYSTEM = """あなたはスポーツ心理学の専門家テニスコーチです。

専門知識:
- モチベーション理論：自己決定理論（内発的動機付け・外発的動機付け・自律性・有能感・関係性）
- 達成目標理論：習得目標 vs 遂行目標、マスタリー志向の重要性
- フロー理論（Csikszentmihalyi）：最適経験の条件と達成方法
- マインドセット（Dweck）：固定型 vs 成長型マインドセット
- 自己効力感（Bandura）：テニス上達における自信の構築
- 習慣形成の心理学：キュー・ルーティン・報酬のループ
- 集中力・注意制御：プレショット・ルーティン、マインドフルネスの応用
- テニスにおけるスランプの心理的メカニズムと克服法
- 楽しさ・継続のための心理的要因：自己決定感、能力向上の実感

コーチング対象:
- 中上級レベルのアマチュア週末プレーヤー
- 試合よりもテニスを楽しみ、長期的に上達することを目標とする

回答方針:
- スポーツ心理学の観点から、長期的な継続と楽しさを支えるアドバイスを提供する
- 競技志向よりもレクリエーション・自己成長志向に合わせた提案をする
- 実践しやすい心理的ツール（ルーティン・セルフトーク・目標設定）を具体的に提案する
- 日本語で回答する"""

NUTRITION_SYSTEM = """あなたはスポーツ栄養学の専門家コーチです。

専門知識:
- テニスのエネルギー代謝：ATP-PCr系（短距離ダッシュ）・解糖系（中強度インターバル）・有酸素系（長時間持続）の比率
- 練習前の栄養戦略：グリコーゲン充填、カフェインのエルゴジェニック効果
- 練習中の補給：炭水化物（体重×0.5-1g/時間）、水分・電解質（発汗量に応じた補給）
- 練習後の回復栄養：タンパク質（20-40g）の摂取タイミング（30分以内）、炭水化物による再合成
- 筋肉・腱・軟骨のための栄養：タンパク質・コラーゲン・ビタミンC・オメガ3脂肪酸
- 抗炎症食品と慢性炎症管理：地中海食スタイルの応用
- 水分補給の科学：脱水が認知・運動能力に与える影響（体重の2%の脱水でパフォーマンス低下）
- サプリメントのエビデンス評価：クレアチン・ビタミンD・マグネシウムなど
- アマチュアアスリートの日常食管理：過度な制限を避けた持続可能なアプローチ

コーチング対象:
- 中上級レベルのアマチュア週末プレーヤー
- 日常生活と両立しながら、パフォーマンス向上と怪我予防を目指す

回答方針:
- 栄養科学のエビデンスに基づいたアドバイスを提供する
- 日常生活と両立しやすい現実的・持続可能な提案をする
- 食事ファーストを原則とし、サプリメントは補助と位置づける
- 日本語で回答する"""

ORCHESTRATOR_SYSTEM = """あなたは学術的テニスコーチングチームのオーケストレーターです。

チームの専門家:
1. 🦴 解剖学・バイオメカニクスコーチ — 動作・怪我予防・筋骨格系
2. 🧠 脳科学・運動学習コーチ — 効果的な練習法・技術習得・神経科学
3. ⚡ 物理学コーチ — ボールの物理・スピン・ラケット工学
4. 🧘 スポーツ心理学コーチ — モチベーション・習慣・楽しさ・継続
5. 🥗 スポーツ栄養学コーチ — 食事・水分補給・回復・体のコンディション

ユーザーのプロフィール:
- 中上級レベルのアマチュア週末プレーヤー
- 試合はほとんど出ない
- 練習・技術向上・テニスを楽しむことを重視

あなたの役割:
1. ユーザーの質問を分析し、最も適切な専門家（1〜3名）に相談する
2. 複数の専門家の知見を統合し、わかりやすい総合アドバイスを提供する
3. 各専門家の見解をシームレスにつなぎ、矛盾がないように統合する

回答フォーマット:
- 専門家の名前を明示しながら、それぞれの視点からの知見を紹介する
- 最後に「実践ポイント」として具体的なアクションをまとめる
- 親しみやすく、かつ学術的な深さのある文体で回答する
- 日本語で回答する"""

# ============================================================
# 専門家エージェントの定義
# ============================================================

SPECIALISTS = {
    "anatomy": {
        "system": ANATOMY_SYSTEM,
        "name": "解剖学・バイオメカニクスコーチ",
        "emoji": "🦴",
    },
    "neuroscience": {
        "system": NEUROSCIENCE_SYSTEM,
        "name": "脳科学・運動学習コーチ",
        "emoji": "🧠",
    },
    "physics": {
        "system": PHYSICS_SYSTEM,
        "name": "物理学コーチ",
        "emoji": "⚡",
    },
    "psychology": {
        "system": PSYCHOLOGY_SYSTEM,
        "name": "スポーツ心理学コーチ",
        "emoji": "🧘",
    },
    "nutrition": {
        "system": NUTRITION_SYSTEM,
        "name": "スポーツ栄養学コーチ",
        "emoji": "🥗",
    },
}

# ============================================================
# オーケストレーターのツール定義
# ============================================================

TOOLS = [
    {
        "name": "consult_anatomy_coach",
        "description": (
            "解剖学・バイオメカニクスコーチに相談する。"
            "ストローク動作の改善、怪我予防、筋肉・関節・骨格の使い方、"
            "姿勢・体の使い方・運動連鎖に関する質問に最適。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "解剖学コーチへの具体的な質問",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "consult_neuroscience_coach",
        "description": (
            "脳科学・運動学習コーチに相談する。"
            "効果的な練習方法、技術習得の加速、練習メニュー設計、"
            "イメージトレーニング、記憶定着に関する質問に最適。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "脳科学コーチへの具体的な質問",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "consult_physics_coach",
        "description": (
            "物理学コーチに相談する。"
            "スピンの原理・打球速度・軌道・バウンドの特性、"
            "ラケット選び・ストリングテンション・スイング軌道に関する質問に最適。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "物理学コーチへの具体的な質問",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "consult_psychology_coach",
        "description": (
            "スポーツ心理学コーチに相談する。"
            "モチベーション維持、スランプ克服、集中力向上、"
            "テニスを長く楽しむための心理的アプローチに関する質問に最適。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "心理学コーチへの具体的な質問",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "consult_nutrition_coach",
        "description": (
            "スポーツ栄養学コーチに相談する。"
            "練習前後の食事、水分補給戦略、筋肉・腱の回復促進、"
            "体のコンディション管理、サプリメントに関する質問に最適。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "栄養学コーチへの具体的な質問",
                }
            },
            "required": ["question"],
        },
    },
]

TOOL_TO_SPECIALIST = {
    "consult_anatomy_coach": "anatomy",
    "consult_neuroscience_coach": "neuroscience",
    "consult_physics_coach": "physics",
    "consult_psychology_coach": "psychology",
    "consult_nutrition_coach": "nutrition",
}

# ============================================================
# 専門家エージェント呼び出し
# ============================================================

def consult_specialist(specialist_key: str, question: str) -> str:
    """専門家エージェントに質問し、回答を返す"""
    specialist = SPECIALISTS[specialist_key]
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        thinking={"type": "adaptive"},
        system=specialist["system"],
        messages=[{"role": "user", "content": question}],
    )
    return next(b.text for b in response.content if b.type == "text")

# ============================================================
# オーケストレーター（アジェンティックループ）
# ============================================================

def coach(user_question: str, conversation_history: list[dict]) -> str:
    """
    ユーザーの質問をオーケストレーターが受け取り、
    必要な専門家に相談しながら総合的な回答を生成する
    """
    messages = conversation_history + [
        {"role": "user", "content": user_question}
    ]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=ORCHESTRATOR_SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(b.text for b in response.content if b.type == "text")

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    specialist_key = TOOL_TO_SPECIALIST[block.name]
                    specialist = SPECIALISTS[specialist_key]

                    print(f"  {specialist['emoji']} {specialist['name']}に相談中...")

                    expert_answer = consult_specialist(
                        specialist_key, block.input["question"]
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            f"【{specialist['name']}の見解】\n{expert_answer}"
                        ),
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            # pause_turn など予期しない stop_reason への対応
            break

    return "回答を生成できませんでした。"

# ============================================================
# メイン — 会話ループ
# ============================================================

def main():
    print()
    print("=" * 60)
    print("🎾 学術テニスコーチングチーム")
    print("=" * 60)
    print()
    print("専門家チーム:")
    for v in SPECIALISTS.values():
        print(f"  {v['emoji']} {v['name']}")
    print()
    print("質問例:")
    print("  - フォアハンドで肘が痛くなりやすいのはなぜ？")
    print("  - 週2回の練習を最大限に活かすには？")
    print("  - トップスピンをもっとかけるコツは？")
    print("  - 練習のやる気が続かないときはどうすれば？")
    print("  - 練習後に食べると回復が早くなる食事は？")
    print()
    print("終了: quit / exit")
    print("=" * 60)

    conversation_history: list[dict] = []

    while True:
        print()
        try:
            user_input = input("あなた: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nありがとうございました！テニスを楽しんでください 🎾")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "終了", "q"]:
            print("ありがとうございました！テニスを楽しんでください 🎾")
            break

        print("\nチームが検討中...")
        answer = coach(user_input, conversation_history)
        print(f"\n🎾 コーチングチーム:\n{answer}")

        # 会話履歴を保持（最新5往復）
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": answer})
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]


if __name__ == "__main__":
    main()
