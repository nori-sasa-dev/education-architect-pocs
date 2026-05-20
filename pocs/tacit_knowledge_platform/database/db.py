import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS knowledge_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT NOT NULL,
            author_role TEXT,
            department TEXT,
            years_of_experience TEXT,
            created_at TEXT NOT NULL,
            session_id TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS knowledge_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            context TEXT,
            keywords TEXT,
            FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id)
        );

        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            author_name TEXT NOT NULL,
            messages TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS thanks_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            thanker_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES knowledge_items(id)
        );

        CREATE TABLE IF NOT EXISTS author_thanks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT NOT NULL,
            thanker_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    # hit_count 列の追加（既存DBへのマイグレーション）
    try:
        conn.execute("ALTER TABLE knowledge_items ADD COLUMN hit_count INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    conn.close()


def save_knowledge(entry_data: dict, items: list[dict]) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO knowledge_entries
               (author_name, author_role, department, years_of_experience, created_at, session_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                entry_data["author_name"],
                entry_data.get("author_role", ""),
                entry_data.get("department", ""),
                entry_data.get("years_of_experience", ""),
                datetime.now().isoformat(),
                entry_data.get("session_id", ""),
            ),
        )
        entry_id = cursor.lastrowid

        for item in items:
            cursor2 = conn.execute(
                """INSERT INTO knowledge_items
                   (entry_id, category, title, content, context, keywords)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    entry_id,
                    item.get("category", "その他"),
                    item["title"],
                    item["content"],
                    item.get("context", ""),
                    item.get("keywords", ""),
                ),
            )
            _ = cursor2.lastrowid

        conn.commit()
        return entry_id
    finally:
        conn.close()


def search_knowledge(query: str, category: str = None) -> list[dict]:
    conn = get_connection()
    try:
        if not query.strip():
            # Return all entries when no query
            sql = """
                SELECT ki.id, ki.title, ki.content, ki.context, ki.keywords,
                       ki.category, ke.author_name, ke.author_role, ke.department
                FROM knowledge_items ki
                JOIN knowledge_entries ke ON ki.entry_id = ke.id
            """
            params = []
            if category:
                sql += " WHERE ki.category = ?"
                params.append(category)
            sql += " ORDER BY ki.id DESC"
            rows = conn.execute(sql, params).fetchall()
        else:
            # LIKE search across title, content, context, keywords
            keywords = query.split()
            conditions = []
            params = []
            for kw in keywords:
                like_pattern = f"%{kw}%"
                conditions.append(
                    "(ki.title LIKE ? OR ki.content LIKE ? OR ki.context LIKE ? OR ki.keywords LIKE ?)"
                )
                params.extend([like_pattern] * 4)

            where_clause = " OR ".join(conditions)
            sql = f"""
                SELECT ki.id, ki.title, ki.content, ki.context, ki.keywords,
                       ki.category, ke.author_name, ke.author_role, ke.department
                FROM knowledge_items ki
                JOIN knowledge_entries ke ON ki.entry_id = ke.id
                WHERE ({where_clause})
            """
            if category:
                sql += " AND ki.category = ?"
                params.append(category)
            sql += " ORDER BY ki.id DESC"
            rows = conn.execute(sql, params).fetchall()

        # 検索ヒット数をカウントアップ
        if rows:
            ids = [row["id"] for row in rows]
            conn.execute(
                "UPDATE knowledge_items SET hit_count = hit_count + 1 WHERE id IN ({})".format(
                    ",".join("?" * len(ids))
                ),
                ids,
            )
            conn.commit()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_categories() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT category FROM knowledge_items ORDER BY category"
        ).fetchall()
        return [row["category"] for row in rows]
    finally:
        conn.close()


def get_all_authors() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT author_name FROM knowledge_entries ORDER BY author_name"
        ).fetchall()
        return [row["author_name"] for row in rows]
    finally:
        conn.close()


def get_author_info(author_name: str) -> dict:
    """特定の記録者の最新プロフィールを取得する"""
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT author_name, author_role, department, years_of_experience
               FROM knowledge_entries WHERE author_name = ?
               ORDER BY created_at DESC LIMIT 1""",
            (author_name,),
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_knowledge_items_by_author(author_name: str) -> list[dict]:
    """特定の記録者の全ナレッジアイテムを取得する"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT ki.id, ki.category, ki.title, ki.content, ki.context, ki.keywords
               FROM knowledge_items ki
               JOIN knowledge_entries ke ON ki.entry_id = ke.id
               WHERE ke.author_name = ?
               ORDER BY ki.id""",
            (author_name,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_stats() -> dict:
    conn = get_connection()
    try:
        entry_count = conn.execute("SELECT COUNT(*) FROM knowledge_entries").fetchone()[0]
        item_count = conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
        category_counts = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM knowledge_items GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
        return {
            "entry_count": entry_count,
            "item_count": item_count,
            "categories": {row["category"]: row["cnt"] for row in category_counts},
        }
    finally:
        conn.close()


def update_knowledge_item(item_id: int, title: str, content: str, category: str, context: str, keywords: str):
    """ナレッジアイテムを更新する"""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE knowledge_items
               SET title = ?, content = ?, category = ?, context = ?, keywords = ?
               WHERE id = ?""",
            (title, content, category, context, keywords, item_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_knowledge_item(item_id: int):
    """ナレッジアイテムを削除する"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def add_thanks(item_id: int, thanker_name: str) -> int:
    """ありがとうを記録して累計数を返す"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO thanks_log (item_id, thanker_name, created_at) VALUES (?, ?, ?)",
            (item_id, thanker_name, datetime.now().isoformat()),
        )
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM thanks_log WHERE item_id = ?", (item_id,)
        ).fetchone()[0]
        return count
    finally:
        conn.close()


def get_thanks_count(item_id: int) -> int:
    """指定ナレッジへのありがとう累計数を返す"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM thanks_log WHERE item_id = ?", (item_id,)
        ).fetchone()[0]
    finally:
        conn.close()


def get_thanks_log(item_id: int) -> list[dict]:
    """指定ナレッジへのありがとう履歴を返す（新しい順）"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT thanker_name, created_at FROM thanks_log WHERE item_id = ? ORDER BY created_at DESC",
            (item_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_knowledge_entry(entry_id: int):
    """ナレッジエントリーとその配下のアイテムを一括削除する"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM knowledge_items WHERE entry_id = ?", (entry_id,))
        conn.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()


