# FamilyHub

コドモンのメール通知を自動解析し、Googleカレンダーに登録するGoogle Apps Script。

## 概要

保育園・学校からのメール通知（休園・イベント・提出物など）をClaude APIで解析し、Googleカレンダーに自動登録します。重要度に応じてリマインダーを二重設定（前日＋1時間前）します。

## 機能

- コドモンメールの自動検出（15分ごとのトリガー）
- Claude APIによるイベント情報の抽出（日時・種別・優先度）
- Googleカレンダーへの自動登録
- 重要イベント（休園・早帰り等）の二重リマインダー
- 処理済みラベルによる重複防止

## 対応イベント種別

`休園` / `休校` / `早帰り` / `給食なし` / `イベント` / `提出物` / `面談`

## 技術スタック

- Google Apps Script
- Claude API（`claude-sonnet-4-6`）
- Gmail API（GAS組み込み）
- Google Calendar API（GAS組み込み）

## セットアップ

1. [Google Apps Script](https://script.google.com) で新規プロジェクトを作成
2. `Code.gs` と `constants.gs` の内容を貼り付け
3. `constants.gs` の `CALENDAR_ID` を自分のGoogleカレンダーIDに変更
4. プロジェクトの「プロパティ」→「スクリプトプロパティ」に `CLAUDE_API_KEY` を設定
5. `setupTrigger` 関数を実行してトリガーを登録

## 注意事項

- 送信元ドメインは `codmon.com`（`codomon.com` ではない）
- 保育園によって送信元アドレスが異なる場合がある
- 日付が本文に明記されていないメールは登録されない
