from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...actions import attack_index


ATTACK_ACTION = attack_index(Path(__file__).resolve().with_name("actions.json"))


@dataclass(frozen=True)
class RewardConfig:
    attack_action: int | None = ATTACK_ACTION
    progress: float = 2  # 10 blocks of approach pays 20, versus 80 for one hit
    attack_range: float = 2.5
    kill: float = 40 # same as damage_dealt
    aimed_attack: float = 0  # fallback
    damage_dealt: float = 40 # per-health
    damage: float = 0


@dataclass(frozen=True)
class Reward:
    value: float
    inferred_kill: bool


def _vector(state: Any, key: str) -> tuple[float, float, float] | None:
    if not isinstance(state, dict):
        return None
    try:
        x, y, z = (float(value) for value in state.get(key))
    except (TypeError, ValueError):
        return None
    return (x, y, z) if all(math.isfinite(value) for value in (x, y, z)) else None


def _offset(state: Any) -> tuple[float, float, float] | None:
    return _vector(state, "target")


def _number(state: Any, key: str) -> float | None:
    if not isinstance(state, dict):
        return None
    try:
        value = float(state.get(key))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _health(state: Any) -> float | None:
    return _number(state, "health")


def _target_health(state: Any) -> float | None:
    return _number(state, "target_health")


def _has_no_target(state: Any) -> bool:
    return isinstance(state, dict) and "target" in state and state["target"] is None


def _same_target(state: Any, next_state: Any) -> bool:
    if not isinstance(state, dict) or not isinstance(next_state, dict):
        return False
    old_id = state.get("target_id")
    return old_id is not None and old_id == next_state.get("target_id")


def reward_transition(transition: dict[str, Any], config: RewardConfig | None = None) -> Reward:
    rules = config or RewardConfig()
    state = transition.get("state")
    next_state = transition.get("next_state")
    done = bool(transition.get("done", False))

    old_offset = _offset(state)
    new_offset = _offset(next_state)

    same_target = _same_target(state, next_state)
    old_th = _target_health(state)
    new_th = _target_health(next_state)

    killed = (
        old_offset is not None and not done and isinstance(next_state, dict) and (
            next_state.get("target_killed") is True
            or (same_target and old_th is not None and old_th > 0
                and new_th is not None and new_th <= 0)
            or (old_th is None and _has_no_target(next_state))  # فقط دیتای قدیمی
       )
    )

    value = 0.0

    # Kill
    if killed:
        value += rules.kill

    # Damage dealt (dense), with attack_hit as fallback
    if same_target and old_th is not None and new_th is not None:
        value += rules.damage_dealt * max(0.0, old_th - new_th)
    elif (
        rules.attack_action is not None
        and transition.get("action") == rules.attack_action
        and isinstance(next_state, dict)
        and next_state.get("attack_hit") is True
    ):
        value += rules.aimed_attack

    # Damage taken
    old_health = _health(state)
    new_health = _health(next_state)
    if old_health is not None and new_health is not None:
        value += rules.damage * max(0.0, old_health - new_health)

    return Reward(value=value, inferred_kill=killed)
