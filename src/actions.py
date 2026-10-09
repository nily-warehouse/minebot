from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ACTIONS_FILE = Path(__file__).resolve().with_name("actions.json")


def load_action_spec(path: Path = ACTIONS_FILE) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        spec = json.load(stream)
    outputs = spec.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise ValueError(f"{path}: 'outputs' must be a non-empty list")
    names = [a.get("name") for a in outputs if a.get("enabled", True)]
    if not names:
        raise ValueError(f"{path}: no enabled actions")
    if len(set(names)) != len(names):
        raise ValueError(f"{path}: duplicate action names among enabled actions")
    return spec


def enabled_actions(path: Path = ACTIONS_FILE) -> list[str]:
    spec = load_action_spec(path)
    return [a["name"] for a in spec["outputs"] if a.get("enabled", True)]


def attack_index(path: Path = ACTIONS_FILE) -> int | None:
    """Index of attack_action among enabled actions, or None if absent/disabled."""
    spec = load_action_spec(path)
    names = enabled_actions(path)
    name = spec.get("attack_action")
    if name is None or name not in names:
        return None
    return names.index(name)