import pytest

from rtlbench import simulate
from rtlbench.providers import _break
from rtlbench.tasks import load_tasks

from conftest import TASKS, needs_sim

ALL = load_tasks(TASKS)


@needs_sim
@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_reference_passes(task):
    r = simulate.run(task.reference_code, task.testbench)
    assert r.passed, r.log


@needs_sim
@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_testbench_catches_bugs(task):
    import random

    broken = _break(task.reference_code, random.Random(1))
    assert broken != task.reference_code
    r = simulate.run(broken, task.testbench)
    assert not r.passed, f"{task.id}: testbench accepted a mutated design"


@needs_sim
def test_compile_error_reported():
    r = simulate.run("module mux4(; endmodule", ALL[0].testbench)
    assert r.status == "compile_error"
