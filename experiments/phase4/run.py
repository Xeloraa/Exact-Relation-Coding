"""Phase 4 orchestrator: run sibling scripts if present.

Does not implement experiments itself. Sibling files (natural.py,
formats.py, scaling.py) may be written separately; missing ones are
skipped so parent runners are not blocked.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = (
    "natural.py",
    "formats.py",
    "scaling.py",
    "structured_text.py",
    "silesia.py",
    "pack_pivots.py",
    "paq_probe.py",
)


def main() -> int:
    missing: list[str] = []
    ran = 0
    for name in SCRIPTS:
        path = HERE / name
        if not path.is_file():
            print(f"skip {name} (missing)")
            missing.append(name)
            continue
        print(f"===== phase4/{name} =====")
        runpy.run_path(str(path), run_name="__main__")
        ran += 1
    if missing:
        print(f"phase4 missing scripts: {', '.join(missing)}")
    if ran == 0:
        print("phase4: no sibling scripts found; continuing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
