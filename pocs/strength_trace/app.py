import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agents.trace_agent import TraceAgent
from utils.viz import TYPE_LABEL, trajectory_sparkline, trajectory_table

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "sample_employees"

st.set_page_config(page_title="軌跡 — 持ち味の発見", page_icon="🧭", layout="centered")


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
        st.info("🎭 デモモード\nAPIキー未設定のため、選んだサンプルの固定結果を表示します。")
    else:
        st.success("✅ APIモード")
    st.divider()
    st.markdown(
        "**あなたの持ち味を、あなたのために見つける道具です。**\n\n"
        "過去のシートを *線* で読み解き、点では見えなかった"
        "あなたらしさに気づき、これからどう活かすかを一緒に考えるために使います。"
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
    st.subheader("あなたのシートを登録する")
    st.markdown(
        "本来は、ここに**ご自身の4期分のシート**（業績・行動・キャリアデザイン）を登録します。\n\n"
        "見えるのは**あなた自身の持ち味だけ**です。他の人のデータを覗くことはできません。"
    )
    st.info("🧪 これはPOCです。下のサンプルを「自分のシート」として読み込んで体験できます。")
    name = st.radio(
        "サンプルで試す",
        list(employees.keys()),
        format_func=lambda n: f"{n}（{employees[n]['role']}）として体験する",
    )
    with st.expander("登録される各期シートを見る"):
        for p in employees[name]["periods"]:
            st.markdown(f"**{p['period']}**　案件：{p['project']}")
            st.caption(f"行動：{p['behavior_sheet']}")
    if st.button("自分の持ち味を分析する", type="primary"):
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
    st.header("あなたの持ち味")
    st.caption("点では見えにくい、けれど線として確かに通っている、あなたの持ち味です。納得できないものは外せます。")
    st.markdown(
        "軌跡の濃淡：**●** 濃い　**◐** 中くらい　**○** 薄い　"
        "（左が古い期 → 右が新しい期）"
    )

    for i, trait in enumerate(st.session_state.traits):
        label, desc = TYPE_LABEL.get(trait["type"], (trait["type"], ""))
        with st.container(border=True):
            st.markdown(f"### {trait['name']}")
            st.markdown(f"**{label}**　— {desc}")
            st.markdown(f"**軌跡**：{trajectory_sparkline(trait['trajectory'])}")
            st.write(trait["summary"])
            with st.expander("この持ち味が育ってきた軌跡を見る"):
                st.markdown(trajectory_table(trait["trajectory"]))
                st.markdown(f"**発揮される環境**：{trait['environment']}")
            # 所有権：本人が共有するかを決める
            st.session_state.share_flags[trait["name"]] = st.checkbox(
                "この持ち味を上長と共有する",
                value=st.session_state.share_flags.get(trait["name"], True),
                key=f"share_{i}",
            )

    st.divider()
    cols = st.columns(2)
    if cols[0].button("← シート登録に戻る"):
        st.session_state.step = 1
        st.rerun()
    if cols[1].button("共有範囲を決めてたたき台を作る →", type="primary"):
        st.session_state.step = 4
        st.rerun()


# ========== Step 4：面談たたき台 + 上長プレビュー ==========
elif st.session_state.step == 4:
    name = st.session_state.selected
    all_traits = st.session_state.traits
    shared = [t for t in all_traits if st.session_state.share_flags.get(t["name"])]
    hidden = [t for t in all_traits if not st.session_state.share_flags.get(t["name"])]

    st.header("面談の準備ができました")

    # --- 上長プレビュー：共有した分だけが渡る非対称性を体験させる ---
    st.subheader("👤 上長に見えるのは、これだけです")
    st.caption(
        f"{len(all_traits)}個の持ち味のうち、あなたが共有を選んだ "
        f"**{len(shared)}個** だけが上長に渡ります。"
        "残りはあなたの手元にのみ残り、上長には見えません。"
    )

    if not shared:
        st.warning("共有する持ち味が選ばれていません。前の画面で少なくとも1つ選んでください。")
    else:
        with st.container(border=True):
            st.markdown(f"**{name} さんが共有した持ち味**")
            for t in shared:
                label, _ = TYPE_LABEL.get(t["type"], (t["type"], ""))
                st.markdown(f"##### {t['name']}")
                st.markdown(f"{label}　{trajectory_sparkline(t['trajectory'])}")
                st.write(t["summary"])
                st.markdown(f"- **発揮される環境**：{t['environment']}")
                st.info(f"💬 一緒に話したい問い：{t['talking_point']}")

    if hidden:
        hidden_names = "、".join(f"「{t['name']}」" for t in hidden)
        st.caption(f"🔒 上長には共有していない持ち味：{hidden_names}（あなたの手元にのみ残ります）")

    # --- ダウンロード（共有分のみ） ---
    if shared:
        md_lines = [f"# {name} さんが共有した持ち味", ""]
        for t in shared:
            label, _ = TYPE_LABEL.get(t["type"], (t["type"], ""))
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

    st.divider()
    if st.button("← 共有範囲を選び直す"):
        st.session_state.step = 2
        st.rerun()
