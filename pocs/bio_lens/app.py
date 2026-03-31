import os
import sys

# Streamlit Cloud でのモジュール解決: app.py のディレクトリを明示的にパスへ追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

from core.video_processor import extract_frames
from core.pose_analyzer import analyze_pose, angles_to_text, IDEAL_RANGES
from agents.biomechanics_agent import BiomechanicsAgent

load_dotenv()

st.set_page_config(page_title="BioLens", page_icon="🔬")

# モバイル最適化CSS
st.markdown("""
<style>
/* ボタンをタップしやすいサイズに */
.stButton button { width: 100%; min-height: 3rem; font-size: 1.05rem; }
/* ファイルアップローダーの余白 */
.stFileUploader { padding-bottom: 0.5rem; }
/* スライダーの余白を広げてタップしやすく */
.stSlider { padding: 0.5rem 0 1rem; }
/* メトリクスを中央寄せ */
[data-testid="metric-container"] { text-align: center; }
</style>
""", unsafe_allow_html=True)

api_key = os.getenv("ANTHROPIC_API_KEY")
agent = BiomechanicsAgent(api_key=api_key)

# --- ヘッダー ---
st.title("🔬 BioLens")
st.caption("テニス姿勢のバイオメカニクス分析 — InnerLensの外側版")

if agent.is_demo_mode:
    st.info("デモモード：APIキー未設定のため固定のレポートを返します。")

# --- セッション状態の初期化 ---
for key, default in {
    "frames": None,
    "video_name": "",
    "selected_frame": 0,
    "angles": None,
    "scores": None,
    "report": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def reset():
    for k in ["frames", "angles", "scores", "report"]:
        st.session_state[k] = None
    st.session_state["video_name"] = ""
    st.session_state["selected_frame"] = 0


# --- クリアボタン ---
if st.session_state.frames is not None:
    if st.button("クリアして最初からやり直す"):
        reset()
        st.rerun()

# ─── STEP 1: 動画アップロード ───────────────────────────
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
        st.session_state.selected_frame = 0
        st.session_state.angles = None
        st.session_state.scores = None
        st.session_state.report = None
        st.success(f"{len(frames)} フレーム読み込み完了（{fps:.0f} fps）")

# ─── STEP 2: フレーム選択 ────────────────────────────────
if st.session_state.frames:
    st.subheader("STEP 2 ｜ 分析したいフレームを選ぶ")
    frames = st.session_state.frames

    frame_idx = st.slider(
        "フレームを動かして「この瞬間！」と思う場所を選んでください",
        min_value=0,
        max_value=len(frames) - 1,
        value=st.session_state.selected_frame,
    )
    st.session_state.selected_frame = frame_idx
    selected = frames[frame_idx]

    annotated, angles, scores = analyze_pose(selected)

    img_tab1, img_tab2 = st.tabs(["姿勢推定 + 角度", "元の画像"])
    with img_tab1:
        st.image(annotated, use_container_width=True)
    with img_tab2:
        st.image(selected, use_container_width=True)

    if angles is None:
        st.warning("このフレームでは姿勢が検出できませんでした。別のフレームを試してください。")
    else:
        st.session_state.angles = angles
        st.session_state.scores = scores

        # ─── STEP 3: 分析実行 ──────────────────────────────────
        st.subheader("STEP 3 ｜ バイオメカニクス分析")

        if st.button("このフレームを分析する", type="primary"):
            with st.spinner("バイオメカニクス分析中..."):
                pose_text = angles_to_text(angles, scores)
                report = agent.analyze(pose_text)
            st.session_state.report = report
            st.rerun()

# ─── レポート表示 ─────────────────────────────────────────
if st.session_state.report and st.session_state.scores:
    report = st.session_state.report
    scores = st.session_state.scores

    st.divider()

    # 総合スコア
    overall = round(sum(scores.values()) / len(scores))
    score_color = "🟢" if overall >= 80 else "🟡" if overall >= 60 else "🔴"

    st.metric("総合スコア", f"{score_color} {overall} / 100")
    st.info(report.get("overall_comment", ""))

    st.divider()

    # 部位別スコア：レーダーチャート → スコア詳細（縦積み）
    st.subheader("部位別スコア")
    names = list(scores.keys())
    values = list(scores.values())

    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=names + [names[0]],
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.25)",
        line=dict(color="rgb(99, 110, 250)", width=2),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

    for name, score in scores.items():
        icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        actual = st.session_state.angles.get(name, "-")
        unit = "" if name == "体の傾き" else "°"
        st.write(f"{icon} **{name}**　{actual}{unit}　→　{score}/100")

    st.divider()

    # 優先改善ポイント
    st.subheader("優先改善ポイント")
    for i, fix in enumerate(report.get("priority_fixes", []), 1):
        with st.expander(f"#{i}　{fix['part']}　— {fix['issue']}", expanded=False):
            st.markdown(f"**なぜ問題か：** {fix['reason']}")
            st.markdown(f"**改善ドリル：** {fix['drill']}")

    st.divider()

    # 運動連鎖コメント（縦積み）
    st.subheader("運動連鎖（Kinetic Chain）")
    st.write(report.get("kinetic_chain_comment", ""))

    st.subheader("良い点")
    for point in report.get("positive_points", []):
        st.success(point)
