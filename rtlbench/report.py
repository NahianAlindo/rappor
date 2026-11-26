"""Summaries, comparisons and the static HTML dashboard."""
from __future__ import annotations

import html
import json
from collections import defaultdict
from dataclasses import dataclass
from statistics import mean

from . import stats
from .telemetry import Telemetry


@dataclass
class RunSummary:
    run_id: str
    experiment: str
    started_at: str
    git_sha: str | None
    config: dict
    outcomes: int
    passed: int
    pass_ci: tuple[float, float]
    pass_at_1: float
    total_cost: float
    cost_per_task: float
    cost_per_pass: float | None
    latency_p50: float
    latency_p95: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    calls: int
    avg_steps: float
    per_task: dict[str, dict]
    per_model: dict[str, dict]
    task_costs: list[float]

    @property
    def pass_rate(self) -> float:
        return self.passed / self.outcomes if self.outcomes else 0.0

    @property
    def cache_hit_rate(self) -> float:
        total = self.input_tokens + self.cache_read_tokens
        return self.cache_read_tokens / total if total else 0.0


def summarize(tel: Telemetry, run_id: str) -> RunSummary:
    db = tel.db
    run = db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if run is None:
        raise KeyError(f"no run {run_id!r}")
    outs = db.execute("SELECT * FROM outcomes WHERE run_id = ?", (run_id,)).fetchall()
    atts = db.execute("SELECT * FROM attempts WHERE run_id = ?", (run_id,)).fetchall()

    passed = sum(o["passed"] for o in outs)
    total_cost = sum(o["cost_usd"] for o in outs)
    lat = [o["latency_s"] for o in outs]

    per_task: dict[str, dict] = defaultdict(lambda: {"n": 0, "c": 0, "cost": 0.0, "steps": 0})
    for o in outs:
        t = per_task[o["task_id"]]
        t["n"] += 1
        t["c"] += o["passed"]
        t["cost"] += o["cost_usd"]
        t["steps"] += o["steps"]
        t["category"] = o["category"]

    # pass@1 from first attempts only, averaged across tasks.
    first = defaultdict(lambda: [0, 0])
    for a in atts:
        if a["step"] == 0:
            first[a["task_id"]][0] += 1
            first[a["task_id"]][1] += a["status"] == "pass"
    p1 = mean(stats.pass_at_k(n, c, 1) for n, c in first.values()) if first else 0.0

    per_model: dict[str, dict] = defaultdict(lambda: {"calls": 0, "pass": 0, "cost": 0.0})
    for a in atts:
        m = per_model[a["model"]]
        m["calls"] += 1
        m["pass"] += a["status"] == "pass"
        m["cost"] += a["cost_usd"]

    return RunSummary(
        run_id=run_id, experiment=run["experiment"], started_at=run["started_at"],
        git_sha=run["git_sha"], config=json.loads(run["config"]),
        outcomes=len(outs), passed=passed, pass_ci=stats.wilson_interval(passed, len(outs)),
        pass_at_1=p1, total_cost=total_cost,
        cost_per_task=total_cost / len(outs) if outs else 0.0,
        cost_per_pass=total_cost / passed if passed else None,
        latency_p50=stats.percentile(lat, 0.5), latency_p95=stats.percentile(lat, 0.95),
        input_tokens=sum(a["input_tokens"] or 0 for a in atts),
        output_tokens=sum(a["output_tokens"] or 0 for a in atts),
        cache_read_tokens=sum(a["cache_read_tokens"] or 0 for a in atts),
        calls=len(atts), avg_steps=mean(o["steps"] for o in outs) if outs else 0.0,
        per_task=dict(per_task), per_model=dict(per_model),
        task_costs=[o["cost_usd"] for o in outs],
    )


def _usd(x: float | None) -> str:
    return "n/a" if x is None else f"${x:.4f}"


