from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ...fitness_report import FitnessReport
from . import reward as rewards

RewardConfig = rewards.RewardConfig

__all__ = ["evaluate_fitness"]


SPEED_PENALTY_PER_STEP = 0.0 # zero for first generations!


def evaluate_fitness(
    transitions: Iterable[dict[str, Any]],
    config: RewardConfig | None = None,
) -> FitnessReport:
    rules = config or rewards.RewardConfig()
    total = 0.0       # sum over finished episodes
    episode = 0.0     # running reward of the current episode
    steps = 0         # decisions in the current episode
    count = 0
    episodes = 0

    for transition in transitions:
        episode += rewards.reward_transition(transition, rules).value
        steps += 1
        count += 1
        if transition.get("done"):
            total += episode - SPEED_PENALTY_PER_STEP * steps
            episodes += 1
            episode, steps = 0.0, 0

    if count == 0:
        return FitnessReport(0.0, 0)

    if steps > 0:  # trailing episode without a done flag
        total += episode - SPEED_PENALTY_PER_STEP * steps
        episodes += 1

    # Mean per episode, so the score doesn't depend on how many episodes ran.
    return FitnessReport(total / episodes, count)