def get_author_ranking() -> list[dict]:
    """登録者ごとの貢献度ランキングを返す（スコア降順）"""
    conn = get_connection()
    try:
        authors = conn.execute(
            """SELECT ke.author_name, ke.author_role, ke.department,
                      COUNT(DISTINCT ki.id) as item_count,
                      COALESCE(SUM(ki.hit_count), 0) as total_hits
               FROM knowledge_entries ke
               LEFT JOIN knowledge_items ki ON ki.entry_id = ke.id
               GROUP BY ke.author_name"""
        ).fetchall()

        result = []
        for row in authors:
            author_name = row["author_name"]

            item_thanks = conn.execute(
                """SELECT COUNT(*) FROM thanks_log tl
                   JOIN knowledge_items ki ON ki.id = tl.item_id
                   JOIN knowledge_entries ke ON ke.id = ki.entry_id
                   WHERE ke.author_name = ?""",
                (author_name,),
            ).fetchone()[0]

            author_thanks = conn.execute(
                "SELECT COUNT(*) FROM author_thanks WHERE author_name = ?",
                (author_name,),
            ).fetchone()[0]

            total_thanks = item_thanks + author_thanks
            score = row["item_count"] * 10 + item_thanks * 20 + author_thanks * 30 + row["total_hits"]

            result.append({
                "author_name": author_name,
                "author_role": row["author_role"] or "",
                "department": row["department"] or "",
                "item_count": row["item_count"],
                "total_hits": row["total_hits"],
                "item_thanks": item_thanks,
                "author_thanks": author_thanks,
                "total_thanks": total_thanks,
                "score": score,
            })

        return sorted(result, key=lambda x: x["score"], reverse=True)
    finally:
        conn.close()


def add_author_thanks(author_name: str, thanker_name: str) -> int:
    """前任者へのありがとうを記録して累計数を返す"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO author_thanks (author_name, thanker_name, created_at) VALUES (?, ?, ?)",
            (author_name, thanker_name, datetime.now().isoformat()),
        )
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM author_thanks WHERE author_name = ?", (author_name,)
        ).fetchone()[0]
        return count
    finally:
        conn.close()


def get_author_thanks_count(author_name: str) -> int:
    """前任者へのありがとう累計数を返す"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM author_thanks WHERE author_name = ?", (author_name,)
        ).fetchone()[0]
    finally:
        conn.close()


def get_author_thanks_log(author_name: str) -> list[dict]:
    """前任者へのありがとう履歴を返す（新しい順）"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT thanker_name, created_at FROM author_thanks WHERE author_name = ? ORDER BY created_at DESC",
            (author_name,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_interview_session(session_id: str, author_name: str, messages: list, status: str = "in_progress"):
    conn = get_connection()
    now = datetime.now().isoformat()
    try:
        conn.execute(
            """INSERT INTO interview_sessions (session_id, author_name, messages, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
               messages = excluded.messages, status = excluded.status, updated_at = excluded.updated_at""",
            (session_id, author_name, json.dumps(messages, ensure_ascii=False), status, now, now),
        )
        conn.commit()
    finally:
        conn.close()
