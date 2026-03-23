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
    """)
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


def delete_knowledge_entry(entry_id: int):
    """ナレッジエントリーとその配下のアイテムを一括削除する"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM knowledge_items WHERE entry_id = ?", (entry_id,))
        conn.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
        conn.commit()
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
