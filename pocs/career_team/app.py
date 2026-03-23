import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from agents import CoachAgent, MirrorAgent, ScoutAgent, StrategistAgent
from agents.base_agent import BaseCareerAgent
from orchestrator import SessionOrchestrator
from database.db import init_db, save_session, get_session, get_all_sessions
from utils.export import report_to_json, report_to_csv

load_dotenv()

st.set_page_config(
    page_title="Career Team AI",
    page_icon="👥",
    layout="wide",
)

# --- DB初期化 ---
init_db()

# --- APIキー & エージェント初期化 ---
api_key = os.getenv("ANTHROPIC_API_KEY")
AGENTS = {
    "coach": CoachAgent(api_key=api_key),
    "mirror": MirrorAgent(api_key=api_key),
    "scout": ScoutAgent(api_key=api_key),
    "strategist": StrategistAgent(api_key=api_key),
}

# エージェントの表示順序
AGENT_ORDER = ["coach", "mirror", "scout", "strategist"]

# --- State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = SessionOrchestrator().to_dict()
if "report" not in st.session_state:
    st.session_state.report = None
if "session_complete" not in st.session_state:
    st.session_state.session_complete = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def get_orchestrator() -> SessionOrchestrator:
    """session_stateからオーケストレーターを復元"""
    return SessionOrchestrator.from_dict(st.session_state.orchestrator)


def save_orchestrator(orch: SessionOrchestrator):
    """オーケストレーターをsession_stateに保存"""
    st.session_state.orchestrator = orch.to_dict()


def get_current_agent(orch: SessionOrchestrator) -> BaseCareerAgent:
    """現在のフェーズの担当エージェントを取得"""
    return AGENTS[orch.get_current_agent_key()]


def persist_session():
    """現在のセッションをDBに保存"""
    if not st.session_state.messages:
        return
    status = "completed" if st.session_state.session_complete else "in_progress"
    save_session(
        session_id=st.session_state.session_id,
        messages=st.session_state.messages,
        orchestrator=st.session_state.orchestrator,
        report=st.session_state.report,
        status=status,
    )


def load_session(session_id: str):
    """DBからセッションを復元"""
    data = get_session(session_id)
    if data is None:
        return
    st.session_state.session_id = data["session_id"]
    st.session_state.messages = data["messages"]
    st.session_state.orchestrator = data["orchestrator"]
    st.session_state.report = data["report"]
    st.session_state.session_complete = (data["status"] == "completed")


def start_new_session():
    """新しいセッションを開始"""
    st.session_state.messages = []
    st.session_state.orchestrator = SessionOrchestrator().to_dict()
    st.session_state.report = None
    st.session_state.session_complete = False
    st.session_state.session_id = str(uuid.uuid4())


