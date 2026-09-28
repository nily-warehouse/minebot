from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


ATTACK_ACTION = 11
EYE_HEIGHT = 1.62
ZOMBIE_CENTER_HEIGHT = 0.975


@dataclass(frozen=True)
class RewardConfig:
    progress_scale: float = 2.0
    max_progress: float = 1.0
    attack_range: float = 3.3
    hit_radius: float = 0.5
    close_attack: float = 0.1
    wasted_attack: float = -0.04
    damage_scale: float = -2.5
    kill: float = 100.0


@dataclass(frozen=True)
class Reward:
    value: float
    inferred_kill: bool


def _distance(state: Any) -> float | None:
    if not isinstance(state, dict):
        return None
    target = state.get("target")
    if not isinstance(target, (list, tuple)) or len(target) < 3:
        return None
    try:
        values = [float(component) for component in target[:3]]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in values):
        return None
    distance = math.hypot(*values)
    return distance if math.isfinite(distance) else None


def _health(state: Any) -> float | None:
    if not isinstance(state, dict):
        return None
    try:
        value = float(state.get("health"))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _observed_no_target(state: Any) -> bool:
    """True only for a valid observation that explicitly has no target."""
    return isinstance(state, dict) and "target" in state and state["target"] is None


def _is_aimed_at_target(state: Any, rules: RewardConfig) -> bool:
    """True if the bot looks at the zombie and is within attack range."""
    if not isinstance(state, dict):
        return False
    try:
        yaw = float(state["yaw"])
        pitch = float(state["pitch"])
        dx, dy, dz = (float(component) for component in state["target"][:3])
    except (KeyError, TypeError, ValueError):
        return False
    dy += ZOMBIE_CENTER_HEIGHT - EYE_HEIGHT  # from the eyes to the zombie's center
    if not all(math.isfinite(value) for value in (yaw, pitch, dx, dy, dz)):
        return False

    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if distance == 0 or distance > rules.attack_range:
        return False

    look = (
        -math.sin(yaw) * math.cos(pitch),
        math.sin(pitch),
        -math.cos(yaw) * math.cos(pitch),
    )
    cosine = (look[0] * dx + look[1] * dy + look[2] * dz) / distance
    angle = math.acos(max(-1.0, min(1.0, cosine)))
    return angle <= math.atan2(rules.hit_radius, distance)


def _progress_reward(old_distance: float, new_distance: float, rules: RewardConfig) -> float:
    progress = max(-rules.max_progress, min(rules.max_progress, old_distance - new_distance))
    return rules.progress_scale * progress


def _attack_reward(state: Any, rules: RewardConfig) -> float:
    return rules.close_attack if _is_aimed_at_target(state, rules) else rules.wasted_attack


def reward_transition(transition: dict[str, Any], config: RewardConfig | None = None) -> Reward:
    rules = config or RewardConfig()
    state = transition.get("state")
    next_state = transition.get("next_state")
    done = bool(transition.get("done", False))
    try:
        action = int(transition.get("action", -1))
    except (TypeError, ValueError):
        action = -1

    old_distance = _distance(state)
    new_distance = _distance(next_state)
    inferred_kill = old_distance is not None and _observed_no_target(next_state) and not done

    value = 0.0
    if old_distance is not None and new_distance is not None:
        value += _progress_reward(old_distance, new_distance, rules)
    if inferred_kill:
        value += rules.kill
    if action == ATTACK_ACTION:
        value += _attack_reward(state, rules)

    old_health = _health(state)
    new_health = _health(next_state)
    if old_health is not None and new_health is not None:
        value += rules.damage_scale * max(0.0, old_health - new_health)

    return Reward(value=value, inferred_kill=inferred_kill)