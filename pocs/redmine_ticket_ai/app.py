import os
import streamlit as st
from dotenv import load_dotenv
from database.db import init_db, get_stats, get_ticket_count, get_features, get_ticket_types
from services.data_ingestion import DataIngestionService

load_dotenv()

st.set_page_config(
    page_title="Redmine Ticket AI",
    page_icon="🎫",
    layout="wide",
)

# --- DB初期化 ---
init_db()

# --- APIキー確認 ---
try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", None) or os.getenv("ANTHROPIC_API_KEY")
except Exception:
    api_key = os.getenv("ANTHROPIC_API_KEY")
is_demo_mode = not bool(api_key)

# --- セッション状態初期化 ---
if "page" not in st.session_state:
    st.session_state.page = "data_management"
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "profile" not in st.session_state:
    st.session_state.profile = None
if "profile_summary" not in st.session_state:
    st.session_state.profile_summary = None

# --- サイドバー ---
with st.sidebar:
    st.markdown("## 🎫 Redmine Ticket AI")
    st.caption("チケット知識を組織の資産に")

    if is_demo_mode:
        st.warning("⚠️ デモモード\n\nAPIキーを設定すると本番モードになります")
    else:
        st.success("✅ Claude API 接続済み")

    st.divider()

    st.markdown("**ナビゲーション**")
    pages = [
        ("data_management", "📥 データ管理"),
        ("similarity_search", "🔍 類似故障検索"),
        ("feature_profile",  "📋 機能カルテ"),
    ]
    for page_key, label in pages:
        btn_type = "primary" if st.session_state.page == page_key else "secondary"
        if st.button(label, use_container_width=True, type=btn_type, key=f"nav_{page_key}"):
            st.session_state.page = page_key
            st.rerun()

    st.divider()

    ticket_count = get_ticket_count()
    st.markdown("**データ件数**")
    st.metric("登録チケット数", ticket_count)


# =============================================
# データ管理ページ
# =============================================
def render_data_management():
    st.markdown("## 📥 データ管理")
    st.caption("RedmineチケットデータをCSVでインポートします")

    ticket_count = get_ticket_count()

    if ticket_count == 0:
        st.info("チケットデータがまだ登録されていません。CSVをインポートするかサンプルデータを読み込んでください。")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 📂 CSVファイルをインポート")
            st.caption("Redmineからエクスポートしたチケット一覧CSVをアップロードします")
            uploaded = st.file_uploader(
                "CSVファイルを選択",
                type=["csv"],
                key="csv_uploader",
            )
            if uploaded is not None:
                if st.button("インポート開始", type="primary", use_container_width=True):
                    csv_content = uploaded.read().decode("utf-8")
                    with st.spinner("インポート中..."):
                        svc = DataIngestionService()
                        result = svc.ingest_csv(csv_content, filename=uploaded.name)
                    if result["success"]:
                        st.success(
                            f"✅ {result['row_count']}件をインポートしました"
                            f"（累計: {result['total_count']}件）"
                        )
                        if result.get("vector_indexed"):
                            st.caption("ベクトルインデックスも更新されました")
                        else:
                            st.caption("ベクトルインデックスの更新は省略されました（ChromaDB未設定）")
                        st.rerun()
                    else:
                        st.error(f"エラー: {result['error']}")

    with col2:
        with st.container(border=True):
            st.markdown("### 🧪 サンプルデータを読み込む")
            st.caption("同梱の35件のサンプルチケットで機能を試せます")
            st.markdown("""
| チケット種別 | 件数 |
|------------|------|
| 故障管理 | 15件 |
| 課題管理 | 9件  |
| レビュー指摘 | 11件 |
            """)
            if st.button("サンプルデータを読み込む", type="primary", use_container_width=True):
                with st.spinner("読み込み中..."):
                    svc = DataIngestionService()
                    result = svc.ingest_sample()
                if result["success"]:
                    st.success(
                        f"✅ {result['row_count']}件のサンプルデータを読み込みました"
                    )
                    if result.get("vector_indexed"):
                        st.caption("ベクトルインデックスも更新されました")
                    else:
                        st.caption("ベクトルインデックスの更新は省略されました（ChromaDB未設定）")
                    st.rerun()
                else:
                    st.error(f"エラー: {result['error']}")

    if ticket_count > 0:
        st.divider()
        st.markdown("### 📊 登録データの概要")
        stats = get_stats()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**チケット種別**")
            for t, cnt in stats["by_type"].items():
                st.metric(t, f"{cnt}件")

        with col_b:
            st.markdown("**機能別件数（上位5件）**")
            for i, (feat, cnt) in enumerate(list(stats["by_feature"].items())[:5]):
                st.metric(feat, f"{cnt}件")


