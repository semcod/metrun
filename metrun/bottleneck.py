"""
metrun.bottleneck
~~~~~~~~~~~~~~~~~

Bottleneck Engine: turns raw FunctionRecords into ranked hotspots with scores
and auto-diagnosis labels.

Score formula (inspired by the problem statement):

    score = normalized_time + log_calls + nested_amplification

where

    normalized_time      = total_time / max_time   (0..1, weighted ×10)
    log_calls            = log10(calls + 1)         (dimensionless depth)
    nested_amplification = number_of_direct_children × 0.5

Diagnosis thresholds
--------------------
    🔥 loop hotspot          calls ≥ LOOP_THRESHOLD
    🌲 dependency bottleneck children ≥ DEP_THRESHOLD
    🐢 slow execution        normalized_time ≥ SLOW_THRESHOLD (no dominant call pattern)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from metrun.profiler import FunctionRecord

# -----------------------------------------------------------------------
# Tunable thresholds
# -----------------------------------------------------------------------
LOOP_THRESHOLD: int = 1_000      # calls that suggest a hot loop
DEP_THRESHOLD: int = 3           # children that suggest a fan-out bottleneck
SLOW_THRESHOLD: float = 0.3      # fraction of total wall-time to flag as slow

# Score weights
W_TIME: float = 10.0
W_NESTED: float = 0.5


@dataclass
class Bottleneck:
    """A single bottleneck entry produced by the engine."""

    name: str
    total_time: float
    calls: int
    score: float
    time_pct: float          # percentage of total traced wall-time
    diagnosis: str
    children: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)


class BottleneckEngine:
    """
    Analyse a dict of FunctionRecords and return a ranked list of Bottlenecks.

    Example::

        engine = BottleneckEngine(records)
        bottlenecks = engine.analyse()
    """

    def __init__(self, records: Dict[str, FunctionRecord]) -> None:
        self._records = records

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _total_wall_time(self) -> float:
        """Sum of all top-level (root) function times, or max if no roots exist."""
        roots = [r for r in self._records.values() if not r.parents]
        if roots:
            return sum(r.total_time for r in roots)
        # Fallback: use the maximum single function time
        if self._records:
            return max(r.total_time for r in self._records.values())
        return 1.0  # guard against division by zero

    @staticmethod
    def _compute_score(
        total_time: float,
        max_time: float,
        calls: int,
        n_children: int,
    ) -> float:
        normalized_time = (total_time / max_time) if max_time > 0 else 0.0
        log_calls = math.log10(calls + 1)
        nested_amplification = n_children * W_NESTED
        return round(W_TIME * normalized_time + log_calls + nested_amplification, 2)

    @staticmethod
    def _diagnose(
        normalized_time: float,
        calls: int,
        n_children: int,
    ) -> str:
        if calls >= LOOP_THRESHOLD:
            return "🔥 loop hotspot"
        if n_children >= DEP_THRESHOLD:
            return "🌲 dependency bottleneck"
        if normalized_time >= SLOW_THRESHOLD:
            return "🐢 slow execution"
        return "✅ nominal"

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def analyse(self) -> List[Bottleneck]:
        """Return bottlenecks sorted by score descending."""
        if not self._records:
            return []

        max_time = max(r.total_time for r in self._records.values())
        total_wall = self._total_wall_time()

        results: List[Bottleneck] = []
        for name, record in self._records.items():
            n_children = len(record.children)
            normalized_time = record.total_time / max_time if max_time > 0 else 0.0
            time_pct = (record.total_time / total_wall * 100) if total_wall > 0 else 0.0

            score = self._compute_score(
                record.total_time, max_time, record.calls, n_children
            )
            diagnosis = self._diagnose(normalized_time, record.calls, n_children)

            results.append(
                Bottleneck(
                    name=name,
                    total_time=record.total_time,
                    calls=record.calls,
                    score=score,
                    time_pct=round(time_pct, 1),
                    diagnosis=diagnosis,
                    children=list(record.children),
                    parents=list(record.parents),
                )
            )

        results.sort(key=lambda b: b.score, reverse=True)
        return results


def analyse(records: Dict[str, FunctionRecord]) -> List[Bottleneck]:
    """Convenience function: run the engine and return ranked bottlenecks."""
    return BottleneckEngine(records).analyse()
