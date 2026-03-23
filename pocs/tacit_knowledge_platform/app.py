import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from agents.extraction_agent import ExtractionAgent
from database.db import (
    init_db, save_knowledge, search_knowledge, get_all_categories, get_stats,
    update_knowledge_item, delete_knowledge_item,
)

load_dotenv()

st.set_page_config(
    page_title="暗黙知継承プラットフォーム",
    page_icon="📚",
    layout="wide",
)

# --- DB Initialization ---
init_db()

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

# --- Agent Setup ---
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = ExtractionAgent(api_key=api_key)

# --- Sidebar ---
with st.sidebar:
    st.title("暗黙知継承プラットフォーム")
    st.caption("ベテランの知恵を次世代へ")

    if agent.is_demo_mode:
        st.warning("デモモードで動作中\n\nAPIキーを設定すると本番モードになります")
        with st.expander("APIキー設定方法"):
            st.code("# .envファイルを作成\nANTHROPIC_API_KEY=sk-ant-xxxxx", language="bash")
    else:
        st.success("Claude API 接続済み")

    st.divider()

    st.subheader("メニュー")
    if st.button("ホーム", use_container_width=True, type="primary" if st.session_state.mode == "home" else "secondary"):
        st.session_state.mode = "home"
        st.rerun()
    if st.button("知識を記録する（インタビュー）", use_container_width=True, type="primary" if st.session_state.mode == "interview" else "secondary"):
        st.session_state.mode = "interview"
        st.rerun()
    if st.button("知識を検索する", use_container_width=True, type="primary" if st.session_state.mode == "search" else "secondary"):
        st.session_state.mode = "search"
        st.rerun()

    st.divider()

    # Stats
    stats = get_stats()
    st.subheader("データベース統計")
    col1, col2 = st.columns(2)
    col1.metric("記録者数", stats["entry_count"])
    col2.metric("知識項目数", stats["item_count"])
    if stats["categories"]:
        st.write("**カテゴリ別:**")
        for cat, cnt in stats["categories"].items():
            st.write(f"  - {cat}: {cnt}件")


# --- Home Page ---
def render_home():
    st.header("暗黙知継承プラットフォーム")
    st.subheader("ベテランの知恵を、組織の資産に。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 知識を記録する")
        st.markdown(
            "AIインタビュアーがベテランの経験・ノウハウを対話で引き出し、"
            "構造化してデータベースに保存します。"
        )
        st.markdown("**対象:** ベテラン社員、退職予定者")
        if st.button("インタビューを開始", key="home_interview", use_container_width=True):
            st.session_state.mode = "interview"
            st.session_state.interview_messages = []
            st.session_state.interview_turn = 0
            st.session_state.extracted_knowledge = None
            st.session_state.interview_complete = False
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

    with col2:
        st.markdown("### 知識を検索する")
        st.markdown(
            "蓄積された暗黙知をキーワードで検索し、"
            "先輩の経験・判断基準を業務に活用できます。"
        )
        st.markdown("**対象:** 若手社員、新規プロジェクトメンバー")
        if st.button("知識を探す", key="home_search", use_container_width=True):
            st.session_state.mode = "search"
            st.rerun()

    st.divider()

    st.markdown("### このツールが解決する課題")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**ベテランの退職問題**")
        st.markdown("マニュアルに書けない判断の理由・肌感覚が失われる")
    with cols[1]:
        st.markdown("**若手の孤立問題**")
        st.markdown("誰に聞けばいいかわからない・記録がない")
    with cols[2]:
        st.markdown("**組織の課題**")
        st.markdown("OJTの属人化・再現性のないスキル継承")


