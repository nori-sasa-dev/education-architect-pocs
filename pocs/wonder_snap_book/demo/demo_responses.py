# デモモード用固定データ
# APIキー未設定時にこのデータを使用する

# 会話フェーズの問いかけ（親のような口調・深さを段階的に）
DEMO_QUESTIONS = [
    "なにを みつけたの？",
    "どんな きもちが した？",
    "さわったら、どんな かんじかな？",
    "もし はなしかけたら、なんて いうかな？",
    "また あいたい？",
]

# 5ページ絵本の固定データ
DEMO_BOOK = {
    "title": "ちいさな、まるい、せかい",
    "pages": [
        {
            "text": "見つけた。",
            "image_prompt": "a tiny round bug on a green leaf, soft watercolor, children's picture book style, warm colors",
        },
        {
            "text": "そっと、のぞいた。",
            "image_prompt": "a child's eye looking closely at a tiny bug with wonder, soft watercolor, picture book illustration",
        },
        {
            "text": "まるまった。\nぎゅっと。",
            "image_prompt": "a pill bug curled into a perfect ball, surrounded by soft golden light, watercolor, picture book style",
        },
        {
            "text": "もしかして、\nおうちの なかに いたのかな。",
            "image_prompt": "a tiny cozy home inside a round ball, dreamy watercolor illustration, children's book style",
        },
        {
            "text": "また、あおう。",
            "image_prompt": "a child waving goodbye to a tiny bug on a leaf, soft watercolor, warm and gentle, picture book",
        },
    ],
}

# 写真解析の固定結果
DEMO_PHOTO_ANALYSIS = "ダンゴムシが葉の上にいます。丸まっています。"
