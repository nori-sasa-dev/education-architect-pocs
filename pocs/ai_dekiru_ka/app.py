import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
from services.diagnosis_agent import DiagnosisAgent, DEMO_TASKS_INPUT
from services.file_extractor import extract_text
from services.team_db import init_db, generate_team_code, save_diagnosis, get_team_data, team_code_exists, update_task_status

load_dotenv()

st.set_page_config(page_title="AIできる課？", page_icon="🤖", layout="wide")

# ─── 定数 ────────────────────────────────────────────────

FREQUENCIES = ["毎日", "週次", "月次", "不定期"]

CATEGORY_INFO = {
    "AI_AUTOMATE": ("🤖 完全自動化可能", "#d62728", "定型・反復・データ処理中心。人間の介入なしにAIが完全実行できます"),
    "AI_AUGMENT":  ("🤝 AI増強",          "#1f77b4", "AIがドラフト・分析・要約を行い、最終判断は人間が担います"),
    "HUMAN_ONLY":  ("👤 人間必須",         "#7f7f7f", "感情・信頼・戦略的判断が核心。AIは補助役にとどまります"),
}
PRIORITY_LABEL = {"HIGH": "🔴 高", "MEDIUM": "🟡 中", "LOW": "🟢 低"}
STATUS_OPTIONS = ["未着手", "進行中", "完了"]
STATUS_EMOJI   = {"未着手": "📋", "進行中": "🔄", "完了": "✅"}

SUGGESTED_QUESTIONS = {
    "AI_AUTOMATE": ["どこから始めればいいですか？", "どのくらいのPythonスキルが必要ですか？",
                    "初期コストはどれくらいかかりますか？", "社内のセキュリティで注意することは？"],
    "AI_AUGMENT":  ["AIと人間の役割分担はどう設計しますか？", "どのくらいの期間で導入できますか？",
                    "チームへの展開はどう進めますか？", "失敗しやすいポイントはどこですか？"],
    "HUMAN_ONLY":  ["周辺業務をAIでサポートする方法は？", "記録・振り返りを自動化できますか？",
                    "この業務の効率を上げる工夫はありますか？", "チームのコミュニケーションをAIで補助するには？"],
}

# ─── ヘルパー関数 ─────────────────────────────────────────

def _default_task():
    return {"name": "", "description": "", "monthly_count": 4, "minutes_per_task": 30, "frequency": "週次"}


def _scroll_to_top():
    st.html("""
<script>
(function() {
    function scrollUp() {
        var doc = window.parent.document;
        ["[data-testid='stMain']",
         "[data-testid='stAppViewContainer'] > section",
         ".main"].forEach(function(sel) {
            var el = doc.querySelector(sel);
            if (el) el.scrollTop = 0;
        });
        doc.documentElement.scrollTop = 0;
        doc.body.scrollTop = 0;
        window.parent.scrollTo(0, 0);
    }
    scrollUp();
    setTimeout(scrollUp, 80);
    setTimeout(scrollUp, 300);
})();
</script>
""", unsafe_allow_javascript=True)


def _go_to_step(step: int, extra_state: dict = None):
    """ステップ遷移の共通関数。スクロールフラグをセットしてrerun。"""
    st.session_state.step = step
    st.session_state._needs_scroll_top = True
    if extra_state:
        for k, v in extra_state.items():
            st.session_state[k] = v
    st.rerun()


def _check_scroll():
    """各ステップ先頭で呼ぶ。遷移直後のときだけスクロール実行。"""
    if st.session_state.get("_needs_scroll_top", False):
        st.session_state._needs_scroll_top = False
        _scroll_to_top()


