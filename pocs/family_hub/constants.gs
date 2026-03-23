// constants.gs - 設定定数（環境に合わせてここを編集する）

// コドモンの送信元メールアドレス（部分一致）
// Gmailの実際の送信元に合わせて変更すること
const CODOMON_SENDER = 'codomon.com';

// 処理済みラベル名（Gmailに自動作成される）
const PROCESSED_LABEL_NAME = 'コドモン処理済み';

// 登録先カレンダーID
// 'primary' = メインカレンダー
// 別のカレンダーに登録する場合は Google Calendar の設定からIDを確認する
const CALENDAR_ID = 'primary';

// 使用するClaudeモデル
const CLAUDE_MODEL = 'claude-sonnet-4-6';

// カレンダー登録の可能性があるキーワード（件名にこれらが含まれない場合はAPIをスキップ）
const CALENDAR_KEYWORDS = [
  '休園', '休講', '早帰り', '給食なし',
  '行事', '提出', '面談', '運動会', '発表会', '遠足',
  '延長', '短縮', '臨時', '変更', '中止',
  '弁当', 'Review', 'レビュー', '写真販売', '重要', 'イベント'
];
