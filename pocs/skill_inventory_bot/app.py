import os
import streamlit as st
from dotenv import load_dotenv
from agents.interview_agent import InterviewAgent, PHASE_NAMES
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
if "current_phase" not in st.session_state:
    st.session_state.current_phase = 1
if "partial_insights" not in st.session_state:
    st.session_state.partial_insights = {"values": [], "strengths": []}

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

    # --- 進捗インジケーター ---
    if not st.session_state.interview_complete:
        phase = InterviewAgent.get_phase(st.session_state.turn)
        phase_name, phase_desc = PHASE_NAMES[phase]
        progress = min(st.session_state.turn / 8, 1.0)

        st.subheader("対話の進捗")
        st.progress(progress)
        st.caption(f"Phase {phase} / 4　　ターン {st.session_state.turn} / 8")
        st.markdown(f"**{phase_name}**")
        st.caption(phase_desc)

        # --- リアルタイムの気づき（E） ---
        partial = st.session_state.partial_insights
        if partial["values"] or partial["strengths"]:
            st.divider()
            st.subheader("見えてきたこと")
            if partial["values"]:
                st.write("大切にしていること：")
                for v in partial["values"]:
                    st.write(f"  - {v}")
            if partial["strengths"]:
                st.write("強み：")
                for s in partial["strengths"]:
                    st.write(f"  - {s}")

    # --- 完了後：自己探索サマリー ---
    if st.session_state.discovery:
        st.subheader("自己探索サマリー")

        discovery = st.session_state.discovery

        if discovery.get("name"):
            st.write(f"**名前:** {discovery['name']}")
        if discovery.get("current_situation"):
            st.write(f"**現在の状況:** {discovery['current_situation']}")

        values = discovery.get("values", [])
        if values:
            st.write("**大切にしている価値観:**")
            for v in values:
                st.write(f"  - {v}")

        strengths = discovery.get("strengths", [])
        if strengths:
            st.write("**強み:**")
            for s in strengths:
                st.write(f"  - {s}")

        skills = discovery.get("skills", {})
        if skills:
            st.write("**スキル:**")
            for category, items in skills.items():
                if items:
                    label = {"technical": "技術", "human": "ヒューマン", "tacit": "暗黙知"}.get(category, category)
                    for item in items:
                        st.write(f"  - [{label}] {item}")

        if discovery.get("direction"):
            st.divider()
            st.write("**方向性:**")
            st.info(discovery["direction"])

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
        st.session_state.current_phase = 1
        st.session_state.partial_insights = {"values": [], "strengths": []}
        st.rerun()

# --- Main Chat Area ---
st.header("キャリア探索AI")
st.caption("AIとの対話を通じて、あなたの価値観・強み・方向性を発見します")

# --- メッセージ履歴の表示 ---
for msg in st.session_state.messages:
    # フェーズ移行マーカーの表示（D）
    if msg.get("role") == "system" and msg.get("type") == "phase_transition":
        phase_num = msg["phase"]
        phase_name, phase_desc = PHASE_NAMES[phase_num]
        st.markdown("---")
        st.caption(f"✦ Phase {phase_num} / 4　{phase_name} ─ {phase_desc}")
        continue

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 初回挨拶（ストリーミング）---
if not st.session_state.messages:
    with st.chat_message("assistant"):
        greeting = st.write_stream(agent.stream_respond([], 0))
    st.session_state.messages.append({"role": "assistant", "content": greeting})

# --- チャット入力 ---
if not st.session_state.interview_complete:
    if user_input := st.chat_input("思いつくままに、自由にお話しください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # フェーズ移行チェック（D）
        st.session_state.turn += 1
        new_phase = InterviewAgent.get_phase(st.session_state.turn)
        if new_phase != st.session_state.current_phase:
            phase_name, phase_desc = PHASE_NAMES[new_phase]
            # チャット履歴にフェーズ移行マーカーを追加
            st.session_state.messages.append({
                "role": "system",
                "type": "phase_transition",
                "phase": new_phase,
                "phase_name": phase_name,
            })
            st.markdown("---")
            st.caption(f"✦ Phase {new_phase} / 4　{phase_name} ─ {phase_desc}")
            st.session_state.current_phase = new_phase

        # APIに渡すメッセージ（user/assistantのみ）
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] in ("user", "assistant")
        ]

        # AIの応答をストリーミング表示（A・C）
        with st.chat_message("assistant"):
            full_response = st.write_stream(
                agent.stream_respond(api_messages, st.session_state.turn)
            )

        # 自己探索サマリーの抽出チェック
        discovery = agent.extract_discovery(full_response)
        if discovery:
            st.session_state.discovery = discovery
            st.session_state.interview_complete = True
            # JSONブロックを除いたテキストをメッセージ履歴に保存
            display_text = full_response.split("[DISCOVERY_COMPLETED]")[0].strip()
            st.session_state.messages.append({"role": "assistant", "content": display_text})
        else:
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        # サイドバーのリアルタイム更新（E）
        all_messages = [
            m for m in st.session_state.messages
            if m["role"] in ("user", "assistant")
        ]
        st.session_state.partial_insights = agent.extract_partial_insights(all_messages)

        if st.session_state.interview_complete:
            st.success("自己探索が完了しました！サイドバーであなたの探索結果を確認できます。")
            st.rerun()
else:
    st.info("自己探索が完了しています。サイドバーで結果を確認し、JSONまたはCSVでエクスポートできます。\n\n新しいセッションを開始するには、サイドバーの「新しいセッション」ボタンを押してください。")