def markdown(s: RunSummary) -> str:
    lo, hi = s.pass_ci
    lines = [
        f"## {s.experiment}  (`{s.run_id}`)",
        "",
        "| metric | value |", "|---|---|",
        f"| pass rate | {s.pass_rate:.1%} ({s.passed}/{s.outcomes}, 95% CI {lo:.1%}-{hi:.1%}) |",
        f"| pass@1 (first attempt) | {s.pass_at_1:.1%} |",
        f"| total cost | {_usd(s.total_cost)} |",
        f"| cost per task | {_usd(s.cost_per_task)} |",
        f"| cost per passing task | {_usd(s.cost_per_pass)} |",
        f"| latency p50 / p95 | {s.latency_p50:.2f}s / {s.latency_p95:.2f}s |",
        f"| model calls | {s.calls} (avg {s.avg_steps:.2f} per task) |",
        f"| tokens in / out | {s.input_tokens:,} / {s.output_tokens:,} |",
        f"| prompt cache hit rate | {s.cache_hit_rate:.1%} |",
        "",
        "| task | category | pass | cost |", "|---|---|---|---|",
    ]
    for tid, t in sorted(s.per_task.items()):
        lines.append(f"| {tid} | {t['category']} | {t['c']}/{t['n']} | {_usd(t['cost'])} |")
    return "\n".join(lines) + "\n"


def compare(a: RunSummary, b: RunSummary) -> str:
    p = stats.two_proportion_p(a.passed, a.outcomes, b.passed, b.outcomes)
    d, lo, hi = stats.bootstrap_mean_diff(a.task_costs, b.task_costs)
    rel = (d / a.cost_per_task) if a.cost_per_task else 0.0
    verdict = "significant" if p < 0.05 else "not significant"
    return "\n".join([
        f"## {a.experiment} -> {b.experiment}", "",
        "| | A | B |", "|---|---|---|",
        f"| pass rate | {a.pass_rate:.1%} | {b.pass_rate:.1%} |",
        f"| cost per task | {_usd(a.cost_per_task)} | {_usd(b.cost_per_task)} |",
        f"| cost per passing task | {_usd(a.cost_per_pass)} | {_usd(b.cost_per_pass)} |",
        f"| latency p50 | {a.latency_p50:.2f}s | {b.latency_p50:.2f}s |", "",
        f"- Pass-rate difference: {b.pass_rate - a.pass_rate:+.1%} (p = {p:.3f}, {verdict} at 0.05)",
        f"- Cost per task change: {_usd(d)} ({rel:+.0%}), 95% bootstrap CI [{_usd(lo)}, {_usd(hi)}]",
        "",
    ])


# ---------------------------------------------------------------- HTML

_CSS = """
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--card:#fff;--line:#e7e5e4;--accent:#2563eb;--good:#16a34a;--bad:#dc2626}
@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#e7e5e4;--muted:#a8a29e;--card:#1c1917;--line:#292524;--accent:#60a5fa;--good:#4ade80;--bad:#f87171}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:32px 16px}h1{margin:0 0 4px;font-size:26px}h2{font-size:18px;margin:32px 0 12px}
.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}.v{font-size:22px;font-weight:600;margin-top:2px}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);border-radius:10px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap;font-variant-numeric:tabular-nums}
th{font-size:12px;color:var(--muted);font-weight:600}tr:last-child td{border-bottom:0}
.bar{height:8px;border-radius:4px;background:var(--accent)}.barwrap{background:var(--line);border-radius:4px;width:120px}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:6px;padding:10px 12px}
.ok{color:var(--good)}.no{color:var(--bad)}code{font-size:13px}
"""


def _bar(frac: float) -> str:
    w = max(0.0, min(1.0, frac)) * 100
    return f'<div class="barwrap"><div class="bar" style="width:{w:.0f}%"></div></div>'


