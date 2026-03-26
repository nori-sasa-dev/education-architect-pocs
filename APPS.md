# POC アプリ一覧

各アプリの起動方法と URL。同時に複数起動してもポートが競合しない。


| #   | アプリ名               | URL                                            | 状態                | ディレクトリ                           |
| --- | ------------------ | ---------------------------------------------- | ----------------- | -------------------------------- |
| ①   | キャリア探索AI             | [http://localhost:8501](http://localhost:8501) | MVP完成（デモモード）      | `pocs/skill_inventory_bot/`      |
| ④   | Career Team AI     | [http://localhost:8502](http://localhost:8502) | MVP完成（実API動作確認済み） | `pocs/career_team/`              |
| ⑥   | 暗黙知継承プラットフォーム      | [http://localhost:8503](http://localhost:8503) | MVP完成（デモモード）      | `pocs/tacit_knowledge_platform/` |
| ⑤   | InnerLens（テニス自己観察） | [http://localhost:8504](http://localhost:8504) | MVP完成（デモモード）      | `pocs/inner_lens/`               |
| -   | Career AI（参考コード）   | [http://localhost:8505](http://localhost:8505) | 初期プロトタイプ          | `pocs/career_ai/`                |
| -   | Game Center        | [http://localhost:8506](http://localhost:8506) | -                 | `pocs/game_center/`              |


## 起動方法

各アプリのディレクトリで以下を実行：

```bash
# 例: InnerLens を起動する場合
cd /Users/sasagawanoritaka/Documents/AI_Projects/02_development/pocs/inner_lens
source venv/bin/activate
streamlit run app.py
```

## 複数アプリを同時起動する場合

ターミナルのタブを分けて、それぞれで上記コマンドを実行する。
ポートが分かれているので競合しない。