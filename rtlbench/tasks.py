from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Task:
    id: str
    module: str
    category: str
    difficulty: str
    spec: str
    testbench: Path
    reference: Path

    @property
    def reference_code(self) -> str:
        return self.reference.read_text()


def load_task(path: Path) -> Task:
    meta = yaml.safe_load((path / "task.yaml").read_text())
    return Task(
        id=meta["id"],
        module=meta["module"],
        category=meta.get("category", "misc"),
        difficulty=meta.get("difficulty", "unknown"),
        spec=(path / "spec.md").read_text().strip(),
        testbench=path / "tb.v",
        reference=path / "ref.v",
    )


def load_tasks(root: Path, ids: list[str] | None = None) -> list[Task]:
    tasks = [load_task(p) for p in sorted(root.iterdir()) if (p / "task.yaml").exists()]
    if ids:
        wanted = set(ids)
        missing = wanted - {t.id for t in tasks}
        if missing:
            raise ValueError(f"unknown task ids: {sorted(missing)}")
        tasks = [t for t in tasks if t.id in wanted]
    return tasks
