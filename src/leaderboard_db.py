"""Persistent global leaderboard, backed by sqlite3 (stdlib - no new
dependency). Every function takes db_path so tests can point at a
temp file instead of the real leaderboard."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(__file__).parent / "leaderboard.db"


@dataclass(frozen=True)
class LeaderboardEntry:
    name: str
    habitat: str
    score: int
    rowid: int | None = None


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS leaderboard ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "name TEXT NOT NULL,"
        "habitat TEXT NOT NULL,"
        "score INTEGER NOT NULL,"
        "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    return connection


def add_entry(name: str, habitat: str, score: int, db_path: Path = DB_PATH) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO leaderboard (name, habitat, score) VALUES (?, ?, ?)",
            (name, habitat, score),
        )
        return cursor.lastrowid


def top_entries(limit: int = 10, db_path: Path = DB_PATH) -> list[LeaderboardEntry]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, name, habitat, score FROM leaderboard "
            "ORDER BY score DESC, created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
    return [LeaderboardEntry(rowid=row[0], name=row[1], habitat=row[2], score=row[3]) for row in rows]


def rank_of(entry_id: int, db_path: Path = DB_PATH) -> int:
    """1-based competition rank: entries with a strictly higher score all
    count, so tied entries share a rank and the next distinct score skips
    ahead (e.g. two entries tied for 2nd, the next is 4th)."""
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) + 1 FROM leaderboard "
            "WHERE score > (SELECT score FROM leaderboard WHERE id = ?)",
            (entry_id,),
        ).fetchone()
    return row[0]
