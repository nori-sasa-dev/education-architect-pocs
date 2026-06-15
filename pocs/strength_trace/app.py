import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agents.trace_agent import TraceAgent
from utils.viz import TYPE_LABEL, trajectory_chart, trajectory_sparkline, trajectory_table

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "sample_employees"

st.set_page_config(page_title="マイ・ストレングス — 持ち味の発見", page_icon="🧭", layout="centered")


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
        "step": 1,            # 1:シート登録 2:持ち味カード（共有選択込み） 4:面談たたき台＋上長プレビュー
        "selected": None,     # 選択中の社員名
        "employee": None,     # 分析対象の元シート（再分析・保存に使う）
        "traits": None,       # 抽出された持ち味リスト
        "share_flags": {},    # 各持ち味の共有ON/OFF
        "interviews": {},     # 持ち味名 -> {"history": [...], "done": bool, "refined": dict}
        "interview_target": None,  # 深掘り中の持ち味名（Noneなら一覧表示）
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# 初期化対象のキー一覧（「最初に戻る」でリセットする）
STATE_KEYS = ("step", "selected", "employee", "traits", "share_flags", "interviews", "interview_target")


def reset_state():
    st.session_state.step = 1
    st.session_state.selected = None
    st.session_state.employee = None
    st.session_state.traits = None
    st.session_state.share_flags = {}
    st.session_state.interviews = {}
    st.session_state.interview_target = None


init_state()
employees = load_employees()

api_key = os.getenv("ANTHROPIC_API_KEY")
agent = TraceAgent(api_key=api_key)


def run_analysis(employee: dict) -> bool:
    """元シートを分析して持ち味を抽出し、session_state を更新する。成功で True。"""
    with st.spinner("シートを線で読み解いています…"):
        text = agent.analyze(employee)
        result = agent.extract_traits(text)
    if result is None:
        st.error("持ち味の抽出に失敗しました。もう一度お試しください。")
        return False
    st.session_state.employee = employee
    st.session_state.selected = employee["employee_name"]
    st.session_state.traits = result["traits"]
    st.session_state.share_flags = {t["name"]: True for t in result["traits"]}
    st.session_state.interviews = {}
    st.session_state.interview_target = None
    st.session_state.step = 2
    return True


# ---------- AIインタビュー深掘りパネル（A） ----------
def render_interview_panel(trait: dict):
    """1つの持ち味についてAIと短い対話をして、本人の言葉で磨き直す。"""
    tname = trait["name"]
    label, _ = TYPE_LABEL.get(trait["type"], (trait["type"], ""))
    st.header(f"🎤 深掘り：{trait['name']}")
    st.caption(f"{label}　— AIと数問だけ対話して、この持ち味をあなたの言葉にします。")

    state = st.session_state.interviews.setdefault(tname, {"history": [], "done": False, "refined": None})

    # まだ問いがなければ最初の問いを取得
    if not state["history"] and not state["done"]:
        with st.spinner("問いを考えています…"):
            q = agent.interview_turn(trait, [])
        if q:
            state["history"].append({"role": "assistant", "content": q})
        else:
            state["done"] = True

    # これまでの対話を表示
    for m in state["history"]:
        if m["role"] == "assistant":
            st.markdown(f"**🤖 {m['content']}**")
        else:
            st.markdown(f"> 🧑 {m['content']}")

    if not state["done"]:
        with st.form(f"answer_form_{tname}", clear_on_submit=True):
            ans = st.text_area("あなたの答え", placeholder="思いつくままで大丈夫です。")
            sent = st.form_submit_button("答える")
        if sent:
            if ans.strip():
                state["history"].append({"role": "user", "content": ans.strip()})
                with st.spinner("受け取っています…"):
                    q = agent.interview_turn(trait, state["history"])
                if q:
                    state["history"].append({"role": "assistant", "content": q})
                else:
                    state["done"] = True
                st.rerun()
            else:
                st.warning("一言でも入れてみてください。")
    else:
        st.success("対話がひと区切りつきました。ここまでの言葉で持ち味を磨き直せます。")
        if not state.get("refined"):
            if st.button("この対話で持ち味を磨き直す", type="primary"):
                with st.spinner("本人の言葉で磨き直しています…"):
                    refined = agent.refine_trait(trait, state["history"])
                if refined:
                    trait["summary"] = refined.get("summary", trait["summary"])
                    if refined.get("future_action"):
                        trait["future_action"] = refined["future_action"]
                    if refined.get("interview_note"):
                        trait["interview_note"] = refined["interview_note"]
                    trait["deepened"] = True
                    state["refined"] = refined
                    st.rerun()
                else:
                    st.error("磨き直しに失敗しました。もう一度お試しください。")
        else:
            st.markdown("**磨き直した持ち味：**")
            st.write(trait["summary"])
            if trait.get("interview_note"):
                st.info(f"💡 {trait['interview_note']}")
            if trait.get("future_action"):
                st.success(f"🚀 これからの活かし方：{trait['future_action']}")

    st.divider()
    if st.button("← 持ち味の一覧に戻る"):
        st.session_state.interview_target = None
        st.rerun()


