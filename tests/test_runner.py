from rtlbench import report
from rtlbench.runner import Experiment, run_experiment
from rtlbench.telemetry import Telemetry

from conftest import TASKS, needs_sim


def _run(tmp_path, **kw):
    exp = Experiment(name=kw.pop("name", "t"), provider="mock", response_cache=False, **kw)
    db = tmp_path / "t.db"
    rid = run_experiment(exp, TASKS, db, log=lambda *_: None)
    return report.summarize(Telemetry(db), rid)


@needs_sim
def test_large_beats_small(tmp_path):
    small = _run(tmp_path, name="s", models=["mock-small"], samples=4)
    large = _run(tmp_path, name="l", models=["mock-large"], samples=4)
    assert large.pass_rate > small.pass_rate
    assert large.cost_per_task > small.cost_per_task


@needs_sim
def test_cascade_escalates_only_on_failure(tmp_path):
    s = _run(tmp_path, models=["mock-small", "mock-large"], samples=3)
    assert 1.0 <= s.avg_steps < 2.0
    assert s.per_model["mock-small"]["calls"] == s.outcomes


@needs_sim
def test_html_renders(tmp_path):
    s = _run(tmp_path, models=["mock-large"], tasks=["mux4", "adder8"])
    page = report.html_dashboard([s])
    assert "<table>" in page and "mux4" in page


@needs_sim
def test_response_cache_avoids_cost(tmp_path):
    exp = Experiment(name="c", provider="mock", models=["mock-large"], tasks=["mux4"],
                     response_cache=True)
    db, cache = tmp_path / "t.db", tmp_path / "cache.db"
    first = run_experiment(exp, TASKS, db, cache, log=lambda *_: None)
    second = run_experiment(exp, TASKS, db, cache, log=lambda *_: None)
    tel = Telemetry(db)
    assert report.summarize(tel, first).total_cost > 0
    assert report.summarize(tel, second).total_cost == 0
