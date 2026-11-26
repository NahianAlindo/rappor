# rtlbench

A small harness for measuring how well LLMs write Verilog, and what it costs.

Each task has a written spec, a self-checking testbench and a reference
design. A model gets the spec, its answer is compiled and simulated with
Icarus Verilog, and every call is logged with tokens, cost, latency and
pass/fail. The goal is to compare setups (model choice, prompt, repair loops,
cheap-then-expensive cascades) on **cost per passing design**, not just
accuracy.

**Live report:** https://nahianalindo.github.io/rappor/ (rebuilt by CI on every push)

## What it measures

| metric | how |
|---|---|
| Functional correctness | Testbench compares the DUT against a behavioural model over hundreds of random and directed vectors |
| pass rate + 95% CI | Wilson interval over task × sample outcomes |
| pass@1 | Unbiased estimator over first attempts |
| cost per task / per pass | Token usage × `rtlbench/pricing.yaml`, including prompt-cache reads and writes |
| latency p50 / p95 | Wall-clock per task, summed across escalations and repairs |
| A/B significance | Two-proportion z-test on pass rate, bootstrap CI on cost difference |

## Cost levers it can test

- **Model routing:** `models: [cheap, strong]` tries the cheap model first and
  escalates only when simulation fails.
- **Repair loop:** `repair_rounds: N` feeds the compiler or simulator output
  back to the model.
- **Prompt variants:** `prompt: verbose | concise` in `rtlbench/prompts.py`.
- **Prompt caching:** the system prompt is kept byte-stable and marked
  cacheable, and the cache hit rate is reported.
- **Effort:** `effort: low | medium | high` for models that support it.
- **Response cache:** re-running an experiment replays stored responses at
  zero cost (`.cache/responses.db`).

## Quick start

```bash
sudo apt-get install -y iverilog
pip install -e ".[dev]"

rtlbench check-tasks                      # every reference design passes its testbench
pytest -q                                 # unit tests, incl. mutation checks on testbenches
rtlbench run experiments/mock/*.yaml      # offline run, no API key needed
rtlbench compare mock-large-only mock-cascade
rtlbench report --html site/index.html
```

Real models (needs `ANTHROPIC_API_KEY`):

```bash
rtlbench run experiments/haiku_only.yaml experiments/cascade.yaml
rtlbench compare haiku-only cascade-haiku-opus
```

## Layout

```
tasks/<id>/        spec.md, tb.v (self-checking), ref.v, task.yaml
experiments/       YAML configs; experiments/mock/ runs offline in CI
rtlbench/
  runner.py        task × sample loop, cascade + repair
  simulate.py      iverilog/vvp wrapper, parses "RESULT errors=N checks=M"
  providers.py     Anthropic API provider and a deterministic mock
  telemetry.py     SQLite: runs, attempts (per call), outcomes (per task)
  report.py        summaries, comparisons, static HTML report
  stats.py         pass@k, Wilson CI, z-test, bootstrap
```

## Tasks

| id | category | notes |
|---|---|---|
| mux4 | combinational | 8-bit 4:1 mux |
| adder8 | arithmetic | carry in/out |
| prio_enc8 | combinational | exhaustive check |
| alu4 | arithmetic | 8 ops, exhaustive check |
| counter4 | sequential | sync reset, enable |
| edge_detect | sequential | rising-edge pulse |
| shift_reg8 | sequential | load / shift priority |
| seq_detect_101 | fsm | Moore, overlapping |
| sync_fifo | memory | 4-deep, fall-through, full/empty |

Adding a task: create `tasks/<id>/` with the four files. The testbench must end by
printing `RESULT errors=<n> checks=<m>`. `pytest` checks that the reference passes
and that a mutated design fails.

## CI

`.github/workflows/ci.yml` installs Icarus Verilog, runs the tests and the mock
benchmark, fails if the cascade's pass rate or cost per task regresses, and deploys
the HTML report to GitHub Pages.

The numbers on the live report come from the **mock provider**. It exists to
exercise the pipeline without API keys, so it shows how the report looks, not how
real models perform. Run the configs in `experiments/` with an API key to get real
results.

## Limitations

- The tasks are small. Real RTL work involves larger designs, existing code,
  lint and CDC checks.
- Testbenches are random and directed, not formal, so a design can pass and still be wrong.
- Prices in `pricing.yaml` must be kept current by hand.

## License

MIT