# --- Interview Page ---
def render_interview():
    st.header("暗黙知インタビュー")
    st.caption("AIが対話を通じて、あなたの経験・ノウハウを引き出します")

    # Display messages
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Initial greeting
    if not st.session_state.interview_messages:
        greeting = agent.respond([], st.session_state.interview_turn)
        st.session_state.interview_messages.append({"role": "assistant", "content": greeting})
        with st.chat_message("assistant"):
            st.markdown(greeting)

    # Chat input
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
        st.success("インタビューが完了しました！抽出された知識をご確認ください。")

        knowledge = st.session_state.extracted_knowledge
        if knowledge:
            st.subheader("抽出された知識")

            st.write(f"**記録者:** {knowledge.get('author_name', '不明')}")
            st.write(f"**役職:** {knowledge.get('author_role', '不明')}")
            st.write(f"**部署:** {knowledge.get('department', '不明')}")
            st.write(f"**経験年数:** {knowledge.get('years_of_experience', '不明')}")

            st.divider()

            items = knowledge.get("knowledge_items", [])
            for i, item in enumerate(items):
                with st.expander(f"📝 {item['title']}（{item.get('category', 'その他')}）", expanded=True):
                    st.markdown(f"**カテゴリ:** {item.get('category', 'その他')}")
                    st.markdown(f"**内容:**\n{item['content']}")
                    if item.get("context"):
                        st.markdown(f"**活用場面:** {item['context']}")
                    if item.get("keywords"):
                        st.markdown(f"**キーワード:** {item['keywords']}")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("データベースに保存", type="primary", use_container_width=True):
                    entry_data = {
                        "author_name": knowledge.get("author_name", "不明"),
                        "author_role": knowledge.get("author_role", ""),
                        "department": knowledge.get("department", ""),
                        "years_of_experience": knowledge.get("years_of_experience", ""),
                        "session_id": st.session_state.session_id,
                    }
                    save_knowledge(entry_data, items)
                    st.success("知識がデータベースに保存されました！")
                    st.balloons()
            with col2:
                if st.button("新しいインタビュー", use_container_width=True):
                    st.session_state.interview_messages = []
                    st.session_state.interview_turn = 0
                    st.session_state.extracted_knowledge = None
                    st.session_state.interview_complete = False
                    st.session_state.session_id = str(uuid.uuid4())
                    st.rerun()


# --- 検索結果の表示（編集・削除機能付き） ---
def _render_knowledge_item(result: dict):
    """ナレッジアイテムを編集・削除機能付きで表示する"""
    item_id = result["id"]

    # 編集モード
    if st.session_state.editing_item_id == item_id:
        with st.form(key=f"edit_form_{item_id}"):
            st.markdown("**編集中**")
            # カテゴリ選択肢
            all_categories = [
                "トラブルシューティング", "判断基準", "人間関係",
                "リスク予測", "効率化", "技術的専門知識", "その他",
            ]
            current_cat_index = all_categories.index(result["category"]) if result["category"] in all_categories else len(all_categories) - 1
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
                # 検索結果を更新するためにクリア
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
        st.markdown(f"**キーワード:** {result['keywords']}")

    # 編集・削除ボタン
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("編集", key=f"edit_{item_id}", use_container_width=True):
            st.session_state.editing_item_id = item_id
            st.session_state.deleting_item_id = None
            st.rerun()
    with col2:
        if st.button("削除", key=f"delete_{item_id}", use_container_width=True):
            st.session_state.deleting_item_id = item_id
            st.session_state.editing_item_id = None
            st.rerun()


# --- Search Page ---
def render_search():
    st.header("知識検索")
    st.caption("蓄積された暗黙知をキーワードで検索します")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("キーワードを入力", placeholder="例: 障害対応, リスク, 判断基準...")
    with col2:
        categories = ["すべて"] + get_all_categories()
        selected_category = st.selectbox("カテゴリ", categories)

    category_filter = None if selected_category == "すべて" else selected_category

    if st.button("検索", type="primary"):
        results = search_knowledge(search_query, category_filter)
        st.session_state.search_results = results
        # 編集・削除状態をリセット
        st.session_state.editing_item_id = None
        st.session_state.deleting_item_id = None

    # 検索結果の表示
    results = st.session_state.get("search_results", [])
    if results:
        st.write(f"**{len(results)}件** の知識が見つかりました")
        for result in results:
            with st.expander(f"📝 {result['title']}（{result['category']}）- {result['author_name']}"):
                _render_knowledge_item(result)
    elif "search_results" in st.session_state:
        st.info("該当する知識が見つかりませんでした。別のキーワードで試してみてください。")

    st.divider()
    st.markdown("### すべての知識を閲覧")
    if st.button("全件表示"):
        all_results = search_knowledge("", category_filter)
        st.session_state.search_results = all_results
        st.session_state.editing_item_id = None
        st.session_state.deleting_item_id = None
        st.rerun()


# --- Routing ---
if st.session_state.mode == "home":
    render_home()
elif st.session_state.mode == "interview":
    render_interview()
elif st.session_state.mode == "search":
    render_search()
