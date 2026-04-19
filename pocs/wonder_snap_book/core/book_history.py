import json
import base64
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """テーブルを初期化する（存在しない場合のみ作成）"""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                created_at  TEXT    NOT NULL,
                pages_json  TEXT    NOT NULL,
                thumbnail   TEXT
            )
        """)


def _to_base64(image_data) -> str | None:
    """image_data（bytes）を base64文字列に変換する。None または非bytes は None を返す"""
    if isinstance(image_data, bytes):
        return base64.b64encode(image_data).decode()
    return None


def save_book(title: str, pages: list) -> int:
    """絵本を保存してIDを返す。image_data は bytes または URL を受け付ける"""
    init_db()
    pages_to_save = []
    thumbnail = None

    for i, page in enumerate(pages):
        p = {k: v for k, v in page.items() if k != "image_url"}
        img_raw = page.get("image_data") or page.get("image_url")
        p["image_data"] = _to_base64(img_raw)
        if i == 0:
            thumbnail = p["image_data"]
        pages_to_save.append(p)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO books (title, created_at, pages_json, thumbnail) VALUES (?, ?, ?, ?)",
            (title, created_at, json.dumps(pages_to_save, ensure_ascii=False), thumbnail),
        )
        return cur.lastrowid


def list_books() -> list[dict]:
    """全絵本の一覧（id, title, created_at, thumbnail）を新しい順で返す"""
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, thumbnail FROM books ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_book(book_id: int) -> dict | None:
    """IDで絵本を取得する。pages の image_data は bytes に戻して返す"""
    init_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, title, created_at, pages_json FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
    if not row:
        return None

    d = dict(row)
    pages = json.loads(d.pop("pages_json"))
    for page in pages:
        img_b64 = page.get("image_data")
        if img_b64 and isinstance(img_b64, str):
            page["image_data"] = base64.b64decode(img_b64)
    d["pages"] = pages
    return d
