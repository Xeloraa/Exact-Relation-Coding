"""Format-awareness: per-record CRC32 as a GF(2) (affine) relation."""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_gf2_matrix, reshape_bits  # noqa: E402
from deductive.relations.gf2 import column_basis  # noqa: E402


def crc_records(*, n_records: int, payload_len: int, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    parts = []
    for _ in range(n_records):
        payload = rng.integers(0, 256, size=payload_len, dtype=np.uint8).tobytes()
        crc = (zlib.crc32(payload) & 0xFFFFFFFF).to_bytes(4, "little")
        parts.append(payload + crc)
    return b"".join(parts)


def main() -> int:
    n_records, payload_len, seed = 4096, 4, 777
    data = crc_records(n_records=n_records, payload_len=payload_len, seed=seed)
    n_cols = (payload_len + 4) * 8
    matrix, leftover = reshape_bits(data, n_cols)
    basis = column_basis(matrix)
    print(f"homogeneous rank={basis.rank}/{n_cols} relations={basis.n_relations}")

    ones = np.ones((matrix.shape[0], 1), dtype=np.uint8)
    affine = np.concatenate([matrix, ones], axis=1)
    abasis = column_basis(affine)
    print(f"affine(+ones) rank={abasis.rank}/{affine.shape[1]} relations={abasis.n_relations}")

    rec = run_codec_experiment(
        phase="phase3",
        experiment_id="phase3_crc32_records_homogeneous",
        dataset_id=f"crc32_n{n_records}_p{payload_len}_s{seed}",
        data=data,
        seed=seed,
        config={
            "codec": "gf2",
            "n_cols": n_cols,
            "payload_len": payload_len,
            "affine": False,
            "label": "format_awareness_CRC32",
        },
        encode_fn=lambda: encode_gf2_matrix(matrix, original=data, leftover=leftover, affine=False),
        hypothesis=(
            "IEEE CRC32 is affine over GF(2). Homogeneous discovery may miss one bit. "
            "Any win is a known checksum, not a new corpus phenomenon."
        ),
        notes="LABEL: CRC / format-aware checksum; not claimed as novel if it works",
    )
    persist(rec, "phase3")
    print_record(rec)

    rec_a = run_codec_experiment(
        phase="phase3",
        experiment_id="phase3_crc32_records_affine",
        dataset_id=f"crc32_n{n_records}_p{payload_len}_s{seed}",
        data=data,
        seed=seed,
        config={
            "codec": "gf2_affine",
            "n_cols": n_cols,
            "payload_len": payload_len,
            "affine": True,
            "label": "format_awareness_CRC32",
        },
        encode_fn=lambda: encode_gf2_matrix(matrix, original=data, leftover=leftover, affine=True),
        hypothesis="Affine GF(2) (implicit ones column) should recover all 32 CRC bits. Still a checksum.",
        notes="LABEL: CRC affine; not claimed as novel",
    )
    persist(rec_a, "phase3")
    print_record(rec_a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
