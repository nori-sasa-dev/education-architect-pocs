import sqlite3
import json
import os
from datetime import datetime

# Streamlit Cloud では /mount/src/ が読み取り専用のため /tmp に書き込む
_default_db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(
    "/tmp" if not os.access(os.path.dirname(os.path.dirname(__file__)), os.W_OK) else _default_db_dir,
    "sessions.db"
)


def get_connection() -> sqlite3.Connection:
    """データベース接続を取得"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """テーブルを初期化"""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'in_progress',
            messages TEXT NOT NULL,
            orchestrator TEXT NOT NULL,
            report TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.close()


def save_session(
    session_id: str,
    messages: list,
    orchestrator: dict,
    report: dict | None = None,
    status: str = "in_progress",
):
    """セッションを保存（UPSERT）"""
    conn = get_connection()
    now = datetime.now().isoformat()
    try:
        conn.execute(
            """INSERT INTO sessions
               (session_id, status, messages, orchestrator, report, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
               status = excluded.status,
               messages = excluded.messages,
               orchestrator = excluded.orchestrator,
               report = excluded.report,
               updated_at = excluded.updated_at""",
            (
                session_id,
                status,
                json.dumps(messages, ensure_ascii=False),
                json.dumps(orchestrator, ensure_ascii=False),
                json.dumps(report, ensure_ascii=False) if report else None,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_session(session_id: str) -> dict | None:
    """セッションを1件取得"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return {
            "session_id": row["session_id"],
            "status": row["status"],
            "messages": json.loads(row["messages"]),
            "orchestrator": json.loads(row["orchestrator"]),
            "report": json.loads(row["report"]) if row["report"] else None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def get_all_sessions() -> list[dict]:
    """全セッション一覧を取得（新しい順）"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT session_id, status, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_session(session_id: str):
    """セッションを削除"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()