def _build_report(tasks: list, roadmap: dict) -> str:
    lines = ["# AIできる課？ 診断レポート\n"]
    total_h = sum(t["monthly_hours"] for t in tasks)
    total_r = sum(t["monthly_reduction_hours"] for t in tasks)
    lines.append(f"月間工数合計: {total_h:.1f}時間 / 削減見込み: {total_r:.1f}時間\n")
    lines.append("## 診断結果\n")
    for cat_key, (cat_label, _, _) in CATEGORY_INFO.items():
        cat_tasks = [t for t in tasks if t["category"] == cat_key]
        if not cat_tasks:
            continue
        lines.append(f"### {cat_label}\n")
        for t in cat_tasks:
            lines.append(f"**{t['name']}** — 削減率{t['time_reduction_pct']}%（月{t['monthly_reduction_hours']:.1f}h削減）")
            lines.append(f"- 根拠: {t.get('reduction_reason', '—')}")
            lines.append(f"- 推奨ツール: {t.get('suggested_tool', '—')}\n")
    lines.append("## ロードマップ\n")
    if msg := roadmap.get("summary_message"):
        lines.append(f"> {msg}\n")
    for phase in roadmap.get("phases", []):
        lines.append(f"### {phase['name']}（{phase['period']}）\n")
        for action in phase.get("actions", []):
            lines.append(f"- **{action['task_name']}**: {action['action']}（{action.get('tool', '—')}）")
        lines.append("")
    if human_tasks := roadmap.get("human_tasks"):
        lines.append("## 人間必須タスク（AI化しない領域）\n")
        for t in human_tasks:
            lines.append(f"- {t}")
    return "\n".join(lines)


