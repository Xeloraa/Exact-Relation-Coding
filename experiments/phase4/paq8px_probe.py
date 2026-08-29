"""Phase 4: paq8px v216 on planted GF(2) vs the accounted DEDC container.

paq8px is a current GPL context mixer (Mahoney et al. / hxim). The binary
stays under gitignored data/downloads/paq8px/. This is not paq8l or cmix.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_gf2_matrix, reshape_bits  # noqa: E402
from deductive.datasets.synthetic import gf2_linear_code  # noqa: E402

PAQ_DIR = ROOT / "data" / "downloads" / "paq8px"
WORK = ROOT / "data" / "downloads" / "paq8px_work"
ARCHIVE_SUFFIX = ".paq8px216"
DEFAULT_LEVELS = (4, 8)  # 660 MB then 2408 MB; skip 8 on MemoryError


def find_paq8px() -> Path | None:
    for p in (
        PAQ_DIR / "bin" / "paq8px.exe",
        PAQ_DIR / "paq8px.exe",
    ):
        if p.is_file():
            return p
    return None


def parse_levels(argv: list[str] | None = None) -> list[int]:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return list(DEFAULT_LEVELS)
    levels: list[int] = []
    for token in argv:
        raw = token.lstrip("-")
        if not raw.isdigit():
            raise SystemExit("usage: paq8px_probe.py [levels...]  (default 4 8)")
        level = int(raw)
        if not 0 <= level <= 12:
            raise SystemExit("paq8px level must be 0..12")
        levels.append(level)
    return levels


def _gf2_fixed(data: bytes, n_cols: int):
    def _enc():
        matrix, leftover = reshape_bits(data, n_cols)
        return encode_gf2_matrix(matrix, original=data, leftover=leftover)

    return _enc


def paq_size(exe: Path, data: bytes, stem: str, level: int) -> tuple[int | None, float, str]:
    WORK.mkdir(parents=True, exist_ok=True)
    src = WORK / f"{stem}.bin"
    out = WORK / f"{stem}.bin{ARCHIVE_SUFFIX}"
    src.write_bytes(data)
    out.unlink(missing_ok=True)
    timeout = 1800 if level >= 7 else 600
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            [str(exe), f"-{level}", str(src)],
            cwd=str(WORK),
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, time.perf_counter() - t0, "timeout"
    elapsed = time.perf_counter() - t0
    err = (proc.stderr or proc.stdout or b"").decode("ascii", errors="replace")[:400]
    if "bad allocation" in err.lower() or "not enough memory" in err.lower():
        return None, elapsed, f"oom rc={proc.returncode} {err}"
    if proc.returncode != 0 or not out.is_file():
        return None, elapsed, f"rc={proc.returncode} {err}"
    return out.stat().st_size, elapsed, ""


def run_level(exe: Path, level: int) -> int:
    print(f"using {exe.name} v216 level -{level}")
    cfg = dict(n_rows=1280, n_info=32, n_parity=32, seed=902)
    ds = gf2_linear_code(**cfg)
    n_cols = cfg["n_info"] + cfg["n_parity"]
    rec = run_codec_experiment(
        phase="phase4_paq",
        experiment_id=f"phase4_paq8px_v216_l{level}_{ds.dataset_id}",
        dataset_id=ds.dataset_id,
        data=ds.data,
        seed=cfg["seed"],
        config={
            **cfg,
            "codec": "gf2",
            "n_cols": n_cols,
            "paq": "paq8px",
            "paq_version": "v216",
            "paq_level": level,
        },
        encode_fn=_gf2_fixed(ds.data, n_cols),
        hypothesis=(
            "paq8px is a current context mixer with file-type models. "
            "If it absorbs planted XOR, paq(raw) approaches DEDC size and "
            "the mixer-relative gap vanishes. If not, paq8l's failure is not "
            "an artifact of using the 2007 mixer only."
        ),
        notes="paq8px v216 GPL from github.com/hxim/paq8px; dump not committed",
    )
    matrix, leftover = reshape_bits(ds.data, n_cols)
    enc = encode_gf2_matrix(matrix, original=ds.data, leftover=leftover)
    raw_n, raw_s, raw_err = paq_size(exe, ds.data, "planted_raw", level)
    dedc_n, dedc_s, dedc_err = paq_size(exe, enc.data, "planted_dedc", level)
    rec.config["paq8px_exe"] = exe.name
    rec.config["paq8px_version"] = "v216"
    rec.config["paq8px_level"] = level
    rec.config["paq8px_raw_bytes"] = raw_n
    rec.config["paq8px_raw_seconds"] = raw_s
    rec.config["paq8px_raw_error"] = raw_err
    rec.config["paq8px_dedc_bytes"] = dedc_n
    rec.config["paq8px_dedc_seconds"] = dedc_s
    rec.config["paq8px_dedc_error"] = dedc_err
    if raw_n is not None:
        rec.config["paq8px_vs_dedc"] = raw_n - rec.total_encoded_bytes
    if raw_n is not None and dedc_n is not None:
        rec.config["paq8px_raw_minus_paq_dedc"] = raw_n - dedc_n
    persist(rec, "phase4_paq")
    print_record(rec)
    print(
        f"  paq8px -{level} raw={raw_n} ({raw_s:.2f}s) "
        f"dedc={dedc_n} ({dedc_s:.2f}s) "
        f"err_raw={raw_err!r} err_dedc={dedc_err!r}"
    )
    return 0 if raw_n is not None and dedc_n is not None else 1


def main(argv: list[str] | None = None) -> int:
    exe = find_paq8px()
    if exe is None:
        print("paq8px not present under data/downloads/paq8px/; skip")
        return 0
    status = 0
    for level in parse_levels(argv):
        if run_level(exe, level) != 0:
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
