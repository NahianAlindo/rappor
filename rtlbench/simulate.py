"""Compile and simulate a candidate design against a task testbench."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

_RESULT = re.compile(r"RESULT errors=(\d+) checks=(\d+)")
_MAX_LOG = 4000


@dataclass
class SimResult:
    compiled: bool
    passed: bool
    errors: int | None
    checks: int | None
    log: str
    sim_seconds: float = 0.0

    @property
    def status(self) -> str:
        if not self.compiled:
            return "compile_error"
        if self.errors is None:
            return "sim_error"
        return "pass" if self.passed else "fail"


def simulator_available() -> bool:
    return shutil.which("iverilog") is not None and shutil.which("vvp") is not None


def run(code: str, testbench: Path, timeout: float = 20.0) -> SimResult:
    import time

    with tempfile.TemporaryDirectory(prefix="rtlbench_") as tmp:
        tmpd = Path(tmp)
        dut = tmpd / "dut.v"
        dut.write_text(code)
        binary = tmpd / "sim.vvp"
        t0 = time.perf_counter()
        comp = subprocess.run(
            ["iverilog", "-g2012", "-o", str(binary), str(dut), str(testbench)],
            capture_output=True, text=True, timeout=timeout,
        )
        if comp.returncode != 0:
            return SimResult(False, False, None, None, _clip(comp.stderr or comp.stdout),
                             time.perf_counter() - t0)
        try:
            sim = subprocess.run(["vvp", "-n", str(binary)], capture_output=True,
                                 text=True, timeout=timeout)
            out = sim.stdout + sim.stderr
        except subprocess.TimeoutExpired:
            return SimResult(True, False, None, None, "simulation timed out",
                             time.perf_counter() - t0)
        elapsed = time.perf_counter() - t0
        m = _RESULT.search(out)
        if not m:
            return SimResult(True, False, None, None, _clip(out), elapsed)
        errors, checks = int(m.group(1)), int(m.group(2))
        return SimResult(True, errors == 0 and checks > 0, errors, checks, _clip(out), elapsed)


def _clip(s: str) -> str:
    return s if len(s) <= _MAX_LOG else s[:_MAX_LOG] + "\n...[truncated]"
