# AIできる課？

業務のAI化可能性を診断し、個人・チームのAI活用ロードマップを生成するStreamlitアプリ。

## 機能

### 個人診断（Step 1〜4）
- **Step 1**: 業務カード入力（業務名・詳細・月間件数・1件あたり分数・頻度）＋ PDF/Excel/PPT ファイル読み込み対応
- **Step 2**: Claude APIが3分類に診断
  - 🤖 **完全自動化可能** — 定型・反復・データ処理中心
  - 🤝 **AI増強** — AIがドラフト・分析、人間が最終判断
  - 👤 **人間必須** — 感情・信頼・戦略的判断が核心
- **Step 3**: AI活用ロードマップをGanttチャートで可視化 + Markdownレポートダウンロード
- **Step 4**: 業務別の実装ガイド生成 + チャットでQ&A

### 実装管理（Step 6）
- 未着手 / 進行中 / 完了 のタブ管理
- ステータス変更でプログレスバーをリアルタイム更新

### チームダッシュボード（Step 5）
- 6文字のチームコードで複数メンバーの診断を集約
- カテゴリ分布（ドーナツグラフ）、削減余地Top10、優先着手リスト
- メンバー別サマリー・部署別比較
- 実装ステータスの集計表示

## セットアップ

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定

streamlit run app.py
```

## デモモード

`.env` にAPIキーを設定しなくても起動できます。サンプルデータで全機能を体験できます。

## 技術スタック

| 分類 | 技術 |
|------|------|
| UI | Streamlit |
| AI | Claude API（claude-sonnet-4-6） |
| DB | SQLite（チームデータ永続化） |
| グラフ | Plotly Express |
| ファイル解析 | pypdf / openpyxl / python-pptx |

## ディレクトリ構成

```
ai_dekiru_ka/
├── app.py                  # メインアプリ（Step 1〜6）
├── services/
│   ├── diagnosis_agent.py  # Claude API診断・ガイド・チャット
│   ├── team_db.py          # SQLiteによるチームデータ管理
│   └── file_extractor.py   # PDF/Excel/PPTテキスト抽出
├── data/                   # SQLiteDB（.gitignore対象）
├── requirements.txt
└── .env.example
```
