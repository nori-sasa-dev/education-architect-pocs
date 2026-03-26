# Career Team AI

ライフデザインをサポートする4エージェント構成のマルチエージェントBot。

## 概要

Coach・Mirror・Scout・Strategist の4つのAIエージェントが協働し、キャリアの振り返り・自己探索・市場調査・戦略設計を一貫してサポートします。セッション履歴はSQLiteに保存され、過去の対話を参照しながら継続的なコーチングが可能です。

## エージェント構成

| エージェント | 役割 |
|------------|------|
| Coach | セッション全体の進行・行動促進 |
| Mirror | 価値観・強みの自己探索支援 |
| Scout | キャリア市場の情報収集・調査 |
| Strategist | キャリア戦略の設計・ロードマップ作成 |

## 機能

- 4エージェントの協調セッション
- セッション履歴の保存・参照（SQLite）
- レポートのJSON/CSVエクスポート

## 技術スタック

- Python 3.12
- Streamlit
- Claude API（`claude-sonnet-4-6`）
- SQLite

## セットアップ

```bash
cd pocs/career_team
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
streamlit run app.py
```
