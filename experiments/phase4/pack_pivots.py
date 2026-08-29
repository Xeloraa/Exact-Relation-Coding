"""Phase 4: pack discovered independent bits, then compress.

On planted GF(2) the payload should already be nearly incompressible.
This checks that xz/brotli on packed pivots does not beat the fully
accounted DEDC container after adding relation description and headers.
"""

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
from deductive.baselines import run_baselines  # noqa: E402
from deductive.codecs.gf2_codec import (  # noqa: E402
    bytes_from_bits,
    encode_gf2_matrix,
    reshape_bits,
)
from deductive.datasets.synthetic import gf2_linear_code  # noqa: E402
from deductive.relations.gf2 import column_basis, extract_pivot_bits  # noqa: E402

PHASE_DIR = "phase4_pack"


def _gf2_fixed_width(data: bytes, n_cols: int):
    def _enc():
        matrix, leftover = reshape_bits(data, n_cols)
        return encode_gf2_matrix(matrix, original=data, leftover=leftover)

    return _enc


def packed_pivot_bytes(matrix: np.ndarray) -> tuple[bytes, int, int]:
    basis = column_basis(matrix)
    piv = extract_pivot_bits(matrix, basis)
    flat = piv.reshape(-1).astype(np.uint8)
    if flat.size % 8:
        pad = 8 - (flat.size % 8)
        flat = np.concatenate([flat, np.zeros(pad, dtype=np.uint8)])
    return bytes_from_bits(flat), basis.rank, basis.n_relations


def main() -> int:
    planted = [
        ("10KiB", dict(n_rows=1280, n_info=32, n_parity=32, seed=902)),
        ("100KiB", dict(n_rows=12800, n_info=32, n_parity=32, seed=903)),
    ]
    for size_label, cfg in planted:
        ds = gf2_linear_code(**cfg)
        n_cols = cfg["n_info"] + cfg["n_parity"]
        rec = run_codec_experiment(
            phase="phase4",
            experiment_id=f"phase4_pack_{ds.dataset_id}",
            dataset_id=ds.dataset_id,
            data=ds.data,
            seed=cfg["seed"],
            config={**cfg, "codec": "gf2", "n_cols": n_cols, "size_label": size_label},
            encode_fn=_gf2_fixed_width(ds.data, n_cols),
            hypothesis=(
                "Packed independent bits of a planted GF(2) code are nearly "
                "incompressible. xz/brotli on that payload cannot beat the "
                "accounted DEDC container once relation description and headers "
                "are added back; composition of the container already measures this."
            ),
            notes="pack pivots then statistical codec; not a new encoder",
        )
        matrix, _leftover = reshape_bits(ds.data, n_cols)
        packed, rank, n_rel = packed_pivot_bytes(matrix)
        packed_bl = run_baselines(packed)
        avail = [b.bytes for b in packed_bl if b.available]
        best_packed = min(avail) if avail else None
        acc = rec.accounting
        extra = (
            int(acc.get("relation_description_bits", 0))
            + int(acc.get("header_bits", 0))
            + int(acc.get("crc_bits", 0))
            + int(acc.get("framing_bits", 0))
            + int(acc.get("leftover_bits", 0))
        )
        extra_bytes = (extra + 7) // 8
        payload_then_stat = None if best_packed is None else best_packed + extra_bytes
        rec.config["packed_payload_bytes"] = len(packed)
        rec.config["packed_rank"] = rank
        rec.config["packed_n_relations"] = n_rel
        rec.config["packed_best_stat_bytes"] = best_packed
        rec.config["relation_header_crc_leftover_bytes"] = extra_bytes
        rec.config["payload_then_stat_bytes"] = payload_then_stat
        rec.config["packed_baselines"] = {
            b.name: {"bytes": b.bytes, "available": b.available, "notes": b.notes}
            for b in packed_bl
        }
        persist(rec, PHASE_DIR)
        print_record(rec)
        print(
            f"  packed={len(packed)} best_packed={best_packed} "
            f"extra={extra_bytes} payload_then_stat={payload_then_stat} "
            f"DEDC={rec.total_encoded_bytes} "
            f"comp_gap={rec.composition_gap_bytes()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