# --- サイドバー ---
with st.sidebar:
    st.title("👥 Career Team AI")
    st.caption("あなただけの特別チーム")

    # デモモード表示
    sample_agent = AGENTS["coach"]
    if sample_agent.is_demo_mode:
        st.warning("デモモードで動作中\n\nAPIキーを設定すると本番モードになります")
        with st.expander("APIキー設定方法"):
            st.code("# .envファイルを作成\nANTHROPIC_API_KEY=sk-ant-xxxxx", language="bash")
    else:
        st.success("Claude API 接続済み")

    st.divider()

    # チームメンバー一覧
    st.subheader("チームメンバー")
    orch = get_orchestrator()

    for agent_key in AGENT_ORDER:
        agent = AGENTS[agent_key]
        status = orch.get_agent_status(agent_key)

        if status == "active":
            st.markdown(f"🟢 **{agent.AGENT_ICON} {agent.AGENT_NAME}** — *発言中*")
        elif status == "completed":
            st.markdown(f"✅ {agent.AGENT_ICON} {agent.AGENT_NAME} — 完了")
        else:
            st.markdown(f"⬜ {agent.AGENT_ICON} {agent.AGENT_NAME} — 待機中")

    st.divider()

    # セッション進捗
    current, total = orch.get_progress()
    phase = orch.get_current_phase()
    if st.session_state.session_complete:
        st.progress(1.0, text="セッション完了！")
    else:
        st.progress(current / total, text=f"Phase {current}/{total}: {phase['label']}")
    st.caption(phase["description"])

    # レポート表示＆エクスポート
    if st.session_state.report:
        st.divider()
        st.subheader("📋 キャリアレポート")

        report = st.session_state.report

        if report.get("team_message"):
            st.info(report["team_message"])

        col1, col2 = st.columns(2)
        with col1:
            json_data = report_to_json(report)
            st.download_button(
                label="JSON",
                data=json_data,
                file_name="career_report.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            csv_data = report_to_csv(report)
            st.download_button(
                label="CSV",
                data=csv_data,
                file_name="career_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # --- 過去のセッション ---
    st.divider()
    st.subheader("📂 過去のセッション")

    past_sessions = get_all_sessions()
    if past_sessions:
        for sess in past_sessions:
            # 現在のセッションはスキップ
            if sess["session_id"] == st.session_state.session_id:
                continue

            # 日時の表示整形
            created = sess["created_at"][:16].replace("T", " ")
            status_icon = "✅" if sess["status"] == "completed" else "🔄"
            label = f"{status_icon} {created}"

            if st.button(label, key=f"load_{sess['session_id']}", use_container_width=True):
                # 現在のセッションを保存してから切り替え
                persist_session()
                load_session(sess["session_id"])
                st.rerun()
    else:
        st.caption("まだ履歴はありません")

    # 新しいセッションボタン
    st.divider()
    if st.button("新しいセッション", use_container_width=True):
        persist_session()
        start_new_session()
        st.rerun()


# --- メインチャットエリア ---
st.header("Career Team AI")
st.caption("4人のAIキャリアチームが、あなたの方向性を一緒に見つけます")

# 既存メッセージの表示
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=msg.get("agent_icon", "🤖")):
            agent_name = msg.get("agent_name", "")
            if agent_name:
                st.caption(f"{msg.get('agent_icon', '')} {agent_name}")
            st.markdown(msg["content"])

# 初回挨拶の自動生成
if not st.session_state.messages:
    orch = get_orchestrator()
    agent = get_current_agent(orch)

    with st.chat_message("assistant", avatar=agent.AGENT_ICON):
        st.caption(f"{agent.AGENT_ICON} {agent.AGENT_NAME}")
        greeting = agent.respond([], 0, is_closing=False)
        display_text = BaseCareerAgent.clean_response(greeting)
        st.markdown(display_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": display_text,
        "agent_key": agent.AGENT_KEY,
        "agent_name": agent.AGENT_NAME,
        "agent_icon": agent.AGENT_ICON,
        "raw_content": greeting,
    })

    # 初回はHANDOFFが含まれるので、オーケストレーターを更新
    phase_changed = orch.process_response(greeting, agent)
    save_orchestrator(orch)

    # DBに保存
    persist_session()

    if phase_changed:
        st.rerun()

# チャット入力
if not st.session_state.session_complete:
    if user_input := st.chat_input("思いつくままに、自由にお話しください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 現在のオーケストレーター状態を取得
        orch = get_orchestrator()
        agent_key = orch.get_current_agent_key()
        agent = AGENTS[agent_key]

        # 会話履歴はrole/contentのみ抽出（API用）
        api_messages = [
            {"role": m["role"], "content": m.get("raw_content", m["content"])}
            for m in st.session_state.messages
        ]

        # コンテキスト（前のエージェントからの引き継ぎ）
        context = orch.build_context()

        # Coachのクロージングかどうか判定
        is_closing = (agent_key == "coach" and orch.get_current_phase()["name"] == "action")

        if agent_key == "coach":
            response = agent.respond(api_messages, orch.phase_turn, context, is_closing=is_closing)
        else:
            response = agent.respond(api_messages, orch.phase_turn, context)

        # 表示用テキスト（マーカー除去）
        display_text = BaseCareerAgent.clean_response(response)

        # レポート抽出チェック
        report = agent.extract_insights(response)
        if agent.MARKER == "[CAREER_REPORT]" and report:
            st.session_state.report = report
            st.session_state.session_complete = True

        # メッセージを保存
        st.session_state.messages.append({
            "role": "assistant",
            "content": display_text,
            "agent_key": agent.AGENT_KEY,
            "agent_name": agent.AGENT_NAME,
            "agent_icon": agent.AGENT_ICON,
            "raw_content": response,
        })

        # メッセージ表示
        with st.chat_message("assistant", avatar=agent.AGENT_ICON):
            st.caption(f"{agent.AGENT_ICON} {agent.AGENT_NAME}")
            st.markdown(display_text)

        # オーケストレーターにレスポンスを処理させる
        phase_changed = orch.process_response(response, agent)
        save_orchestrator(orch)

        # DBに保存
        persist_session()

        # フェーズ遷移時はリランして次のエージェント情報を更新
        if phase_changed or st.session_state.session_complete:
            if st.session_state.session_complete:
                st.success("セッション完了！サイドバーでキャリアレポートを確認できます。")
            st.rerun()
else:
    st.info(
        "セッションが完了しました。サイドバーでキャリアレポートを確認し、"
        "JSONまたはCSVでエクスポートできます。\n\n"
        "新しいセッションを開始するには、サイドバーの「新しいセッション」ボタンを押してください。"
    )
