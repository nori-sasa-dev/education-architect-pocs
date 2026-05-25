# Safari お気に入り整理AI

SafariのブックマークをClaudeが自動でカテゴリ分類し、整理済みHTMLで書き出すStreamlitアプリ。

## 機能

- Safari の `Bookmarks.plist` を読み込み、全お気に入りを一覧表示
- Claude APIがURLとタイトルを解析し、カテゴリを自動分類
- 追加指示（例: 「仕事とプライベートに大きく分けて」）でカスタマイズ
- 整理済みお気に入りをHTML形式でエクスポート
- デモモード対応（APIキー不要）

## セットアップ

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定

streamlit run app.py
```

## 技術スタック

| 分類 | 技術 |
|------|------|
| UI | Streamlit |
| AI | Claude API（claude-sonnet-4-6） |
| ファイル解析 | plistlib（macOS標準ライブラリ） |
