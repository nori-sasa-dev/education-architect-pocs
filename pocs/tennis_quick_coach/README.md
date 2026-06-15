# 🎾 テニス・クイックコーチ（tennis_quick_coach）

試合・練習中の状況をテキストで入力すると、AIコーチが「今すぐ使える戦術アドバイス」を返す Streamlit アプリです。

ベンチでひと息つく合間に状況を打ち込めば、次のポイントで試せる具体策がその場で手に入ります。

## できること

- **状況入力**: 「相手のバックが弱い。2-3でリードされている。風が強い」のように自由テキストで入力
- **プレースタイル選択**: 攻撃型 / 守備型 / オールラウンド を選ぶと、それに合わせたアドバイスに調整
- **構造化アドバイスの表示**:
  - 📋 状況の要約（summary）
  - 🎯 推奨戦術（tactics・優先順位つき3つ）
  - ⚡ 次のポイントで試す1アクション（next_action）
  - 🧘 メンタル面の一言（mental）

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `app.py` | Streamlit の単一画面UI |
| `coach.py` | `CoachAgent` クラスと `DEMO_RESPONSES`、`extract_advice()` |
| `requirements.txt` | 依存ライブラリ |
| `.env.example` | APIキーのテンプレート |
| `README.md` | 本ファイル |

## セットアップ

```bash
# 1. このディレクトリに移動
cd pocs/tennis_quick_coach

# 2. 仮想環境を作成して有効化
python3 -m venv venv
source venv/bin/activate

# 3. 依存ライブラリをインストール
pip install -r requirements.txt

# 4. （任意）APIキーを設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定する
```

## 起動

```bash
streamlit run app.py
```

ブラウザが開いたら、状況を入力してプレースタイルを選び、「アドバイスをもらう」を押します。

## デモモードについて

`ANTHROPIC_API_KEY` を設定していない場合は **デモモード** で動作します。
Claude API を呼ばず、`coach.py` の `DEMO_RESPONSES`（プレースタイル別の固定サンプル）を返すため、
APIキーなしでも画面の動きをそのまま確認できます。

## 技術メモ

- AIモデル: `claude-sonnet-4-6`
- アドバイスは `[ADVICE]` マーカー + ` ```json ``` ` ブロックで返し、`extract_advice()` で辞書化
- JSONのパースに失敗しても画面が壊れないよう、フォールバック処理を入れています
