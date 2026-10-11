from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def consume_transition_file(path: Path) -> tuple[list[dict[str, Any]], int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    records: list[dict[str, Any]] = []
    invalid = 0

    with path.open("r+", encoding="utf-8", errors="replace") as stream:
        lines = stream.readlines()
        stream.seek(0)
        stream.truncate(0)

    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            invalid += 1

    return records, invalid


def clear_transition_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8"):
        pass