# ---------- サイドバー ----------
with st.sidebar:
    st.title("🧭 マイ・ストレングス / My Strengths")
    st.caption("持ち味の発見ツール（POC）")
    if agent.is_demo_mode:
        st.caption("🎭 デモモード")
    else:
        st.caption("✅ APIモード")
    st.divider()
    st.markdown("**あなたの持ち味を、あなたのために。**")
    with st.expander("このツールについて"):
        st.caption(
            "過去のシートを *線* で読み解き、点では見えなかった"
            "あなたらしさに気づくための道具です。"
            "評価ではなく、これからどう活かすかを一緒に考えます。"
        )
    if st.button("最初に戻る"):
        reset_state()
        st.rerun()


# ========== Step 1：目的提示 + 社員選択 ==========
if st.session_state.step == 1:
    st.header("あなたの持ち味を、線で見つける")
    st.caption("一期ごとの「点」が、つながって「線」になる")
    with st.expander("なぜ「線」で見るの？"):
        st.caption(
            "業績・行動・キャリアの各シートは「その時点（点）」の記録です。"
            "でも数期分を時系列でつなぐと、一回きりでは「たまたま」に見えた行動の中に、"
            "あなたらしい持ち味が一本の線として浮かび上がります。"
        )
    st.divider()
    if agent.is_demo_mode:
        st.info("🎭 デモモードです。実シート入力（P1）や深掘り（インタビュー）を試すには `.env` にAPIキーを設定してください。デモではサンプルの固定応答になります。")

    tab_sample, tab_custom = st.tabs(["サンプルで試す", "自分のシートを入力する"])

    # --- サンプルで試す ---
    with tab_sample:
        st.caption("🧪 下のサンプルを「自分のシート」として体験できます。見えるのはあなた自身の持ち味だけ。")
        name = st.radio(
            "サンプル",
            list(employees.keys()),
            format_func=lambda n: f"{n}（{employees[n]['role']}）",
            label_visibility="collapsed",
        )
        with st.expander("登録される各期シートを見る"):
            for p in employees[name]["periods"]:
                st.markdown(f"**{p['period']}**　案件：{p['project']}")
                st.caption(f"行動：{p['behavior_sheet']}")
        if st.button("自分の持ち味を分析する", type="primary"):
            if run_analysis(employees[name]):
                st.rerun()

    # --- 自分のシートを入力する（P1） ---
    with tab_custom:
        st.caption("あなた自身の過去シートを入力すると、AIが点→線で持ち味を読み解きます（実APIモード推奨）。")
        n = st.number_input("入力する期の数", min_value=2, max_value=6, value=4, step=1)
        with st.form("custom_input_form"):
            c1, c2 = st.columns(2)
            in_name = c1.text_input("お名前", placeholder="例：山田 太郎")
            in_role = c2.text_input("役割・立場", placeholder="例：エンジニア（入社5年目）")
            periods_input = []
            for i in range(int(n)):
                st.markdown(f"**第{i + 1}期**")
                pc1, pc2 = st.columns(2)
                p_period = pc1.text_input("時期", key=f"p_period_{i}", placeholder="例：2024上期")
                p_project = pc2.text_input("案件・担当", key=f"p_project_{i}", placeholder="例：◯◯システム改修")
                p_perf = st.text_area("業績目標シート", key=f"p_perf_{i}", placeholder="目標と成果")
                p_beh = st.text_area("行動目標シート", key=f"p_beh_{i}", placeholder="どんな行動をとったか（具体的に）")
                p_career = st.text_area("キャリアデザインシート", key=f"p_career_{i}", placeholder="どうなりたいか")
                periods_input.append({
                    "period": p_period, "project": p_project,
                    "performance_sheet": p_perf, "behavior_sheet": p_beh, "career_sheet": p_career,
                })
            custom_submitted = st.form_submit_button("自分の持ち味を分析する", type="primary")
        if custom_submitted:
            filled = [p for p in periods_input if p["behavior_sheet"].strip()]
            if not in_name.strip():
                st.warning("お名前を入れてください。")
            elif len(filled) < 2:
                st.warning("点→線で読むため、行動目標シートを2期以上入力してください。")
            else:
                employee = {
                    "employee_name": in_name.strip(),
                    "role": in_role.strip(),
                    "periods": filled,
                }
                if run_analysis(employee):
                    st.rerun()

    # --- 続きから：前回保存した分析を読み込む（DBを持たず、本人の手元のファイルで継続） ---
    st.divider()
    with st.expander("📂 前回の続きから（保存した分析を読み込む）"):
        st.caption("前にダウンロードした分析ファイル（.json）を読み込むと、続きから再開できます。半年後に期を足すときにも。")
        uploaded = st.file_uploader("分析ファイル（JSON）", type="json", label_visibility="collapsed")
        if uploaded is not None:
            try:
                saved = json.load(uploaded)
                traits = saved["traits"]
                st.session_state.selected = saved.get("selected", "あなた")
                st.session_state.employee = saved.get("employee")  # 旧形式は None（再分析不可）
                st.session_state.traits = traits
                st.session_state.share_flags = saved.get(
                    "share_flags", {t["name"]: True for t in traits}
                )
                st.session_state.interviews = {}
                st.session_state.interview_target = None
                st.session_state.step = 2
                st.rerun()
            except (json.JSONDecodeError, KeyError, TypeError):
                st.error("ファイルを読み込めませんでした。正しい分析ファイルかご確認ください。")


