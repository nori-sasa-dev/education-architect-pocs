import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from agents.extraction_agent import ExtractionAgent
from agents.qa_agent import QAAgent
from database.db import (
    init_db, save_knowledge, search_knowledge, get_all_categories, get_stats,
    update_knowledge_item, delete_knowledge_item,
    get_all_authors, get_author_info, get_knowledge_items_by_author,
    add_thanks, get_thanks_count, get_thanks_log,
    add_author_thanks, get_author_thanks_count, get_author_thanks_log,
    get_author_ranking,
)

load_dotenv()

st.set_page_config(
    page_title="ナレッジブリッジ",
    page_icon="🌉",
    layout="wide",
)

st.markdown("""
<style>
.brand-title {
    font-size: 4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #1a237e 0%, #0288d1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}
.brand-sub {
    font-size: 1.2rem;
    color: #546e7a;
    margin-bottom: 1.5rem;
    letter-spacing: 0.01em;
}
</style>
""", unsafe_allow_html=True)

# --- DB Initialization ---
init_db()
from seed_demo import seed_if_empty
seed_if_empty()

# --- State Initialization ---
if "mode" not in st.session_state:
    st.session_state.mode = "home"
if "interview_messages" not in st.session_state:
    st.session_state.interview_messages = []
if "interview_turn" not in st.session_state:
    st.session_state.interview_turn = 0
if "extracted_knowledge" not in st.session_state:
    st.session_state.extracted_knowledge = None
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "editing_item_id" not in st.session_state:
    st.session_state.editing_item_id = None
if "deleting_item_id" not in st.session_state:
    st.session_state.deleting_item_id = None
if "qa_messages" not in st.session_state:
    st.session_state.qa_messages = []
if "qa_selected_author" not in st.session_state:
    st.session_state.qa_selected_author = None

# --- Agent Setup ---
# Streamlit Cloud では st.secrets、ローカルでは .env から読む
api_key = st.secrets.get("ANTHROPIC_API_KEY", None) or os.getenv("ANTHROPIC_API_KEY")
agent = ExtractionAgent(api_key=api_key)
qa_agent = QAAgent(api_key=api_key)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 🌉 ナレッジブリッジ")
    st.caption("ベテランの知恵を、次世代の力に")

    if agent.is_demo_mode:
        st.warning("⚠️ デモモードで動作中\n\nAPIキーを設定すると本番モードになります")
        with st.expander("APIキー設定方法"):
            st.code("# .envファイルを作成\nANTHROPIC_API_KEY=sk-ant-xxxxx", language="bash")
    else:
        st.success("✅ Claude API 接続済み")

    st.divider()

    st.markdown("**ナビゲーション**")
    menu_items = [
        ("home",      "🏠 ホーム"),
        ("interview", "🎙️ 知識を記録する"),
        ("search",    "🔍 知識を検索する"),
        ("qa",        "💬 前任者に質問する"),
        ("ranking",   "🏆 貢献ランキング"),
    ]
    for mode_key, label in menu_items:
        btn_type = "primary" if st.session_state.mode == mode_key else "secondary"
        if st.button(label, use_container_width=True, type=btn_type, key=f"nav_{mode_key}"):
            st.session_state.mode = mode_key
            st.rerun()

    st.divider()

    stats = get_stats()
    st.markdown("**データベース統計**")
    col1, col2 = st.columns(2)
    col1.metric("記録者数", stats["entry_count"])
    col2.metric("知識項目数", stats["item_count"])
    if stats["categories"]:
        for cat, cnt in stats["categories"].items():
            st.caption(f"  {cat}: {cnt}件")


