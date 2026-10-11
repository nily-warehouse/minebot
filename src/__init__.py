from typing import Any, Iterable

from .configs import fitness_module, reward_module
from .fitness_report import FitnessReport

RewardConfig = reward_module().RewardConfig
reward_transition = reward_module().reward_transition


def evaluate_fitness(
    transitions: Iterable[dict[str, Any]],
    config_id: int = 1,
) -> FitnessReport:
    return fitness_module(config_id).evaluate_fitness(transitions)


__all__ = [
    "FitnessReport",
    "RewardConfig",
    "evaluate_fitness",
    "reward_transition",
]
