from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RewardConfig:
    progress: float = 1.0    # weight of "got closer to the item"
    item_range: float = 6.0  # must match RANGE in the client .env (normalizes progress)


@dataclass(frozen=True)
class Reward:
    value: float


def _number(state: Any, key: str) -> float | None:
    if not isinstance(state, dict):
        return None
    try:
        value = float(state.get(key))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _same_target(state: Any, next_state: Any) -> bool:
    if not isinstance(state, dict) or not isinstance(next_state, dict):
        return False
    old_id = state.get("target_id")
    return old_id is not None and old_id == next_state.get("target_id")


def reward_transition(transition: dict[str, Any], config: RewardConfig | None = None) -> Reward:
    rules = config or RewardConfig()
    state = transition.get("state")
    next_state = transition.get("next_state")

    old_d = _number(state, "target_distance")
    new_d = _number(next_state, "target_distance")

    # Progress: potential-based shaping. Summed over one target it telescopes to
    # (start_distance - end_distance) / item_range, so wiggling back and forth earns nothing.
    value = 0.0
    if _same_target(state, next_state) and old_d is not None and new_d is not None:
        value = rules.progress * (old_d - new_d) / rules.item_range

    return Reward(value=value)