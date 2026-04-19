# Education Architect POCs

**教育 × コーチング × AI** の交差点でPOCアプリを開発するポートフォリオ。

「Education Architect（教育アーキテクト）」として独立することを目指し、
アイデアの検証・技術習得・ポートフォリオ構築を目的として開発しています。

---

## POCアプリ一覧

| # | アプリ名 | 概要 | 技術 |
|---|---------|------|------|
| ① | [キャリア探索AI](pocs/skill_inventory_bot/) | 対話を通じてスキル・強み・価値観を引き出し、キャリアの方向性を探索するBot | Python / Streamlit / Claude API |
| ② | [スキル×職種マッピングビジュアライザー](pocs/skill_mapping_visualizer/) | 保有スキルと10職種とのマッチ度をヒートマップ・レーダーチャートで可視化 | Python / Streamlit / Claude API / Plotly |
| ③ | [スキルギャップ分析ツール](pocs/skill_gap_analyzer/) | 目標職種に向けたスキルギャップを分析し、学習ロードマップを自動生成 | Python / Streamlit / Claude API / Plotly |
| ④ | [Career Team AI](pocs/career_team/) | ライフデザインをサポートするマルチエージェントBot | Python / Streamlit / Claude API |
| ⑤ | [InnerLens](pocs/inner_lens/) | テニスの自己観察・振り返りジャーナルアプリ | Python / Streamlit / Claude API |
| ⑥ | [暗黙知継承プラットフォーム](pocs/tacit_knowledge_platform/) | 組織の暗黙知を対話で引き出し・蓄積するプラットフォーム | Python / Streamlit / Claude API |
| ⑦ | [FamilyHub](pocs/family_hub/) | コドモンのメール通知を解析してGoogleカレンダーに自動登録 | Google Apps Script / Claude API |
| ⑧ | [学術テニスコーチングチーム](pocs/tennis_coaching_team/) | 解剖学・脳科学・物理学・心理学・栄養学の専門家AIが協働するコーチングBot | Python / Claude API（マルチエージェント） |
| ⑨ | [BioLens](pocs/bio_lens/) | テニスのフォーム動画をバイオメカニクス的に分析するアプリ | Python / Streamlit / Claude API |
| ⑩ | [WonderSnap Book](pocs/wonder_snap_book/) | 子どもが撮った写真をもとに、AIとの会話から絵本を自動生成するアプリ | Python / Streamlit / Claude API / DALL-E 3 / ElevenLabs |
| ⑪ | [Safari Bookmark Organizer](pocs/safari_bookmark_organizer/) | SafariのブックマークをClaudeが自動でカテゴリ分類し、整理済みHTMLで書き出すアプリ | Python / Streamlit / Claude API / plistlib |

---

## 技術スタック

- **言語**: Python 3.12
- **UI**: Streamlit
- **AI**: Claude API（`claude-sonnet-4-6` / `claude-opus-4-6`）
- **画像生成**: DALL-E 3（OpenAI）
- **音声合成**: ElevenLabs
- **音声入力**: Whisper（OpenAI）
- **その他**: Google Apps Script

---

## セットアップ

各アプリのディレクトリに移動して、以下を実行してください。

```bash
# 仮想環境の作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存ライブラリのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定

# アプリ起動（Streamlitアプリの場合）
streamlit run app.py
```

---

## 作者

**Nori Sasagawa** — Education Architect を目指して開発中。

教育 × コーチング × AI の掛け合わせで、学びの体験を再設計することがビジョンです。

- GitHub: [@nori-sasa-dev](https://github.com/nori-sasa-dev)
