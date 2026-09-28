from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import HarnessConfig, PROJECT_ROOT
from src.evaluator import EvaluationResult
from src.trainer import GenerationStats, Trainer


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train bot03 policies with neat-python."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    initialize = commands.add_parser("init", help="create generation 0")
    initialize.add_argument("--population", type=int, default=50)

    train = commands.add_parser("train", help="continue a saved generation")
    train.add_argument("--from-generation", type=int, required=True)
    train.add_argument("--generations", type=int, default=1)
    train.add_argument("--episodes", type=int, default=3)
    return parser


def _print_generation(
    stats: GenerationStats, results: list[EvaluationResult]
) -> None:
    print(
        f"generation={stats.generation} "
        f"best={stats.best_fitness:.3f} mean={stats.mean_fitness:.3f} "
        f"species={stats.species} transitions={stats.transitions} "
        f"kills={stats.inferred_kills} failures={stats.failed_evaluations}"
    )
    for result in results:
        if result.return_code != 0 or result.report.transitions == 0:
            reason = (
                f"exit {result.return_code}"
                if result.return_code != 0
                else "no transitions"
            )
            print(
                f"  {result.model_name} on slot {result.slot}: {reason}\n"
                f"{result.output_tail.rstrip()}",
                file=sys.stderr,
            )


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "init":
        harness = HarnessConfig(project_root=PROJECT_ROOT)
        trainer = Trainer.create(harness, args.population)
        names = trainer.initialize()
        print(
            f"created generation 0 with {len(names)} brains in "
            f"{trainer.generation_dir(0)}"
        )
        return

    harness = HarnessConfig(project_root=PROJECT_ROOT, episodes=args.episodes)
    trainer = Trainer.restore(harness, args.from_generation)
    try:
        trainer.advance(args.generations, on_generation=_print_generation)
    except KeyboardInterrupt:
        print("training interrupted", file=sys.stderr)
        raise SystemExit(130)
    print(f"population is now at generation {trainer.population.generation}")


if __name__ == "__main__":
    main()