import json
import os

import streamlit as st
from dotenv import load_dotenv

from agents.mapping_agent import MappingAgent
from utils.chart import build_heatmap, build_overall_bar, build_radar

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="スキル × 職種マッピングビジュアライザー",
    page_icon="🗺️",
    layout="wide",
)

# エージェント初期化
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = MappingAgent(api_key=api_key)


def init_session():
    """セッション状態の初期化"""
    if "mapping_result" not in st.session_state:
        st.session_state.mapping_result = None
    if "skills_input" not in st.session_state:
        st.session_state.skills_input = ""
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None


def parse_skills_from_text(text: str) -> list[str]:
    """テキスト入力からスキルリストを生成する（カンマ・改行区切り対応）"""
    items = []
    for line in text.replace("、", ",").replace("，", ",").split("\n"):
        for item in line.split(","):
            s = item.strip()
            if s:
                items.append(s)
    return items


def main():
    init_session()

    st.title("🗺️ スキル × 職種マッピングビジュアライザー")
    st.caption("あなたのスキルが各職種にどれだけマッチするかを可視化します")

    if agent.is_demo_mode:
        st.warning("⚠️ デモモードで動作中です（APIキー未設定）。固定データで表示します。")

    # ─── 入力セクション ──────────────────────────────────────────
    st.subheader("① スキルを入力")

    input_tab1, input_tab2 = st.tabs(["テキスト入力", "①キャリア探索AI連携（JSON貼り付け）"])

    skills = []

    with input_tab1:
        skills_text = st.text_area(
            "スキルをカンマ区切りまたは1行1スキルで入力してください",
            placeholder="例: Python, プロジェクト管理, コーチング, AI活用, 教育設計",
            height=120,
            key="text_input",
        )
        if skills_text:
            skills = parse_skills_from_text(skills_text)

    with input_tab2:
        st.caption("①キャリア探索AIで生成したJSONをそのまま貼り付けてください")
        json_text = st.text_area(
            "JSONを貼り付け",
            placeholder='{"skills": {"technical": [...], "human": [...], "tacit": [...]}, ...}',
            height=150,
            key="json_input",
        )
        if json_text:
            try:
                discovery_data = json.loads(json_text)
                extracted = agent.extract_skills_from_discovery(discovery_data)
                if extracted:
                    skills = extracted
                    st.success(f"✅ {len(skills)}件のスキルを抽出しました: {', '.join(skills)}")
                else:
                    st.error("スキルデータが見つかりませんでした。JSONの形式を確認してください。")
            except json.JSONDecodeError:
                st.error("JSONの解析に失敗しました。形式を確認してください。")

    # スキルプレビュー
    if skills:
        st.info(f"**分析対象スキル（{len(skills)}件）**: {', '.join(skills)}")

    # 分析ボタン
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        analyze_btn = st.button(
            "🔍 分析する",
            type="primary",
            disabled=len(skills) == 0,
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 リセット", use_container_width=True):
            st.session_state.mapping_result = None
            st.session_state.selected_job = None
            st.rerun()

    # 分析実行
    if analyze_btn and skills:
        with st.spinner("Claudeがスキルを分析中..."):
            raw_response = agent.analyze(skills)
            result = agent.extract_mapping(raw_response)
            if result:
                # スキルリストを入力値で上書き（API側がスキル名を変える場合があるため）
                result["skills"] = skills
                # scoresのキーも入力スキルに合わせて正規化
                for job in result["job_types"]:
                    normalized_scores = {}
                    for skill in skills:
                        # APIが返したスコアを優先、なければ0
                        normalized_scores[skill] = job["scores"].get(skill, 0)
                    job["scores"] = normalized_scores
                st.session_state.mapping_result = result
                st.session_state.selected_job = result["job_types"][0]["name"]
                st.rerun()
            else:
                st.error("分析結果の解析に失敗しました。もう一度お試しください。")

    # ─── 可視化セクション ─────────────────────────────────────────
    if st.session_state.mapping_result:
        result = st.session_state.mapping_result
        job_types = result["job_types"]
        skills_list = result["skills"]

        st.divider()
        st.subheader("② 分析結果")

        # 上段：ヒートマップ（全体俯瞰）
        st.plotly_chart(build_heatmap(result), use_container_width=True)

        st.divider()

        # 下段：左に棒グラフ / 右にレーダーチャート
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.plotly_chart(build_overall_bar(result), use_container_width=True)

        with col_right:
            job_names = [j["name"] for j in job_types]
            selected = st.selectbox(
                "職種を選んでレーダーチャートを表示",
                job_names,
                index=0,
                key="job_selector",
            )
            selected_job_data = next(j for j in job_types if j["name"] == selected)
            st.plotly_chart(build_radar(selected_job_data, skills_list), use_container_width=True)
            # 職種コメント表示
            comment = selected_job_data.get("comment", "")
            if comment:
                st.caption(f"💬 {comment}")

        # ─── 詳細テーブル ─────────────────────────────────────────
        with st.expander("📊 詳細スコア表を見る"):
            import pandas as pd
            rows = []
            for j in sorted(job_types, key=lambda x: x["overall_match"], reverse=True):
                row = {
                    "職種": j["name"],
                    "カテゴリ": j.get("category", ""),
                    "総合スコア": j["overall_match"],
                }
                for s in skills_list:
                    row[s] = j["scores"].get(s, 0)
                rows.append(row)
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
