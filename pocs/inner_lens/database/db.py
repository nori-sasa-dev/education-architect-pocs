import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "inner_lens.db")
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "images")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT NOT NULL,
            video_name  TEXT,
            frame_index INTEGER,
            conversation TEXT,
            summary     TEXT,
            image_path  TEXT
        );
    """)
    conn.close()


def save_session(
    video_name: str,
    frame_index: int,
    conversation: list[dict],
    summary: str,
    image_bytes: bytes | None = None,
) -> int:
    """会話履歴・まとめ・姿勢推定画像を記録する"""
    # 画像をファイルに保存
    image_path = None
    if image_bytes:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(IMAGES_DIR, f"session_{timestamp}.png")
        with open(image_path, "wb") as f:
            f.write(image_bytes)

    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO sessions (created_at, video_name, frame_index, conversation, summary, image_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                video_name,
                frame_index,
                json.dumps(conversation, ensure_ascii=False),
                summary,
                image_path,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_sessions() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["conversation"] = json.loads(d["conversation"]) if d["conversation"] else []
            result.append(d)
        return result
    finally:
        conn.close()


def delete_session(session_id: int):
    """セッションとその画像ファイルを削除する"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT image_path FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row and row["image_path"] and os.path.exists(row["image_path"]):
            os.remove(row["image_path"])
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()
