from pathlib import Path

import pytest

from rtlbench import simulate

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"

needs_sim = pytest.mark.skipif(not simulate.simulator_available(),
                               reason="iverilog not installed")
