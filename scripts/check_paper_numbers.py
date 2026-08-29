"""Fail if any experimental number in the paper is not backed by the ledger.

Two checks:

1. paper/results_tables.md must be byte-identical to a fresh
   `regen_tables.py` run against the current `results/ledger.json`
   (i.e. the generated tables are not stale).

2. Every marker of the form
       <!-- src: <experiment_id> / <field> = <value> -->
   in paper/deductive-coding.md must resolve: `<experiment_id>` exists in the
   ledger and `ledger[experiment_id][field] == <value>` (string-compared after
   normalising ints/floats). This is how inline prose numbers stay honest.

Exit non-zero on any failure. Run after build_ledger.py + regen_tables.py.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results" / "ledger.json"
TABLES = ROOT / "paper" / "results_tables.md"
PAPER = ROOT / "paper" / "deductive-coding.md"

MARKER = re.compile(r"<!--\s*src:\s*([A-Za-z0-9_][A-Za-z0-9_./-]*)\s*/\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*-->")
# the literal token 'id/field' is used in prose to describe the marker syntax; skip it
_PLACEHOLDER_IDS = {"id", "<id>", "experiment_id"}


def _match(claimed: str, actual) -> bool:
    claimed = claimed.strip()
    if isinstance(actual, bool):
        return claimed == str(actual)
    if isinstance(actual, (int,)) and not isinstance(actual, bool):
        try:
            return int(claimed) == actual
        except ValueError:
            return False
    if isinstance(actual, float):
        try:
            a = float(claimed)
        except ValueError:
            return False
        return abs(a - actual) <= 1e-6 * max(1.0, abs(actual))
    return claimed == str(actual)


def check_tables_fresh() -> list[str]:
    if not TABLES.is_file():
        return [f"{TABLES} does not exist; run scripts/regen_tables.py"]
    before = TABLES.read_text(encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "regen_tables.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return [f"regen_tables.py failed: {r.stderr}"]
    after = TABLES.read_text(encoding="utf-8")
    if before != after:
        return ["paper/results_tables.md was stale relative to results/ledger.json "
                "(regen_tables.py just rewrote it). Commit the regenerated file."]
    return []


def check_markers() -> list[str]:
    if not PAPER.is_file():
        return []  # paper not written yet
    if not LEDGER.is_file():
        return [f"{LEDGER} missing"]
    ledger = {r["experiment_id"]: r for r in json.loads(LEDGER.read_text(encoding="utf-8"))}
    problems = []
    n = 0
    for m in MARKER.finditer(PAPER.read_text(encoding="utf-8")):
        exp_id, field, claimed = m.group(1), m.group(2), m.group(3)
        if exp_id in _PLACEHOLDER_IDS:
            continue
        n += 1
        row = ledger.get(exp_id)
        if row is None:
            problems.append(f"marker [{exp_id}/{field}]: experiment_id not in ledger")
            continue
        if field not in row:
            problems.append(f"marker [{exp_id}/{field}]: field not in ledger row "
                            f"(have: {sorted(row)[:12]}...)")
            continue
        if not _match(claimed, row[field]):
            problems.append(f"marker [{exp_id}/{field}]: paper says {claimed!r} "
                            f"but ledger has {row[field]!r}")
    print(f"paper markers checked: {n}")
    return problems


def main() -> int:
    problems = check_tables_fresh() + check_markers()
    if problems:
        print("PAPER-NUMBER CHECK: FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PAPER-NUMBER CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
