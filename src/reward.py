from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


ATTACK_ACTION = 11
MAX_PROGRESS = 1.0
ATTACK_RANGE = 3.3
HIT_RADIUS = 0.5
EYE_HEIGHT = 1.62
ZOMBIE_CENTER_HEIGHT = 0.975


@dataclass(frozen=True)
class RewardConfig:
    progress: float = 1
    kill: float = 100
    aimed_attack: float = 20
    damage: float = -5


@dataclass(frozen=True)
class Reward:
    value: float
    inferred_kill: bool


def _offset(state: Any) -> tuple[float, float, float] | None:
    if not isinstance(state, dict):
        return None
    try:
        x, y, z = (float(value) for value in state.get("target"))
    except (TypeError, ValueError):
        return None
    return (x, y, z) if all(math.isfinite(value) for value in (x, y, z)) else None


def _health(state: Any) -> float | None:
    if not isinstance(state, dict):
        return None
    try:
        value = float(state.get("health"))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _has_no_target(state: Any) -> bool:
    return isinstance(state, dict) and "target" in state and state["target"] is None


def _is_aimed(state: Any) -> bool:
    offset = _offset(state)
    if offset is None:
        return False
    try:
        yaw = float(state["yaw"])
        pitch = float(state["pitch"])
    except (KeyError, TypeError, ValueError):
        return False
    if not (math.isfinite(yaw) and math.isfinite(pitch)):
        return False

    dx, dy, dz = offset
    dy += ZOMBIE_CENTER_HEIGHT - EYE_HEIGHT  # aim from the eyes at the zombie's center
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if not 0 < distance <= ATTACK_RANGE:
        return False

    look = (
        -math.sin(yaw) * math.cos(pitch),
        math.sin(pitch),
        -math.cos(yaw) * math.cos(pitch),
    )
    cosine = (look[0] * dx + look[1] * dy + look[2] * dz) / distance
    angle = math.acos(max(-1.0, min(1.0, cosine)))
    return angle <= math.atan2(HIT_RADIUS, distance)


def reward_transition(transition: dict[str, Any], config: RewardConfig | None = None) -> Reward:
    rules = config or RewardConfig()
    state = transition.get("state")
    next_state = transition.get("next_state")
    done = bool(transition.get("done", False))

    old_offset = _offset(state)
    new_offset = _offset(next_state)
    killed = old_offset is not None and _has_no_target(next_state) and not done

    value = 0.0
    if old_offset is not None and new_offset is not None:
        progress = math.hypot(*old_offset) - math.hypot(*new_offset)
        value += rules.progress * max(-MAX_PROGRESS, min(MAX_PROGRESS, progress))
    if killed:
        value += rules.kill
    if transition.get("action") == ATTACK_ACTION and _is_aimed(state):
        value += rules.aimed_attack

    old_health = _health(state)
    new_health = _health(next_state)
    if old_health is not None and new_health is not None:
        value += rules.damage * max(0.0, old_health - new_health)

    return Reward(value=value, inferred_kill=killed)