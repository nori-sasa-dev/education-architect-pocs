# キャリア探索AI

対話を通じてスキル・強み・価値観を引き出し、キャリアの方向性を探索するチャットBot。

## 概要

インタビュー形式の対話セッションを通じて、自分では言語化しにくいスキルや価値観を引き出します。セッション終了後は探索結果をJSON/CSVでエクスポートできます。

## 機能

- フェーズ構成のインタビュー（段階的にスキル・強み・価値観を深掘り）
- リアルタイムでの発見事項の可視化
- 探索結果のJSON/CSVエクスポート
- APIキー未設定時のデモモード対応

## 技術スタック

- Python 3.12
- Streamlit
- Claude API（`claude-sonnet-4-6`）

## セットアップ

```bash
cd pocs/skill_inventory_bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
streamlit run app.py
```

## デモモード

`ANTHROPIC_API_KEY` を設定しなくても起動できます。固定応答でUIと流れを確認できます。
