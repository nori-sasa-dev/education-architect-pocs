# InnerLens

テニスの自己観察・振り返りジャーナルアプリ。インナーゲーム理論に基づくAIフィードバック付き。

## 概要

「インナーゲーム」の考え方をベースに、テニスの練習・試合を内側から振り返るジャーナルアプリです。動画フレームのポーズ解析とAIによる問いかけを組み合わせ、技術だけでなくメンタル・感覚の自己観察をサポートします。

## 機能

- 練習動画のフレーム抽出・ポーズ解析
- インナーゲーム式の振り返り問いかけ（AIフィードバック）
- ジャーナル記録・履歴の保存（SQLite）
- セッション削除・管理

## 技術スタック

- Python 3.12
- Streamlit
- Claude API（`claude-sonnet-4-6`）
- SQLite

## セットアップ

```bash
cd pocs/inner_lens
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
streamlit run app.py
```

## デモモード

`ANTHROPIC_API_KEY` を設定しなくても起動できます。固定の問いかけでUIと流れを確認できます。
