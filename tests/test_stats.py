import math

from rtlbench import stats


def test_pass_at_k_edges():
    assert stats.pass_at_k(5, 0, 1) == 0.0
    assert stats.pass_at_k(5, 5, 1) == 1.0
    assert math.isclose(stats.pass_at_k(5, 2, 1), 0.4)
    assert math.isclose(stats.pass_at_k(4, 1, 2), 0.5)


def test_wilson_contains_point_estimate():
    lo, hi = stats.wilson_interval(7, 10)
    assert lo < 0.7 < hi
    assert stats.wilson_interval(0, 0) == (0.0, 0.0)


def test_two_proportion():
    assert stats.two_proportion_p(50, 100, 50, 100) == 1.0
    assert stats.two_proportion_p(90, 100, 50, 100) < 0.001


def test_bootstrap_sign():
    d, lo, hi = stats.bootstrap_mean_diff([1.0] * 20, [2.0] * 20)
    assert d == 1.0 and lo == 1.0 and hi == 1.0


def test_percentile():
    assert stats.percentile([1, 2, 3, 4], 0.5) == 2.5