# =============================================
# 類似故障検索ページ
# =============================================
def render_similarity_search():
    st.markdown("## 🔍 類似故障検索")
    st.caption("発生した事象を入力すると、過去の類似チケットをベクトル検索で探します")

    ticket_count = get_ticket_count()
    if ticket_count == 0:
        st.warning("チケットデータが登録されていません。先にデータ管理ページからインポートしてください。")
        return

    try:
        from services.similarity_search import SimilaritySearchService
        svc = SimilaritySearchService()
        vector_available = True
    except Exception:
        vector_available = False

    if not vector_available:
        st.error("ChromaDB または sentence-transformers が利用できません。`pip install chromadb sentence-transformers` を実行してください。")
        return

    # --- 検索フォーム ---
    with st.form("search_form"):
        query = st.text_area(
            "事象・キーワードを入力",
            placeholder="例: ログイン後にセッションが切れる / メール送信が失敗する",
            height=80,
        )
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            types = ["すべて"] + get_ticket_types()
            selected_type = st.selectbox("チケット種別", types)
        with col2:
            features = ["すべて"] + get_features()
            selected_feature = st.selectbox("機能", features)
        with col3:
            top_k = st.number_input("表示件数", min_value=1, max_value=20, value=5)
        submitted = st.form_submit_button("🔍 検索", type="primary", use_container_width=True)

    if submitted:
        if not query.strip():
            st.warning("事象・キーワードを入力してください")
        else:
            with st.spinner("類似チケットを検索中..."):
                try:
                    results = svc.search(
                        query.strip(),
                        top_k=int(top_k),
                        ticket_type=selected_type,
                        feature=selected_feature,
                    )
                    st.session_state.search_results = results
                    st.session_state.search_query = query.strip()
                except Exception as e:
                    st.error(f"検索エラー: {e}")
                    return

    results = st.session_state.get("search_results", [])
    query_text = st.session_state.get("search_query", "")

    if not results:
        return

    st.divider()
    st.markdown(f"**{len(results)}件** の類似チケットが見つかりました")

    # --- 結果一覧 ---
    for r in results:
        score = r.get("similarity", 0)
        score_color = "#1565c0" if score >= 70 else "#f57c00" if score >= 40 else "#757575"
        with st.expander(
            f"[{r['ticket_type']}] {r['title']}  —  {r['feature']}",
            expanded=score >= 60,
        ):
            col_a, col_b, col_c = st.columns([1, 1, 1])
            col_a.metric("類似スコア", f"{score}%")
            col_b.metric("機能", r["feature"])
            col_c.metric("ステータス", r["status"])

            if r.get("description"):
                st.markdown(f"**現象・説明:**\n{r['description']}")
            if r.get("root_cause"):
                st.markdown(f"**真の原因:** {r['root_cause']}")
            if r.get("resolution"):
                st.markdown(f"**解決策:** {r['resolution']}")
            if r.get("review_comment"):
                st.caption(f"レビュー指摘: {r['review_comment']}")

    # --- 解決策サジェスト（Claude API） ---
    st.divider()
    if not is_demo_mode:
        if st.button("💡 類似事例から解決策を提案（Claude API）", type="primary"):
            with st.spinner("解決策を生成中..."):
                try:
                    suggestion = svc.suggest_solution(query_text, results, api_key)
                    st.markdown("### 💡 解決策の提案")
                    st.markdown(suggestion)
                except Exception as e:
                    st.error(f"生成エラー: {e}")
    else:
        st.info("💡 解決策サジェストはAPIキーを設定すると利用できます")


