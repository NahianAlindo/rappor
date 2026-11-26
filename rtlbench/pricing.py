from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_PRICING_FILE = Path(__file__).with_name("pricing.yaml")


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cache_read_tokens + other.cache_read_tokens,
            self.cache_write_tokens + other.cache_write_tokens,
        )


@lru_cache(maxsize=1)
def _table() -> dict:
    with open(_PRICING_FILE) as f:
        return yaml.safe_load(f)


def cost_usd(model: str, usage: Usage) -> float:
    table = _table()
    try:
        p = table["models"][model]
    except KeyError as e:
        raise KeyError(f"no pricing for model {model!r}; add it to pricing.yaml") from e
    mult = table.get("cache_write_multiplier", 1.25)
    return (
        usage.input_tokens * p["input"]
        + usage.cache_write_tokens * p["input"] * mult
        + usage.cache_read_tokens * p["cache_read"]
        + usage.output_tokens * p["output"]
    ) / 1_000_000
