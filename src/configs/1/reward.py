from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["RewardConfig", "reward_transition"]


@dataclass(frozen=True)
class RewardConfig:
    pass


def reward_transition(transition: dict[str, Any]) -> int:
    return 0
