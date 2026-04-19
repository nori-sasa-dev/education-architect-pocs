"""
Safari お気に入り整理アプリ
Streamlit UI
"""

import os
import streamlit as st
from organizer import BookmarkOrganizer

st.set_page_config(
    page_title="Safari お気に入り整理AI",
    page_icon="⭐",
    layout="wide"
)

st.title("⭐ Safari お気に入り整理AI")
st.caption("ClaudeがSafariのお気に入りを自動でカテゴリ分類します")

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        help="未入力の場合はデモモードで分類します（お気に入りの読み込みは実行されます）"
    )
    extra = st.text_area(
        "追加指示（任意）",
        placeholder="例：「仕事関連」と「プライベート」で大きく2グループに分けてください",
        height=100
    )
    st.divider()
    st.markdown("**デモモード**: APIキー未入力時はサンプルデータで分類します")

organizer = BookmarkOrganizer(api_key=api_key if api_key else None)

if organizer.is_demo_mode:
    st.info("🎭 デモモードで動作中（APIキーを入力するとClaudeが実際に分類します）")

# Step 1: フォルダ選択 & お気に入り読み込み
st.subheader("Step 1：読み込むフォルダを選択する")

# フォルダ一覧を取得（デモモードでも実行）
if "folder_names" not in st.session_state:
    with st.spinner("フォルダ一覧を取得中..."):
        names, err = organizer.get_folder_names()
        st.session_state["folder_names"] = names
        st.session_state["folder_error"] = err

folder_names = st.session_state["folder_names"]

if st.session_state.get("folder_error"):
    st.error(f"フォルダ取得エラー: {st.session_state['folder_error']}")

if folder_names:
    # デフォルトを「お気に入り」系のフォルダに設定
    FAVORITES_KEYWORDS = ["お気に入り", "Favorites", "BookmarksBar"]
    default_idx = 0
    for i, name in enumerate(folder_names):
        if any(kw in name for kw in FAVORITES_KEYWORDS):
            default_idx = i
            break

    selected_folder = st.selectbox(
        "フォルダ",
        options=["すべて"] + folder_names,
        index=default_idx + 1 if default_idx < len(folder_names) else 0,
        help="「すべて」を選ぶと全フォルダのお気に入りを対象にします"
    )
    target_folder = None if selected_folder == "すべて" else selected_folder
else:
    st.warning("フォルダ一覧を取得できませんでした。「すべて」で読み込みます。")
    target_folder = None

if st.button("📂 お気に入りを読み込む", type="primary"):
    with st.spinner("読み込み中..."):
        try:
            bookmarks = organizer.load_bookmarks(target_folder=target_folder)
            st.session_state["bookmarks"] = bookmarks
            st.session_state["categorized"] = None
        except PermissionError as e:
            st.error(str(e))
            st.stop()

if "bookmarks" in st.session_state and st.session_state["bookmarks"]:
    bookmarks = st.session_state["bookmarks"]
    st.success(f"✅ {len(bookmarks)} 件のお気に入りを読み込みました")

    with st.expander("読み込んだお気に入り一覧を確認する"):
        for b in bookmarks:
            folder_label = f"　`{b['folder']}`" if b.get("folder") else ""
            st.markdown(f"- **{b['title']}** — `{b['url']}`{folder_label}")

    st.divider()

    # Step 2: 分類実行
    st.subheader("Step 2：AIで分類する")

    if st.button("🤖 Claudeで分類する", type="primary"):
        with st.spinner("Claudeが分類中...（数秒かかります）"):
            try:
                categorized = organizer.categorize(bookmarks, extra_instruction=extra)
                st.session_state["categorized"] = categorized
            except Exception as e:
                st.error(f"分類中にエラーが発生しました: {e}")

if "categorized" in st.session_state and st.session_state["categorized"]:
    categorized = st.session_state["categorized"]

    st.success(f"✅ {len(categorized)} カテゴリに分類しました")
    st.divider()

    # Step 3: 結果表示
    st.subheader("Step 3：分類結果を確認する")

    cols = st.columns(3)
    for i, (category, items) in enumerate(categorized.items()):
        with cols[i % 3]:
            st.markdown(f"### {category}（{len(items)}件）")
            for item in items:
                st.markdown(f"- [{item['title']}]({item['url']})")

    st.divider()

    # Step 4: エクスポート
    st.subheader("Step 4：エクスポート")

    export_path = os.path.expanduser("~/Desktop/organized_bookmarks.html")
    if st.button("💾 HTMLとして書き出す（デスクトップに保存）"):
        try:
            path = organizer.export_html(categorized, export_path)
            st.success(f"✅ デスクトップに保存しました: `{path}`")
            st.info("Safariで開き、「ファイル → ブックマークを読み込む」でインポートできます")
        except Exception as e:
            st.error(f"書き出しエラー: {e}")
