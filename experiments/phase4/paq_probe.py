"""Phase 4: paq8l on planted GF(2) vs the accounted DEDC container.

paq8l is a 2007 GPL context mixer (Matt Mahoney et al.). The binary stays
under gitignored data/downloads/paq8l/. This is not paq8px/cmix.
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

PAQ_DIR = ROOT / "data" / "downloads" / "paq8l"
WORK = ROOT / "data" / "downloads" / "paq8l_work"
LEVEL = 3  # 59 MB RAM; -8 needs ~1.6 GB


def find_paq8l() -> Path | None:
    for name in ("paq8l.exe", "paq-8l_intel.exe"):
        p = PAQ_DIR / name
        if p.is_file():
            return p
    return None


def _gf2_fixed(data: bytes, n_cols: int):
    def _enc():
        matrix, leftover = reshape_bits(data, n_cols)
        return encode_gf2_matrix(matrix, original=data, leftover=leftover)

    return _enc


def paq_size(exe: Path, data: bytes, stem: str) -> tuple[int | None, float, str]:
    WORK.mkdir(parents=True, exist_ok=True)
    src = WORK / f"{stem}.bin"
    out = WORK / f"{stem}.bin.paq8l"
    src.write_bytes(data)
    out.unlink(missing_ok=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        [str(exe), f"-{LEVEL}", str(src)],
        cwd=str(WORK),
        input=b"\n",
        capture_output=True,
        timeout=600,
    )
    elapsed = time.perf_counter() - t0
    if proc.returncode != 0 or not out.is_file():
        err = (proc.stderr or proc.stdout or b"").decode("ascii", errors="replace")[:400]
        return None, elapsed, f"rc={proc.returncode} {err}"
    return out.stat().st_size, elapsed, ""


def main() -> int:
    exe = find_paq8l()
    if exe is None:
        print("paq8l not present under data/downloads/paq8l/; skip")
        return 0
    print(f"using {exe.name} level -{LEVEL}")
    cfg = dict(n_rows=1280, n_info=32, n_parity=32, seed=902)
    ds = gf2_linear_code(**cfg)
    n_cols = cfg["n_info"] + cfg["n_parity"]
    rec = run_codec_experiment(
        phase="phase4_paq",
        experiment_id=f"phase4_paq8l_l{LEVEL}_{ds.dataset_id}",
        dataset_id=ds.dataset_id,
        data=ds.data,
        seed=cfg["seed"],
        config={**cfg, "codec": "gf2", "n_cols": n_cols, "paq": "paq8l", "paq_level": LEVEL},
        encode_fn=_gf2_fixed(ds.data, n_cols),
        hypothesis=(
            "paq8l is a context mixer. If it absorbs planted XOR, paq(raw) "
            "approaches DEDC size and the mixer-relative gap vanishes. If not, "
            "the gzip/xz composed gap is not an artifact of weak baselines."
        ),
        notes="paq8l GPL from mattmahoney.net/dc/paq8l.zip; dump not committed",
    )
    matrix, leftover = reshape_bits(ds.data, n_cols)
    enc = encode_gf2_matrix(matrix, original=ds.data, leftover=leftover)
    raw_n, raw_s, raw_err = paq_size(exe, ds.data, "planted_raw")
    dedc_n, dedc_s, dedc_err = paq_size(exe, enc.data, "planted_dedc")
    rec.config["paq8l_exe"] = exe.name
    rec.config["paq8l_level"] = LEVEL
    rec.config["paq8l_raw_bytes"] = raw_n
    rec.config["paq8l_raw_seconds"] = raw_s
    rec.config["paq8l_raw_error"] = raw_err
    rec.config["paq8l_dedc_bytes"] = dedc_n
    rec.config["paq8l_dedc_seconds"] = dedc_s
    rec.config["paq8l_dedc_error"] = dedc_err
    if raw_n is not None:
        rec.config["paq8l_vs_dedc"] = raw_n - rec.total_encoded_bytes
    if raw_n is not None and dedc_n is not None:
        rec.config["paq8l_raw_minus_paq_dedc"] = raw_n - dedc_n
    persist(rec, "phase4_paq")
    print_record(rec)
    print(
        f"  paq8l -{LEVEL} raw={raw_n} ({raw_s:.2f}s) "
        f"dedc={dedc_n} ({dedc_s:.2f}s) "
        f"err_raw={raw_err!r} err_dedc={dedc_err!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
