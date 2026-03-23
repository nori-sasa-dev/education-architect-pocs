import os
import streamlit as st
from dotenv import load_dotenv
from agents.interview_agent import InterviewAgent
from utils.export import discovery_to_json, discovery_to_csv

load_dotenv()

st.set_page_config(
    page_title="キャリア探索AI",
    page_icon="🔍",
    layout="wide",
)

# --- State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "turn" not in st.session_state:
    st.session_state.turn = 0
if "discovery" not in st.session_state:
    st.session_state.discovery = None
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False

# --- Agent Setup ---
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = InterviewAgent(api_key=api_key)

# --- Sidebar ---
with st.sidebar:
    st.title("キャリア探索AI")
    st.caption("対話を通じて、自分を発見する")

    if agent.is_demo_mode:
        st.warning("デモモードで動作中\n\nAPIキーを設定すると本番モードになります")
        with st.expander("APIキー設定方法"):
            st.code("# .envファイルを作成\nANTHROPIC_API_KEY=sk-ant-xxxxx", language="bash")
    else:
        st.success("Claude API 接続済み")

    st.divider()

    if st.session_state.discovery:
        st.subheader("自己探索サマリー")

        discovery = st.session_state.discovery

        if discovery.get("name"):
            st.write(f"**名前:** {discovery['name']}")
        if discovery.get("current_situation"):
            st.write(f"**現在の状況:** {discovery['current_situation']}")

        # 価値観
        values = discovery.get("values", [])
        if values:
            st.write("**大切にしている価値観:**")
            for v in values:
                st.write(f"  - {v}")

        # 強み
        strengths = discovery.get("strengths", [])
        if strengths:
            st.write("**強み:**")
            for s in strengths:
                st.write(f"  - {s}")

        # スキル
        skills = discovery.get("skills", {})
        if skills:
            st.write("**スキル:**")
            for category, items in skills.items():
                if items:
                    label = {"technical": "技術", "human": "ヒューマン", "tacit": "暗黙知"}.get(category, category)
                    for item in items:
                        st.write(f"  - [{label}] {item}")

        # 方向性
        if discovery.get("direction"):
            st.divider()
            st.write("**方向性:**")
            st.info(discovery["direction"])

        # 自己探索サマリー
        if discovery.get("discovery_summary"):
            st.divider()
            st.write("**あなたを一言で:**")
            st.success(discovery["discovery_summary"])

        st.divider()
        st.subheader("エクスポート")

        col1, col2 = st.columns(2)
        with col1:
            json_data = discovery_to_json(discovery)
            st.download_button(
                label="JSON",
                data=json_data,
                file_name="discovery.json",
                mime="application/json",
            )
        with col2:
            csv_data = discovery_to_csv(discovery)
            st.download_button(
                label="CSV",
                data=csv_data,
                file_name="discovery.csv",
                mime="text/csv",
            )

    if st.button("新しいセッション", use_container_width=True):
        st.session_state.messages = []
        st.session_state.turn = 0
        st.session_state.discovery = None
        st.session_state.interview_complete = False
        st.rerun()

# --- Main Chat Area ---
st.header("キャリア探索AI")
st.caption("AIとの対話を通じて、あなたの価値観・強み・方向性を発見します")

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Generate initial greeting
if not st.session_state.messages:
    with st.chat_message("assistant"):
        greeting = agent.respond([], st.session_state.turn)
        st.markdown(greeting)
    st.session_state.messages.append({"role": "assistant", "content": greeting})

# Chat input
if not st.session_state.interview_complete:
    if user_input := st.chat_input("思いつくままに、自由にお話しください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # エージェントの応答を生成
        st.session_state.turn += 1
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        response = agent.respond(api_messages, st.session_state.turn)

        # 自己探索サマリーの抽出チェック
        discovery = agent.extract_discovery(response)
        if discovery:
            st.session_state.discovery = discovery
            st.session_state.interview_complete = True
            # JSON部分を表示から除外
            display_text = response.split("[DISCOVERY_COMPLETED]")[0].strip()
        else:
            display_text = response

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(display_text)

        if st.session_state.interview_complete:
            st.success("自己探索が完了しました！サイドバーであなたの探索結果を確認できます。")
            st.rerun()
else:
    st.info("自己探索が完了しています。サイドバーで結果を確認し、JSONまたはCSVでエクスポートできます。\n\n新しいセッションを開始するには、サイドバーの「新しいセッション」ボタンを押してください。")