# --- Home Page ---
def render_home():
    st.markdown(
        '<p style="font-size:4rem;font-weight:900;'
        'background:linear-gradient(135deg,#1a237e 0%,#0288d1 100%);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        'background-clip:text;line-height:1.15;letter-spacing:-0.02em;margin-bottom:0.4rem">'
        '🌉 ナレッジブリッジ</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:1.2rem;color:#546e7a;margin-bottom:1.5rem;letter-spacing:0.01em">'
        'ベテランの知恵を、組織の財産に。'
        '退職とともに消えていくノウハウを、次世代への贈り物に変えます。</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("### 🎙️ 知識を記録する")
            st.markdown(
                "AIインタビュアーが対話を通じてベテランの経験・ノウハウを引き出し、"
                "構造化してデータベースに保存します。"
            )
            st.caption("対象: ベテラン社員・退職予定者")
            if st.button("インタビューを開始", key="home_interview", type="primary", use_container_width=True):
                st.session_state.mode = "interview"
                st.session_state.interview_messages = []
                st.session_state.interview_turn = 0
                st.session_state.extracted_knowledge = None
                st.session_state.interview_complete = False
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 🔍 知識を検索する")
            st.markdown(
                "蓄積された暗黙知をキーワードで検索し、"
                "先輩の経験・判断基準を業務に活用できます。"
            )
            st.caption("対象: 若手社員・新規プロジェクトメンバー")
            if st.button("知識を探す", key="home_search", type="primary", use_container_width=True):
                st.session_state.mode = "search"
                st.rerun()

    with col3:
        with st.container(border=True):
            st.markdown("### 💬 前任者に質問する")
            st.markdown(
                "蓄積したナレッジをもとに、前任者の視点でリアルタイムに答えます。"
                "疑問をそのままぶつけてください。"
            )
            st.caption("対象: 業務引き継ぎ中のメンバー")
            if st.button("前任者に聞く", key="home_qa", type="primary", use_container_width=True):
                st.session_state.mode = "qa"
                st.rerun()

    st.divider()

    st.markdown("### このツールが解決する3つの課題")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.container(border=True):
            st.markdown("**🚨 ベテランの退職リスク**")
            st.markdown("マニュアルに書けない判断の根拠・肌感覚が消える前に、体系的に記録。")
    with col_b:
        with st.container(border=True):
            st.markdown("**😰 若手の孤立問題**")
            st.markdown("「誰に聞けばいいか」「どこに記録があるか」わからない状況を解消。")
    with col_c:
        with st.container(border=True):
            st.markdown("**🔄 OJTの属人化**")
            st.markdown("再現性のないスキル継承を、AIが対話で体系化。組織全体の資産に。")


# --- Interview Phase Helper ---
def _get_interview_phase(turn: int) -> tuple[str, float]:
    if turn == 0:
        return "👋 はじめに", 0.05
    elif turn <= 2:
        return "📖 エピソード引き出し", 0.35
    elif turn <= 4:
        return "🔍 深掘り（Why連鎖）", 0.65
    elif turn <= 6:
        return "💡 暗黙知の抽出", 0.85
    else:
        return "📝 まとめ", 1.0


# --- Interview Page ---
def render_interview():
    st.markdown("## 🎙️ 暗黙知インタビュー")
    st.caption("AIが対話を通じて、あなたの経験・ノウハウを引き出します")

    if not st.session_state.interview_complete:
        phase_label, progress_val = _get_interview_phase(st.session_state.interview_turn)
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            st.markdown(f"**フェーズ:** {phase_label}")
        with col_p2:
            st.progress(progress_val)
        st.divider()

    # 会話履歴表示
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 初回挨拶
    if not st.session_state.interview_messages:
        with st.spinner("インタビュアーが準備しています..."):
            greeting = agent.respond([], st.session_state.interview_turn)
        st.session_state.interview_messages.append({"role": "assistant", "content": greeting})
        with st.chat_message("assistant"):
            st.markdown(greeting)

    # チャット入力
    if not st.session_state.interview_complete:
        if user_input := st.chat_input("メッセージを入力してください..."):
            st.session_state.interview_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            st.session_state.interview_turn += 1
            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.interview_messages
            ]

            with st.spinner("インタビュアーが考えています..."):
                response = agent.respond(api_messages, st.session_state.interview_turn)

            knowledge = agent.extract_knowledge(response)
            if knowledge:
                st.session_state.extracted_knowledge = knowledge
                st.session_state.interview_complete = True
                display_text = response.split("[KNOWLEDGE_EXTRACTED]")[0].strip()
            else:
                display_text = response

            st.session_state.interview_messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(display_text)

            if st.session_state.interview_complete:
                st.rerun()
    else:
        st.success("🎉 インタビューが完了しました！抽出された知識をご確認ください。")

        knowledge = st.session_state.extracted_knowledge
        if knowledge:
            st.subheader("抽出された知識")

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("記録者", knowledge.get("author_name", "不明"))
                col2.metric("役職", knowledge.get("author_role", "不明"))
                col3.metric("部署", knowledge.get("department", "不明"))
                col4.metric("経験年数", knowledge.get("years_of_experience", "不明"))

            st.divider()

            items = knowledge.get("knowledge_items", [])
            for item in items:
                with st.expander(f"📝 {item['title']}（{item.get('category', 'その他')}）", expanded=True):
                    st.markdown(f"**カテゴリ:** {item.get('category', 'その他')}")
                    st.markdown(f"**内容:**\n{item['content']}")
                    if item.get("context"):
                        st.markdown(f"**活用場面:** {item['context']}")
                    if item.get("keywords"):
                        st.markdown(f"**キーワード:** `{item['keywords']}`")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 データベースに保存", type="primary", use_container_width=True):
                    entry_data = {
                        "author_name": knowledge.get("author_name", "不明"),
                        "author_role": knowledge.get("author_role", ""),
                        "department": knowledge.get("department", ""),
                        "years_of_experience": knowledge.get("years_of_experience", ""),
                        "session_id": st.session_state.session_id,
                    }
                    save_knowledge(entry_data, items)
                    st.success("✅ 知識がデータベースに保存されました！")
                    st.balloons()
            with col2:
                if st.button("🔄 新しいインタビュー", use_container_width=True):
                    st.session_state.interview_messages = []
                    st.session_state.interview_turn = 0
                    st.session_state.extracted_knowledge = None
                    st.session_state.interview_complete = False
                    st.session_state.session_id = str(uuid.uuid4())
                    st.rerun()