def html_dashboard(summaries: list[RunSummary]) -> str:
    e = html.escape
    latest_by_exp: dict[str, RunSummary] = {}
    for s in summaries:
        latest_by_exp[s.experiment] = s
    latest = list(latest_by_exp.values())
    max_cpp = max((s.cost_per_pass or 0) for s in latest) or 1.0
    best = max(latest, key=lambda s: (s.pass_rate, -(s.cost_per_pass or 1e9)), default=None)

    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
             f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>RTL LLM Benchmark</title><style>{_CSS}</style></head><body><main>",
             "<h1>RTL LLM Benchmark</h1>",
             "<p class='muted'>Functional correctness of LLM-generated Verilog, checked by "
             "simulation, with token cost and latency per task.</p>"]

    if any(s.config.get("provider") == "mock" for s in latest):
        parts.append("<p class='note'>Runs marked <b>mock</b> use the offline mock provider "
                     "that exercises the pipeline in CI. They are not real model results.</p>")
    if best:
        parts.append("<div class='grid'>")
        for k, v in [("experiments", str(len(latest))),
                     ("best pass rate", f"{best.pass_rate:.0%}"),
                     ("best config", best.experiment),
                     ("its cost / pass", _usd(best.cost_per_pass))]:
            parts.append(f"<div class='card'><div class='k'>{k}</div><div class='v'>{e(v)}</div></div>")
        parts.append("</div>")

    parts.append("<h2>Experiments (latest run of each)</h2><div class='scroll'><table><tr>"
                 "<th>experiment</th><th>models</th><th>pass rate</th><th></th><th>95% CI</th>"
                 "<th>pass@1</th><th>cost / task</th><th>cost / pass</th><th></th>"
                 "<th>p50 latency</th><th>calls / task</th><th>cache hit</th></tr>")
    for s in sorted(latest, key=lambda s: -s.pass_rate):
        lo, hi = s.pass_ci
        cpp = s.cost_per_pass or 0
        parts.append(
            f"<tr><td><b>{e(s.experiment)}</b>{' <span class=muted>(mock)</span>' if s.config.get('provider') == 'mock' else ''}</td><td>{e(' → '.join(s.config.get('models', [])))}</td>"
            f"<td>{s.pass_rate:.1%}</td><td>{_bar(s.pass_rate)}</td><td>{lo:.0%}–{hi:.0%}</td>"
            f"<td>{s.pass_at_1:.1%}</td><td>{_usd(s.cost_per_task)}</td><td>{_usd(s.cost_per_pass)}</td>"
            f"<td>{_bar(cpp / max_cpp)}</td><td>{s.latency_p50:.2f}s</td><td>{s.avg_steps:.2f}</td>"
            f"<td>{s.cache_hit_rate:.0%}</td></tr>")
    parts.append("</table></div>")

    task_ids = sorted({t for s in latest for t in s.per_task})
    parts.append("<h2>Pass rate by task</h2><div class='scroll'><table><tr><th>task</th>"
                 + "".join(f"<th>{e(s.experiment)}</th>" for s in latest) + "</tr>")
    for tid in task_ids:
        row = f"<tr><td><code>{e(tid)}</code></td>"
        for s in latest:
            t = s.per_task.get(tid)
            if not t:
                row += "<td class='muted'>–</td>"
                continue
            cls = "ok" if t["c"] == t["n"] else ("no" if t["c"] == 0 else "")
            row += f"<td class='{cls}'>{t['c']}/{t['n']}</td>"
        parts.append(row + "</tr>")
    parts.append("</table></div>")

    parts.append("<h2>Run history</h2><div class='scroll'><table><tr><th>run</th><th>experiment</th>"
                 "<th>commit</th><th>pass rate</th><th>total cost</th><th>tokens in / out</th></tr>")
    for s in reversed(summaries):
        parts.append(f"<tr><td><code>{e(s.run_id)}</code></td><td>{e(s.experiment)}</td>"
                     f"<td><code>{e(s.git_sha or '')}</code></td><td>{s.pass_rate:.1%}</td>"
                     f"<td>{_usd(s.total_cost)}</td><td>{s.input_tokens:,} / {s.output_tokens:,}</td></tr>")
    parts.append("</table></div>")
    parts.append("</main></body></html>")
    return "\n".join(parts)
