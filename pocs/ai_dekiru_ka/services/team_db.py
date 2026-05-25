import sqlite3
import os
import random
import string

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "team_data.db")


def init_db() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(_DB_PATH)), exist_ok=True)
    with sqlite3.connect(_DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                team_code              TEXT    NOT NULL,
                user_name              TEXT    NOT NULL,
                department             TEXT    DEFAULT '',
                task_name              TEXT    NOT NULL,
                category               TEXT    NOT NULL,
                time_reduction_pct     INTEGER DEFAULT 0,
                monthly_hours          REAL    DEFAULT 0,
                monthly_reduction_hours REAL   DEFAULT 0,
                priority               TEXT    DEFAULT 'LOW',
                suggested_tool         TEXT    DEFAULT '',
                reduction_reason       TEXT    DEFAULT '',
                status                 TEXT    DEFAULT '未着手',
                created_at             TEXT    DEFAULT (datetime('now', 'localtime'))
            )
        """)
        # 既存テーブルへの status カラム追加（マイグレーション）
        try:
            con.execute("ALTER TABLE diagnoses ADD COLUMN status TEXT DEFAULT '未着手'")
        except Exception:
            pass


def generate_team_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def save_diagnosis(team_code: str, user_name: str, department: str, tasks: list) -> None:
    with sqlite3.connect(_DB_PATH) as con:
        # 同一チーム・ユーザーの既存データを削除（再診断対応）
        con.execute(
            "DELETE FROM diagnoses WHERE team_code = ? AND user_name = ?",
            (team_code, user_name),
        )
        con.executemany(
            """INSERT INTO diagnoses
               (team_code, user_name, department, task_name, category,
                time_reduction_pct, monthly_hours, monthly_reduction_hours,
                priority, suggested_tool, reduction_reason)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [
                (
                    team_code, user_name, department or "",
                    t["name"], t["category"],
                    t.get("time_reduction_pct", 0),
                    t.get("monthly_hours", 0.0),
                    t.get("monthly_reduction_hours", 0.0),
                    t.get("priority", "LOW"),
                    t.get("suggested_tool", ""),
                    t.get("reduction_reason", ""),
                )
                for t in tasks
            ],
        )


def get_team_data(team_code: str) -> list:
    with sqlite3.connect(_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """SELECT * FROM diagnoses
               WHERE team_code = ?
               ORDER BY user_name, monthly_reduction_hours DESC""",
            (team_code,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_task_status(team_code: str, user_name: str, task_name: str, status: str) -> None:
    with sqlite3.connect(_DB_PATH) as con:
        con.execute(
            "UPDATE diagnoses SET status = ? WHERE team_code = ? AND user_name = ? AND task_name = ?",
            (status, team_code, user_name, task_name),
        )


def team_code_exists(team_code: str) -> bool:
    with sqlite3.connect(_DB_PATH) as con:
        count = con.execute(
            "SELECT COUNT(*) FROM diagnoses WHERE team_code = ?", (team_code,)
        ).fetchone()[0]
    return count > 0
