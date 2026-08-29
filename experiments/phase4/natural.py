"""Phase 4: natural and local byte corpora (not committed)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_bytes_best_gf2  # noqa: E402
from deductive.codecs.tabular_codec import encode_tabular_affine  # noqa: E402
from deductive.datasets.corpora import (  # noqa: E402
    load_enwik8_prefix,
    local_pe_sample,
    make_csv_fd,
    python_stdlib_sample,
    try_download_enwik8_zip,
)


def _gf2(data: bytes):
    widths = (8, 16, 32, 64) if len(data) > 80_000 else (8, 16, 32, 64, 128)
    return lambda d=data, w=widths: encode_bytes_best_gf2(d, widths=w)


def _csv_table(raw: bytes) -> np.ndarray:
    rows = []
    for line in raw.decode("ascii").splitlines()[1:]:
        if line:
            rows.append([int(x) for x in line.split(",")])
    return np.asarray(rows, dtype=np.int64)


def main() -> int:
    dl = try_download_enwik8_zip(timeout=90)
    enw, enw_note = load_enwik8_prefix(1_000_000)
    print(f"enwik8: {dl}; {enw_note}")

    std = python_stdlib_sample(max_bytes=400_000)
    if std is None:
        print("skip python_stdlib_sample (None)")
    else:
        rec = run_codec_experiment(
            phase="phase4_natural",
            experiment_id="phase4_natural_stdlib_py",
            dataset_id="python_stdlib_py_prefix",
            data=std,
            seed=None,
            config={"codec": "gf2_best", "category": "source_code", "max_bytes": 400_000},
            encode_fn=_gf2(std),
            hypothesis="Local CPython Lib/*.py: composed gap vs xz/brotli should be negative.",
            notes="not uploaded; local stdlib sample",
            skip_slow_baselines=len(std) > 2_000_000,
        )
        persist(rec, "phase4_natural")
        print_record(rec)

    pe = local_pe_sample(max_bytes=256_000)
    if pe is None:
        print("skip local_pe_sample (None)")
    else:
        rec = run_codec_experiment(
            phase="phase4_natural",
            experiment_id="phase4_natural_pe_prefix",
            dataset_id="python_executable_prefix",
            data=pe,
            seed=None,
            config={"codec": "gf2_best", "category": "binary", "max_bytes": 256_000},
            encode_fn=_gf2(pe),
            hypothesis="PE/ELF interpreter prefix: general GF(2) should lose to xz on composition.",
            notes="not uploaded; sys.executable prefix",
            skip_slow_baselines=len(pe) > 2_000_000,
        )
        persist(rec, "phase4_natural")
        print_record(rec)

    csv = make_csv_fd(n_rows=8000, seed=701)
    rec = run_codec_experiment(
        phase="phase4_natural",
        experiment_id="phase4_natural_csv_fd_gf2",
        dataset_id="csv_fd_n8000_s701",
        data=csv,
        seed=701,
        config={"codec": "gf2_best", "category": "csv", "label": "FD_in_text"},
        encode_fn=_gf2(csv),
        hypothesis="Text CSV with c=a+b: gzip/xz see the text; GF(2) on bytes should not beat composition.",
        notes="LABEL: FD-in-text / format trap if any composed win",
    )
    persist(rec, "phase4_natural")
    print_record(rec)

    table = _csv_table(csv)
    rec = run_codec_experiment(
        phase="phase4_natural",
        experiment_id="phase4_natural_csv_fd_tabular",
        dataset_id="csv_fd_n8000_s701_int64",
        data=table.tobytes(order="C"),
        seed=701,
        config={"codec": "tabular_affine", "label": "FD_elimination_prior_art", "n_cols": 3},
        encode_fn=lambda t=table: encode_tabular_affine(t),
        hypothesis="Parsed int64 table of the same CSV: composition win is FD elimination, not novel.",
        notes="LABEL: functional-dependency column elimination; prior art",
    )
    persist(rec, "phase4_natural")
    print_record(rec)

    if enw is not None:
        rec = run_codec_experiment(
            phase="phase4_natural",
            experiment_id="phase4_natural_enwik8_1mb",
            dataset_id="enwik8_prefix_1mb",
            data=enw,
            seed=None,
            config={"codec": "gf2_best", "category": "text", "n_bytes": len(enw)},
            encode_fn=_gf2(enw),
            hypothesis="enwik8 1MB prefix: experimental control; composed gap expected negative.",
            notes=enw_note,
            skip_slow_baselines=len(enw) > 2_000_000,
        )
        persist(rec, "phase4_natural")
        print_record(rec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
