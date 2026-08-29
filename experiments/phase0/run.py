"""Phase 0: repository smoke tests and environment snapshot."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs import encode_passthrough  # noqa: E402
from deductive.codecs.gf2_codec import encode_gf2_matrix  # noqa: E402
from deductive.datasets.synthetic import gf2_linear_code, mixed_noise_bits  # noqa: E402
from deductive.environment import machine_info  # noqa: E402
from deductive.relations.gf2 import column_basis  # noqa: E402
from deductive.codecs.gf2_codec import bits_from_bytes, reshape_bits  # noqa: E402


def main() -> int:
    env_path = ROOT / "results" / "phase0" / "environment.json"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(json.dumps(machine_info(), indent=2) + "\n", encoding="utf-8")

    noise = mixed_noise_bits(n_rows=64, n_cols=32, seed=0)
    rec0 = run_codec_experiment(
        phase="phase0",
        experiment_id="phase0_passthrough_noise",
        dataset_id=noise.dataset_id,
        data=noise.data,
        seed=0,
        config={"codec": "passthrough"},
        encode_fn=lambda: encode_passthrough(noise.data),
        hypothesis="Passthrough is lossless and larger than raw by a counted header.",
    )
    persist(rec0, "phase0")
    print_record(rec0)

    planted = gf2_linear_code(n_rows=128, n_info=8, n_parity=8, seed=1)
    n_cols = int(planted.meta["n_cols"])

    def _enc():
        matrix, leftover = reshape_bits(planted.data, n_cols)
        return encode_gf2_matrix(matrix, original=planted.data, leftover=leftover)

    rec1 = run_codec_experiment(
        phase="phase0",
        experiment_id="phase0_gf2_tiny",
        dataset_id=planted.dataset_id,
        data=planted.data,
        seed=1,
        config={"codec": "gf2", "n_cols": n_cols},
        encode_fn=_enc,
        hypothesis="Tiny planted GF(2) code round-trips and discovery finds rank n_info.",
    )
    persist(rec1, "phase0")
    print_record(rec1)

    matrix, _ = reshape_bits(planted.data, n_cols)
    basis = column_basis(matrix)
    rank_ok = basis.rank == planted.meta["n_info"]
    print(f"phase0_gf2_rank: rank={basis.rank} expected={planted.meta['n_info']} ok={rank_ok}")
    if not rank_ok:
        return 1
    if rec0.total_encoded_bytes <= rec0.dataset_bytes:
        print("passthrough header missing from accounting")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
