// Code.gs - FamilyHub Phase1 メイン処理
// コドモンのメール通知を解析し、Googleカレンダーに自動登録する

/**
 * メイン関数：コドモンメールをチェックしてカレンダーに登録する
 * トリガー設定後、毎週金曜22時に自動実行される
 */
function checkCodomonEmails() {
  const scriptProps = PropertiesService.getScriptProperties();
  const claudeApiKey = scriptProps.getProperty('CLAUDE_API_KEY');

  if (!claudeApiKey) {
    Logger.log('エラー: CLAUDE_API_KEY が Script Properties に設定されていません');
    return;
  }

  // 未処理のコドモンメールを検索（処理済みラベルなし・未読）
  // newer_than:7d で直近7日以内のメールのみ対象（過去メールの誤処理を防ぐ）
  const query = `from:(${CODOMON_SENDER}) -label:${PROCESSED_LABEL_NAME} newer_than:7d`;
  const threads = GmailApp.search(query, 0, 20);

  Logger.log(`未処理スレッド数: ${threads.length}`);

  threads.forEach(thread => {
    // スレッド内の最新メール1件のみ処理（API消費を抑えるため）
    const messages = thread.getMessages();
    const latestMessage = messages[messages.length - 1];
    processEmail(latestMessage, claudeApiKey);
  });
}

/**
 * 個別メールを処理する
 * @param {GmailMessage} message - 処理対象のメール
 * @param {string} claudeApiKey - Claude APIキー
 */
function processEmail(message, claudeApiKey) {
  const subject = message.getSubject();
  const body = message.getPlainBody();

  Logger.log(`処理中: ${subject}`);

  // 件名にキーワードが含まれない場合はAPIをスキップ
  const hasKeyword = CALENDAR_KEYWORDS.some(kw => subject.includes(kw));
  if (!hasKeyword) {
    Logger.log(`スキップ（APIなし）: ${subject}`);
    markAsProcessed(message);
    return;
  }

  try {
    // Claude APIでカレンダー登録情報を抽出
    const events = extractInfoWithClaude(subject, body, claudeApiKey);

    if (!events || events.length === 0) {
      Logger.log('カレンダー登録対象なし');
    } else {
      // カレンダーに登録
      events.forEach(event => {
        createCalendarEvent(event, subject);
      });
      Logger.log(`${events.length}件をカレンダーに登録しました`);
    }

    // 処理済みラベルを付けて再処理を防ぐ
    markAsProcessed(message);

  } catch (e) {
    Logger.log(`エラー [${subject}]: ${e.toString()}`);
  }
}

/**
 * Claude APIを呼び出してメールから日程情報を抽出する
 * @param {string} subject - メール件名
 * @param {string} body - メール本文
 * @param {string} apiKey - Claude APIキー
 * @returns {Array} 抽出されたイベント情報の配列
 */
function extractInfoWithClaude(subject, body, apiKey) {
  const today = new Date();
  const todayStr = Utilities.formatDate(today, 'Asia/Tokyo', 'yyyy年MM月dd日');
  const yearStr = Utilities.formatDate(today, 'Asia/Tokyo', 'yyyy');

  const prompt = `あなたは保育園・学校からの連絡メールを解析するアシスタントです。
今日の日付: ${todayStr}（年が明記されていない場合は${yearStr}年とする）

以下のメール内容から、Googleカレンダーに登録すべき情報を抽出してください。

件名: ${subject}
本文:
${body}

【抽出対象】
- 休園日・休校日（臨時休園含む）
- 早帰り（何時まで）
- 給食なしの日
- イベント・行事の日程（運動会、発表会、遠足など）
- 提出物の締め切り
- 保護者会・個人面談の日程

【注意事項】
- 日付が明確でないものは登録しない
- 定期的なお知らせ（月のお便りなど）は登録しない
- 複数の日程が含まれる場合はそれぞれ別のイベントとして返す

以下のJSON形式で返してください。登録すべき情報がない場合は空配列 [] を返してください。

\`\`\`json
[
  {
    "title": "イベントタイトル（例：保育園 休園、保育園 早帰り 14時、保育園 給食なし、運動会）",
    "date": "YYYY-MM-DD形式",
    "allDay": true,
    "startTime": "HH:MM（allDayがfalseの場合のみ記載）",
    "endTime": "HH:MM（allDayがfalseの場合のみ記載）",
    "description": "詳細・注意事項（持ち物など）",
    "priority": "high（休園・早帰り・給食なし）またはnormal（それ以外）"
  }
]
\`\`\``;

  const requestBody = {
    model: CLAUDE_MODEL,
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }]
  };

  const options = {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    payload: JSON.stringify(requestBody),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', options);
  const responseCode = response.getResponseCode();

  if (responseCode !== 200) {
    throw new Error(`Claude API エラー (HTTP ${responseCode}): ${response.getContentText()}`);
  }

  const responseData = JSON.parse(response.getContentText());
  const content = responseData.content[0].text;

  // JSONブロックを抽出
  const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
  if (!jsonMatch) {
    Logger.log(`JSONブロックが見つかりませんでした。レスポンス: ${content}`);
    return [];
  }

  return JSON.parse(jsonMatch[1]);
}

