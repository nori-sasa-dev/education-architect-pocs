# 暗黙知継承プラットフォーム

組織の暗黙知を対話で引き出し、蓄積・検索できるプラットフォーム。

## 概要

熟練者が持つ「なんとなくわかること」「言葉にしにくいノウハウ」を、AIとの対話インタビューで形式知化します。蓄積した知識はカテゴリ分類・キーワード検索で活用できます。

## 機能

- AIインタビューによる暗黙知の引き出し・構造化
- 知識のカテゴリ分類・タグ付け
- キーワード検索（SQLite）
- 知識の編集・削除・統計表示
- APIキー未設定時のデモモード対応

## 技術スタック

- Python 3.12
- Streamlit
- Claude API（`claude-sonnet-4-6`）
- SQLite

## セットアップ

```bash
cd pocs/tacit_knowledge_platform
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
streamlit run app.py
```

## デモモード

`ANTHROPIC_API_KEY` を設定しなくても起動できます。固定応答でUIと流れを確認できます。
