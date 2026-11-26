"""Prompt variants. Kept stable byte-for-byte so prompt caching can hit."""
from __future__ import annotations

from .tasks import Task

SYSTEM_VERBOSE = """You are an expert ASIC RTL design engineer.
You write clean, synthesizable Verilog-2005 that follows these rules:
- Use exactly the module name and port list given in the specification.
- Use non-blocking assignments (<=) in clocked always blocks and blocking
  assignments (=) in combinational always blocks.
- Avoid latches: assign every combinational output on every path.
- Use synchronous resets unless told otherwise.
- Do not include a testbench, $display calls, or initial blocks.
- Do not add extra ports.
Think about corner cases such as reset, wrap-around, and simultaneous events.
Reply with a single ```verilog code block containing the complete module and
nothing else."""

SYSTEM_CONCISE = """Write synthesizable Verilog-2005 for the module described.
Match the module name and ports exactly. No testbench. Reply with one
```verilog block only."""

PROMPTS = {"verbose": SYSTEM_VERBOSE, "concise": SYSTEM_CONCISE}


def system_prompt(variant: str) -> str:
    try:
        return PROMPTS[variant]
    except KeyError as e:
        raise ValueError(f"unknown prompt variant {variant!r}; choose from {list(PROMPTS)}") from e


def task_message(task: Task) -> str:
    return f"Task `{task.id}`\n\n{task.spec}"


def repair_message(status: str, log: str) -> str:
    return (f"Your design failed ({status}). Simulator output:\n\n```\n{log.strip()}\n```\n\n"
            "Fix the design and reply with the complete corrected module.")