/**
 * Googleカレンダーにイベントを作成する
 * @param {Object} eventInfo - 抽出されたイベント情報
 * @param {string} emailSubject - 元のメール件名（説明欄に記録）
 */
function createCalendarEvent(eventInfo, emailSubject) {
  const calendar = CalendarApp.getCalendarById(CALENDAR_ID)
    || CalendarApp.getDefaultCalendar();

  const eventDate = new Date(eventInfo.date);

  const description = [
    eventInfo.description || '',
    '',
    `---`,
    `[FamilyHub] コドモンメールより自動登録`,
    `元メール: ${emailSubject}`,
    `登録日時: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}`
  ].filter(Boolean).join('\n');

  let event;

  if (eventInfo.allDay) {
    event = calendar.createAllDayEvent(eventInfo.title, eventDate, { description });
  } else {
    const start = new Date(`${eventInfo.date}T${eventInfo.startTime || '09:00'}:00+09:00`);
    const end = new Date(`${eventInfo.date}T${eventInfo.endTime || '10:00'}:00+09:00`);
    event = calendar.createEvent(eventInfo.title, start, end, { description });
  }

  // 優先度に応じてリマインダーを設定
  if (eventInfo.priority === 'high') {
    event.addPopupReminder(60);   // 1時間前
    event.addPopupReminder(1440); // 前日
  } else {
    event.addPopupReminder(1440); // 前日のみ
  }

  Logger.log(`登録完了: ${eventInfo.title} (${eventInfo.date}) priority=${eventInfo.priority}`);
}

/**
 * メールに処理済みラベルを付ける
 * @param {GmailMessage} message
 */
function markAsProcessed(message) {
  let label = GmailApp.getUserLabelByName(PROCESSED_LABEL_NAME);
  if (!label) {
    label = GmailApp.createLabel(PROCESSED_LABEL_NAME);
  }
  message.getThread().addLabel(label);
}

// =============================================================
// セットアップ・テスト用関数
// =============================================================

/**
 * 【初回セットアップ】毎週金曜22時の自動実行トリガーを設定する
 * 一度だけ実行すればOK
 */
function setupTrigger() {
  // 既存トリガーを全削除してから再設定
  ScriptApp.getProjectTriggers().forEach(trigger => {
    ScriptApp.deleteTrigger(trigger);
  });

  ScriptApp.newTrigger('checkCodomonEmails')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.FRIDAY)
    .atHour(22)
    .create();

  Logger.log('トリガー設定完了（毎週金曜22時に自動実行）');
}

/**
 * 【テスト】最新のコドモンメール1件を試し処理する（カレンダー登録も実行される）
 * 動作確認時に手動で実行する
 */
function testWithLatestEmail() {
  const scriptProps = PropertiesService.getScriptProperties();
  const claudeApiKey = scriptProps.getProperty('CLAUDE_API_KEY');

  if (!claudeApiKey) {
    Logger.log('エラー: CLAUDE_API_KEY を Script Properties に設定してください');
    Logger.log('設定方法: 「プロジェクトの設定」→「スクリプトプロパティ」→ CLAUDE_API_KEY を追加');
    return;
  }

  const query = `from:(${CODOMON_SENDER}) -label:${PROCESSED_LABEL_NAME} newer_than:7d`;
  const threads = GmailApp.search(query, 0, 1);

  if (threads.length === 0) {
    Logger.log(`コドモンのメールが見つかりませんでした（検索条件: ${query}）`);
    Logger.log(`constants.gs の CODOMON_SENDER を実際の送信元ドメインに変更してください`);
    return;
  }

  const message = threads[0].getMessages()[0];
  Logger.log(`テスト対象メール: "${message.getSubject()}" (${message.getDate()})`);

  processEmail(message, claudeApiKey);
}

/**
 * 【デバッグ】コドモンメールの送信元アドレスを確認する
 * CODOMON_SENDER の設定値を確認したいときに実行する
 */
function debugCheckSender() {
  // Gmailの全メールから「コドモン」関連を探す
  const keywords = ['コドモン', 'codomon', 'CoDMON'];
  keywords.forEach(kw => {
    const threads = GmailApp.search(`subject:(${kw}) OR from:(${kw})`, 0, 3);
    threads.forEach(thread => {
      const msg = thread.getMessages()[0];
      Logger.log(`件名: ${msg.getSubject()}`);
      Logger.log(`送信元: ${msg.getFrom()}`);
      Logger.log('---');
    });
  });
}
