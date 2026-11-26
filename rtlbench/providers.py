"""Model providers. Each returns text plus token usage and latency."""
from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass

from .pricing import Usage


@dataclass
class Completion:
    text: str
    usage: Usage
    latency_s: float
    model: str            # model that actually served the request
    stop_reason: str = "end_turn"


class AnthropicProvider:
    # Models that accept server-side refusal fallbacks.
    _FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}

    def __init__(self, effort: str | None = None, prompt_cache: bool = True,
                 max_tokens: int = 4096):
        import anthropic

        self._client = anthropic.Anthropic()
        self.effort = effort
        self.prompt_cache = prompt_cache
        self.max_tokens = max_tokens

    def complete(self, model: str, system: str, messages: list[dict]) -> Completion:
        if self.prompt_cache:
            system_param = [{"type": "text", "text": system,
                             "cache_control": {"type": "ephemeral"}}]
        else:
            system_param = system
        kwargs: dict = dict(model=model, max_tokens=self.max_tokens,
                            system=system_param, messages=messages)
        if self.effort:
            kwargs["output_config"] = {"effort": self.effort}

        t0 = time.perf_counter()
        if model in self._FALLBACK_MODELS:
            resp = self._client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
        else:
            resp = self._client.messages.create(**kwargs)
        latency = time.perf_counter() - t0

        text = "".join(b.text for b in resp.content if b.type == "text")
        u = resp.usage
        usage = Usage(
            input_tokens=u.input_tokens or 0,
            output_tokens=u.output_tokens or 0,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )
        return Completion(text, usage, latency, resp.model, resp.stop_reason or "")


class MockProvider:
    """Deterministic offline provider for tests and CI.

    Returns the task's reference design with probability `skill[model]`,
    otherwise a design with a planted bug. Token counts are estimated from
    text length so cost reports have realistic shape.
    """

    def __init__(self, references: dict[str, str], skill: dict[str, float] | None = None,
                 seed: int = 0):
        self.references = references
        self.skill = skill or {"mock-small": 0.6, "mock-large": 0.95}
        self.seed = seed
        self._calls: dict[str, int] = {}

    def complete(self, model: str, system: str, messages: list[dict]) -> Completion:
        prompt = system + "".join(m["content"] for m in messages)
        task_id = next((t for t in self.references if f"`{t}`" in prompt), None)
        if task_id is None:
            raise ValueError("mock provider could not identify the task")
        key = f"{model}:{task_id}:{len(messages)}"
        n = self._calls[key] = self._calls.get(key, 0) + 1
        h = hashlib.sha256(f"{self.seed}:{key}:{n}".encode()).digest()
        rng = random.Random(h)
        # Later repair turns get a bonus: the error log helps.
        p = min(1.0, self.skill.get(model, 0.5) + 0.15 * (len(messages) // 2))
        code = self.references[task_id]
        if rng.random() >= p:
            code = _break(code, rng)
        text = f"```verilog\n{code}```"
        usage = Usage(input_tokens=len(prompt) // 4, output_tokens=len(text) // 4)
        return Completion(text, usage, 0.2 + rng.random() * 0.8, model)


def _break(code: str, rng: random.Random) -> str:
    swaps = [("<= 1'b0", "<= 1'b1"), ("+ 1", "- 1"), ("& ", "| "), ("== ", "!= "),
             ("? 4'd1 : 4'd0", "? 4'd0 : 4'd1"), ("q[6:0], sin", "sin, q[7:1]")]
    rng.shuffle(swaps)
    for a, b in swaps:
        if a in code:
            return code.replace(a, b, 1)
    return code.replace("endmodule", "  wire syntax_error = ;\nendmodule", 1)
