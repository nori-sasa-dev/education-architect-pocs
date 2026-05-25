# Redmine Ticket AI

Redmineのチケットデータ（故障管理・課題管理・レビュー指摘）をAIで分析するツール。

## 機能

| ページ | 概要 | 状態 |
|--------|------|------|
| 📥 データ管理 | CSVインポート / サンプルデータ読み込み / 統計表示 | Phase 0 ✅ |
| 🔍 類似故障検索 | ChromaDB ベクトル類似検索 + 解決策サジェスト | Phase 1a 🚧 |
| 📋 機能カルテ | 機能単位の故障パターン集約 + サマリー生成 | Phase 1b 🚧 |

## セットアップ

```bash
cd pocs/redmine_ticket_ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
streamlit run app.py
```

## CSVフォーマット

Redmineからエクスポートしたチケット一覧CSVに以下のカラムが必要です。

| カラム名 | 説明 |
|---------|------|
| id | チケットID（整数） |
| ticket_type | 故障管理 / 課題管理 / レビュー指摘 |
| feature | 機能名 |
| title | チケットタイトル |
| description | 説明・現象 |
| root_cause | 真の原因 |
| resolution | 解決策 |
| review_comment | レビュー指摘コメント |
| status | ステータス |
| created_at | 作成日（YYYY-MM-DD） |

## 技術スタック

- Python 3.12 / Streamlit
- SQLite（メタデータ）
- ChromaDB（ベクトル検索）
- sentence-transformers: paraphrase-multilingual-mpnet-base-v2
- Claude API（解決策サジェスト・機能サマリー生成）
