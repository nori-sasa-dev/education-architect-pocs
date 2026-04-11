import io

# ページごとのデモ用背景色（絵本らしい淡い色・5ページ分）
DEMO_COLORS = [
    (255, 245, 220),   # あたたかいクリーム色
    (220, 240, 255),   # やさしい水色
    (220, 255, 230),   # やわらかい緑色
    (255, 230, 245),   # やわらかいピンク
    (245, 240, 210),   # やさしいきみどり
]

# ページごとのデモ用テキスト（絵柄の代わり）
DEMO_LABELS = [
    "🐛  見つけた",
    "👀  のぞいた",
    "🔵  まるまった",
    "🏠  おうち？",
    "👋  また、あおう",
]

# 挿絵生成の共通スタイル指示
IMAGE_STYLE = (
    "soft watercolor illustration, children's picture book style, "
    "warm and gentle colors, minimal detail, dreamy atmosphere, "
    "white background, simple and pure"
)


def _create_demo_image(page_index: int) -> bytes:
    """Pillowでデモ用プレースホルダー画像を生成してbytesで返す"""
    from PIL import Image, ImageDraw, ImageFont

    color = DEMO_COLORS[page_index % len(DEMO_COLORS)]
    label = DEMO_LABELS[page_index % len(DEMO_LABELS)]

    # 512x512の単色画像を作成
    img = Image.new("RGB", (512, 512), color=color)
    draw = ImageDraw.Draw(img)

    # 中央にラベルを描画（デフォルトフォント使用）
    draw.text((256, 256), label, fill=(100, 100, 100), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_illustration(prompt: str, page_index: int, openai_api_key: str = None) -> str | bytes:
    """挿絵を生成して返す。
    APIキー未設定時はPillowで生成したbytesを返す。
    APIキー設定時はDALL-E 3で生成したURLを返す。
    """
    if not openai_api_key:
        # デモモード：Pillowでプレースホルダー画像を生成
        return _create_demo_image(page_index)

    from openai import OpenAI
    client = OpenAI(api_key=openai_api_key)

    # 絵本スタイルを付加
    full_prompt = f"{prompt}, {IMAGE_STYLE}"

    response = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return response.data[0].url