# --- 検索結果の表示（編集・削除機能付き） ---
def _render_knowledge_item(result: dict):
    item_id = result["id"]

    # 編集モード
    if st.session_state.editing_item_id == item_id:
        with st.form(key=f"edit_form_{item_id}"):
            st.markdown("**✏️ 編集中**")
            all_categories = [
                "トラブルシューティング", "判断基準", "人間関係",
                "リスク予測", "効率化", "技術的専門知識", "その他",
            ]
            current_cat_index = (
                all_categories.index(result["category"])
                if result["category"] in all_categories
                else len(all_categories) - 1
            )
            new_title = st.text_input("タイトル", value=result["title"])
            new_category = st.selectbox("カテゴリ", all_categories, index=current_cat_index)
            new_content = st.text_area("内容", value=result["content"], height=150)
            new_context = st.text_input("活用場面", value=result.get("context", ""))
            new_keywords = st.text_input("キーワード", value=result.get("keywords", ""))

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("保存", type="primary", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("キャンセル", use_container_width=True)

            if submitted:
                update_knowledge_item(item_id, new_title, new_content, new_category, new_context, new_keywords)
                st.session_state.editing_item_id = None
                if "search_results" in st.session_state:
                    del st.session_state["search_results"]
                st.success("更新しました！")
                st.rerun()
            if cancelled:
                st.session_state.editing_item_id = None
                st.rerun()
        return

    # 削除確認モード
    if st.session_state.deleting_item_id == item_id:
        st.warning(f"「{result['title']}」を削除しますか？この操作は元に戻せません。")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("本当に削除する", key=f"confirm_delete_{item_id}", type="primary", use_container_width=True):
                delete_knowledge_item(item_id)
                st.session_state.deleting_item_id = None
                if "search_results" in st.session_state:
                    del st.session_state["search_results"]
                st.success("削除しました！")
                st.rerun()
        with col2:
            if st.button("キャンセル", key=f"cancel_delete_{item_id}", use_container_width=True):
                st.session_state.deleting_item_id = None
                st.rerun()
        return

    # 通常表示
    st.markdown(f"**カテゴリ:** {result['category']}")
    st.markdown(f"**記録者:** {result['author_name']}（{result.get('author_role', '')}）")
    st.markdown(f"**内容:**\n{result['content']}")
    if result.get("context"):
        st.markdown(f"**活用場面:** {result['context']}")
    if result.get("keywords"):
        st.markdown(f"**キーワード:** `{result['keywords']}`")

    # ありがとうボタン
    thanks_count = get_thanks_count(item_id)
    thanks_log = get_thanks_log(item_id)

    col_t1, col_t2 = st.columns([2, 4])
    with col_t1:
        thanker_name = st.text_input(
            "あなたの名前", key=f"thanker_input_{item_id}",
            placeholder="名前を入力...", label_visibility="collapsed"
        )
        if st.button(f"ありがとう 🙏 （{thanks_count}）", key=f"thanks_{item_id}", use_container_width=True):
            if thanker_name.strip():
                new_count = add_thanks(item_id, thanker_name.strip())
                st.success(f"ありがとうが伝わりました！（累計 {new_count} 件）")
                st.rerun()
            else:
                st.warning("名前を入力してください")
    with col_t2:
        if thanks_log:
            names = "、".join([t["thanker_name"] for t in thanks_log[:5]])
            suffix = f" 他{len(thanks_log)-5}名" if len(thanks_log) > 5 else ""
            st.caption(f"感謝した人: {names}{suffix}")

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("✏️ 編集", key=f"edit_{item_id}", use_container_width=True):
            st.session_state.editing_item_id = item_id
            st.session_state.deleting_item_id = None
            st.rerun()
    with col2:
        if st.button("🗑️ 削除", key=f"delete_{item_id}", use_container_width=True):
            st.session_state.deleting_item_id = item_id
            st.session_state.editing_item_id = None
            st.rerun()


# --- Search Page ---
def render_search():
    st.markdown("## 🔍 知識を検索する")
    st.caption("蓄積された暗黙知をキーワードで検索します")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("キーワードを入力", placeholder="例: 障害対応, リスク, 判断基準...")
    with col2:
        categories = ["すべて"] + get_all_categories()
        selected_category = st.selectbox("カテゴリ", categories)

    category_filter = None if selected_category == "すべて" else selected_category

    col_s1, col_s2 = st.columns([1, 4])
    with col_s1:
        if st.button("🔍 検索", type="primary", use_container_width=True):
            results = search_knowledge(search_query, category_filter)
            st.session_state.search_results = results
            st.session_state.editing_item_id = None
            st.session_state.deleting_item_id = None
    with col_s2:
        if st.button("全件表示", use_container_width=True):
            all_results = search_knowledge("", category_filter)
            st.session_state.search_results = all_results
            st.session_state.editing_item_id = None
            st.session_state.deleting_item_id = None
            st.rerun()

    results = st.session_state.get("search_results", [])
    if results:
        st.write(f"**{len(results)}件** の知識が見つかりました")
        for result in results:
            with st.expander(f"📝 {result['title']}（{result['category']}）- {result['author_name']}"):
                _render_knowledge_item(result)
    elif "search_results" in st.session_state:
        st.info("該当する知識が見つかりませんでした。別のキーワードで試してみてください。")


# --- Q&A Page ---
def render_qa():
    st.markdown("## 💬 前任者に質問する")
    st.caption("蓄積されたナレッジをもとに、前任者の視点で答えます")

    authors = get_all_authors()
    if not authors:
        st.info("まだナレッジが登録されていません。先にインタビューを行ってください。")
        return

    selected = st.selectbox(
        "質問したい前任者を選んでください",
        options=authors,
        key="qa_author_select",
    )

    if selected != st.session_state.qa_selected_author:
        st.session_state.qa_selected_author = selected
        st.session_state.qa_messages = []
        st.rerun()

    author_info = get_author_info(selected)
    knowledge_items = get_knowledge_items_by_author(selected)

    # プロフィール表示
    with st.expander(f"📋 {selected} さんのプロフィールと知識一覧", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**役職:** {author_info.get('author_role', '—')}")
        col2.markdown(f"**部署:** {author_info.get('department', '—')}")
        col3.markdown(f"**経験:** {author_info.get('years_of_experience', '—')}")
        st.markdown(f"**登録ナレッジ数:** {len(knowledge_items)} 件")
        for item in knowledge_items:
            st.markdown(f"- [{item['category']}] {item['title']}")

    st.divider()

    # 会話履歴表示
    for msg in st.session_state.qa_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 初回ガイダンス
    if not st.session_state.qa_messages:
        with st.chat_message("assistant"):
            st.markdown(
                f"こんにちは。{selected} です。\n\n"
                "業務でわからないことや、判断に迷っていることがあれば何でも聞いてください。"
                "私の経験をもとにお答えします。"
            )

    # 入力
    if user_input := st.chat_input(f"{selected} さんに質問する..."):
        st.session_state.qa_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.qa_messages]
        with st.spinner(f"{selected} さんが考えています..."):
            reply = qa_agent.respond(api_messages, author_info, knowledge_items)

        st.session_state.qa_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    # ありがとう + リセット
    if st.session_state.qa_messages:
        st.divider()
        author_thanks_count = get_author_thanks_count(selected)
        author_thanks_log = get_author_thanks_log(selected)

        col_t1, col_t2, col_t3 = st.columns([2, 4, 2])
        with col_t1:
            qa_thanker = st.text_input(
                "感謝を伝える", key=f"qa_thanker_{selected}",
                placeholder="あなたの名前...", label_visibility="collapsed"
            )
            if st.button(f"ありがとう 🙏 （{author_thanks_count}）", key=f"qa_thanks_{selected}", use_container_width=True):
                if qa_thanker.strip():
                    new_count = add_author_thanks(selected, qa_thanker.strip())
                    st.success(f"感謝が {selected} さんに伝わりました！（累計 {new_count} 件）")
                    st.rerun()
                else:
                    st.warning("名前を入力してください")
        with col_t2:
            if author_thanks_log:
                names = "、".join([t["thanker_name"] for t in author_thanks_log[:5]])
                suffix = f" 他{len(author_thanks_log)-5}名" if len(author_thanks_log) > 5 else ""
                st.caption(f"感謝した人: {names}{suffix}")
        with col_t3:
            if st.button("🔄 会話をリセット", use_container_width=True):
                st.session_state.qa_messages = []
                st.rerun()


# --- Ranking Page ---
def render_ranking():
    st.markdown("## 🏆 貢献ランキング")
    st.caption("ナレッジ登録・活用の貢献度で組織のヒーローを称えます")

    ranking = get_author_ranking()

    if not ranking:
        st.info("まだナレッジが登録されていません。先にインタビューを行ってください。")
        return

    # --- スコア説明 ---
    with st.expander("📊 スコアの計算方法", expanded=False):
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("📚 登録ナレッジ", "10pt / 件")
        col_s2.metric("🙏 ありがとう（ナレッジ）", "20pt / 件")
        col_s3.metric("🙏 ありがとう（Q&A）", "30pt / 件")
        col_s4.metric("🔍 検索ヒット", "1pt / 回")

    st.divider()

    # --- Top 3 ヒーロー枠 ---
    medals = ["🥇", "🥈", "🥉"]
    top_n = min(3, len(ranking))
    hero_cols = st.columns(top_n)
    for i, col in enumerate(hero_cols):
        r = ranking[i]
        with col:
            with st.container(border=True):
                st.markdown(f"### {medals[i]} {r['author_name']}")
                st.caption(f"{r['author_role']}　{r['department']}")
                m1, m2, m3 = st.columns(3)
                m1.metric("📚 登録", r["item_count"])
                m2.metric("🙏 感謝", r["total_thanks"])
                m3.metric("🔍 ヒット", r["total_hits"])
                st.markdown(
                    f"<div style='text-align:center; font-size:1.4rem; font-weight:800;"
                    f"color:#1565c0; margin-top:0.5rem'>{r['score']} pt</div>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # --- 全体ランキングテーブル（トップ10）---
    st.markdown("### 全体ランキング TOP 10")

    rows_data = []
    for i, r in enumerate(ranking[:10]):
        medal = medals[i] if i < 3 else f"{i + 1}位"
        rows_data.append({
            "順位": medal,
            "氏名": r["author_name"],
            "役職": r["author_role"],
            "📚 登録数": r["item_count"],
            "🙏 感謝（ナレッジ）": r["item_thanks"],
            "🙏 感謝（Q&A）": r["author_thanks"],
            "🔍 ヒット数": r["total_hits"],
            "🏅 スコア": r["score"],
        })

    import pandas as pd
    df = pd.DataFrame(rows_data)
    max_score = df["🏅 スコア"].max() if not df.empty else 1
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "🏅 スコア": st.column_config.ProgressColumn(
                "🏅 スコア",
                min_value=0,
                max_value=int(max_score),
                format="%d pt",
            ),
            "📚 登録数": st.column_config.NumberColumn("📚 登録数", format="%d 件"),
            "🙏 感謝（ナレッジ）": st.column_config.NumberColumn("🙏 感謝（ナレッジ）", format="%d 件"),
            "🙏 感謝（Q&A）": st.column_config.NumberColumn("🙏 感謝（Q&A）", format="%d 件"),
            "🔍 ヒット数": st.column_config.NumberColumn("🔍 ヒット数", format="%d 回"),
        },
    )

    st.divider()

    # --- バーチャート比較 ---
    st.markdown("### カテゴリ別比較")
    col_c1, col_c2 = st.columns(2)

    names = [r["author_name"] for r in ranking]

    with col_c1:
        st.markdown("**📚 登録ナレッジ数**")
        chart_df1 = pd.DataFrame(
            {"登録数": [r["item_count"] for r in ranking]},
            index=names,
        )
        st.bar_chart(chart_df1)

    with col_c2:
        st.markdown("**🙏 獲得ありがとう数**")
        chart_df2 = pd.DataFrame(
            {
                "ナレッジへの感謝": [r["item_thanks"] for r in ranking],
                "Q&Aへの感謝": [r["author_thanks"] for r in ranking],
            },
            index=names,
        )
        st.bar_chart(chart_df2)

    st.markdown("**🔍 検索ヒット数**")
    chart_df3 = pd.DataFrame(
        {"ヒット数": [r["total_hits"] for r in ranking]},
        index=names,
    )
    st.bar_chart(chart_df3)


# --- Routing ---
if st.session_state.mode == "home":
    render_home()
elif st.session_state.mode == "interview":
    render_interview()
elif st.session_state.mode == "search":
    render_search()
elif st.session_state.mode == "qa":
    render_qa()
elif st.session_state.mode == "ranking":
    render_ranking()
