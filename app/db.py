import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "grants.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                organization_name TEXT NOT NULL,
                project_title TEXT NOT NULL,
                funder_name TEXT NOT NULL,
                request_json TEXT NOT NULL,
                draft TEXT NOT NULL
            )
            """
        )


def save_draft(
    organization_name: str,
    project_title: str,
    funder_name: str,
    request_json: str,
    draft: str,
) -> sqlite3.Row:
    created_at = datetime.now(UTC).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO drafts
                (created_at, organization_name, project_title, funder_name, request_json, draft)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (created_at, organization_name, project_title, funder_name, request_json, draft),
        )
        draft_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    return row


def list_drafts(limit: int = 20, offset: int = 0) -> list[sqlite3.Row]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, organization_name, project_title, funder_name
            FROM drafts
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return rows


def get_draft(draft_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    return row
