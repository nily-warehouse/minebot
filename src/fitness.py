from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .reward import RewardConfig, reward_transition

NO_DATA_FITNESS = -100.0


@dataclass(frozen=True)
class FitnessReport:
    fitness: float
    transitions: int
    inferred_kills: int


def evaluate_fitness(
    transitions: Iterable[dict[str, Any]],
    expected_episodes: int = 1,
    config: RewardConfig | None = None,
) -> FitnessReport:
    if expected_episodes < 1:
        raise ValueError("expected_episodes must be at least 1")

    rewards = [reward_transition(transition, config) for transition in transitions]
    if not rewards:
        return FitnessReport(NO_DATA_FITNESS, transitions=0, inferred_kills=0)

    total = sum(reward.value for reward in rewards)
    kills = sum(reward.inferred_kill for reward in rewards)
    return FitnessReport(total / expected_episodes, len(rewards), kills)