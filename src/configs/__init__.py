from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import ModuleType


def config_dir(config_id: int) -> Path:
    path = Path(__file__).resolve().parent / str(config_id)
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def fitness_module(config_id: int = 1) -> ModuleType:
    return import_module(f".{config_id}.fitness", package=__name__)


def reward_module(config_id: int = 1) -> ModuleType:
    return import_module(f".{config_id}.reward", package=__name__)


NEAT_CONFIG = config_dir(1) / "neat_config.ini"
