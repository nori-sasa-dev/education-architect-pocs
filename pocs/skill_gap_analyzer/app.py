import json
import os

import streamlit as st
from dotenv import load_dotenv

from agents.gap_agent import GapAgent, JOB_OPTIONS
from utils.chart import build_gap_bar, build_radar_comparison, build_priority_pie

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="スキルギャップ分析ツール",
    page_icon="📊",
    layout="wide",
)

# エージェント初期化
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = GapAgent(api_key=api_key)


def init_session():
    if "gap_result" not in st.session_state:
        st.session_state.gap_result = None
    if "skills" not in st.session_state:
        st.session_state.skills = []
    if "skill_levels" not in st.session_state:
        st.session_state.skill_levels = {}


def parse_skills_from_text(text: str) -> list[str]:
    """テキスト入力からスキルリストを生成する"""
    items = []
    for line in text.replace("、", ",").replace("，", ",").split("\n"):
        for item in line.split(","):
            s = item.strip()
            if s:
                items.append(s)
    return items


def main():
    init_session()

    st.title("📊 スキルギャップ分析ツール")
    st.caption("目標職種に向けた現在のスキルギャップと学習ロードマップを提示します")

    if agent.is_demo_mode:
        st.warning("⚠️ デモモードで動作中です（APIキー未設定）。固定データで表示します。")

    # ─── 入力セクション ──────────────────────────────────────────
    st.subheader("① スキルと目標職種を入力")

    col_input, col_job = st.columns([2, 1])

    with col_input:
        input_tab1, input_tab2 = st.tabs(["テキスト入力", "②マッピングビジュアライザー連携（JSON）"])

        skills = []

        with input_tab1:
            skills_text = st.text_area(
                "現在のスキルをカンマ区切りで入力",
                placeholder="例: Python, コーチング, 教育設計, AI活用, プロジェクト管理",
                height=100,
                key="text_input",
            )
            if skills_text:
                skills = parse_skills_from_text(skills_text)

        with input_tab2:
            st.caption("②スキル×職種マッピングビジュアライザーで生成したJSONを貼り付けてください")
            json_text = st.text_area(
                "JSONを貼り付け",
                placeholder='{"skills": [...], "job_types": [...]}',
                height=120,
                key="json_input",
            )
            if json_text:
                try:
                    mapping_data = json.loads(json_text)
                    extracted = mapping_data.get("skills", [])
                    if extracted:
                        skills = extracted
                        st.success(f"✅ {len(skills)}件のスキルを取得しました")
                    else:
                        st.error("スキルデータが見つかりませんでした。")
                except json.JSONDecodeError:
                    st.error("JSONの解析に失敗しました。")

    with col_job:
        target_job = st.selectbox(
            "目標職種",
            JOB_OPTIONS,
            index=5,  # デフォルト: EdTechプランナー
        )

    # スキルプレビュー
    if skills:
        st.info(f"**分析対象スキル（{len(skills)}件）**: {', '.join(skills)}")

        # 自己評価スライダー（オプション）
        with st.expander("🎚️ スキルの自己評価を設定する（任意）"):
            st.caption("設定しない場合はClaudeが推定します")
            skill_levels = {}
            cols = st.columns(min(3, len(skills)))
            for i, skill in enumerate(skills):
                with cols[i % len(cols)]:
                    skill_levels[skill] = st.slider(
                        skill,
                        min_value=0,
                        max_value=100,
                        value=50,
                        step=5,
                        key=f"slider_{skill}",
                    )
            st.session_state.skill_levels = skill_levels
    else:
        skill_levels = {}

    # 分析ボタン
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        analyze_btn = st.button(
            "🔍 ギャップ分析する",
            type="primary",
            disabled=len(skills) == 0,
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 リセット", use_container_width=True):
            st.session_state.gap_result = None
            st.rerun()

    # 分析実行
    if analyze_btn and skills:
        with st.spinner(f"Claudeが「{target_job}」へのギャップを分析中..."):
            levels = st.session_state.skill_levels if st.session_state.skill_levels else None
            raw_response = agent.analyze(skills, target_job, levels)
            result = agent.extract_gap_analysis(raw_response)
            if result:
                st.session_state.gap_result = result
                st.rerun()
            else:
                st.error("分析結果の解析に失敗しました。もう一度お試しください。")

    # ─── 可視化セクション ─────────────────────────────────────────
    if st.session_state.gap_result:
        result = st.session_state.gap_result

        st.divider()
        st.subheader(f"② ギャップ分析結果 — 目標: {result['target_job']}")

        # サマリーカード
        col_a, col_b, col_c = st.columns(3)
        total_skills = len(result["required_skills"])
        high_priority = sum(1 for s in result["required_skills"] if s["priority"] == "高")
        overall_gap = result.get("overall_gap_score", 0)

        with col_a:
            st.metric("分析スキル数", f"{total_skills} 件")
        with col_b:
            st.metric("優先度「高」ギャップ", f"{high_priority} 件", delta=f"-{high_priority}" if high_priority > 0 else None, delta_color="inverse")
        with col_c:
            readiness = 100 - overall_gap
            st.metric("達成度（推定）", f"{readiness}%", delta=f"あと{overall_gap}%")

        # サマリーテキスト
        st.info(f"💬 {result['summary']}")

        # 強み
        if result.get("strengths"):
            with st.expander("✨ 現在の強み（即戦力になるスキル）"):
                for s in result["strengths"]:
                    st.markdown(f"- {s}")

        st.divider()

        # ギャップバーチャート（全幅）
        st.plotly_chart(build_gap_bar(result), use_container_width=True)

        # レーダーチャート + 円グラフ
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.plotly_chart(build_radar_comparison(result), use_container_width=True)
        with col_right:
            st.plotly_chart(build_priority_pie(result), use_container_width=True)

        st.divider()

        # ─── 学習ロードマップ ──────────────────────────────────────
        st.subheader("③ 学習ロードマップ")

        for phase in result.get("roadmap", []):
            with st.expander(
                f"Phase {phase['phase']}: {phase['title']}　（{phase['duration']}）",
                expanded=(phase["phase"] == 1),
            ):
                st.markdown(f"**マイルストーン**: {phase['milestone']}")
                st.markdown("**アクション:**")
                for action in phase["actions"]:
                    st.markdown(f"- {action}")

        # 詳細テーブル
        with st.expander("📊 詳細スコア表"):
            import pandas as pd
            rows = []
            for s in sorted(result["required_skills"], key=lambda x: x["gap"], reverse=True):
                rows.append({
                    "スキル": s["skill"],
                    "優先度": s["priority"],
                    "現在レベル": s["current_level"],
                    "必要レベル": s["required_level"],
                    "ギャップ": s["gap"],
                    "理由": s["reason"],
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
