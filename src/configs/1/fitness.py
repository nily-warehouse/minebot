from __future__ import annotations

from typing import Any, Iterable

from ...fitness_report import FitnessReport

__all__ = ["evaluate_fitness"]


def evaluate_fitness(transitions: Iterable[dict[str, Any]]) -> FitnessReport:
    transitions = list(transitions)
    # TODO: fitness design goes here
    return FitnessReport(0.0, len(transitions))
