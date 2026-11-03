"""Small SQLite store for accounts, saved analysis summaries, and progress notes."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import STORAGE_DIR

DB_PATH = Path(os.getenv("SKINAI_DB", STORAGE_DIR / "skinai.sqlite3"))


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS saved_analyses (
                analysis_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                summary_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS saved_analyses_user_date
                ON saved_analyses(user_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS progress_entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                lesion_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                analysis_id TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS progress_user_lesion_date
                ON progress_entries(user_id, lesion_id, recorded_at DESC);
            """
        )


def create_user(email: str, password_hash: str) -> dict | None:
    user_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    try:
        with _connect() as db:
            db.execute(
                "INSERT INTO users(id,email,password_hash,created_at) VALUES(?,?,?,?)",
                (user_id, email, password_hash, now),
            )
    except sqlite3.IntegrityError:
        return None
    return {"id": user_id, "email": email, "created_at": now}


def find_user_by_email(email: str) -> dict | None:
    with _connect() as db:
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def find_user(user_id: str) -> dict | None:
    with _connect() as db:
        row = db.execute(
            "SELECT id,email,created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def save_analysis(user_id: str, result: dict) -> dict | None:
    predictions = result.get("predictions") or []
    top = predictions[0] if predictions else {}
    summary = {
        "id": result["id"],
        "created_at": result["created_at"],
        "top_label": top.get("label", "unknown"),
        "top_name": top.get("name", "Unknown"),
        "risk": top.get("risk", "unknown"),
        "probability": top.get("probability", 0.0),
        "urgency": result.get("urgency", {}).get("level", "routine"),
        "demo": bool(result.get("demo")),
    }
    with _connect() as db:
        existing = db.execute(
            "SELECT user_id FROM saved_analyses WHERE analysis_id = ?", (result["id"],)
        ).fetchone()
        if existing and existing["user_id"] != user_id:
            return None
        db.execute(
            "INSERT OR REPLACE INTO saved_analyses(analysis_id,user_id,created_at,summary_json) "
            "VALUES(?,?,?,?)",
            (result["id"], user_id, result["created_at"], json.dumps(summary)),
        )
    return summary


def analysis_owner(analysis_id: str) -> str | None:
    with _connect() as db:
        row = db.execute(
            "SELECT user_id FROM saved_analyses WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
    return row["user_id"] if row else None


def is_saved(analysis_id: str) -> bool:
    return analysis_owner(analysis_id) is not None


def list_analyses(user_id: str, limit: int = 100) -> list[dict]:
    with _connect() as db:
        rows = db.execute(
            "SELECT summary_json FROM saved_analyses WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, max(1, min(limit, 100))),
        ).fetchall()
    return [json.loads(row["summary_json"]) for row in rows]


def delete_analysis(user_id: str, analysis_id: str) -> bool:
    with _connect() as db:
        result = db.execute(
            "DELETE FROM saved_analyses WHERE user_id = ? AND analysis_id = ?",
            (user_id, analysis_id),
        )
    return result.rowcount > 0


def add_progress(
    user_id: str, lesion_id: str, recorded_at: str, note: str, analysis_id: str | None
) -> dict:
    entry = {
        "id": uuid.uuid4().hex,
        "lesion_id": lesion_id,
        "recorded_at": recorded_at,
        "note": note,
        "analysis_id": analysis_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _connect() as db:
        if analysis_id:
            owner = db.execute(
                "SELECT user_id FROM saved_analyses WHERE analysis_id = ?", (analysis_id,)
            ).fetchone()
            if not owner or owner["user_id"] != user_id:
                raise ValueError("Analysis is not in this account's saved history.")
        db.execute(
            "INSERT INTO progress_entries(id,user_id,lesion_id,recorded_at,note,analysis_id,created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (
                entry["id"], user_id, lesion_id, recorded_at, note,
                analysis_id, entry["created_at"],
            ),
        )
    return entry


def list_progress(user_id: str, lesion_id: str | None = None, limit: int = 100) -> list[dict]:
    query = "SELECT id,lesion_id,recorded_at,note,analysis_id,created_at FROM progress_entries WHERE user_id = ?"
    args: list = [user_id]
    if lesion_id:
        query += " AND lesion_id = ?"
        args.append(lesion_id)
    query += " ORDER BY recorded_at DESC LIMIT ?"
    args.append(max(1, min(limit, 200)))
    with _connect() as db:
        rows = db.execute(query, args).fetchall()
    return [dict(row) for row in rows]


def delete_progress(user_id: str, entry_id: str) -> bool:
    with _connect() as db:
        result = db.execute(
            "DELETE FROM progress_entries WHERE user_id = ? AND id = ?",
            (user_id, entry_id),
        )
    return result.rowcount > 0


def delete_user(user_id: str) -> bool:
    """Remove the account and cascade-delete saved summaries and progress notes."""
    with _connect() as db:
        result = db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return result.rowcount > 0
