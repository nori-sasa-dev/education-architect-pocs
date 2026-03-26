# 学術テニスコーチングチーム

解剖学・脳科学・物理学・心理学・栄養学の専門家AIが協働するCLIコーチングBot。

## 概要

5つの学術領域の専門家AIエージェントがマルチエージェントで協働し、テニスの悩みや質問に対して多角的なコーチングを提供します。

## エージェント構成

| 専門家 | 担当領域 |
|--------|---------|
| 解剖学者 | バイオメカニクス・怪我予防・運動連鎖 |
| 脳科学者 | 運動学習・集中力・メンタルトレーニング |
| 物理学者 | ボールの軌道・スピン・ラケット物理 |
| 心理学者 | インナーゲーム・メンタル・試合心理 |
| 栄養学者 | パフォーマンス栄養・コンディショニング |

## 技術スタック

- Python 3.12
- Claude API（`claude-opus-4-6`）— マルチエージェント

## セットアップ

```bash
cd pocs/tennis_coaching_team
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
python coach.py
```

## 使い方

起動後、CLIでテニスの悩みや質問を入力すると、各専門家エージェントが順番に分析・アドバイスを提供します。
