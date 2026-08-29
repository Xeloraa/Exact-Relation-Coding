"""Phase 2: blind discovery, adversarial nulls, composition emphasis."""

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
from deductive.codecs.tabular_codec import bytes_to_table, encode_tabular_affine  # noqa: E402
from deductive.datasets.corpora import builtin_corpora  # noqa: E402
from deductive.datasets.synthetic import (  # noqa: E402
    exact_functional_table,
    gf2_linear_code,
    mixed_noise_bits,
    near_relation_bits,
)


def main() -> int:
    # Blind: planted relations are not passed into encode_gf2_matrix
    ds = gf2_linear_code(n_rows=8192, n_info=24, n_parity=24, seed=101, dense=False)
    n_cols = 48

    def _enc():
        matrix, leftover = reshape_bits(ds.data, n_cols)
        return encode_gf2_matrix(matrix, original=ds.data, leftover=leftover)

    rec = run_codec_experiment(
        phase="phase2",
        experiment_id=f"phase2_blind_{ds.dataset_id}",
        dataset_id=ds.dataset_id,
        data=ds.data,
        seed=101,
        config={"codec": "gf2", "n_cols": n_cols, "dense": False, "blind": True},
        encode_fn=_enc,
        hypothesis="Sparse planted parities are found by rank/nullspace without being named.",
    )
    persist(rec, "phase2")
    print_record(rec)

    # Crypto-like noise (numpy CSPRNG is not crypto; this is iid bits)
    noise = mixed_noise_bits(n_rows=4096, n_cols=128, seed=202)
    rec = run_codec_experiment(
        phase="phase2",
        experiment_id="phase2_null_iid_bits",
        dataset_id=noise.dataset_id,
        data=noise.data,
        seed=202,
        config={"codec": "gf2_best"},
        encode_fn=lambda d=noise.data: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64, 128)),
        hypothesis="IID bits: best encoding is passthrough or no smaller than raw+header.",
    )
    persist(rec, "phase2")
    print_record(rec)

    near = near_relation_bits(n_rows=8192, n_info=32, seed=303, n_flips=3)
    rec = run_codec_experiment(
        phase="phase2",
        experiment_id="phase2_adversarial_near_relation",
        dataset_id=near.dataset_id,
        data=near.data,
        seed=303,
        config={"codec": "gf2", "n_cols": 33, "n_flips": 3},
        encode_fn=lambda d=near.data: encode_gf2_matrix(
            reshape_bits(d, 33)[0], original=d, leftover=reshape_bits(d, 33)[1]
        ),
        hypothesis="Near-relations must not be treated as exact.",
    )
    persist(rec, "phase2")
    print_record(rec)

    # Product is an exact FD, not affine
    prod = exact_functional_table(n_rows=2048, seed=404, fn="product")
    rec = run_codec_experiment(
        phase="phase2",
        experiment_id=f"phase2_{prod.dataset_id}",
        dataset_id=prod.dataset_id,
        data=prod.data,
        seed=404,
        config={"codec": "tabular_affine", "fn": "product"},
        encode_fn=lambda d=prod.data: encode_tabular_affine(bytes_to_table(d, 3)),
        hypothesis="C=A*B+1 is not affine; affine codec must not claim a relation.",
    )
    persist(rec, "phase2")
    print_record(rec)

    # Tiny builtin corpora: format-awareness trap / no silent wins
    for item in builtin_corpora():
        rec = run_codec_experiment(
            phase="phase2",
            experiment_id=f"phase2_corpus_{item.dataset_id}",
            dataset_id=item.dataset_id,
            data=item.data,
            seed=None,
            config={"codec": "gf2_best", "category": item.category},
            encode_fn=lambda d=item.data: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64)),
            hypothesis="Tiny fixtures: record sizes; do not claim a real-corpus deduction gap.",
            notes=item.notes,
        )
        persist(rec, "phase2")
        print_record(rec)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
