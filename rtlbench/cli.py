from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import report, simulate
from .runner import Experiment, run_experiment
from .tasks import load_tasks
from .telemetry import Telemetry

DEFAULT_DB = Path("results/telemetry.db")
DEFAULT_CACHE = Path(".cache/responses.db")


def cmd_check(args) -> int:
    if not simulate.simulator_available():
        print("iverilog/vvp not found on PATH", file=sys.stderr)
        return 2
    bad = 0
    for t in load_tasks(args.tasks):
        r = simulate.run(t.reference_code, t.testbench)
        print(f"{t.id:<16} {r.status:<14} checks={r.checks}")
        bad += not r.passed
    return 1 if bad else 0


def cmd_run(args) -> int:
    for path in args.experiments:
        exp = Experiment.from_yaml(Path(path))
        print(f"[{exp.name}] models={exp.models} samples={exp.samples} repair={exp.repair_rounds}")
        run_id = run_experiment(exp, args.tasks, args.db,
                                None if args.no_cache else args.cache)
        print(report.markdown(report.summarize(Telemetry(args.db), run_id)))
    return 0


def cmd_report(args) -> int:
    tel = Telemetry(args.db)
    runs = tel.runs()
    if not runs:
        print("no runs recorded", file=sys.stderr)
        return 1
    summaries = [report.summarize(tel, r["run_id"]) for r in runs]
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(report.html_dashboard(summaries))
        print(f"wrote {args.html}")
    latest = {s.experiment: s for s in summaries}
    md = "".join(report.markdown(s) + "\n" for s in latest.values())
    if args.markdown:
        args.markdown.write_text("# Results\n\n" + md)
    else:
        print(md)
    return 0


def cmd_compare(args) -> int:
    tel = Telemetry(args.db)
    ids = []
    for name in (args.a, args.b):
        rid = tel.latest_run(name) or name
        ids.append(rid)
    print(report.compare(report.summarize(tel, ids[0]), report.summarize(tel, ids[1])))
    return 0


def cmd_gate(args) -> int:
    tel = Telemetry(args.db)
    rid = tel.latest_run(args.experiment)
    if rid is None:
        print(f"no run for {args.experiment!r}", file=sys.stderr)
        return 2
    s = report.summarize(tel, rid)
    problems = []
    if s.pass_rate < args.min_pass:
        problems.append(f"pass rate {s.pass_rate:.1%} < {args.min_pass:.1%}")
    if args.max_cost_per_task is not None and s.cost_per_task > args.max_cost_per_task:
        problems.append(f"cost/task ${s.cost_per_task:.4f} > ${args.max_cost_per_task:.4f}")
    if problems:
        print("GATE FAILED: " + "; ".join(problems))
        return 1
    print(f"gate ok: pass {s.pass_rate:.1%}, cost/task ${s.cost_per_task:.4f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rtlbench")
    p.add_argument("--tasks", type=Path, default=Path("tasks"))
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check-tasks", help="verify every reference design passes its testbench")

    r = sub.add_parser("run", help="run one or more experiment configs")
    r.add_argument("experiments", nargs="+")
    r.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    r.add_argument("--no-cache", action="store_true")

    rep = sub.add_parser("report", help="summarize recorded runs")
    rep.add_argument("--html", type=Path)
    rep.add_argument("--markdown", type=Path)

    c = sub.add_parser("compare", help="compare two experiments (latest runs) or run ids")
    c.add_argument("a")
    c.add_argument("b")

    g = sub.add_parser("gate", help="fail if the latest run regresses")
    g.add_argument("experiment")
    g.add_argument("--min-pass", type=float, default=0.9)
    g.add_argument("--max-cost-per-task", type=float)

    args = p.parse_args(argv)
    return {"check-tasks": cmd_check, "run": cmd_run, "report": cmd_report,
            "compare": cmd_compare, "gate": cmd_gate}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
