import os
import sys

# Streamlit Cloud でのモジュール解決
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv
from coach import coach, SPECIALISTS

load_dotenv()

st.set_page_config(
    page_title="学術テニスコーチングチーム",
    page_icon="🎾",
    layout="wide",
)

api_key = os.getenv("ANTHROPIC_API_KEY")
IS_DEMO = not bool(api_key)

# デモ用の固定回答
DEMO_RESPONSES = [
    (
        "**🦴 解剖学コーチより：** フォアハンドの痛みは、グリップが厚すぎる場合に"
        "回旋筋腱板に過剰な負荷がかかることで生じやすいです。スイング時に肘を体幹に"
        "近づけ、前腕の回内（プロネーション）をスムーズに行うことが予防の鍵です。\n\n"
        "**🧠 脳科学コーチより：** 痛みが出る動作パターンは「運動プログラム」として"
        "定着しています。まず低強度でフォームを意識的に修正し、新しいパターンを"
        "自動化させましょう。週2回の練習では、各セッションの最初15分を意識的な"
        "フォーム練習に充てると効果的です。\n\n"
        "**実践ポイント：** ①グリップを少し薄め（セミウエスタン以下）に調整、"
        "②スイング後に手首が自然に返るよう練習、③痛みがある場合は48時間休息。"
    ),
    (
        "**⚡ 物理学コーチより：** トップスピンはラケット面を閉じ（前傾させ）、"
        "ボールの下から上にスイングすることで生まれます。毎秒3000回転以上の回転数が"
        "あると、マグヌス効果により軌道が急激に落ち、コートに収まりやすくなります。\n\n"
        "**🦴 解剖学コーチより：** スピン量を増やすには、手首のラグ（遅れ）を作り、"
        "インパクト直前にスナップすることが重要です。前鋸筋と肩甲骨の安定が"
        "スムーズなフォロースルーを支えます。\n\n"
        "**実践ポイント：** ①ラケットヘッドを下げてから上に振り抜く意識、"
        "②「こすり上げる」より「振り抜く」感覚で、③ボールの赤道より下を当てる。"
    ),
    (
        "**🧘 心理学コーチより：** 練習継続には「自律性」「有能感」「つながり」の"
        "3つが重要です（自己決定理論）。やる気が出ないときは目標を小さくし、"
        "「今日は10球だけ」という達成可能な目標設定が効果的です。\n\n"
        "**🥗 栄養学コーチより：** エネルギー不足もモチベーション低下の原因です。"
        "練習前90分に炭水化物（バナナ・おにぎり等）を摂取し、血糖値を安定させましょう。"
        "また練習後30分以内にタンパク質20gの摂取が回復を促進します。\n\n"
        "**実践ポイント：** ①練習前に「今日の小目標」を1つ決める、"
        "②仲間と練習する機会を増やす、③練習後にプロテインまたは牛乳を摂取。"
    ),
]

# --- サイドバー ---
with st.sidebar:
    st.title("🎾 学術テニスコーチングチーム")
    st.caption("5つの学術領域の専門家AIが協働")

    if IS_DEMO:
        st.warning("デモモードで動作中\n\nAPIキーを設定すると本番モードになります")
        with st.expander("APIキー設定方法"):
            st.code("# .envファイルを作成\nANTHROPIC_API_KEY=sk-ant-xxxxx", language="bash")
    else:
        st.success("Claude API 接続済み")

    st.divider()
    st.subheader("専門家チーム")
    for v in SPECIALISTS.values():
        st.markdown(f"{v['emoji']} {v['name']}")

    st.divider()
    st.subheader("質問例")
    examples = [
        "フォアハンドで肘が痛くなりやすいのはなぜ？",
        "週2回の練習を最大限に活かすには？",
        "トップスピンをもっとかけるコツは？",
        "練習のやる気が続かないときはどうすれば？",
        "練習後に食べると回復が早くなる食事は？",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_input = ex
            st.rerun()

    st.divider()
    if st.button("会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.demo_idx = 0
        st.rerun()

# --- セッション状態の初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "demo_idx" not in st.session_state:
    st.session_state.demo_idx = 0
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# --- メインエリア ---
st.header("🎾 学術テニスコーチングチーム")
st.caption("解剖学・脳科学・物理学・心理学・栄養学の専門家AIが、あなたのテニスをサポートします")

# 既存メッセージの表示
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🎾"):
            st.markdown(msg["content"])

# サイドバーのボタンで入力された質問を処理
user_input = st.chat_input("テニスの悩みや質問を入力してください...")
if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    # ユーザーメッセージ表示
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🎾"):
        if IS_DEMO:
            # デモモード：固定回答をローテーション
            idx = st.session_state.demo_idx % len(DEMO_RESPONSES)
            answer = DEMO_RESPONSES[idx]
            st.session_state.demo_idx += 1
            st.markdown(answer)
        else:
            # 本番モード：専門家チームに相談
            consulted = []

            def on_consult(specialist):
                consulted.append(f"{specialist['emoji']} {specialist['name']}")

            with st.status("チームが検討中...", expanded=True) as status:
                answer = coach(
                    user_input,
                    st.session_state.history,
                    api_key=api_key,
                    on_consult=lambda s: (
                        status.update(
                            label=f"{s['emoji']} {s['name']}に相談中...",
                            expanded=True,
                        ),
                        on_consult(s),
                    ),
                )
                if consulted:
                    status.update(
                        label="相談完了: " + "、".join(consulted),
                        state="complete",
                        expanded=False,
                    )

            st.markdown(answer)

    # 会話履歴を保存（API用・表示用）
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": answer})

    # 履歴は最新5往復に制限
    if len(st.session_state.history) > 10:
        st.session_state.history = st.session_state.history[-10:]

    st.rerun()
