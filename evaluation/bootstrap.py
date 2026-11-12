"""Percentile bootstrap interval for the mean of per-query scores. Pass the
per-query differences of two paired runs to test whether one beats the other:
an interval above zero is a win, one that contains zero is noise."""

import numpy as np


def bootstrap_ci(values: list[float], resamples: int = 2000, seed: int = 0,
                 level: float = 0.95) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    scores = np.asarray(values, dtype=float)
    picks = np.random.default_rng(seed).integers(0, len(scores), size=(resamples, len(scores)))
    means = scores[picks].mean(axis=1)
    tail = (1 - level) / 2 * 100
    low, high = np.percentile(means, [tail, 100 - tail])
    return (round(float(low), 3), round(float(high), 3))
