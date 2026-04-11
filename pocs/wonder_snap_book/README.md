# WonderSnap Book 📖

子どもが撮った写真をもとに、AIとの会話から絵本を自動生成するアプリ。

**デモ**: https://education-architect-pocs-4myvg8hjyyymmmkdjzhj6r.streamlit.app

---

## 概要

1. 子どもが「見つけたもの」の写真をアップロード
2. AIが写真を解析し、やさしいひらがなで問いかける（最大5往復）
3. 子どもの言葉をもとに、5ページの絵本を自動生成
4. 挿絵・ナレーション・BGM付きで読める

---

## 機能

| 機能 | 詳細 |
|------|------|
| 写真解析 | Claude Vision APIで写真の内容を理解 |
| 会話問いかけ | ひらがなのみ・最大5往復・音声入力にも対応 |
| 絵本生成 | 5ページ構成（出会い→近づく→感じる→想像→余韻） |
| 挿絵 | DALL-E 3で水彩タッチのイラストを生成 |
| ナレーション | ElevenLabsで各ページを読み上げ |
| BGM | アンビエント音楽をループ再生 |

---

## セットアップ

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env にAPIキーを設定

streamlit run app.py
```

### 必要なAPIキー

| キー | 用途 | 未設定時 |
|------|------|---------|
| `ANTHROPIC_API_KEY` | 写真解析・会話・絵本テキスト生成 | デモモード |
| `OPENAI_API_KEY` | 挿絵生成（DALL-E 3）・音声入力（Whisper） | プレースホルダー画像 |
| `ELEVENLABS_API_KEY` | ナレーション音声合成 | 音声なし |

---

## 技術スタック

- Python 3.12 / Streamlit
- Claude API（`claude-sonnet-4-6`）— Vision・会話・絵本生成
- DALL-E 3（OpenAI）— 挿絵生成
- ElevenLabs — ナレーション
- Whisper（OpenAI）— 音声入力
