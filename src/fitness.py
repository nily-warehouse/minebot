from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

from .reward import RewardConfig, _vector, reward_transition

NO_DATA_FITNESS = 0


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

    rules = config or RewardConfig()
    best: dict[Any, float] = {}
    total = 0.0
    kills = 0
    count = 0

    for transition in transitions:
        reward = reward_transition(transition, rules)
        total += reward.value
        kills += reward.inferred_kill
        count += 1

        state = transition.get("state")
        next_state = transition.get("next_state")
        if isinstance(state, dict) and isinstance(next_state, dict):
            target_id = state.get("target_id")
            if target_id is not None and target_id == next_state.get("target_id"):
                target = _vector(state, "target_position")
                old_position = _vector(state, "position")
                new_position = _vector(next_state, "position")
                if target is not None and old_position is not None and new_position is not None:
                    d_old = math.hypot(target[0] - old_position[0], target[2] - old_position[2])
                    d_new = math.hypot(target[0] - new_position[0], target[2] - new_position[2])
                    best_dist = min(best.get(target_id, d_old), d_old)
                    gain = max(0.0, best_dist - d_new)
                    best[target_id] = min(best_dist, d_new)
                    if d_new >= rules.attack_range:
                        total += rules.progress * gain

        if transition.get("done"):
            best.clear()

    if not count:
        return FitnessReport(NO_DATA_FITNESS, transitions=0, inferred_kills=0)

    return FitnessReport(total / expected_episodes, count, kills)
