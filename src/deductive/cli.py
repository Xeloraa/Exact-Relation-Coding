"""Command-line entry: run tests or experiment phases."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="deductive", description="Deductive Coding research runner")
    p.add_argument(
        "command",
        choices=("phase0", "phase1", "phase2", "phase3", "all"),
        help="experiment phase to run",
    )
    args = p.parse_args(argv)
    mapping = {
        "phase0": ROOT / "experiments" / "phase0" / "run.py",
        "phase1": ROOT / "experiments" / "phase1" / "run.py",
        "phase2": ROOT / "experiments" / "phase2" / "run.py",
        "phase3": ROOT / "experiments" / "phase3" / "run.py",
    }
    commands = list(mapping) if args.command == "all" else [args.command]
    for name in commands:
        print(f"===== {name} =====")
        runpy.run_path(str(mapping[name]), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
