"""Pull Verilog source out of a model response."""
from __future__ import annotations

import re

_FENCE = re.compile(r"```[ \t]*(?:verilog|systemverilog|sv|v)?[ \t]*\n(.*?)```", re.S | re.I)
_MODULE = re.compile(r"\bmodule\b.*?\bendmodule\b", re.S)


def extract_verilog(text: str) -> str | None:
    """Return the code block that defines a module, or None if there isn't one.

    Prefers fenced blocks; falls back to the first bare module...endmodule span.
    """
    for block in _FENCE.findall(text):
        if _MODULE.search(block):
            return block.strip() + "\n"
    m = _MODULE.search(text)
    return m.group(0).strip() + "\n" if m else None
