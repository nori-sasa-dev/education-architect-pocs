"""
🎾 テニス・クイックコーチ — Streamlit アプリ

試合・練習中の状況をテキスト入力すると、
AIコーチが「今すぐ使える戦術アドバイス」を返す単一画面アプリ。
"""

import os

import streamlit as st
from dotenv import load_dotenv

from coach import CoachAgent, CoachError

# .env からAPIキーを読み込む
load_dotenv()

# ============================================================
# ページ設定
# ============================================================
st.set_page_config(page_title="テニス・クイックコーチ", page_icon="🎾")

st.title("🎾 テニス・クイックコーチ")
st.caption("試合・練習中の状況を入力すると、次のポイントで使える戦術をその場で返します。")

# エージェントを生成（APIキーが無ければ自動でデモモード）
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = CoachAgent(api_key=api_key)

# デモモードならユーザーに知らせる
if agent.is_demo_mode:
    st.info("デモモードで動作中です（APIキー未設定）。固定のサンプルアドバイスを表示します。")

# ============================================================
# 入力フォーム
# ============================================================
with st.form("situation_form"):
    situation = st.text_area(
        "今の状況を入力してください",
        placeholder="例: 相手のバックが弱い。2-3でリードされている。風が強い。",
        height=120,
    )
    play_style = st.selectbox(
        "あなたのプレースタイル",
        ["攻撃型", "守備型", "オールラウンド"],
    )
    submitted = st.form_submit_button("アドバイスをもらう")

# ============================================================
# アドバイス生成・表示
# ============================================================
if submitted:
    if not situation.strip():
        st.warning("状況を入力してください。")
    else:
        # 実API呼び出しが失敗（ネットワーク断・認証・レート超過など）しても
        # 生のトレースバックを出さず、穏やかなメッセージで知らせる。
        try:
            with st.spinner("コーチが状況を読み解いています..."):
                advice = agent.respond(situation, play_style)
        except CoachError:
            st.error("アドバイス取得に失敗しました（ネットワーク/APIキーをご確認ください）。")
            st.stop()

        st.divider()

        # デモモード時はサンプル応答である旨を明示し、透明性を高める
        if agent.is_demo_mode:
            st.caption("※これはサンプル応答です（APIキー未設定）。入力内容に関わらず固定のアドバイスを表示しています。")

        # 状況の要約
        st.subheader("📋 状況の要約")
        st.write(advice["summary"])

        # 推奨戦術（優先順位つき）
        st.subheader("🎯 推奨戦術（優先順位順）")
        if advice["tactics"]:
            for i, tactic in enumerate(advice["tactics"], start=1):
                st.markdown(f"**{i}.** {tactic}")
        else:
            st.write("（戦術を取得できませんでした）")

        # 次の1アクション
        st.subheader("⚡ 次のポイントで試す1アクション")
        if advice["next_action"]:
            st.success(advice["next_action"])
        else:
            st.write("（アクションを取得できませんでした）")

        # メンタル面の一言
        if advice["mental"]:
            st.subheader("🧘 メンタルの一言")
            st.info(advice["mental"])