# =============================================
# 機能カルテページ
# =============================================
def render_feature_profile():
    st.markdown("## 📋 機能カルテ")
    st.caption("機能単位で故障パターン・真の原因・レビュー指摘傾向を集約します")

    ticket_count = get_ticket_count()
    if ticket_count == 0:
        st.warning("チケットデータが登録されていません。先にデータ管理ページからインポートしてください。")
        return

    from services.feature_profile import FeatureProfileService
    svc = FeatureProfileService()

    features = get_features()
    if not features:
        st.info("機能データがありません。")
        return

    selected_feature = st.selectbox("機能を選択してください", features)

    if st.button("カルテを表示", type="primary"):
        st.session_state.profile = svc.get_profile(selected_feature)
        st.session_state.profile_summary = None

    profile = st.session_state.get("profile")
    if not profile:
        return

    st.divider()

    # --- サマリー指標 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総チケット数", profile["total"])
    col2.metric("🔴 故障管理", len(profile["defects"]))
    col3.metric("🟡 課題管理", len(profile["issues"]))
    col4.metric("🔵 レビュー指摘", len(profile["reviews"]))

    # --- 特徴サマリー（自動生成・APIなし）---
    with st.container(border=True):
        st.markdown("### 📌 特徴サマリー")
        sum_col1, sum_col2 = st.columns(2)

        with sum_col1:
            st.markdown("**🔴 よく起きる故障の原因**")
            if profile["root_causes"]:
                for rc in profile["root_causes"][:3]:
                    st.markdown(f"- {rc}")
            else:
                st.caption("故障チケットなし")

        with sum_col2:
            st.markdown("**🔵 レビューで繰り返し指摘されること**")
            if profile["review_comments"]:
                for c in profile["review_comments"][:3]:
                    st.markdown(f"- {c}")
            else:
                st.caption("レビュー指摘チケットなし")

        # 代表的な解決策
        if profile["resolutions"]:
            st.markdown("**✅ 代表的な解決策**")
            res_cols = st.columns(min(3, len(profile["resolutions"])))
            for i, res in enumerate(profile["resolutions"][:3]):
                with res_cols[i]:
                    with st.container(border=True):
                        st.caption(res["title"])
                        st.markdown(res["resolution"])

    # --- タブ表示 ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 故障一覧", "🟡 課題一覧", "🔵 レビュー指摘", "📤 エクスポート"])

    with tab1:
        if profile["defects"]:
            for t in profile["defects"]:
                with st.expander(f"[{t.get('status','')}] {t['title']}"):
                    if t.get("description"):
                        st.markdown(f"**現象:** {t['description']}")
                    if t.get("root_cause"):
                        st.markdown(f"**真の原因:** {t['root_cause']}")
                    if t.get("resolution"):
                        st.markdown(f"**解決策:** {t['resolution']}")
        else:
            st.info("故障管理チケットはありません")

    with tab2:
        if profile["issues"]:
            for t in profile["issues"]:
                with st.expander(f"[{t.get('status','')}] {t['title']}"):
                    if t.get("description"):
                        st.markdown(f"**内容:** {t['description']}")
                    if t.get("resolution"):
                        st.markdown(f"**対応:** {t['resolution']}")
        else:
            st.info("課題管理チケットはありません")

    with tab3:
        if profile["reviews"]:
            for t in profile["reviews"]:
                with st.expander(f"{t['title']}"):
                    if t.get("root_cause"):
                        st.markdown(f"**指摘種別:** {t['root_cause']}")
                    if t.get("review_comment"):
                        st.markdown(f"**コメント:** {t['review_comment']}")
                    if t.get("resolution"):
                        st.markdown(f"**対応:** {t['resolution']}")
        else:
            st.info("レビュー指摘チケットはありません")

    with tab4:
        st.markdown("### 📤 AIコンテキスト注入用エクスポート")
        st.caption("Copilot等のAIツールに貼り付けることで、この機能の品質傾向をコンテキストとして提供できます")

        summary = st.session_state.get("profile_summary")

        if not is_demo_mode:
            if st.button("💡 Claudeでサマリーを生成", type="primary"):
                with st.spinner("サマリーを生成中..."):
                    try:
                        summary = svc.generate_summary(profile, api_key)
                        st.session_state.profile_summary = summary
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成エラー: {e}")
        else:
            st.info("💡 サマリー生成はAPIキーを設定すると利用できます")

        if summary:
            st.markdown("#### Claudeによる品質サマリー")
            st.markdown(summary)
            st.divider()

        export_text = svc.export_context(profile, summary)
        st.text_area(
            "コンテキストテキスト（コピーしてAIツールに貼り付け）",
            value=export_text,
            height=300,
        )
        st.download_button(
            "⬇️ テキストをダウンロード",
            data=export_text,
            file_name=f"feature_profile_{profile['feature']}.txt",
            mime="text/plain",
        )


# --- ルーティング ---
if st.session_state.page == "data_management":
    render_data_management()
elif st.session_state.page == "similarity_search":
    render_similarity_search()
elif st.session_state.page == "feature_profile":
    render_feature_profile()
