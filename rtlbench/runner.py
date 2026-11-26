"""Run an experiment: tasks x samples through a model cascade with optional repair."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import prompts, simulate
from .cache import ResponseCache
from .extract import extract_verilog
from .pricing import cost_usd
from .providers import AnthropicProvider, MockProvider
from .tasks import Task, load_tasks
from .telemetry import Telemetry


@dataclass
class Experiment:
    name: str
    models: list[str]
    provider: str = "anthropic"
    prompt: str = "verbose"
    samples: int = 1
    repair_rounds: int = 0
    effort: str | None = None
    prompt_cache: bool = True
    response_cache: bool = True
    tasks: list[str] | None = None
    seed: int = 0
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "Experiment":
        data = yaml.safe_load(path.read_text())
        known = set(cls.__dataclass_fields__)
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(**{k: v for k, v in data.items() if k in known}, extra=extra)

    def config(self) -> dict:
        d = dict(self.__dict__)
        d.pop("extra")
        return d


def build_provider(exp: Experiment, tasks: list[Task]):
    if exp.provider == "mock":
        return MockProvider({t.id: t.reference_code for t in tasks}, seed=exp.seed)
    if exp.provider == "anthropic":
        return AnthropicProvider(effort=exp.effort, prompt_cache=exp.prompt_cache)
    raise ValueError(f"unknown provider {exp.provider!r}")


def run_experiment(exp: Experiment, tasks_root: Path, db_path: Path,
                   cache_path: Path | None = None, provider=None, log=print) -> str:
    tasks = load_tasks(tasks_root, exp.tasks)
    provider = provider or build_provider(exp, tasks)
    cache = ResponseCache(cache_path) if (exp.response_cache and cache_path) else None
    tel = Telemetry(db_path)
    run_id = tel.start_run(exp.name, exp.config())
    system = prompts.system_prompt(exp.prompt)
    cache_extra = {"provider": exp.provider, "effort": exp.effort, "seed": exp.seed}

    for task in tasks:
        for sample in range(exp.samples):
            passed, step, total_cost, total_latency, final_model = False, 0, 0.0, 0.0, None
            for model in exp.models:
                messages = [{"role": "user", "content": prompts.task_message(task)}]
                for round_ in range(exp.repair_rounds + 1):
                    key = ResponseCache.key(model, system, messages, sample, cache_extra)
                    hit = cache.get(key) if cache else None
                    comp = hit or provider.complete(model, system, messages)
                    if cache and not hit:
                        cache.put(key, comp)
                    cost = 0.0 if hit else cost_usd(model, comp.usage)

                    code = extract_verilog(comp.text)
                    if code is None:
                        sim = simulate.SimResult(False, False, None, None, "no Verilog module in response")
                    else:
                        sim = simulate.run(code, task.testbench)

                    tel.log_attempt(
                        run_id=run_id, task_id=task.id, sample=sample, step=step, model=model,
                        served_model=comp.model, input_tokens=comp.usage.input_tokens,
                        output_tokens=comp.usage.output_tokens,
                        cache_read_tokens=comp.usage.cache_read_tokens,
                        cache_write_tokens=comp.usage.cache_write_tokens, cost_usd=cost,
                        latency_s=0.0 if hit else comp.latency_s, from_cache=int(bool(hit)),
                        status=sim.status, errors=sim.errors, checks=sim.checks,
                        stop_reason=comp.stop_reason,
                    )
                    step += 1
                    total_cost += cost
                    total_latency += 0.0 if hit else comp.latency_s
                    final_model = model
                    if sim.passed:
                        passed = True
                        break
                    if round_ < exp.repair_rounds:
                        messages = messages + [
                            {"role": "assistant", "content": comp.text},
                            {"role": "user", "content": prompts.repair_message(sim.status, sim.log)},
                        ]
                if passed:
                    break
            tel.log_outcome(run_id=run_id, task_id=task.id, category=task.category,
                            sample=sample, passed=int(passed), steps=step,
                            final_model=final_model, cost_usd=total_cost,
                            latency_s=total_latency)
            log(f"  {task.id:<16} sample {sample}  {'PASS' if passed else 'FAIL'}  "
                f"steps={step}  ${total_cost:.5f}")
    return run_id
