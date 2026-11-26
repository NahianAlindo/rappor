"""Small, dependency-free statistics helpers."""
from __future__ import annotations

import math
import random
from statistics import mean


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al., 2021) for n samples, c correct."""
    if n < k:
        raise ValueError("need n >= k")
    if n - c < k:
        return 1.0
    return 1.0 - math.prod((n - c - i) / (n - i) for i in range(k))


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def two_proportion_p(s1: int, n1: int, s2: int, n2: int) -> float:
    """Two-sided p-value for a difference in pass rates (pooled z-test)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p = (s1 + s2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (s1 / n1 - s2 / n2) / se
    return math.erfc(abs(z) / math.sqrt(2))


def bootstrap_mean_diff(a: list[float], b: list[float], iters: int = 2000,
                        seed: int = 0) -> tuple[float, float, float]:
    """Mean(b) - mean(a) with a 95% bootstrap interval."""
    if not a or not b:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    diffs = sorted(
        mean(rng.choices(b, k=len(b))) - mean(rng.choices(a, k=len(a))) for _ in range(iters)
    )
    return (mean(b) - mean(a), diffs[int(0.025 * iters)], diffs[int(0.975 * iters) - 1])


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = (len(s) - 1) * q
    lo, hi = math.floor(idx), math.ceil(idx)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)
