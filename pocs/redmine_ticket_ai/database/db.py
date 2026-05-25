import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "redmine.db"
CHROMA_PATH = Path(__file__).parent / "chroma_store"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """SQLiteテーブルを初期化する"""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tickets (
                id          INTEGER PRIMARY KEY,
                ticket_type TEXT NOT NULL,
                feature     TEXT NOT NULL,
                title       TEXT NOT NULL,
                description TEXT,
                root_cause  TEXT,
                resolution  TEXT,
                review_comment TEXT,
                status      TEXT,
                created_at  TEXT,
                imported_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS import_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                row_count   INTEGER NOT NULL,
                imported_at TEXT DEFAULT (datetime('now', 'localtime'))
            );
        """)


def upsert_tickets(rows: list[dict]) -> int:
    """チケットリストをupsertし、挿入件数を返す"""
    sql = """
        INSERT OR REPLACE INTO tickets
            (id, ticket_type, feature, title, description,
             root_cause, resolution, review_comment, status, created_at)
        VALUES
            (:id, :ticket_type, :feature, :title, :description,
             :root_cause, :resolution, :review_comment, :status, :created_at)
    """
    with get_conn() as conn:
        conn.executemany(sql, rows)
    return len(rows)


def log_import(filename: str, row_count: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO import_log (filename, row_count) VALUES (?, ?)",
            (filename, row_count),
        )


def get_all_tickets() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_ticket_count() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]


def get_features() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT feature FROM tickets ORDER BY feature"
        ).fetchall()
    return [r[0] for r in rows]


def get_ticket_types() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ticket_type FROM tickets ORDER BY ticket_type"
        ).fetchall()
    return [r[0] for r in rows]


def get_stats() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        by_type = conn.execute(
            "SELECT ticket_type, COUNT(*) as cnt FROM tickets GROUP BY ticket_type"
        ).fetchall()
        by_feature = conn.execute(
            "SELECT feature, COUNT(*) as cnt FROM tickets GROUP BY feature ORDER BY cnt DESC"
        ).fetchall()
    return {
        "total": total,
        "by_type": {r["ticket_type"]: r["cnt"] for r in by_type},
        "by_feature": {r["feature"]: r["cnt"] for r in by_feature},
    }


def get_tickets_by_ids(ids: list[int]) -> list[dict]:
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM tickets WHERE id IN ({placeholders})", ids
        ).fetchall()
    id_order = {tid: i for i, tid in enumerate(ids)}
    result = [dict(r) for r in rows]
    result.sort(key=lambda r: id_order.get(r["id"], 999))
    return result


def get_feature_tickets(feature: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE feature = ? ORDER BY ticket_type, id",
            (feature,),
        ).fetchall()
    return [dict(r) for r in rows]
