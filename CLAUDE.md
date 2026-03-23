# Education Architect POC 開発プロジェクト

## プロジェクト概要

Education Architect（教育アーキテクト）を目指す笹川典孝の個人POC開発プロジェクト。
AI x 教育 x 経営 の3軸を掛け合わせたプロダクトを開発し、ポートフォリオを構築する。

- **開発リソース**: 月36時間（自己実現時間73時間の半分。残りは中小企業診断士の学習）
- **技術レベル**: Python 初〜中級
- **ビジョン（正典）**: `/Users/sasagawanoritaka/Documents/AI_Projects/05_career/vision/vision.md`

## POCアプリ一覧

| # | アプリ名 | 状態 | ディレクトリ |
|---|---------|------|------------|
| ① | スキル棚卸しチャットボット | MVP完成（デモモード） | `pocs/skill_inventory_bot/` |
| ② | スキル × 職種マッピングビジュアライザー | 未着手 | - |
| ③ | スキルギャップ分析ツール | 未着手 | - |
| ④ | Career Team AI（ライフデザインコーチBot） | MVP完成（実API動作確認済み） | `pocs/career_team/` |
| ⑤ | InnerLens（テニス自己観察ジャーナル） | MVP完成（実API動作確認済み） | `pocs/inner_lens/` |
| ⑥ | 暗黙知継承プラットフォーム | MVP完成（デモモード） | `pocs/tacit_knowledge_platform/` |
| ⑦ | FamilyHub（コドモンメール→カレンダー自動登録） | MVP完成（GAS・実API動作確認済み） | `pocs/family_hub/` |

## 7エージェントチーム

開発プロセスの各フェーズを担当するAIエージェントをスラッシュコマンドとして利用できる。

| コマンド | エージェント名 | 担当フェーズ | 使い時 |
|---------|-------------|------------|--------|
| `/visionary` | Visionary | 企画 | 新しいアイデアが出たとき、方向性に迷ったとき |
| `/researcher` | Researcher | 企画・要件定義 | 競合調査、技術トレンド調査が必要なとき |
| `/product-designer` | Product Designer | 要件定義・設計 | ペルソナ設計、課題仮説、UX設計をするとき |
| `/architect` | Architect | 設計 | 技術選定、DB設計、ディレクトリ構成を決めるとき |
| `/dev` | Developer | 実装 | コーディング、バグ修正、機能追加をするとき |
| `/reviewer` | Reviewer | テスト・評価 | 実装後のレビュー、品質チェックをするとき |
| `/scribe` | Scribe | 全フェーズ横断 | セッション終了時に記録を自動生成するとき |

## 標準的な開発セッションフロー

```
セッション開始
  │
  ├→ /visionary（ビジョン整合チェック）
  │
  ├→ /researcher または /product-designer（企画・要件定義）
  │
  ├→ /architect（設計）
  │
  ├→ /dev（実装）
  │
  ├→ /reviewer（レビュー）
  │
  └→ /scribe（セッション記録を自動生成して終了）
```

※ 全コマンドを毎回使う必要はない。必要なフェーズだけ使えばよい。

## キャリアデザイン支援チーム

キャリア戦略の検討・振り返り・記録を支援するAIエージェント群。開発チームとは独立して利用できる。

| コマンド | エージェント名 | 担当 | 使い時 |
|---------|-------------|------|--------|
| `/mirror` | Mirror | 自己探索 | 価値観・強みを言語化したいとき |
| `/scout` | Scout | 市場調査 | キャリア関連の市場動向を調べたいとき |
| `/strategist` | Strategist | 戦略設計 | ロードマップ見直し、リソース配分を考えるとき |
| `/coach` | Coach | 行動促進 | 月次振り返り、意思決定支援が欲しいとき |
| `/connector` | Connector | ブランディング | ポートフォリオ戦略、発信計画を立てるとき |
| `/horizon` | Horizon | AI動向分析 | AI進化がキャリア戦略に与える影響を評価するとき |
| `/chronicle` | Chronicle | 記録 | キャリアの決断や気づきを記録するとき |

### キャリアセッションフロー例

```
キャリアセッション
  │
  ├→ /mirror（自己探索・価値観の確認）
  │
  ├→ /scout または /horizon（市場情報・AI動向の収集）
  │
  ├→ /strategist（戦略の見直し）
  │
  ├→ /coach（行動計画・振り返り）
  │
  ├→ /connector（発信・ブランディング計画）
  │
  └→ /chronicle（気づき・決断の記録）
```

※ 全コマンドを毎回使う必要はない。必要なフェーズだけ使えばよい。

## ディレクトリ構成

```
02_development/
├── CLAUDE.md                  # 本ファイル（プロジェクト共通コンテキスト）
├── .claude/
│   └── commands/              # 14のエージェントコマンド（開発7 + キャリア7）
├── planning/
│   ├── sessions/              # セッション記録（/scribe が自動生成）
│   └── validation/            # 課題検証ドキュメント
├── pocs/                      # POCアプリ群
│   ├── skill_inventory_bot/   # App①
│   ├── tacit_knowledge_platform/ # App⑥
│   ├── career_ai/             # 参考コード（初期プロトタイプ）
│   └── game_center/           # ゲームPOC
├── playground/                # 技術検証・実験用
└── products/                  # 将来のプロダクト化用

05_career/                        # キャリア関連（02_development の外）
├── vision/
│   └── vision.md              # ビジョン（正典）
└── journal/                   # キャリアジャーナル（/chronicle が生成）
```

## 技術スタック

- **言語**: Python 3.12
- **仮想環境**: venv（各アプリ独立）
- **UI**: Streamlit
- **AI**: Claude API（`claude-sonnet-4-6`）
- **DB**: SQLite（LIKE検索。FTS5は日本語非対応のため不採用）
- **開発環境**: Claude Code / Cursor

## 重要なコンテキスト

- **session02の問い直し**: 「スキル言語化は入口に過ぎない。本当に作りたいのは自己探索・ビジョン形成の体験」。ソリューション先行にならないこと。
- **デモモード設計**: APIキー未設定時は `DEMO_RESPONSES` リストから固定応答を返す。`is_demo_mode` プロパティで判定。
- **エージェントクラスパターン**: `XxxAgent(api_key=None)` → `respond(messages, turn)` → `extract_xxx(text)`
- **抽出マーカーパターン**: `[MARKER_NAME]` + ` ```json ``` ` ブロックで構造化データを返す

## コーディング規約

- コメントは日本語で記述する
- 新アプリは既存のデモモードパターンを踏襲する
- `.env.example` を必ず用意する（APIキーのテンプレート）
- 各アプリは独立した venv を持つ
