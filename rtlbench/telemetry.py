"""SQLite telemetry: one row per model call, one row per task outcome."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    experiment TEXT NOT NULL,
    config TEXT NOT NULL,
    git_sha TEXT,
    started_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    sample INTEGER NOT NULL,
    step INTEGER NOT NULL,
    model TEXT NOT NULL,
    served_model TEXT,
    input_tokens INTEGER, output_tokens INTEGER,
    cache_read_tokens INTEGER, cache_write_tokens INTEGER,
    cost_usd REAL, latency_s REAL, from_cache INTEGER,
    status TEXT, errors INTEGER, checks INTEGER, stop_reason TEXT,
    ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    category TEXT,
    sample INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    steps INTEGER NOT NULL,
    final_model TEXT,
    cost_usd REAL, latency_s REAL,
    PRIMARY KEY (run_id, task_id, sample)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class Telemetry:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def start_run(self, experiment: str, config: dict) -> str:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?)",
                        (run_id, experiment, json.dumps(config, sort_keys=True), _git_sha(), _now()))
        self.db.commit()
        return run_id

    def log_attempt(self, **row) -> None:
        row.setdefault("ts", _now())
        cols = ", ".join(row)
        qs = ", ".join("?" for _ in row)
        self.db.execute(f"INSERT INTO attempts ({cols}) VALUES ({qs})", tuple(row.values()))

    def log_outcome(self, **row) -> None:
        cols = ", ".join(row)
        qs = ", ".join("?" for _ in row)
        self.db.execute(f"INSERT OR REPLACE INTO outcomes ({cols}) VALUES ({qs})",
                        tuple(row.values()))
        self.db.commit()

    def runs(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM runs ORDER BY started_at, run_id").fetchall()

    def latest_run(self, experiment: str | None = None) -> str | None:
        q = "SELECT run_id FROM runs"
        args: tuple = ()
        if experiment:
            q += " WHERE experiment = ?"
            args = (experiment,)
        row = self.db.execute(q + " ORDER BY started_at DESC, run_id DESC LIMIT 1", args).fetchone()
        return row["run_id"] if row else None
