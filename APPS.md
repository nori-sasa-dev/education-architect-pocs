# POC アプリ一覧（単一の情報源 / SoT）

各アプリの状態・ディレクトリ・起動方法。`02_development/CLAUDE.md` からはこのファイルを参照する。

| #   | アプリ名 | 状態 | ディレクトリ |
| --- | ------- | ---- | ---------- |
| ①   | キャリア探索AI | MVP完成（デモモード） | `pocs/skill_inventory_bot/` |
| ②   | スキル × 職種マッピングビジュアライザー | MVP完成（実API動作確認済み） | `pocs/skill_mapping_visualizer/` |
| ③   | スキルギャップ分析ツール | MVP完成（実API動作確認済み） | `pocs/skill_gap_analyzer/` |
| ④   | Career Team AI（ライフデザインコーチBot） | MVP完成（実API動作確認済み） | `pocs/career_team/` |
| ⑤   | InnerLens（テニス自己観察ジャーナル） | MVP完成（実API動作確認済み） | `pocs/inner_lens/` |
| ⑥   | ナレッジブリッジ（旧:暗黙知継承プラットフォーム） | MVP完成（デモモード） | `pocs/tacit_knowledge_platform/` |
| ⑦   | FamilyHub（コドモンメール→カレンダー自動登録） | MVP完成（GAS・実API動作確認済み） | `pocs/family_hub/` |
| ⑧   | 学術テニスコーチングチーム（CLIマルチエージェント） | MVP完成（実API動作確認済み） | `pocs/tennis_coaching_team/` |
| ⑨   | BioLens（テニス姿勢バイオメカニクス分析） | MVP完成（実API動作確認済み） | `pocs/bio_lens/` |
| ⑩   | WonderSnap Book（写真→会話→絵本生成） | MVP完成・デプロイ済み | `pocs/wonder_snap_book/` |
| ⑪   | Safari Bookmark Organizer | MVP完成（実API動作確認済み） | `pocs/safari_bookmark_organizer/` |
| ⑫   | AIできる課？（業務AI化診断） | MVP完成（デモモード・チームDB対応） | `pocs/ai_dekiru_ka/` |
| ⑬   | Redmine Ticket AI | Phase 0〜1b実装済み（CSV取込・類似検索・機能カルテ） | `pocs/redmine_ticket_ai/` |
| ⑭   | マイ・ストレングス（持ち味発見ツール／旧:軌跡 Trace） | MVP完成（デモモード・点→線分析） | `pocs/strength_trace/` |
| ⑮   | テニス・クイックコーチ（試合状況→即時戦術アドバイス） | MVP完成（デモモード・自動パイプライン初作品） | `pocs/tennis_quick_coach/` |
| ⑯   | Courtside（練習前の問いかけ型・自己決定支援） | MVP完成（デモモード／実API未確認・自動パイプライン配線検証作品） | `pocs/courtside/` |

> 参考コード：`pocs/career_ai/`（初期プロトタイプ）、`pocs/game_center/`（ゲームPOC）

## 起動方法

各アプリのディレクトリで以下を実行：

```bash
# 例: InnerLens を起動する場合
cd pocs/inner_lens
source venv/bin/activate
streamlit run app.py
```

## 複数アプリを同時起動する場合

ターミナルのタブを分け、それぞれで上記コマンドを実行する。
ポートが被る場合は `streamlit run app.py --server.port 8502` のように変えれば競合しない。

---
*最終更新: 2026-06-15*
