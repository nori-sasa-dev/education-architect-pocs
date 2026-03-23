import os
import streamlit as st
from dotenv import load_dotenv

from core.video_processor import extract_frames, frame_to_bytes
from core.pose_analyzer import analyze_pose, angles_to_text
from agents.reflection_agent import ReflectionAgent
from database.db import init_db, save_session, get_all_sessions, delete_session

load_dotenv()

# DB初期化
init_db()

# エージェント初期化
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = ReflectionAgent(api_key=api_key)

# ページ設定
st.set_page_config(page_title="InnerLens", page_icon="🎾", layout="wide")

st.title("🎾 InnerLens")
st.caption("テニスの自己観察ジャーナル — インナーゲーム式")

if agent.is_demo_mode:
    st.info("デモモード：APIキー未設定のため固定の問いを返します。")

# ─── タブ ─────────────────────────────────────────────
tab_analyze, tab_journal = st.tabs(["今日の練習を振り返る", "ジャーナル"])


# ─── セッション状態リセット関数 ───────────────────────
def reset_session():
    for key in ["frames", "selected_frame", "video_name", "angles",
                "chat_history", "api_history", "turn", "saved",
                "chat_started", "skeleton_bytes"]:
        if key in st.session_state:
            del st.session_state[key]


# ─── 振り返りタブ ──────────────────────────────────────
with tab_analyze:

    # セッション状態の初期化
    for key, default in {
        "frames": None,
        "selected_frame": 0,
        "video_name": "",
        "angles": None,
        "skeleton_bytes": None,
        "chat_history": [],
        "api_history": [],
        "turn": 0,
        "saved": False,
        "chat_started": False,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # ── クリアボタン（常に表示）──
    if st.session_state.frames is not None:
        if st.button("クリアして最初からやり直す"):
            reset_session()
            st.rerun()

    # ── STEP 1: 動画アップロード ──
    st.subheader("STEP 1 ｜ 動画をアップロード")
    video_file = st.file_uploader(
        "練習動画（mp4, mov, avi）をアップロードしてください",
        type=["mp4", "mov", "avi"],
    )

    if video_file:
        if st.session_state.video_name != video_file.name:
            with st.spinner("動画を読み込んでいます..."):
                frames, fps = extract_frames(video_file)
            st.session_state.frames = frames
            st.session_state.video_name = video_file.name
            st.session_state.chat_history = []
            st.session_state.api_history = []
            st.session_state.turn = 0
            st.session_state.saved = False
            st.session_state.chat_started = False
            st.session_state.angles = None
            st.session_state.skeleton_bytes = None
            st.session_state.selected_frame = 0
            st.success(f"{len(frames)} フレーム読み込み完了（{fps:.0f}fps）")

    # ── STEP 2: フレーム選択 ──
    if st.session_state.frames:
        st.subheader("STEP 2 ｜ 注目したい瞬間を選ぶ")
        frames = st.session_state.frames

        frame_idx = st.slider(
            "フレームを動かして「この瞬間！」と思う場所を選んでください",
            min_value=0,
            max_value=len(frames) - 1,
            value=st.session_state.selected_frame,
            key="frame_slider",
        )
        st.session_state.selected_frame = frame_idx

        selected = frames[frame_idx]
        skeleton_frame, angles = analyze_pose(selected)

        col1, col2 = st.columns(2)
        with col1:
            st.caption("元の画像")
            st.image(selected, use_container_width=True)
        with col2:
            st.caption("姿勢推定")
            st.image(skeleton_frame, use_container_width=True)

        if angles is None:
            st.warning("このフレームでは姿勢が検出できませんでした。別のフレームを試してください。")
        else:
            st.session_state.angles = angles
            st.session_state.skeleton_bytes = frame_to_bytes(skeleton_frame)

        # ── STEP 3: 対話開始 ──
        st.subheader("STEP 3 ｜ コーチと振り返る")

        if not st.session_state.chat_started:
            if st.button("このフレームで振り返りを始める", type="primary", disabled=(angles is None)):
                with st.spinner("考えています..."):
                    pose_text = angles_to_text(st.session_state.angles)
                    first_q = agent.open_conversation(pose_text)
                st.session_state.chat_history = [{"role": "assistant", "content": first_q}]
                st.session_state.api_history = [{"role": "assistant", "content": first_q}]
                st.session_state.turn = 1
                st.session_state.chat_started = True
                st.session_state.saved = False
                st.rerun()

        # ── STEP 4: チャット対話 ──
        if st.session_state.chat_started:
            st.divider()
            st.subheader("STEP 4 ｜ 対話")

            for msg in st.session_state.chat_history:
                with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                    st.write(msg["content"])

            if not st.session_state.saved:
                user_input = st.chat_input("感じたこと・気づいたことを書いてください")

                if user_input:
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.api_history.append({"role": "user", "content": user_input})

                    next_q = agent.continue_conversation(
                        st.session_state.api_history, st.session_state.turn
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": next_q})
                    st.session_state.api_history.append({"role": "assistant", "content": next_q})
                    st.session_state.turn += 1
                    st.rerun()

                # 2往復以上で記録ボタンを表示
                if st.session_state.turn >= 2:
                    st.divider()
                    summary = st.text_area(
                        "今日の一番の気づきを一言で（記録用）",
                        placeholder="例：膝が伸びていることに気づいていなかった",
                        height=80,
                        key="summary_input",
                    )
                    if st.button("記録する", type="primary"):
                        if summary.strip():
                            save_session(
                                video_name=st.session_state.video_name,
                                frame_index=st.session_state.selected_frame,
                                conversation=st.session_state.chat_history,
                                summary=summary.strip(),
                                image_bytes=st.session_state.skeleton_bytes,
                            )
                            st.session_state.saved = True
                            st.success("記録しました。ジャーナルタブで確認できます。")
                            st.rerun()
                        else:
                            st.warning("一言だけでも書いてから記録してください。")
            else:
                st.success("記録済み。ジャーナルタブで確認できます。")


# ─── ジャーナルタブ ────────────────────────────────────
with tab_journal:
    st.subheader("振り返りの記録")

    sessions = get_all_sessions()

    if not sessions:
        st.info("まだ記録がありません。「今日の練習を振り返る」タブから始めてください。")
    else:
        for s in sessions:
            with st.expander(f"📅 {s['created_at']}　{s['video_name']}"):

                # 姿勢推定画像
                if s.get("image_path") and os.path.exists(s["image_path"]):
                    st.image(s["image_path"], caption="姿勢推定", width=300)

                # 対話履歴
                st.markdown("**対話**")
                for msg in s["conversation"]:
                    role_label = "コーチ" if msg["role"] == "assistant" else "あなた"
                    st.markdown(f"**{role_label}**: {msg['content']}")

                # 気づき
                st.markdown("**今日の気づき**")
                st.write(s["summary"])

                # 削除ボタン
                st.divider()
                if st.button("この記録を削除", key=f"delete_{s['id']}", type="secondary"):
                    delete_session(s["id"])
                    st.success("削除しました。")
                    st.rerun()
