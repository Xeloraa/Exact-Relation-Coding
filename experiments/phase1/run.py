"""Phase 1: synthetic falsification with complete accounting."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_bytes_best_gf2, encode_gf2_matrix, reshape_bits  # noqa: E402
from deductive.codecs.tabular_codec import encode_tabular_affine, bytes_to_table  # noqa: E402
from deductive.datasets.synthetic import (  # noqa: E402
    exact_functional_table,
    gf2_linear_code,
    integer_linear_table,
    mixed_noise_bits,
    mixed_noise_table,
    near_relation_bits,
    shuffled_bits,
)


def _gf2_fixed_width(data: bytes, n_cols: int):
    def _enc():
        matrix, leftover = reshape_bits(data, n_cols)
        return encode_gf2_matrix(matrix, original=data, leftover=leftover)

    return _enc


def main() -> int:
    records = []

    # A. GF(2) linear codes at several scales
    gf2_cfgs = [
        dict(n_rows=1024, n_info=16, n_parity=16, seed=11),
        dict(n_rows=4096, n_info=32, n_parity=32, seed=12),
        dict(n_rows=16384, n_info=32, n_parity=32, seed=13),
        dict(n_rows=65536, n_info=64, n_parity=64, seed=14),
    ]
    for cfg in gf2_cfgs:
        ds = gf2_linear_code(**cfg)
        n_cols = cfg["n_info"] + cfg["n_parity"]
        rec = run_codec_experiment(
            phase="phase1",
            experiment_id=f"phase1_{ds.dataset_id}",
            dataset_id=ds.dataset_id,
            data=ds.data,
            seed=cfg["seed"],
            config={**cfg, "codec": "gf2", "n_cols": n_cols},
            encode_fn=_gf2_fixed_width(ds.data, n_cols),
            hypothesis=(
                "Exact GF(2) parity bits are deductively recoverable. After "
                "relation-description cost, total size should beat gzip/zstd/xz "
                "on incompressible information bits."
            ),
        )
        persist(rec, "phase1")
        print_record(rec)
        records.append(rec)

    # B. Exact functional dependency (affine)
    fd = exact_functional_table(n_rows=8192, seed=21, fn="affine")
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{fd.dataset_id}",
        dataset_id=fd.dataset_id,
        data=fd.data,
        seed=21,
        config={"codec": "tabular_affine", "fn": "affine", "n_rows": 8192},
        encode_fn=lambda d=fd.data: encode_tabular_affine(bytes_to_table(d, 3)),
        hypothesis="Blind affine discovery finds C=3A+5B+7 without being told.",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    # B2. XOR+offset is an exact FD but not integer-affine — must not invent affine savings
    xor_fd = exact_functional_table(n_rows=4096, seed=22, fn="xor_plus")
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{xor_fd.dataset_id}",
        dataset_id=xor_fd.dataset_id,
        data=xor_fd.data,
        seed=22,
        config={"codec": "tabular_affine", "fn": "xor_plus", "n_rows": 4096},
        encode_fn=lambda d=xor_fd.data: encode_tabular_affine(bytes_to_table(d, 3)),
        hypothesis="C=(A XOR B)+3 is not affine; discovery must not emit a false relation.",
        notes="control: exact FD outside the affine family",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    # C. Integer linear
    il = integer_linear_table(n_rows=8192, seed=31, extra_independent=1)
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{il.dataset_id}",
        dataset_id=il.dataset_id,
        data=il.data,
        seed=31,
        config={"codec": "tabular_affine", "n_rows": 8192, "n_cols": 4},
        encode_fn=lambda d=il.data: encode_tabular_affine(bytes_to_table(d, 4)),
        hypothesis="z=2x+3y+5 is discovered; extra independent column is kept.",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    # D. Mixed/noise controls
    noise_bits = mixed_noise_bits(n_rows=8192, n_cols=64, seed=41)
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{noise_bits.dataset_id}",
        dataset_id=noise_bits.dataset_id,
        data=noise_bits.data,
        seed=41,
        config={"codec": "gf2_best", "n_rows": 8192, "n_cols": 64},
        encode_fn=lambda d=noise_bits.data: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64)),
        hypothesis="Independent random bits: deduction must not invent a net saving.",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    noise_tbl = mixed_noise_table(n_rows=2048, n_cols=4, seed=42)
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{noise_tbl.dataset_id}",
        dataset_id=noise_tbl.dataset_id,
        data=noise_tbl.data,
        seed=42,
        config={"codec": "tabular_affine", "n_rows": 2048, "n_cols": 4},
        encode_fn=lambda d=noise_tbl.data: encode_tabular_affine(bytes_to_table(d, 4)),
        hypothesis="Independent random integers: no affine relation, no invented saving.",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    # Near-relation: one flipped parity bit destroys the global linear code
    near = near_relation_bits(n_rows=4096, n_info=16, seed=51, n_flips=1)
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{near.dataset_id}",
        dataset_id=near.dataset_id,
        data=near.data,
        seed=51,
        config={"codec": "gf2", "n_cols": 17, "n_flips": 1},
        encode_fn=_gf2_fixed_width(near.data, 17),
        hypothesis="A single corrupted parity bit makes the exact global relation false; no free column.",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    # Shuffled planted GF(2): structure exists in another alignment
    planted = gf2_linear_code(n_rows=4096, n_info=16, n_parity=16, seed=61)
    shuf = shuffled_bits(planted, seed=62)
    rec = run_codec_experiment(
        phase="phase1",
        experiment_id=f"phase1_{shuf.dataset_id}",
        dataset_id=shuf.dataset_id,
        data=shuf.data,
        seed=62,
        config={"codec": "gf2_best", "source": planted.dataset_id},
        encode_fn=lambda d=shuf.data: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64)),
        hypothesis="Byte shuffle destroys column alignment; discovery should not recover the planted code.",
    )
    persist(rec, "phase1")
    print_record(rec)
    records.append(rec)

    # Gate: substantial NET saving on at least one planted GF(2) vs best baseline
    gf2_recs = [r for r in records if r.dataset_id.startswith("gf2_")]
    wins = [r for r in gf2_recs if (r.deduction_gap_bytes() or 0) > 0]
    print("---")
    print(f"phase1 GF(2) planted experiments: {len(gf2_recs)}; net wins vs best baseline: {len(wins)}")
    if not wins:
        print("PHASE1 GATE: FAIL — no net saving on planted GF(2) after full accounting")
        return 2
    print("PHASE1 GATE: PASS — planted GF(2) shows net saving after full accounting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
