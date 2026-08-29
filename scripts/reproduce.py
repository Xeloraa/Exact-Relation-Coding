"""One entry point for the whole campaign; regenerates results/REPRODUCE.md.

    python scripts/reproduce.py [--mode slice|whole] [--skip-download] [--skip-phases]

Steps, in order:
  1. pytest (must pass; aborts otherwise)
  2. codec equivalence reference check (part of pytest, called out here)
  3. best-effort corpus downloads (unless --skip-download)
  4. experiments/controls/run.py           -> results/controls/
  5. experiments/natural/run.py --mode M   -> results/natural[_slice]/
  6. (optional) legacy phase0..phase4      -> results/phase*/
  7. write results/REPRODUCE.md: machine, package versions, git commit,
     per-step exit codes, timings, and every corpus_manifest.json entry.

--mode whole is for a machine with >= 32 GiB RAM (see
docs/environment_constraints.md). On the development machine use the default
--mode slice; its output is provenance, not the pre-registered answer.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _run(cmd: list[str], label: str) -> dict:
    print(f"\n===== {label} =====\n$ {' '.join(cmd)}")
    t0 = time.perf_counter()
    rc = subprocess.call(cmd, cwd=str(ROOT))
    return {"label": label, "cmd": " ".join(cmd), "returncode": rc, "seconds": round(time.perf_counter() - t0, 2)}


def _machine() -> dict:
    from deductive.environment import compressor_versions

    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": sys.version.split()[0],
        "package_versions": compressor_versions(),
    }
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                       ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                       ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong), ("c", ctypes.c_ulonglong),
                       ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]

        m = MS(); m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))  # type: ignore[attr-defined]
        info["ram_total_mib"] = m.ullTotalPhys // 1048576
        info["ram_avail_mib"] = m.ullAvailPhys // 1048576
    except Exception:  # noqa: BLE001
        pass
    return info


def _git_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
        dirty = subprocess.call(["git", "diff", "--quiet"], cwd=str(ROOT))
        return out + ("-dirty" if dirty else "")
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("slice", "whole"), default="slice")
    ap.add_argument("--slice-bytes", type=int, default=262_144)
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--skip-phases", action="store_true", help="skip legacy phase0..4")
    args = ap.parse_args(argv)

    steps: list[dict] = []
    steps.append(_run([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], "pytest + codec-equivalence"))
    if steps[-1]["returncode"] != 0:
        _write_report(steps, args, aborted="pytest failed")
        return steps[-1]["returncode"]

    if not args.skip_download:
        dl = _run([sys.executable, "-c",
                   "import sys; sys.path.insert(0,'src');"
                   "from deductive.datasets import corpora as C;"
                   "print('silesia:', C.try_download_silesia_zip());"
                   "print('enwik8 :', C.try_download_enwik8_zip());"
                   "print('sdrbench:', C.try_download_sdrbench_bundle('exaalt-2869440',"
                   f"max_mb={'4000' if args.mode=='whole' else '120'}));"
                   "print('uci    :', C.try_download_uci_household_power())"],
                  "corpus downloads (best-effort)")
        steps.append(dl)

    steps.append(_run([sys.executable, str(ROOT / "verification" / "independent_verify.py"), "--self-test"],
                      "independent verifier self-test"))
    steps.append(_run([sys.executable, str(ROOT / "experiments" / "controls" / "run.py")], "controls"))
    steps.append(_run([sys.executable, str(ROOT / "experiments" / "natural" / "run.py"),
                       "--mode", args.mode, "--slice-bytes", str(args.slice_bytes)], f"natural ({args.mode})"))

    if not args.skip_phases:
        for phase in ("phase0", "phase1", "phase2", "phase3", "phase4"):
            steps.append(_run([sys.executable, str(ROOT / "experiments" / phase / "run.py")], phase))

    steps.append(_run([sys.executable, str(ROOT / "scripts" / "build_ledger.py")], "build ledger"))
    steps.append(_run([sys.executable, str(ROOT / "scripts" / "regen_tables.py")], "regen paper tables"))
    steps.append(_run([sys.executable, str(ROOT / "scripts" / "check_paper_numbers.py")], "check paper numbers"))
    steps.append(_run([sys.executable, str(ROOT / "verification" / "independent_verify.py"),
                       "--ledger", str(ROOT / "results" / "ledger.json")], "independent verify ledger"))

    _write_report(steps, args)
    # controls / natural exit non-zero on a real gate failure; treat every step as load-bearing
    return 0 if all(s["returncode"] == 0 for s in steps) else 1


def _write_report(steps: list[dict], args, aborted: str | None = None) -> None:
    manifest = {}
    mpath = ROOT / "results" / "corpus_manifest.json"
    if mpath.is_file():
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    lines = [
        "# REPRODUCE",
        "",
        f"- generated: {datetime.now(timezone.utc).isoformat()}",
        f"- git commit: {_git_commit()}",
        f"- mode: {args.mode}" + (f" (slice-bytes {args.slice_bytes})" if args.mode == "slice" else ""),
    ]
    if aborted:
        lines.append(f"- ABORTED: {aborted}")
    lines += ["", "## Machine", "", "```json", json.dumps(_machine(), indent=2), "```", "",
              "## Steps", "", "| step | returncode | seconds |", "| --- | ---: | ---: |"]
    for s in steps:
        lines.append(f"| {s['label']} | {s['returncode']} | {s['seconds']} |")
    lines += ["", "## Corpus manifest (SHA-256 pins)", "", "```json", json.dumps(manifest, indent=2), "```", ""]
    if args.mode == "slice":
        lines += ["> Slice mode: `results/natural_slice/` rows are dev-machine feasibility",
                  "> slices, not whole-file results. The pre-registered question is settled",
                  "> only by a `--mode whole` run (docs/preregistration.md S4)."]
    (ROOT / "results" / "REPRODUCE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {ROOT / 'results' / 'REPRODUCE.md'}")


if __name__ == "__main__":
    raise SystemExit(main())