def _colored_section_header(label: str, desc: str, color: str):
    st.markdown(
        f'<div style="border-left:5px solid {color}; padding:6px 0 4px 12px; margin:16px 0 4px 0;">'
        f'<span style="font-size:1.15em; font-weight:700; color:{color};">{label}</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(desc)


# ─── 起動処理 ─────────────────────────────────────────────

init_db()

try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", None) or os.getenv("ANTHROPIC_API_KEY")
except Exception:
    api_key = os.getenv("ANTHROPIC_API_KEY")
is_demo_mode = not bool(api_key)
agent = DiagnosisAgent(api_key=api_key)

# ─── セッション状態 ────────────────────────────────────────

for k, v in [
    ("step", 1),
    ("task_list", [_default_task()]),
    ("diagnosis", None),
    ("roadmap", None),
    ("selected_task", None),
    ("task_guide", None),
    ("chat_history", []),
    ("pending_question", None),
    ("_needs_scroll_top", False),
    # チームモード
    ("team_code", ""),
    ("user_name", ""),
    ("department", ""),
    ("team_saved", False),
    ("dashboard_team_code", ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── サイドバー ────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 AIできる課？")
    st.caption("あなたの業務のAI化可能性を診断")
    if is_demo_mode:
        st.warning("⚠️ デモモード")
    else:
        st.success("✅ Claude API 接続済み")
    st.divider()

    step = st.session_state.step

    # 実装管理ボタン（Step 6 以外の全ステップで常に表示。診断前は disabled）
    if step != 6:
        has_diag = bool(st.session_state.diagnosis)
        if st.button("📋 実装管理", use_container_width=True, disabled=not has_diag):
            _go_to_step(6)
        st.divider()

    if step == 4:
        if st.button("← 診断結果に戻る", use_container_width=True):
            _go_to_step(2, {"selected_task": None, "task_guide": None,
                            "chat_history": [], "pending_question": None})

    elif step == 5:
        if st.button("← 戻る", use_container_width=True):
            back = 2 if st.session_state.diagnosis else 1
            _go_to_step(back)

    elif step == 6:
        if st.button("← 診断結果に戻る", use_container_width=True):
            _go_to_step(2)

    else:
        # ステップ進捗
        labels = ["① 業務入力", "② 診断結果", "③ ロードマップ"]
        for i, label in enumerate(labels, 1):
            if i < step:
                st.markdown(f"✅ {label}")
            elif i == step:
                st.markdown(f"**▶ {label}**")
            else:
                st.markdown(f"○ {label}")

        st.divider()

        # チームダッシュボードへのアクセス
        if st.session_state.team_code:
            st.caption(f"チームコード: **{st.session_state.team_code}**")
            if st.button("📊 チームダッシュボード", use_container_width=True):
                st.session_state.dashboard_team_code = st.session_state.team_code
                _go_to_step(5)
        else:
            with st.expander("📊 ダッシュボードを参照"):
                view_code = st.text_input("チームコードを入力", max_chars=10, key="sidebar_view_code")
                if st.button("参照する", use_container_width=True):
                    if view_code.strip():
                        st.session_state.dashboard_team_code = view_code.upper().strip()
                        _go_to_step(5)

        st.divider()
        if st.button("最初からやり直す", use_container_width=True):
            _go_to_step(1, {
                "task_list": [_default_task()],
                "diagnosis": None, "roadmap": None,
                "selected_task": None, "task_guide": None,
                "chat_history": [], "pending_question": None,
                "team_saved": False,
                # team_code / user_name / department は保持
            })

# ════════════════════════════════════════════════════════════
# Step 1: 業務入力
# ════════════════════════════════════════════════════════════

if st.session_state.step == 1:
    _check_scroll()

    st.title("🤖 AIできる課？")
    st.markdown(
        "あなたの日常業務を入力するだけで、AIが **「完全自動化」「AI増強」「人間必須」** に分類し、"
        "月間の削減時間と具体的な導入ロードマップを生成します。"
    )

    # ── ファイルアップロード ──
    with st.expander("📎 資料ファイルから業務を追加（PDF / Excel / PowerPoint）"):
        uploaded = st.file_uploader("業務マニュアル・業務一覧などを読み込めます",
                                    type=["pdf", "xlsx", "xls", "pptx", "ppt"])
        if uploaded:
            with st.spinner("ファイルを読み込み中..."):
                extracted = extract_text(uploaded)
            if extracted:
                st.text_area("抽出テキスト（参考）", value=extracted[:2000], height=120, disabled=True)
                if st.button("この内容を新しいカードに追加"):
                    t = _default_task()
                    t["name"] = uploaded.name
                    t["description"] = extracted[:500]
                    st.session_state.task_list.append(t)
                    st.rerun()
            else:
                st.warning("テキストを抽出できませんでした。")

    # ── チームモード ──
    with st.expander("👥 チームで診断する（任意）— 複数人の結果をまとめてダッシュボードで確認"):
        st.markdown("同じチームコードを使うと、管理者がチーム全体のAI化余地を一覧で把握できます。")
        col_code, col_gen = st.columns([3, 1])
        with col_code:
            new_code = st.text_input("チームコード", value=st.session_state.team_code,
                                     placeholder="例: ABC123 / 新規の場合は→のボタンで生成",
                                     max_chars=10, key="team_code_input")
            st.session_state.team_code = new_code.upper().strip()
        with col_gen:
            st.markdown("&nbsp;", unsafe_allow_html=True)  # vertical align
            if st.button("自動生成", use_container_width=True):
                st.session_state.team_code = generate_team_code()
                st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            st.session_state.user_name = st.text_input(
                "あなたの名前（チームモード時必須）", value=st.session_state.user_name)
        with c2:
            st.session_state.department = st.text_input(
                "部署（任意）", value=st.session_state.department)

        if st.session_state.team_code:
            st.info(f"チームコード「**{st.session_state.team_code}**」で参加します。"
                    "診断後にこのコードをメンバーに共有してください。")

    st.divider()

    # ── カード入力 ──
    col_label, col_demo = st.columns([3, 1])
    with col_label:
        st.markdown("**業務カード入力** — 1枚 = 1業務")
        if is_demo_mode:
            st.caption("⚠️ デモモード: 診断カテゴリはサンプル固定。工数・削減時間は入力した件数・分数から計算します")
    with col_demo:
        if is_demo_mode and st.button("📋 デモデータを読み込む", use_container_width=True):
            st.session_state.task_list = [
                {k: t[k] for k in ["name", "description", "monthly_count", "minutes_per_task", "frequency"]}
                for t in DEMO_TASKS_INPUT
            ]
            st.rerun()

    to_delete = None
    for i, task in enumerate(st.session_state.task_list):
        with st.container(border=True):
            col_title, col_del = st.columns([7, 1])
            with col_title:
                st.markdown(f"**業務 #{i + 1}**")
            with col_del:
                if st.button("削除", key=f"del_{i}"):
                    to_delete = i
            task["name"] = st.text_input("業務名 *", value=task["name"], key=f"name_{i}",
                                          placeholder="例: 週次レポートの作成")
            task["description"] = st.text_area("業務の詳細説明（任意）", value=task["description"],
                                                key=f"desc_{i}", height=68,
                                                placeholder="例: ExcelでKPIを集計しWord報告書を作成してメール送付する")
            c1, c2, c3 = st.columns(3)
            with c1:
                task["monthly_count"] = st.number_input("月間件数（回）（目安）", min_value=1, max_value=9999,
                                                          value=task["monthly_count"], key=f"cnt_{i}")
            with c2:
                task["minutes_per_task"] = st.number_input("1件あたり（分）（目安）", min_value=1, max_value=9999,
                                                             value=task["minutes_per_task"], key=f"min_{i}")
            with c3:
                task["frequency"] = st.selectbox("頻度", FREQUENCIES,
                                                   index=FREQUENCIES.index(task.get("frequency", "週次")),
                                                   key=f"freq_{i}")
            monthly_h = task["monthly_count"] * task["minutes_per_task"] / 60
            st.caption(f"月間工数: 約 **{monthly_h:.1f} 時間**")

    if to_delete is not None:
        st.session_state.task_list.pop(to_delete)
        st.rerun()

    col_add, col_go, _ = st.columns([2, 2, 3])
    with col_add:
        if st.button("＋ 業務を追加する", use_container_width=True):
            st.session_state.task_list.append(_default_task())
            st.rerun()
    with col_go:
        if st.button("診断する →", type="primary", use_container_width=True):
            valid = [t for t in st.session_state.task_list if t["name"].strip()]
            if not valid:
                st.error("業務名を1件以上入力してください。")
            elif st.session_state.team_code and not st.session_state.user_name:
                st.error("チームモードの場合はあなたの名前を入力してください。")
            else:
                try:
                    with st.spinner("AIが分析中..."):
                        result = agent.diagnose(valid)
                    _go_to_step(2, {"diagnosis": result, "team_saved": False})
                except Exception as e:
                    st.error(f"診断に失敗しました: {e}")

# ════════════════════════════════════════════════════════════
# Step 2: 診断結果
# ════════════════════════════════════════════════════════════

elif st.session_state.step == 2:
    _check_scroll()

    tasks = st.session_state.diagnosis
    if not tasks:
        st.error("診断結果がありません。最初からやり直してください。")
        st.stop()

    st.title("🔍 診断結果")

    # チームモード: 自動保存
    if (st.session_state.team_code and st.session_state.user_name
            and not st.session_state.team_saved):
        with st.spinner("チームに診断結果を保存中..."):
            save_diagnosis(st.session_state.team_code, st.session_state.user_name,
                           st.session_state.department, tasks)
        st.session_state.team_saved = True

    # チームモード: 共有案内
    if st.session_state.team_code and st.session_state.team_saved:
        with st.container(border=True):
            col_msg, col_btn = st.columns([4, 1])
            with col_msg:
                st.markdown(f"✅ チームコード **`{st.session_state.team_code}`** に保存しました。"
                            "このコードをメンバーに共有すると、全員の診断をまとめて確認できます。")
            with col_btn:
                if st.button("📊 ダッシュボード", use_container_width=True):
                    st.session_state.dashboard_team_code = st.session_state.team_code
                    _go_to_step(5)

    with st.expander("ℹ️ 分類基準について（境界線の説明）"):
        for _, (label, color, desc) in CATEGORY_INFO.items():
            st.markdown(f'<span style="color:{color}; font-weight:700;">{label}</span>: {desc}',
                        unsafe_allow_html=True)

    counts = {k: sum(1 for t in tasks if t["category"] == k) for k in CATEGORY_INFO}
    total_monthly_h = sum(t["monthly_hours"] for t in tasks)
    total_reduction_h = sum(t["monthly_reduction_hours"] for t in tasks)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総業務数", f"{len(tasks)} 件")
    c2.metric("🤖 完全自動化", f"{counts['AI_AUTOMATE']} 件")
    c3.metric("🤝 AI増強", f"{counts['AI_AUGMENT']} 件")
    c4.metric("👤 人間必須", f"{counts['HUMAN_ONLY']} 件")

    if total_reduction_h > 0:
        pct = total_reduction_h / total_monthly_h * 100 if total_monthly_h else 0
        st.info(f"⏱️ AIを活用することで **月{total_reduction_h:.1f}時間**（全体の{pct:.0f}%）の削減が見込めます")

    st.divider()

    for cat_key, (cat_label, color, cat_desc) in CATEGORY_INFO.items():
        cat_tasks = [t for t in tasks if t["category"] == cat_key]
        if not cat_tasks:
            continue
        _colored_section_header(cat_label, cat_desc, color)
        for task in cat_tasks:
            with st.container(border=True):
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    priority = PRIORITY_LABEL.get(task.get("priority", "LOW"), "—")
                    current_status = task.get("status", "未着手")
                    status_badge = f"{STATUS_EMOJI[current_status]} {current_status}"
                    st.markdown(
                        f"{priority}　**{task['name']}**　　"
                        f'<span style="font-size:0.85em; color:#888;">{status_badge}</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"削減率 {task['time_reduction_pct']}%（月{task['monthly_reduction_hours']:.1f}h削減）"
                               f"　　推奨: {task.get('suggested_tool', '—')}")
                with col_btn:
                    if st.button("📖 進め方", key=f"guide_{task['name']}", use_container_width=True):
                        _go_to_step(4, {"selected_task": task, "task_guide": None,
                                        "chat_history": [], "pending_question": None})
                with st.expander("削減率の根拠・詳細"):
                    ca, cb = st.columns(2)
                    with ca:
                        st.markdown(f"**月間工数**: {task['monthly_hours']:.1f}h"
                                    f"（{task['monthly_count']}件 × {task['minutes_per_task']}分）")
                    with cb:
                        st.markdown(f"**削減率の根拠**: {task.get('reduction_reason', '—')}")
        st.markdown("")

    st.divider()
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("ロードマップを見る →", type="primary", use_container_width=True):
            if st.session_state.roadmap:
                _go_to_step(3)
            else:
                try:
                    with st.spinner("ロードマップを生成中..."):
                        roadmap = agent.generate_roadmap(tasks)
                    _go_to_step(3, {"roadmap": roadmap})
                except Exception as e:
                    st.error(f"ロードマップの生成に失敗しました: {e}")

# ════════════════════════════════════════════════════════════
# Step 3: ロードマップ
# ════════════════════════════════════════════════════════════

elif st.session_state.step == 3:
    _check_scroll()
    st.title("🗺️ あなたの AI 活用ロードマップ")

    roadmap = st.session_state.roadmap
    diagnosis = st.session_state.diagnosis
    if not roadmap:
        st.warning("ロードマップデータがありません。")
        st.stop()

    if msg := roadmap.get("summary_message"):
        st.info(msg)

    phases = roadmap.get("phases", [])
    chart_rows = []
    phase_colors = {"今すぐ着手": "#d62728", "次のステップ": "#1f77b4", "中長期": "#2ca02c"}

    for phase in phases:
        for action in phase.get("actions", []):
            chart_rows.append({
                "フェーズ": phase["name"], "期間": phase["period"],
                "業務": action["task_name"], "アクション": action["action"],
                "ツール": action.get("tool", "—"),
                "開始月": phase["month_start"], "終了月": phase["month_end"],
            })

    if chart_rows:
        df = pd.DataFrame(chart_rows)
        df["開始日"] = pd.Timestamp("2026-06-01") + pd.to_timedelta(df["開始月"] * 30, unit="D")
        df["終了日"] = pd.Timestamp("2026-06-01") + pd.to_timedelta(df["終了月"] * 30, unit="D")
        fig = px.timeline(df, x_start="開始日", x_end="終了日", y="業務",
                          color="フェーズ", text="アクション", color_discrete_map=phase_colors,
                          title="AI活用ロードマップ（フェーズ別）",
                          hover_data={"ツール": True, "期間": True, "アクション": True,
                                      "開始日": False, "終了日": False})
        fig.update_yaxes(autorange="reversed")
        fig.update_traces(textposition="inside", insidetextanchor="start")
        fig.update_layout(height=max(300, len(chart_rows) * 45 + 80))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("バーにカーソルを合わせると詳細が表示されます")

    if human_tasks := roadmap.get("human_tasks"):
        st.divider()
        st.subheader("👤 大切にしてほしいこと")
        st.markdown("以下はAIに代替させず、あなた自身が担い続ける領域です。AIが時間を創ることで、ここに集中できます。")
        for t in human_tasks:
            st.markdown(f"- {t}")

    st.divider()
    col_dl, col_back, _ = st.columns([2, 2, 3])
    with col_dl:
        report_md = _build_report(diagnosis, roadmap)
        st.download_button("📄 Markdownでダウンロード", data=report_md,
                           file_name="ai_dekiru_ka_report.md", mime="text/markdown",
                           use_container_width=True)
    with col_back:
        if st.button("← 診断結果に戻る", use_container_width=True):
            _go_to_step(2)

# ════════════════════════════════════════════════════════════
# Step 4: 具体的な進め方 + チャット
# ════════════════════════════════════════════════════════════

elif st.session_state.step == 4:
    _check_scroll()
    task = st.session_state.selected_task
    if not task:
        st.error("業務が選択されていません。")
        st.stop()

    cat_label, cat_color, _ = CATEGORY_INFO.get(task["category"], ("—", "#888", ""))
    st.markdown(f'<span style="color:{cat_color}; font-weight:700; font-size:0.95em;">{cat_label}</span>',
                unsafe_allow_html=True)
    st.title(f"📖 {task['name']}")
    st.caption(f"月間工数 {task['monthly_hours']:.1f}h　→　削減見込み {task['monthly_reduction_hours']:.1f}h/月"
               f"（削減率 {task['time_reduction_pct']}%）")
    st.divider()

    if st.session_state.task_guide is None:
        with st.spinner("実装ガイドを生成中..."):
            guide = agent.generate_guide(task)
        st.session_state.task_guide = guide
    st.markdown(st.session_state.task_guide)

    col_back, _ = st.columns([2, 5])
    with col_back:
        if st.button("← 診断結果に戻る", key="back_from_guide", use_container_width=True):
            _go_to_step(2, {"selected_task": None, "task_guide": None,
                            "chat_history": [], "pending_question": None})

    st.divider()
    st.subheader("💬 何でも聞いてください")
    st.caption("この業務のAI化について、実装方法・スキル・コスト・リスクなど自由に質問できます")

    if st.session_state.pending_question:
        prompt = st.session_state.pending_question
        st.session_state.pending_question = None
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        reply = agent.chat(task, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if not st.session_state.chat_history:
        st.markdown("**よくある質問:**")
        questions = SUGGESTED_QUESTIONS.get(task.get("category", "AI_AUGMENT"), [])
        cols = st.columns(2)
        for i, q in enumerate(questions):
            with cols[i % 2]:
                if st.button(q, key=f"sq_{i}", use_container_width=True):
                    st.session_state.pending_question = q
                    st.rerun()
        st.markdown("")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("質問を入力してください"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("考え中..."):
                reply = agent.chat(task, st.session_state.chat_history)
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ════════════════════════════════════════════════════════════
# Step 5: チームダッシュボード
# ════════════════════════════════════════════════════════════

elif st.session_state.step == 5:
    _check_scroll()

    team_code = st.session_state.dashboard_team_code

    if not team_code:
        st.warning("チームコードが指定されていません。サイドバーからコードを入力してください。")
        st.stop()

    data = get_team_data(team_code)

    # ── ヘッダー ──
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.title(f"📊 チームダッシュボード")
        st.caption(f"チームコード: **{team_code}**")
    with col_refresh:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("🔄 更新", use_container_width=True):
            st.rerun()

    # ── データなし ──
    if not data:
        st.warning(f"チームコード「{team_code}」のデータがまだありません。")
        st.markdown("メンバーに以下のコードを共有し、各自が診断を完了してください。")
        st.code(team_code, language=None)
        st.stop()

    df = pd.DataFrame(data)
    members = sorted(df["user_name"].unique().tolist())
    total_reduction = df["monthly_reduction_hours"].sum()
    total_monthly = df["monthly_hours"].sum()
    ai_rate = (df[df["category"] != "HUMAN_ONLY"]["monthly_hours"].sum() / total_monthly * 100
               if total_monthly > 0 else 0)

    # ── メトリクス ──
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("参加人数", f"{len(members)} 人")
    m2.metric("総業務数", f"{len(df)} 件")
    m3.metric("月間削減見込み合計", f"{total_reduction:.1f} h")
    m4.metric("AI化対象率", f"{ai_rate:.0f} %")

    st.divider()

    # ── チャート行 ──
    col_pie, col_bar = st.columns(2)

    with col_pie:
        cat_label_map = {k: v[0] for k, v in CATEGORY_INFO.items()}
        cat_color_map = {v[0]: v[1] for v in CATEGORY_INFO.values()}
        pie_df = (df.groupby("category", as_index=False)
                    .agg(件数=("task_name", "count"))
                    .assign(カテゴリ=lambda d: d["category"].map(cat_label_map)))
        fig_pie = px.pie(pie_df, values="件数", names="カテゴリ",
                         color="カテゴリ", color_discrete_map=cat_color_map,
                         title="全業務のカテゴリ分布", hole=0.4)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        top_df = (df[["task_name", "category", "monthly_reduction_hours", "user_name"]]
                  .sort_values("monthly_reduction_hours", ascending=True)
                  .tail(10)
                  .assign(カテゴリ=lambda d: d["category"].map(cat_label_map)))
        fig_bar = px.bar(top_df, x="monthly_reduction_hours", y="task_name",
                         color="カテゴリ", color_discrete_map=cat_color_map,
                         orientation="h",
                         title="削減余地トップ10（月間削減時間）",
                         labels={"monthly_reduction_hours": "削減見込み（h/月）",
                                 "task_name": "業務名", "user_name": "担当者"},
                         hover_data={"user_name": True})
        fig_bar.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── 優先着手リスト ──
    st.subheader("🎯 優先着手リスト")
    st.caption("削減余地が大きく、完全自動化できる業務。最初に取り組むべき候補です。")
    priority_cols = ["user_name", "department", "task_name", "monthly_hours",
                     "monthly_reduction_hours", "time_reduction_pct", "suggested_tool"]
    priority_rename = {
        "user_name": "担当者", "department": "部署", "task_name": "業務名",
        "monthly_hours": "月間工数(h)", "monthly_reduction_hours": "削減見込み(h)",
        "time_reduction_pct": "削減率(%)", "suggested_tool": "推奨ツール",
    }
    if "status" in df.columns:
        priority_cols.append("status")
        priority_rename["status"] = "ステータス"
    priority_df = (df[(df["category"] == "AI_AUTOMATE") & (df["priority"] == "HIGH")]
                   .sort_values("monthly_reduction_hours", ascending=False)
                   [priority_cols]
                   .rename(columns=priority_rename))
    if priority_df.empty:
        st.info("HIGH優先度の完全自動化業務はありません。")
    else:
        st.dataframe(priority_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── メンバー別サマリー ──
    st.subheader("👥 メンバー別サマリー")
    member_df = (df.groupby(["user_name", "department"], as_index=False)
                   .agg(業務数=("task_name", "count"),
                        月間工数=("monthly_hours", "sum"),
                        削減見込み=("monthly_reduction_hours", "sum"))
                   .sort_values("削減見込み", ascending=False)
                   .rename(columns={"user_name": "名前", "department": "部署"})
                   .assign(削減率=lambda d: (d["削減見込み"] / d["月間工数"] * 100).round(0).astype(int).astype(str) + "%",
                           月間工数=lambda d: d["月間工数"].round(1),
                           削減見込み=lambda d: d["削減見込み"].round(1)))
    st.dataframe(member_df, use_container_width=True, hide_index=True)

    # ── 実装ステータス ──
    if "status" in df.columns:
        st.divider()
        st.subheader("📋 実装ステータス（AI化対象業務）")
        ai_df = df[df["category"] != "HUMAN_ONLY"]
        sc1, sc2, sc3 = st.columns(3)
        for col, status in zip([sc1, sc2, sc3], STATUS_OPTIONS):
            count = int((ai_df["status"] == status).sum())
            hours = float(ai_df.loc[ai_df["status"] == status, "monthly_reduction_hours"].sum())
            col.metric(
                f"{STATUS_EMOJI[status]} {status}",
                f"{count} 件",
                f"削減見込み {hours:.1f} h",
            )

    # ── 部署別集計（複数部署がある場合のみ）──
    if df["department"].nunique() > 1:
        st.divider()
        st.subheader("🏢 部署別 削減余地")
        dept_df = (df[df["department"] != ""]
                   .groupby("department", as_index=False)
                   .agg(削減見込み=("monthly_reduction_hours", "sum"),
                        業務数=("task_name", "count"))
                   .sort_values("削減見込み", ascending=False)
                   .rename(columns={"department": "部署"}))
        fig_dept = px.bar(dept_df, x="部署", y="削減見込み",
                          title="部署別 月間削減見込み（h）",
                          color="削減見込み", color_continuous_scale="Reds")
        fig_dept.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig_dept, use_container_width=True)

# ════════════════════════════════════════════════════════════
# Step 6: 実装管理
# ════════════════════════════════════════════════════════════

elif st.session_state.step == 6:
    _check_scroll()

    tasks = st.session_state.diagnosis
    if not tasks:
        st.error("診断結果がありません。最初からやり直してください。")
        st.stop()

    ai_tasks   = [t for t in tasks if t["category"] != "HUMAN_ONLY"]
    human_tasks = [t for t in tasks if t["category"] == "HUMAN_ONLY"]

    total           = len(ai_tasks)
    done_count      = sum(1 for t in ai_tasks if t.get("status", "未着手") == "完了")
    in_prog_count   = sum(1 for t in ai_tasks if t.get("status", "未着手") == "進行中")
    not_start_count = total - done_count - in_prog_count

    st.title("📋 実装管理")
    st.caption("AI化・自動化の実装進捗を記録します。ステータスを変更すると自動保存されます。")

    # ── 進捗サマリー ──
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("対象業務", f"{total} 件")
    m2.metric(f"{STATUS_EMOJI['未着手']} 未着手", f"{not_start_count} 件")
    m3.metric(f"{STATUS_EMOJI['進行中']} 進行中", f"{in_prog_count} 件")
    m4.metric(f"{STATUS_EMOJI['完了']} 完了", f"{done_count} 件")

    if total > 0:
        pct = done_count / total
        st.progress(pct, text=f"完了率 {pct * 100:.0f}%（{done_count}/{total} 件）")

    st.divider()

    # ── タスクカードの描画関数 ──
    def _render_status_cards(task_list, tab_key: str):
        if not task_list:
            st.caption("該当する業務はありません")
            return
        for task in task_list:
            cat_label, cat_color, _ = CATEGORY_INFO.get(task["category"], ("", "#888", ""))
            with st.container(border=True):
                col_info, col_guide = st.columns([5, 1])
                with col_info:
                    priority = PRIORITY_LABEL.get(task.get("priority", "LOW"), "—")
                    st.markdown(
                        f'<div style="border-left:4px solid {cat_color}; padding-left:10px; margin-bottom:4px;">'
                        f'{priority}　<b>{task["name"]}</b><br>'
                        f'<span style="font-size:0.82em; color:{cat_color};">{cat_label}</span>'
                        f'　<span style="font-size:0.82em; color:#888;">削減見込み {task["monthly_reduction_hours"]:.1f}h/月</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_guide:
                    if st.button("📖", key=f"{tab_key}_guide_{task['name']}", use_container_width=True,
                                 help="実装ガイドを見る"):
                        _go_to_step(4, {"selected_task": task, "task_guide": None,
                                        "chat_history": [], "pending_question": None})

                current = task.get("status", "未着手")
                new_status = st.selectbox(
                    "ステータス",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(current),
                    key=f"{tab_key}_status_{task['name']}",
                    label_visibility="collapsed",
                )
                if new_status != current:
                    task["status"] = new_status
                    if st.session_state.team_code and st.session_state.user_name:
                        update_task_status(
                            st.session_state.team_code, st.session_state.user_name,
                            task["name"], new_status,
                        )
                    st.rerun()

    # ── タブ ──
    tab_labels = [
        f"全て（{total}）",
        f"{STATUS_EMOJI['未着手']} 未着手（{not_start_count}）",
        f"{STATUS_EMOJI['進行中']} 進行中（{in_prog_count}）",
        f"{STATUS_EMOJI['完了']} 完了（{done_count}）",
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_status_cards(ai_tasks, "all")
    with tabs[1]:
        _render_status_cards([t for t in ai_tasks if t.get("status", "未着手") == "未着手"], "ns")
    with tabs[2]:
        _render_status_cards([t for t in ai_tasks if t.get("status", "未着手") == "進行中"], "ip")
    with tabs[3]:
        _render_status_cards([t for t in ai_tasks if t.get("status", "未着手") == "完了"], "done")

    if human_tasks:
        st.divider()
        st.caption(
            f"👤 人間必須の業務（{len(human_tasks)}件）はステータス管理の対象外です: "
            + "、".join(t["name"] for t in human_tasks)
        )
