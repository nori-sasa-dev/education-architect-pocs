import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agents.trace_agent import TraceAgent
from utils.viz import TYPE_LABEL, trajectory_sparkline, trajectory_table

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "sample_employees"

st.set_page_config(page_title="軌跡 — 持ち味の発見", page_icon="🧭", layout="wide")


# ---------- データ読み込み ----------
def load_employees() -> dict:
    """サンプル社員データを全件読み込む。"""
    employees = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        employees[data["employee_name"]] = data
    return employees


# ---------- セッション状態の初期化 ----------
def init_state():
    defaults = {
        "step": 1,            # 1:選択 2:分析結果 3:共有選択 4:面談たたき台
        "selected": None,     # 選択中の社員名
        "traits": None,       # 抽出された持ち味リスト
        "share_flags": {},    # 各持ち味の共有ON/OFF
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
employees = load_employees()

api_key = os.getenv("ANTHROPIC_API_KEY")
agent = TraceAgent(api_key=api_key)


# ---------- サイドバー ----------
with st.sidebar:
    st.title("🧭 軌跡 / Trace")
    st.caption("持ち味の発見ツール（POC）")
    if agent.is_demo_mode:
        st.info("🎭 デモモード\nAPIキー未設定のため、佐々木さんの固定サンプルを表示します。")
    else:
        st.success("✅ APIモード")
    st.divider()
    st.markdown(
        "**これは査定ツールではありません。**\n\n"
        "過去のシートを *線* で読み解き、点では見えなかった"
        "あなたの持ち味を見つけるための道具です。"
    )
    if st.button("最初に戻る"):
        for k in ("step", "selected", "traits", "share_flags"):
            st.session_state[k] = 1 if k == "step" else (None if k != "share_flags" else {})
        st.rerun()


# ========== Step 1：目的提示 + 社員選択 ==========
if st.session_state.step == 1:
    st.header("あなたの持ち味を、線で見つける")
    st.markdown(
        "業績・行動・キャリアデザインの各シートは「その時点（点）」を写したものです。\n\n"
        "でも、**数期分を時系列でつなぐと**、一回きりでは「たまたま」に見えた行動の中に、"
        "あなたらしい持ち味が一本の線として浮かび上がってきます。"
    )
    st.divider()
    st.subheader("誰の軌跡を見ますか？")
    name = st.radio(
        "社員を選択",
        list(employees.keys()),
        format_func=lambda n: f"{n}（{employees[n]['role']}）",
        label_visibility="collapsed",
    )
    with st.expander("この人の各期シートを見る"):
        for p in employees[name]["periods"]:
            st.markdown(f"**{p['period']}**　案件：{p['project']}")
            st.caption(f"行動：{p['behavior_sheet']}")
    if st.button("この人の持ち味を分析する", type="primary"):
        st.session_state.selected = name
        with st.spinner("4期分のシートを線で読み解いています…"):
            text = agent.analyze(employees[name])
            result = agent.extract_traits(text)
        if result is None:
            st.error("持ち味の抽出に失敗しました。もう一度お試しください。")
        else:
            st.session_state.traits = result["traits"]
            st.session_state.share_flags = {t["name"]: True for t in result["traits"]}
            st.session_state.step = 2
            st.rerun()


# ========== Step 2：持ち味カード表示 + 本人編集 ==========
elif st.session_state.step == 2:
    name = st.session_state.selected
    st.header(f"{name} さんの持ち味")
    st.caption("点では見えにくい、けれど線として確かに通っている持ち味です。納得できないものは外せます。")

    for i, trait in enumerate(st.session_state.traits):
        label, desc = TYPE_LABEL.get(trait["type"], (trait["type"], ""))
        with st.container(border=True):
            top = st.columns([4, 1])
            with top[0]:
                st.markdown(f"### {trait['name']}")
                st.markdown(f"**{label}**　— {desc}")
            with top[1]:
                st.markdown(f"#### {trajectory_sparkline(trait['trajectory'])}")
            st.write(trait["summary"])
            with st.expander("この持ち味が育ってきた軌跡を見る"):
                st.markdown(trajectory_table(trait["trajectory"]))
                st.markdown(f"**発揮される環境**：{trait['environment']}")
            st.info(f"💬 面談での問い：{trait['talking_point']}")
            # 所有権：本人が共有するかを決める
            st.session_state.share_flags[trait["name"]] = st.checkbox(
                "この持ち味を上長と共有する",
                value=st.session_state.share_flags.get(trait["name"], True),
                key=f"share_{i}",
            )

    st.divider()
    cols = st.columns(2)
    if cols[0].button("← 社員選択に戻る"):
        st.session_state.step = 1
        st.rerun()
    if cols[1].button("面談用のたたき台を作る →", type="primary"):
        st.session_state.step = 4
        st.rerun()


# ========== Step 4：面談用たたき台 ==========
elif st.session_state.step == 4:
    name = st.session_state.selected
    shared = [t for t in st.session_state.traits if st.session_state.share_flags.get(t["name"])]
    st.header("面談用のたたき台")
    st.caption("これは評価シートではありません。上長との対話の出発点として使ってください。")

    if not shared:
        st.warning("共有する持ち味が選ばれていません。前の画面で選び直してください。")
    else:
        md_lines = [f"# {name} さんの持ち味（本人が共有を選んだもの）", ""]
        for t in shared:
            label, _ = TYPE_LABEL.get(t["type"], (t["type"], ""))
            st.subheader(f"{t['name']}")
            st.markdown(f"**{label}**　{trajectory_sparkline(t['trajectory'])}")
            st.write(t["summary"])
            st.markdown(f"- **発揮される環境**：{t['environment']}")
            st.markdown(f"- **一緒に話したい問い**：{t['talking_point']}")
            st.divider()
            md_lines += [
                f"## {t['name']}（{label}）",
                f"- 軌跡：{trajectory_sparkline(t['trajectory'])}",
                f"- {t['summary']}",
                f"- 発揮される環境：{t['environment']}",
                f"- 一緒に話したい問い：{t['talking_point']}",
                "",
            ]
        st.download_button(
            "このたたき台をダウンロード（Markdown）",
            data="\n".join(md_lines),
            file_name=f"{name}_持ち味たたき台.md",
            mime="text/markdown",
        )

    if st.button("← 持ち味カードに戻る"):
        st.session_state.step = 2
        st.rerun()
