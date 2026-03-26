# Education Architect POCs

**教育 × コーチング × AI** の交差点でPOCアプリを開発するポートフォリオ。

「Education Architect（教育アーキテクト）」として独立することを目指し、
アイデアの検証・技術習得・ポートフォリオ構築を目的として開発しています。

---

## POCアプリ一覧

| # | アプリ名 | 概要 | 技術 |
|---|---------|------|------|
| ① | [キャリア探索AI](pocs/skill_inventory_bot/) | 対話形式でスキルを言語化するチャットBot | Python / Streamlit / Claude API |
| ② | [Career Team AI](pocs/career_team/) | ライフデザインをサポートするマルチエージェントBot | Python / Streamlit / Claude API |
| ③ | [InnerLens](pocs/inner_lens/) | テニスの自己観察・振り返りジャーナルアプリ | Python / Streamlit / Claude API |
| ④ | [暗黙知継承プラットフォーム](pocs/tacit_knowledge_platform/) | 組織の暗黙知を対話で引き出し・蓄積するプラットフォーム | Python / Streamlit / Claude API |
| ⑤ | [FamilyHub](pocs/family_hub/) | コドモンのメール通知を解析してGoogleカレンダーに自動登録 | Google Apps Script / Claude API |
| ⑥ | [学術テニスコーチングチーム](pocs/tennis_coaching_team/) | 解剖学・脳科学・物理学・心理学・栄養学の専門家AIが協働するコーチングBot | Python / Claude API（マルチエージェント） |

---

## 技術スタック

- **言語**: Python 3.12
- **UI**: Streamlit
- **AI**: Claude API（`claude-sonnet-4-6` / `claude-opus-4-6`）
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
