"""デモデータ投入スクリプト。既存デモデータを削除してから再投入する。"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db import init_db, get_connection
from datetime import datetime, timedelta
import random

init_db()

DEMO_AUTHORS = [
    {
        "author_name": "田中 誠一",
        "author_role": "シニアエンジニア",
        "department": "システム開発部",
        "years_of_experience": "28年",
        "items": [
            {
                "category": "トラブルシューティング",
                "title": "本番障害の初動対応フロー",
                "content": "障害発生時はまず影響範囲の特定が最優先。直近1週間の変更履歴（デプロイ、設定変更、パッチ適用）を必ず確認する。原因の8割は直近の変更に起因する。",
                "context": "本番環境で障害が発生した際の初動対応",
                "keywords": "障害対応, 影響範囲, 変更履歴, 初動",
                "hit_count": 42,
                "thanks": ["佐藤", "鈴木", "高橋", "伊藤"],
            },
            {
                "category": "判断基準",
                "title": "リリース判断の見極め方",
                "content": "迷ったら『このバグでユーザーの業務が止まるか？』を基準にする。止まらなければ80%品質でリリースし後から直す。",
                "context": "リリース前のGo/No-Go判断",
                "keywords": "リリース判断, 品質基準, Go/No-Go",
                "hit_count": 31,
                "thanks": ["渡辺", "山本"],
            },
            {
                "category": "リスク予見",
                "title": "プロジェクトリスクの予兆察知",
                "content": "報告の頻度が減る、会議で目を合わせない、進捗が急に楽観的になる――この3つが重なったときは必ず1on1で直接聞く。",
                "context": "プロジェクト進行中のリスクモニタリング",
                "keywords": "リスク予見, 予兆, プロジェクト管理",
                "hit_count": 19,
                "thanks": ["小林", "加藤", "吉田"],
            },
        ],
        "author_thanks": ["佐藤", "高橋", "渡辺", "伊藤", "小林"],
    },
    {
        "author_name": "山田 花子",
        "author_role": "プロジェクトマネージャー",
        "department": "PMO",
        "years_of_experience": "20年",
        "items": [
            {
                "category": "人間関係・調整",
                "title": "ステークホルダー調整の勘所",
                "content": "提案は『相手のメリット』を先に語る。技術の話は後。キーパーソンには事前に根回しする。『聞いてない』が最大の敵。",
                "context": "システム改修・新規導入の提案・承認取得",
                "keywords": "ステークホルダー, 根回し, 提案, 合意形成",
                "hit_count": 55,
                "thanks": ["田中", "鈴木", "伊藤", "渡辺", "山本", "中村"],
            },
            {
                "category": "業務効率化",
                "title": "会議を30分以内に終わらせる技術",
                "content": "アジェンダは事前に送り、ゴールを明確にする。『決めること』と『共有すること』を区別する。議事録はその場でリアルタイムに書き、終了と同時に送る。",
                "context": "日常の会議運営・プロジェクト定例",
                "keywords": "会議, アジェンダ, 議事録, 時間管理",
                "hit_count": 38,
                "thanks": ["高橋", "小林", "加藤"],
            },
            {
                "category": "判断基準",
                "title": "スコープクリープを防ぐ一言",
                "content": "追加要件が来たら『では何を削りますか？』と返す。トレードオフを可視化すると依頼側も考える。",
                "context": "プロジェクト中盤の要件追加要望への対応",
                "keywords": "スコープ, 要件管理, トレードオフ",
                "hit_count": 27,
                "thanks": ["田中", "吉田"],
            },
        ],
        "author_thanks": ["鈴木", "高橋", "伊藤", "中村", "小林", "加藤", "吉田"],
    },
    {
        "author_name": "鈴木 健太",
        "author_role": "インフラエンジニア",
        "department": "基盤技術部",
        "years_of_experience": "15年",
        "items": [
            {
                "category": "技術ノウハウ",
                "title": "障害時のログ読み方三原則",
                "content": "①最新のエラーから遡る、②タイムスタンプの飛びに注目、③同じエラーの繰り返しは初回が本当の原因。まずgrepで絞ってから読む。",
                "context": "サーバ・ミドルウェア障害の原因調査",
                "keywords": "ログ解析, grep, 障害調査, インフラ",
                "hit_count": 48,
                "thanks": ["田中", "山田", "佐藤"],
            },
            {
                "category": "業務効率化",
                "title": "定期メンテナンスの失敗ゼロ化チェックリスト",
                "content": "作業前：バックアップ確認・切り戻し手順の準備・関係者への周知。作業中：手順書の音読確認（1人作業禁止）。作業後：サービス疎通確認・監視アラートの確認。",
                "context": "計画メンテナンス・バッチ変更作業",
                "keywords": "メンテナンス, チェックリスト, 切り戻し",
                "hit_count": 33,
                "thanks": ["渡辺"],
            },
        ],
        "author_thanks": ["田中", "山田"],
    },
    {
        "author_name": "佐藤 美咲",
        "author_role": "カスタマーサクセス",
        "department": "営業推進部",
        "years_of_experience": "12年",
        "items": [
            {
                "category": "人間関係・調整",
                "title": "クレーム対応で絶対に言ってはいけないこと",
                "content": "『でも』『だって』は禁句。まず徹底的に共感する。謝罪と説明を混ぜない――謝罪は謝罪だけで完結させる。",
                "context": "顧客からのクレーム・強い不満への対応",
                "keywords": "クレーム, 顧客対応, 共感",
                "hit_count": 61,
                "thanks": ["田中", "山田", "鈴木", "高橋", "伊藤"],
            },
            {
                "category": "判断基準",
                "title": "契約更新の危険信号3つ",
                "content": "①返信速度が遅くなる、②定例に上位者が参加しなくなる、③問い合わせが極端に減る。サインを見つけたらすぐに経営層との直接面談をセット。",
                "context": "顧客の契約更新・解約リスク管理",
                "keywords": "チャーン, 契約更新, リテンション",
                "hit_count": 29,
                "thanks": ["渡辺", "山本"],
            },
        ],
        "author_thanks": ["田中", "山田", "鈴木"],
    },
    {
        "author_name": "高橋 龍二",
        "author_role": "データアナリスト",
        "department": "データ推進部",
        "years_of_experience": "8年",
        "items": [
            {
                "category": "技術ノウハウ",
                "title": "分析結果を経営陣に伝える見せ方",
                "content": "『だから何をすべきか』を最初のスライドに書く。経営陣が見るのは最初の3枚だけと思って設計する。詳細データは付録扱い。",
                "context": "経営報告・意思決定支援の資料作成",
                "keywords": "データ分析, プレゼン, 経営報告",
                "hit_count": 22,
                "thanks": ["山田"],
            },
        ],
        "author_thanks": [],
    },
    {
        "author_name": "中村 雅也",
        "author_role": "営業部長",
        "department": "法人営業部",
        "years_of_experience": "22年",
        "items": [
            {
                "category": "人間関係・調整",
                "title": "初回商談で信頼を得る3ステップ",
                "content": "①最初の5分は相手の話だけ聞く、②課題を自分の言葉で言い換えて確認する、③提案は次回以降にする。初回で売ろうとすると必ず失敗する。",
                "context": "新規顧客との初回商談",
                "keywords": "営業, 商談, 信頼構築, ヒアリング",
                "hit_count": 34,
                "thanks": ["佐藤", "田中", "鈴木"],
            },
            {
                "category": "業務効率化",
                "title": "月末追い込みをなくすパイプライン管理",
                "content": "受注予測を週次で更新し、月初に月末の着地を見通す。月末に慌てるのはパイプラインを週次で見ていないから。案件ごとに『次のアクション日』を必ず設定する。",
                "context": "営業チームの数字管理・予実管理",
                "keywords": "パイプライン, 営業管理, 予実, KPI",
                "hit_count": 28,
                "thanks": ["伊藤", "渡辺"],
            },
        ],
        "author_thanks": ["佐藤", "高橋", "田中"],
    },
    {
        "author_name": "小林 香奈",
        "author_role": "人事マネージャー",
        "department": "人事部",
        "years_of_experience": "18年",
        "items": [
            {
                "category": "人間関係・調整",
                "title": "1on1で本音を引き出す問いかけ",
                "content": "『最近どう？』は機能しない。『今週一番消耗したことは？』『もし制約がなかったら何を変えたい？』など具体的な問いを使う。沈黙を埋めようとしない。",
                "context": "部下・後輩との1on1面談",
                "keywords": "1on1, コーチング, 傾聴, マネジメント",
                "hit_count": 44,
                "thanks": ["山田", "中村", "田中", "吉田"],
            },
            {
                "category": "判断基準",
                "title": "採用面接で見抜く「伸びる人材」の共通点",
                "content": "失敗体験を語るときに他責にしない人。『自分はこう変えた』が出てくる人。スキルは後から身につくが、この姿勢は変わらない。",
                "context": "中途・新卒採用の面接評価",
                "keywords": "採用, 面接, 人材評価, 自責思考",
                "hit_count": 39,
                "thanks": ["田中", "山田", "佐藤"],
            },
            {
                "category": "業務効率化",
                "title": "評価面談を建設的に終わらせる構成",
                "content": "①過去の振り返り（事実ベース）→②強みの確認→③次期の期待→④本人の目標確認、の順で進める。評価の高低より『次に向けた合意』で終わることが重要。",
                "context": "半期・年次の評価面談",
                "keywords": "評価面談, フィードバック, 人事評価",
                "hit_count": 26,
                "thanks": ["中村"],
            },
        ],
        "author_thanks": ["山田", "中村", "佐藤", "田中"],
    },
    {
        "author_name": "加藤 進",
        "author_role": "経理部長",
        "department": "財務経理部",
        "years_of_experience": "26年",
        "items": [
            {
                "category": "判断基準",
                "title": "予算超過を察知する早期警戒サイン",
                "content": "月次で予算消化率が前年同月より5%以上高いときは必ず原因を確認する。『来月から絞る』は大抵うまくいかない。異常を見つけた瞬間に手を打つ。",
                "context": "月次予算管理・コスト管理",
                "keywords": "予算管理, コスト, 財務, 早期警戒",
                "hit_count": 18,
                "thanks": ["山田", "田中"],
            },
            {
                "category": "技術ノウハウ",
                "title": "監査対応を楽にする証跡管理の習慣",
                "content": "判断した理由をその場でメモに残す。後から『なぜそうしたか』を説明できれば監査は怖くない。エビデンスは判断時点の情報で残すのがルール。",
                "context": "会計監査・内部統制への対応",
                "keywords": "監査, 内部統制, 証跡, コンプライアンス",
                "hit_count": 15,
                "thanks": ["鈴木"],
            },
        ],
        "author_thanks": ["山田"],
    },
    {
        "author_name": "渡辺 大輔",
        "author_role": "品質保証リード",
        "department": "品質管理部",
        "years_of_experience": "16年",
        "items": [
            {
                "category": "トラブルシューティング",
                "title": "バグの再現率を上げる情報収集の型",
                "content": "①発生環境、②操作手順（スクショ付き）、③期待値と実際値、④発生頻度を必ず聞く。『なんか変』だけ報告するユーザーには、この4点をテンプレで返す。",
                "context": "バグ報告受付・品質問い合わせ対応",
                "keywords": "QA, バグ再現, 品質, テスト",
                "hit_count": 37,
                "thanks": ["田中", "鈴木", "高橋"],
            },
            {
                "category": "業務効率化",
                "title": "テスト工数を半減させる優先順位付け",
                "content": "変更箇所に隣接するコードと、過去バグが多かった箇所を重点テストする。全件テストは幻想。リスクベースで絞り込めば同じ品質を半分の時間で担保できる。",
                "context": "リリース前のテスト計画・工数見積もり",
                "keywords": "テスト計画, リスクベース, 工数削減, QA",
                "hit_count": 30,
                "thanks": ["田中"],
            },
        ],
        "author_thanks": ["田中", "鈴木"],
    },
    {
        "author_name": "吉田 恵子",
        "author_role": "法務スペシャリスト",
        "department": "法務部",
        "years_of_experience": "14年",
        "items": [
            {
                "category": "判断基準",
                "title": "契約書レビューで必ず確認する5条項",
                "content": "①損害賠償の上限、②知的財産の帰属、③契約解除条件、④準拠法・裁判管轄、⑤秘密保持の範囲と期間。この5つを最初に読めば全体のリスク感が掴める。",
                "context": "取引先との契約書レビュー・締結判断",
                "keywords": "契約書, 法務, リスク管理, レビュー",
                "hit_count": 25,
                "thanks": ["山田", "中村"],
            },
        ],
        "author_thanks": ["山田"],
    },
    {
        "author_name": "伊藤 勇介",
        "author_role": "製造ライン長",
        "department": "製造部",
        "years_of_experience": "30年",
        "items": [
            {
                "category": "技術ノウハウ",
                "title": "設備の異音を聞き分ける経験則",
                "content": "正常時の音を体で覚えることが全ての基本。異音は『音程の変化』より『リズムの乱れ』で気づくことが多い。週1回は意識して設備の音を聞く時間を作る。",
                "context": "製造ライン設備の日常点検・異常検知",
                "keywords": "設備管理, 異常検知, 点検, 製造",
                "hit_count": 20,
                "thanks": ["田中", "鈴木"],
            },
            {
                "category": "人間関係・調整",
                "title": "現場の不満を改善につなげる聞き方",
                "content": "『何が嫌か』より『どうなったらいいか』を聞く。不満は感情だが、理想は行動に変えられる。週次の短い立ち話が月次の大きな問題を防ぐ。",
                "context": "製造現場のメンバーマネジメント",
                "keywords": "現場管理, コミュニケーション, 改善, 製造",
                "hit_count": 16,
                "thanks": ["小林"],
            },
        ],
        "author_thanks": ["小林", "田中"],
    },
]


def seed():
    conn = get_connection()
    now = datetime.now()

    # 既存デモデータを削除（session_id が "demo-" で始まるもの）
    existing = conn.execute(
        "SELECT id FROM knowledge_entries WHERE session_id LIKE 'demo-%'"
    ).fetchall()
    for row in existing:
        entry_id = row["id"]
        item_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM knowledge_items WHERE entry_id = ?", (entry_id,)
        ).fetchall()]
        for item_id in item_ids:
            conn.execute("DELETE FROM thanks_log WHERE item_id = ?", (item_id,))
        conn.execute("DELETE FROM knowledge_items WHERE entry_id = ?", (entry_id,))
        conn.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
    # author_thanks のデモデータ削除
    demo_names = [a["author_name"] for a in DEMO_AUTHORS]
    for name in demo_names:
        conn.execute("DELETE FROM author_thanks WHERE author_name = ?", (name,))
    conn.commit()

    # デモデータを投入
    for author_data in DEMO_AUTHORS:
        cursor = conn.execute(
            """INSERT INTO knowledge_entries
               (author_name, author_role, department, years_of_experience, created_at, session_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                author_data["author_name"],
                author_data["author_role"],
                author_data["department"],
                author_data["years_of_experience"],
                (now - timedelta(days=random.randint(1, 90))).isoformat(),
                f"demo-{author_data['author_name']}",
            ),
        )
        entry_id = cursor.lastrowid

        for item_data in author_data["items"]:
            cursor2 = conn.execute(
                """INSERT INTO knowledge_items
                   (entry_id, category, title, content, context, keywords, hit_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry_id,
                    item_data["category"],
                    item_data["title"],
                    item_data["content"],
                    item_data["context"],
                    item_data["keywords"],
                    item_data["hit_count"],
                ),
            )
            item_id = cursor2.lastrowid
            for thanker in item_data["thanks"]:
                conn.execute(
                    "INSERT INTO thanks_log (item_id, thanker_name, created_at) VALUES (?, ?, ?)",
                    (item_id, thanker, (now - timedelta(days=random.randint(0, 30))).isoformat()),
                )

        for thanker in author_data["author_thanks"]:
            conn.execute(
                "INSERT INTO author_thanks (author_name, thanker_name, created_at) VALUES (?, ?, ?)",
                (author_data["author_name"], thanker, (now - timedelta(days=random.randint(0, 30))).isoformat()),
            )

    conn.commit()
    conn.close()
    print(f"デモデータを投入しました（{len(DEMO_AUTHORS)}名）。")
    for a in DEMO_AUTHORS:
        print(f"  - {a['author_name']}（{a['author_role']}）: {len(a['items'])}件")


def seed_if_empty():
    """DBにデータがない場合のみデモデータを投入する（Streamlit Cloud起動時用）"""
    from database.db import get_stats
    if get_stats()["entry_count"] == 0:
        seed()


if __name__ == "__main__":
    seed()
