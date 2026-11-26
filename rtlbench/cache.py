"""Local response cache so re-running an experiment does not re-bill."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .pricing import Usage
from .providers import Completion


class ResponseCache:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, body TEXT)")

    @staticmethod
    def key(model: str, system: str, messages: list[dict], sample: int, extra: dict) -> str:
        blob = json.dumps({"m": model, "s": system, "msgs": messages, "i": sample, "x": extra},
                          sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key: str) -> Completion | None:
        row = self._db.execute("SELECT body FROM responses WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        d = json.loads(row[0])
        return Completion(d["text"], Usage(**d["usage"]), d["latency_s"], d["model"],
                          d.get("stop_reason", ""))

    def put(self, key: str, c: Completion) -> None:
        body = json.dumps({"text": c.text, "usage": c.usage.__dict__, "latency_s": c.latency_s,
                           "model": c.model, "stop_reason": c.stop_reason})
        self._db.execute("INSERT OR REPLACE INTO responses VALUES (?, ?)", (key, body))
        self._db.commit()
