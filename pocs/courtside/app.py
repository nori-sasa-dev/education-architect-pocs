import os
import streamlit as st
from dotenv import load_dotenv

from agents.grow_agent import GrowAgent, GROW_STEPS

load_dotenv()

# ─── 設定 ─────────────────────────────────────────────
# 往復の安全弁：これを超えたら強制的にテーマカード生成へ。
# （AIが処方型に逸脱して延々と問いを続けるのを防ぐ）
MAX_TURNS = 5

# エージェント初期化
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = GrowAgent(api_key=api_key)

# ページ設定（1カラム＝InnerLens踏襲）
st.set_page_config(page_title="Courtside", page_icon="🎾", layout="centered")

st.title("🎾 Courtside")
st.caption("練習の“前”に、3分で「今日の自分のテーマ」を自分で決める")

if agent.is_demo_mode:
    st.info("デモモード：APIキー未設定のため固定の問いを返します。")


# ─── セッション状態の初期化 ───────────────────────────
def init_state():
    st.session_state.setdefault("step", 0)            # 0=G,1=R,2=O,3=W,4=done
    st.session_state.setdefault("chat_history", [])   # 画面表示用
    st.session_state.setdefault("api_history", [])    # API送信用
    st.session_state.setdefault("turn", 0)            # ユーザー送信回数
    st.session_state.setdefault("theme_card", None)   # 生成したテーマカード
    st.session_state.setdefault("started", False)     # 最初の問いを出したか


def reset_state():
    """最初からやり直す。"""
    for key in ["step", "chat_history", "api_history", "turn", "theme_card", "started"]:
        if key in st.session_state:
            del st.session_state[key]


init_state()


# ─── 進捗の可視化（●○）────────────────────────────────
def render_progress():
    labels = [s["key"] for s in GROW_STEPS]  # G R O W
    marks = []
    for i, label in enumerate(labels):
        # 現在ステップ以前は ●（完了/進行中）、それ以降は ○
        mark = "●" if (i < st.session_state.step or st.session_state.step >= 4) else "○"
        marks.append(f"{mark} {label}")
    st.markdown("　".join(marks))


render_progress()
st.divider()


# ─── テーマカード生成 ─────────────────────────────────
def generate_theme_card():
    with st.spinner("今日のテーマをまとめています..."):
        card = agent.build_theme_card(st.session_state.api_history)
    st.session_state.theme_card = card
    st.session_state.step = 4


# ─── 最初の問い（Goal）を出す ─────────────────────────
if not st.session_state.started:
    with st.spinner("考えています..."):
        first_q = agent.respond([], step=0)
    st.session_state.chat_history.append({"role": "assistant", "content": first_q})
    st.session_state.api_history.append({"role": "assistant", "content": first_q})
    st.session_state.started = True


# ─── これまでの対話を表示 ─────────────────────────────
for msg in st.session_state.chat_history:
    role = "assistant" if msg["role"] == "assistant" else "user"
    with st.chat_message(role):
        st.write(msg["content"])


# ─── テーマカード表示（step==4）────────────────────────
if st.session_state.step >= 4 and st.session_state.theme_card:
    card = st.session_state.theme_card
    st.divider()
    st.subheader("🎯 今日のテーマカード")

    with st.container(border=True):
        st.markdown(f"### {card['theme']}")
        if card.get("quote"):
            st.markdown(f"> あなたの言葉：「{card['quote']}」")
        if card.get("reason"):
            st.caption(card["reason"])

    # コピー用（本人がそのまま控えられるように）
    copy_text = card["theme"]
    if card.get("quote"):
        copy_text += f"\n（あなたの言葉：{card['quote']}）"
    st.code(copy_text, language=None)

    st.success("これが今日のあなたのテーマです。コートに立つ前に、もう一度だけ思い出してください。")

    if st.button("最初からやり直す", type="secondary"):
        reset_state()
        st.rerun()

# ─── 対話継続（step < 4）──────────────────────────────
else:
    user_input = st.chat_input("あなたの言葉で答えてください")

    if user_input:
        # ユーザー発話を記録
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.api_history.append({"role": "user", "content": user_input})
        st.session_state.turn += 1
        # 1回答ごとにGROWステップを進める
        st.session_state.step += 1

        # 安全弁：Willまで到達 or 往復上限を超えたらテーマカードへ
        if st.session_state.step >= 4 or st.session_state.turn >= MAX_TURNS:
            generate_theme_card()
            st.rerun()
        else:
            # 次のステップの問いを1つだけ生成
            with st.spinner("考えています..."):
                next_q = agent.respond(
                    st.session_state.api_history, step=st.session_state.step
                )
            st.session_state.chat_history.append({"role": "assistant", "content": next_q})
            st.session_state.api_history.append({"role": "assistant", "content": next_q})
            st.rerun()

    # いつでも最初からやり直せる
    st.divider()
    if st.button("最初からやり直す", type="secondary"):
        reset_state()
        st.rerun()
