"""Exact edge times avoid quantizing duty ratio to the integration grid."""

import math


def bridge_level(modulation: float, phase: float) -> int:
    carrier = 4 * abs(phase % 1 - 0.5) - 1
    return int(modulation >= carrier) - int(-modulation >= carrier)


def switching_edges(modulation: float) -> tuple[float, ...]:
    if not math.isfinite(modulation) or abs(modulation) > 1:
        raise ValueError("modulation must be finite and in [-1, 1]")
    a = abs(modulation)
    return (0.0, (1 - a) / 4, (1 + a) / 4, (3 - a) / 4, (3 + a) / 4, 1.0)


def segments(modulation: float, start: float, stop: float):
    """Yield (fraction of carrier period, bridge level) inside [start, stop]."""
    boundaries = [start, *(x for x in switching_edges(modulation) if start < x < stop), stop]
    for left, right in zip(boundaries[:-1], boundaries[1:], strict=True):
        if right > left:
            yield right - left, bridge_level(modulation, (left + right) / 2)
