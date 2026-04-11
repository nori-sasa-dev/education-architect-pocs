import os
import io
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from agents.story_agent import StoryAgent, MAX_TURNS
from core.image_generator import generate_illustration
from core.narrator import text_to_speech
from core.music_selector import get_bgm_path

load_dotenv()

# ============================
# ページ設定
# ============================
st.set_page_config(
    page_title="WonderSnap Book",
    page_icon="📖",
    layout="centered",
)

# ============================
# 子ども向けCSS
# ============================
st.markdown("""
<style>
/* 背景：クリーム色 + かわいいドット柄 */
.stApp {
    background-color: #FFF8F0;
    background-image:
        radial-gradient(circle, #FFD6A5 1.5px, transparent 1.5px),
        radial-gradient(circle, #FADADD 1px, transparent 1px);
    background-size: 28px 28px, 14px 14px;
    background-position: 0 0, 7px 7px;
}

/* 全テキストを濃く */
.stApp, .stApp p, .stApp div, .stApp span, .stApp label {
    color: #1A1A1A !important;
}

/* ボタンを大きく・丸く */
.stButton > button {
    font-size: 1.2rem !important;
    padding: 0.7rem 2rem !important;
    border-radius: 50px !important;
    font-weight: bold !important;
    border: 2px solid #CCC !important;
    color: #1A1A1A !important;
    transition: transform 0.1s;
}
.stButton > button:hover {
    transform: scale(1.03);
}

/* プライマリボタン：オレンジ */
.stButton > button[kind="primary"] {
    background-color: #FF8C42 !important;
    color: white !important;
    border: none !important;
}

/* テキスト入力を大きく */
.stTextInput input {
    font-size: 1.2rem !important;
    border-radius: 20px !important;
    border: 2px solid #FFD6A5 !important;
    padding: 0.5rem 1rem !important;
    color: #1A1A1A !important;
}

/* 見出し */
h1, h2, h3 {
    font-family: sans-serif;
    color: #2C1A0E !important;
}

/* サイドバー */
[data-testid="stSidebar"] {
    background-color: #FFF0D6;
}
[data-testid="stSidebar"] * {
    color: #1A1A1A !important;
}

/* トップヘッダーを非表示 */
[data-testid="stHeader"] {
    background-color: #FFF8F0 !important;
}
header[data-testid="stHeader"] * {
    color: #1A1A1A !important;
}

/* ファイルアップローダーを明るく */
[data-testid="stFileUploader"] {
    background-color: #FFFFFF !important;
}
[data-testid="stFileUploaderDropzone"] {
    background-color: #FFFFFF !important;
    border: 2px dashed #FFB347 !important;
    border-radius: 15px !important;
    color: #1A1A1A !important;
}
[data-testid="stFileUploaderDropzone"] * {
    color: #1A1A1A !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #FF8C42 !important;
    color: white !important;
    border-radius: 20px !important;
    border: none !important;
}

/* Streamlit全体のdark要素を明るくする */
.stApp [class*="dark"] {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}

/* audio_input も明るく */
[data-testid="stAudioInput"] {
    background-color: #FFF0D6 !important;
    border-radius: 15px !important;
    border: 2px solid #FFD6A5 !important;
}

/* AIの問いかけをカードっぽく */
.wonder-question {
    background-color: rgba(255, 240, 214, 0.9);
    border-left: 5px solid #FF8C42;
    border-radius: 20px;
    padding: 1rem 1.5rem;
    font-size: 1.6rem;
    font-weight: bold;
    color: #7B3F00;
    margin: 1rem 0;
    font-family: "Hiragino Maru Gothic ProN", "rounded-mplus-1p", sans-serif;
    letter-spacing: 0.05em;
}

/* 子どもの発言 */
.child-answer {
    background-color: rgba(232, 244, 253, 0.9);
    border-radius: 20px;
    padding: 0.8rem 1.2rem;
    font-size: 1.3rem;
    color: #1A4A6B;
    margin: 0.5rem 0 0.5rem 2rem;
    font-family: "Hiragino Maru Gothic ProN", "rounded-mplus-1p", sans-serif;
}

/* 絵本ページのテキスト */
.book-text {
    font-size: 2.2rem;
    text-align: center;
    line-height: 2;
    color: #7B3F00;
    font-weight: bold;
    padding: 1.5rem;
    font-family: "Hiragino Maru Gothic ProN", "rounded-mplus-1p", sans-serif;
    background-color: rgba(255, 255, 255, 0.75);
    border-radius: 20px;
    letter-spacing: 0.08em;
}

/* 移行メッセージ */
.transition-message {
    text-align: center;
    font-size: 2rem;
    color: #FF8C42;
    font-weight: bold;
    padding: 2rem;
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ページめくりアニメーション */
@keyframes slideInFromRight {
    from { opacity: 0; transform: translateX(60px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes slideInFromLeft {
    from { opacity: 0; transform: translateX(-60px); }
    to   { opacity: 1; transform: translateX(0); }
}
.page-next {
    animation: slideInFromRight 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.page-prev {
    animation: slideInFromLeft 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 絵本ページ全体のラッパー（影をつけて本っぽく） */
.book-page {
    background-color: rgba(255, 255, 255, 0.92);
    border-radius: 20px;
    padding: 1rem;
    box-shadow: 4px 4px 16px rgba(0,0,0,0.12), -2px 0px 8px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ============================
# APIキー読み込み
# ============================
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

agent = StoryAgent(api_key=anthropic_api_key)

# ============================
# セッション初期化
# ============================
if "phase" not in st.session_state:
    st.session_state.phase = "upload"   # upload / conversation / ready / generating / book
if "photo_bytes" not in st.session_state:
    st.session_state.photo_bytes = None
if "photo_description" not in st.session_state:
    st.session_state.photo_description = ""
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "wonder_words" not in st.session_state:
    st.session_state.wonder_words = []
if "book" not in st.session_state:
    st.session_state.book = None
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "audio_cache" not in st.session_state:
    st.session_state.audio_cache = {}
if "input_key" not in st.session_state:
    st.session_state.input_key = 0  # テキスト入力をリセットするためのカウンター
if "page_direction" not in st.session_state:
    st.session_state.page_direction = "next"  # ページめくり方向（next / prev）
if "bgm_path" not in st.session_state:
    st.session_state.bgm_path = None  # 絵本フェーズで固定する1曲

# ============================
# サイドバー
# ============================
with st.sidebar:
    st.markdown("## 📖 WonderSnap Book")
    st.caption("きょうの はっけんを、えほんにしよう")

    if agent.is_demo_mode:
        st.warning("デモモードで うごいています")
        with st.expander("APIキーの せっていかた"):
            st.code(
                "# .envファイルを つくる\n"
                "ANTHROPIC_API_KEY=sk-ant-xxxxx\n"
                "OPENAI_API_KEY=sk-xxxxx\n"
                "ELEVENLABS_API_KEY=xxxxx",
                language="bash",
            )
    else:
        st.success("つながっているよ ✓")

    st.divider()

    if st.button("🔄 はじめから やりなおす", use_container_width=True):
        for key in ["phase", "photo_bytes", "photo_description", "conversation",
                    "wonder_words", "book", "current_page", "audio_cache", "bgm_path"]:
            del st.session_state[key]
        st.rerun()

# ============================
# フェーズ1: 写真アップロード
# ============================
if st.session_state.phase == "upload":
    st.markdown("## 📷 なにか みつけたの？")
    st.markdown("きょう みつけたものの しゃしんを みせてね 🌿")
    st.markdown("")

    uploaded = st.file_uploader(
        "写真をえらぶ",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )

    if uploaded:
        image = Image.open(uploaded)

        # 長辺を1024pxに制限してリサイズ（メモリ節約・Safari対策）
        max_size = 1024
        image.thumbnail((max_size, max_size), Image.LANCZOS)

        # RGBに変換（PNG/RGBA対応）
        if image.mode != "RGB":
            image = image.convert("RGB")

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        image_bytes = buf.getvalue()

        st.image(image, use_container_width=True)
        st.markdown("")

        if st.button("この しゃしんで えほんを つくる ✨", use_container_width=True, type="primary"):
            st.session_state.photo_bytes = image_bytes
            with st.spinner("しゃしんを みています..."):
                st.session_state.photo_description = agent.analyze_photo(image_bytes)
            st.session_state.phase = "conversation"
            st.rerun()

# ============================
# フェーズ2: 会話（最大MAX_TURNSターン）
# ============================
elif st.session_state.phase == "conversation":
    st.markdown("## 💬 おはなしして みよう")

    # 写真を小さく表示
    if st.session_state.photo_bytes:
        image = Image.open(io.BytesIO(st.session_state.photo_bytes))
        st.image(image, width=180)

    st.markdown("")

    # これまでの会話を表示
    for msg in st.session_state.conversation:
        if msg["role"] == "ai":
            st.markdown(
                f'<div class="wonder-question">🌿 {msg["text"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="child-answer">👦 {msg["text"]}</div>',
                unsafe_allow_html=True,
            )

    turn = len([m for m in st.session_state.conversation if m["role"] == "ai"])

    # 最初の問いかけを出す
    if not st.session_state.conversation:
        question = agent.get_question(
            turn=0,
            photo_description=st.session_state.photo_description,
            conversation_so_far="",
        )
        st.session_state.conversation.append({"role": "ai", "text": question})
        st.rerun()

    # 「絵本にしよう」が来たら移行フェーズへ
    last_ai_msg = next(
        (m["text"] for m in reversed(st.session_state.conversation) if m["role"] == "ai"), ""
    )
    if "絵本にしよう" in last_ai_msg or turn >= MAX_TURNS:
        st.session_state.phase = "ready"
        st.rerun()

    # テキスト入力：Enterで送信（on_changeで即時処理）
    input_key = f"child_text_{st.session_state.input_key}"

    def on_text_submit():
        val = st.session_state.get(input_key, "").strip()
        if val:
            st.session_state.pending_answer = val

    # 入力エリア
    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        audio_input = st.audio_input("🎤 こえで はなす")

    with col2:
        st.text_input(
            "✏️ もじで かく（Enterで おくれるよ）",
            placeholder="なんでも いいよ",
            key=input_key,
            on_change=on_text_submit,
        )

    # 「スキップ」ボタン（答えられなくてもOK）
    st.markdown("")
    if st.button("こたえなくて いいや → えほんにしよう", use_container_width=False):
        st.session_state.phase = "ready"
        st.rerun()

    child_answer = None

    # 音声入力の処理
    if audio_input:
        if openai_api_key:
            from openai import OpenAI
            oai = OpenAI(api_key=openai_api_key)
            audio_bytes = audio_input.read()
            transcript = oai.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio_bytes, "audio/wav"),
                language="ja",
            )
            child_answer = transcript.text
        else:
            child_answer = "（おんせいにゅうりょく・デモ）"

    # テキスト入力（Enterで送信）の処理
    elif st.session_state.get("pending_answer"):
        child_answer = st.session_state.pop("pending_answer")

    if child_answer:
        st.session_state.conversation.append({"role": "child", "text": child_answer})
        st.session_state.wonder_words.append(child_answer)
        # キーをインクリメントしてテキストボックスをリセット
        st.session_state.input_key += 1

        conversation_text = "\n".join(
            [f"{'AI' if m['role'] == 'ai' else '子ども'}: {m['text']}"
             for m in st.session_state.conversation]
        )
        next_question = agent.get_question(
            turn=len(st.session_state.wonder_words),
            photo_description=st.session_state.photo_description,
            conversation_so_far=conversation_text,
        )
        st.session_state.conversation.append({"role": "ai", "text": next_question})
        st.rerun()

# ============================
# フェーズ2.5: 絵本化への移行メッセージ
# ============================
elif st.session_state.phase == "ready":
    st.markdown("")
    st.markdown(
        '<div class="transition-message">📖 きょうの はっけんを<br>えほんに してみよう！</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        if st.button("✨ えほんを つくる ✨", use_container_width=True, type="primary"):
            st.session_state.phase = "generating"
            st.rerun()

# ============================
# フェーズ3: 絵本生成中
# ============================
elif st.session_state.phase == "generating":
    st.markdown("## 📖 えほんを つくっているよ...")
    st.markdown("")

    with st.status("えほんを つくっています...", expanded=True) as status:
        st.write("ものがたりを かんがえています... 🖊️")
        wonder_text = "、".join(st.session_state.wonder_words) if st.session_state.wonder_words else ""
        book = agent.generate_book(
            photo_description=st.session_state.photo_description,
            wonder_words=wonder_text,
        )

        st.write("えを かいています... 🎨")
        for i, page in enumerate(book["pages"]):
            image_data = generate_illustration(
                prompt=page["image_prompt"],
                page_index=i,
                openai_api_key=openai_api_key,
            )
            book["pages"][i]["image_data"] = image_data

        st.write("こえを つくっています... 🎙️")
        for i, page in enumerate(book["pages"]):
            audio = text_to_speech(
                text=page["text"],
                elevenlabs_api_key=elevenlabs_api_key,
            )
            st.session_state.audio_cache[i] = audio

        st.session_state.book = book
        status.update(label="できたよ！ 🎉", state="complete")

    st.session_state.phase = "book"
    st.rerun()

# ============================
# フェーズ4: 絵本ビューア
# ============================
elif st.session_state.phase == "book":
    book = st.session_state.book
    pages = book["pages"]
    current = st.session_state.current_page

    # BGM再生（絵本フェーズ開始時に1曲を固定し、autoplayで自動再生）
    if st.session_state.bgm_path is None:
        st.session_state.bgm_path = get_bgm_path()
    if st.session_state.bgm_path:
        import base64
        with open(st.session_state.bgm_path, "rb") as f:
            bgm_b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<audio autoplay loop style="display:none">'
            f'<source src="data:audio/mp3;base64,{bgm_b64}" type="audio/mp3">'
            f'</audio>',
            unsafe_allow_html=True,
        )

    # タイトル
    st.markdown(f"# 📖 {book['title']}")

    # ページ数インジケーター（ドット）
    dots = ""
    for i in range(len(pages)):
        dots += "🟠 " if i == current else "⚪ "
    st.markdown(f"<p style='text-align:center; font-size:1.2rem;'>{dots}</p>", unsafe_allow_html=True)

    # ページ方向に応じたスライドアニメーション
    anim_class = "page-next" if st.session_state.page_direction == "next" else "page-prev"
    page = pages[current]
    image_data = page.get("image_data") or page.get("image_url")

    # アニメーション付きラッパーで挿絵＋テキストを包む
    st.markdown(f'<div class="book-page {anim_class}">', unsafe_allow_html=True)
    if image_data:
        st.image(image_data, use_container_width=True)
    st.markdown(
        f'<div class="book-text">{page["text"].replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ナレーション
    audio = st.session_state.audio_cache.get(current)
    if audio:
        st.audio(audio, format="audio/mpeg")
    else:
        st.caption("🎧 APIキーを設定すると音声が流れます")

    # ページ操作
    st.markdown("---")
    col_prev, col_spacer, col_next = st.columns([1, 2, 1])

    with col_prev:
        if current > 0:
            if st.button("← まえ", use_container_width=True):
                st.session_state.page_direction = "prev"
                st.session_state.current_page -= 1
                st.rerun()

    with col_next:
        if current < len(pages) - 1:
            if st.button("つぎ →", use_container_width=True, type="primary"):
                st.session_state.page_direction = "next"
                st.session_state.current_page += 1
                st.rerun()
        else:
            st.markdown("")
            st.success("🎉 おわり！")
            if st.button("もう一度 つくる ✨", use_container_width=True, type="primary"):
                for key in ["phase", "photo_bytes", "photo_description", "conversation",
                            "wonder_words", "book", "current_page", "audio_cache", "page_direction", "bgm_path"]:
                    del st.session_state[key]
                st.rerun()
