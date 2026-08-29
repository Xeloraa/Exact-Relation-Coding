"""Phase 4 scaling: planted GF(2) at 1/10/100 KiB (optional ~256 KiB).

Uses fixed-width encode_gf2_matrix + reshape_bits, not encode_bytes_best_gf2.
Also compares homogeneous vs affine discovery on one XOR+1 parity column
at the 10 KiB row scale.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import (  # noqa: E402
    bytes_from_bits,
    encode_gf2_matrix,
    reshape_bits,
)
from deductive.datasets.synthetic import gf2_linear_code  # noqa: E402
from deductive.results import ExperimentRecord  # noqa: E402

PHASE_DIR = "phase4_scaling"
OPTIONAL_MAX_S = 180.0


def _gf2_fixed_width(data: bytes, n_cols: int, *, affine: bool = False):
    def _enc():
        matrix, leftover = reshape_bits(data, n_cols)
        return encode_gf2_matrix(
            matrix, original=data, leftover=leftover, affine=affine
        )

    return _enc


def _csv_row(size_label: str, rec: ExperimentRecord) -> str:
    rel_bits = rec.accounting.get("relation_description_bits", 0)
    best = rec.best_baseline_bytes()
    cgap = rec.composition_gap_bytes()
    best_s = "" if best is None else str(best)
    cgap_s = "" if cgap is None else str(cgap)
    return (
        f"{size_label},{rec.dataset_bytes},{rec.total_encoded_bytes},"
        f"{rel_bits},{rec.recovered_bits},{best_s},{cgap_s},"
        f"{rec.encode_seconds:.6f},{rec.decode_seconds:.6f}"
    )


def _run_planted(cfg: dict, size_label: str) -> ExperimentRecord:
    ds = gf2_linear_code(**cfg)
    n_cols = cfg["n_info"] + cfg["n_parity"]
    if (n_cols * cfg["n_rows"]) % 8 != 0:
        raise ValueError(f"n_cols*n_rows not divisible by 8: {cfg}")
    rec = run_codec_experiment(
        phase="phase4",
        experiment_id=f"phase4_scaling_{ds.dataset_id}",
        dataset_id=ds.dataset_id,
        data=ds.data,
        seed=cfg["seed"],
        config={**cfg, "codec": "gf2", "n_cols": n_cols, "size_label": size_label},
        encode_fn=_gf2_fixed_width(ds.data, n_cols),
        hypothesis=(
            "Exact planted GF(2) parity is deductively recoverable. Relation "
            "description is independent of n_rows; recovered bits and the "
            "composed gap should scale with n_rows."
        ),
    )
    persist(rec, PHASE_DIR)
    print_record(rec)
    return rec


def _affine_parity_matrix(*, n_rows: int, n_info: int, seed: int) -> tuple[np.ndarray, bytes]:
    """Info bits plus one parity = XOR(all info) XOR 1 (constant offset)."""
    rng = np.random.default_rng(seed)
    info = rng.integers(0, 2, size=(n_rows, n_info), dtype=np.uint8)
    parity = (np.bitwise_xor.reduce(info, axis=1) ^ np.uint8(1)).reshape(-1, 1)
    matrix = np.concatenate([info, parity], axis=1)
    n_cols = int(matrix.shape[1])
    if (n_cols * n_rows) % 8 != 0:
        raise ValueError(f"n_cols*n_rows not divisible by 8: {n_rows}x{n_cols}")
    data = bytes_from_bits(matrix.reshape(-1))
    return matrix, data


def _run_affine_control(n_rows: int, n_info: int, seed: int) -> list[tuple[str, ExperimentRecord]]:
    matrix, data = _affine_parity_matrix(n_rows=n_rows, n_info=n_info, seed=seed)
    n_cols = int(matrix.shape[1])
    dataset_id = f"gf2_affine_parity_n{n_rows}_k{n_info}_s{seed}"
    out: list[tuple[str, ExperimentRecord]] = []
    for affine, tag, hypothesis in (
        (
            False,
            "affine10_hom",
            "XOR(all info) XOR 1 is affine, not homogeneous; linear GF(2) should miss it.",
        ),
        (
            True,
            "affine10_aff",
            "Affine GF(2) (implicit ones) should recover the constant-offset parity.",
        ),
    ):
        rec = run_codec_experiment(
            phase="phase4",
            experiment_id=f"phase4_scaling_{dataset_id}_{'affine' if affine else 'homogeneous'}",
            dataset_id=dataset_id,
            data=data,
            seed=seed,
            config={
                "codec": "gf2_affine" if affine else "gf2",
                "n_rows": n_rows,
                "n_info": n_info,
                "n_parity": 1,
                "n_cols": n_cols,
                "affine": affine,
                "size_label": tag,
            },
            encode_fn=_gf2_fixed_width(data, n_cols, affine=affine),
            hypothesis=hypothesis,
            notes="control: planted affine parity XOR(all info) XOR 1",
        )
        persist(rec, PHASE_DIR)
        print_record(rec)
        print(f"  n_relations[{tag}]={rec.n_relations} affine={affine}")
        out.append((tag, rec))
    return out


def main() -> int:
    csv_header = (
        "size,raw,DEDC,relation_bits,recovered_bits,best_stat,composed_gap,encode_s,decode_s"
    )
    rows: list[str] = [csv_header]
    records: list[tuple[str, ExperimentRecord]] = []

    planted = [
        ("1KiB", dict(n_rows=128, n_info=32, n_parity=32, seed=901)),
        ("10KiB", dict(n_rows=1280, n_info=32, n_parity=32, seed=902)),
        ("100KiB", dict(n_rows=12800, n_info=32, n_parity=32, seed=903)),
    ]
    t_100kib: float | None = None
    for size_label, cfg in planted:
        t0 = time.perf_counter()
        rec = _run_planted(cfg, size_label)
        elapsed = time.perf_counter() - t0
        if size_label == "100KiB":
            t_100kib = elapsed
            print(f"100KiB wall_s={elapsed:.3f}")
        records.append((size_label, rec))
        rows.append(_csv_row(size_label, rec))

    # Optional ~256 KiB if 100 KiB was cheap. Skip 1 MiB (already in phase1).
    if t_100kib is not None and t_100kib < OPTIONAL_MAX_S:
        opt = dict(n_rows=32000, n_info=32, n_parity=32, seed=904)
        rec = _run_planted(opt, "256KiB")
        records.append(("256KiB", rec))
        rows.append(_csv_row("256KiB", rec))
    else:
        print(
            f"skip 256KiB (100KiB wall_s={t_100kib!r} not < {OPTIONAL_MAX_S})"
        )

    for tag, rec in _run_affine_control(n_rows=1280, n_info=32, seed=910):
        records.append((tag, rec))
        rows.append(_csv_row(tag, rec))

    print("---")
    print("CSV")
    for line in rows:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
