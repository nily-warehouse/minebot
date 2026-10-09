from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .configs import NEAT_CONFIG, config_dir

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_SLOTS = 10


@dataclass(frozen=True)
class HarnessConfig:

    project_root: Path = PROJECT_ROOT
    episodes: int = 3
    config_id: int = 1
    episode_timeout_seconds = 60

    @property
    def neat_config(self) -> Path:
        return config_dir(self.config_id) / "neat_config.ini"

    @property
    def client_path(self) -> Path:
        return self.project_root / "bots" / "bot03" / "client.js"

    @property
    def models_dir(self) -> Path:
        return self.project_root / "pool" / "models"

    @property
    def transitions_dir(self) -> Path:
        return self.project_root / "pool" / "transitions"

    @property
    def generations_dir(self) -> Path:
        return self.project_root / "pool" / "generations"

    def transition_path(self, slot: int) -> Path:
        return self.transitions_dir / f"transitions_slot_{slot}.jsonl"