# ========== Step 2：持ち味カード表示 + 本人編集 ==========
elif st.session_state.step == 2:
    name = st.session_state.selected

    # 深掘り中なら、その持ち味のインタビューパネルだけを表示
    _target = st.session_state.interview_target
    _target_trait = next((t for t in st.session_state.traits if t["name"] == _target), None) if _target else None
    if _target_trait is not None:
        render_interview_panel(_target_trait)
        st.stop()

    st.header("あなたの持ち味")
    st.caption("線として確かに通っている持ち味です。納得できないものは外せます。")
    st.caption("グラフの横＝いつ（左が古い）／縦＝どれくらい発揮したか（薄・中・濃）")

    for i, trait in enumerate(st.session_state.traits):
        label, desc = TYPE_LABEL.get(trait["type"], (trait["type"], ""))
        with st.container(border=True):
            badge = ""
            if trait.get("self_added"):
                badge += "　✍️ 自分で追加"
            if trait.get("deepened"):
                badge += "　✨ 深掘り済み"
            st.markdown(f"#### {label}　{trait['name']}{badge}")
            st.caption(desc)
            # AI抽出の持ち味だけが軌跡グラフを持つ。手動追加分はグラフを省く
            if trait.get("trajectory"):
                st.altair_chart(
                    trajectory_chart(trait["trajectory"], trait["type"]),
                    use_container_width=True,
                )
            st.write(trait["summary"])
            if trait.get("interview_note"):
                st.info(f"💡 {trait['interview_note']}")
            if trait.get("future_action"):
                st.success(f"🚀 これからの活かし方：{trait['future_action']}")
            if trait.get("trajectory") or trait.get("environment"):
                with st.expander("どの出来事でそう言えるのか見る"):
                    if trait.get("trajectory"):
                        st.markdown(trajectory_table(trait["trajectory"]))
                    if trait.get("environment"):
                        st.markdown(f"**発揮される環境**：{trait['environment']}")
            # AIインタビューで本人の言葉に深める
            if st.button("🎤 この持ち味を深掘りする", key=f"dig_{i}"):
                st.session_state.interview_target = trait["name"]
                st.rerun()
            # 所有権：本人が共有するかを決める
            st.session_state.share_flags[trait["name"]] = st.checkbox(
                "上長と共有する",
                value=st.session_state.share_flags.get(trait["name"], True),
                key=f"share_{i}",
            )

    # --- 本人所有：AIが見落とした持ち味を自分で足す ---
    with st.expander("＋ 自分で持ち味を足す"):
        st.caption("AIが見落とした、あなただけが知っている持ち味も、ここに加えられます。")
        type_options = {label: key for key, (label, _) in TYPE_LABEL.items()}
        # st.form でまとめて送信。入力途中の再実行でフォームが閉じるのを防ぐ
        with st.form("add_trait_form", clear_on_submit=True):
            new_name = st.text_input("持ち味の名前", placeholder="例：人の話を最後まで聴ける")
            new_type_label = st.radio("どんな出方をする強み？", list(type_options.keys()), horizontal=True)
            new_summary = st.text_area("どんな持ち味か、一言で", placeholder="どんな場面で、どう発揮されますか？")
            submitted = st.form_submit_button("この持ち味を加える")
        if submitted:
            if new_name.strip():
                st.session_state.traits.append({
                    "name": new_name.strip(),
                    "type": type_options[new_type_label],
                    "summary": new_summary.strip(),
                    "self_added": True,
                })
                st.session_state.share_flags[new_name.strip()] = True
                st.rerun()
            else:
                st.warning("持ち味の名前を入れてください。")

    # --- P3本体：新しい期を足して、軌跡を伸ばす（全期を線で再分析） ---
    with st.expander("＋ 新しい期を追加して軌跡を伸ばす"):
        if st.session_state.employee is None:
            st.caption("この分析には元シートが含まれていないため、期の追加・再分析はできません（旧形式の保存ファイルなど）。新しく分析し直すと利用できます。")
        else:
            st.caption("半年後など、新しい期のシートを足すと、これまでの全期を“線”として読み直します。")
            with st.form("add_period_form", clear_on_submit=True):
                ap1, ap2 = st.columns(2)
                ap_period = ap1.text_input("時期", placeholder="例：2026上期")
                ap_project = ap2.text_input("案件・担当", placeholder="例：新規プロジェクト")
                ap_perf = st.text_area("業績目標シート", placeholder="目標と成果")
                ap_beh = st.text_area("行動目標シート", placeholder="どんな行動をとったか（具体的に）")
                ap_career = st.text_area("キャリアデザインシート", placeholder="どうなりたいか")
                add_period_submitted = st.form_submit_button("この期を足して再分析する", type="primary")
            if add_period_submitted:
                if ap_beh.strip():
                    employee = dict(st.session_state.employee)
                    employee["periods"] = list(employee["periods"]) + [{
                        "period": ap_period.strip(), "project": ap_project.strip(),
                        "performance_sheet": ap_perf.strip(), "behavior_sheet": ap_beh.strip(),
                        "career_sheet": ap_career.strip(),
                    }]
                    if run_analysis(employee):
                        st.rerun()
                else:
                    st.warning("行動目標シートを入力してください。")

    # --- 本人所有：分析を手元に保存し、半年後に続きから再開できる（DBは持たない） ---
    save_payload = json.dumps(
        {
            "selected": name,
            "employee": st.session_state.employee,  # 元シート（再分析・期追加に使う）
            "traits": st.session_state.traits,
            "share_flags": st.session_state.share_flags,
        },
        ensure_ascii=False,
        indent=2,
    )
    st.download_button(
        "💾 この分析を保存する（あとで続きから再開できます）",
        data=save_payload,
        file_name=f"{name}_持ち味分析.json",
        mime="application/json",
    )
    st.caption("ファイルはあなたの手元に残ります。次回その読み込みで続きから。")

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
    c1, c2 = st.columns(2)
    c1.metric("あなたの持ち味", f"{len(all_traits)} 個")
    c2.metric("上長に共有", f"{len(shared)} 個")
    st.caption("共有を選んだ分だけが上長に渡ります。残りはあなたの手元に。")

    st.subheader("👤 上長に見えるのは、これだけ")
    if not shared:
        st.warning("共有する持ち味が選ばれていません。前の画面で少なくとも1つ選んでください。")
    else:
        with st.container(border=True):
            for t in shared:
                label, _ = TYPE_LABEL.get(t["type"], (t["type"], ""))
                badge = "　✍️ 自分で追加" if t.get("self_added") else ""
                st.markdown(f"##### {label}　{t['name']}{badge}")
                if t.get("trajectory"):
                    st.altair_chart(
                        trajectory_chart(t["trajectory"], t["type"]),
                        use_container_width=True,
                    )
                st.caption(t["summary"])
                if t.get("interview_note"):
                    st.markdown(f"- 💡 {t['interview_note']}")
                if t.get("environment"):
                    st.markdown(f"- **発揮される環境**：{t['environment']}")
                if t.get("future_action"):
                    st.success(f"🚀 これからの活かし方：{t['future_action']}")
                if t.get("talking_point"):
                    st.info(f"💬 一緒に話したい問い：{t['talking_point']}")

    if hidden:
        hidden_names = "、".join(f"「{t['name']}」" for t in hidden)
        st.caption(f"🔒 上長には共有していない持ち味：{hidden_names}（あなたの手元にのみ残ります）")

    # --- ダウンロード（共有分のみ） ---
    if shared:
        md_lines = [f"# {name} さんが共有した持ち味", ""]
        for t in shared:
            label, _ = TYPE_LABEL.get(t["type"], (t["type"], ""))
            md_lines.append(f"## {t['name']}（{label}）")
            if t.get("trajectory"):
                md_lines.append(f"- 軌跡：{trajectory_sparkline(t['trajectory'])}")
            md_lines.append(f"- {t['summary']}")
            if t.get("interview_note"):
                md_lines.append(f"- 深掘りメモ：{t['interview_note']}")
            if t.get("environment"):
                md_lines.append(f"- 発揮される環境：{t['environment']}")
            if t.get("future_action"):
                md_lines.append(f"- これからの活かし方：{t['future_action']}")
            if t.get("talking_point"):
                md_lines.append(f"- 一緒に話したい問い：{t['talking_point']}")
            md_lines.append("")
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
