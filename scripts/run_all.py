"""Run pytest then phase 0–3 experiments."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    r = subprocess.call([sys.executable, "-m", "pytest", str(ROOT / "tests")], cwd=str(ROOT))
    if r != 0:
        return r
    for phase in ("phase0", "phase1", "phase2", "phase3"):
        script = ROOT / "experiments" / phase / "run.py"
        print(f"===== {phase} =====")
        r = subprocess.call([sys.executable, str(script)], cwd=str(ROOT))
        if r != 0:
            return r
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
