"""Phase 4 format-awareness traps: general GF(2) on PNG/ZIP/SQLite.

Not a format parser. Per-chunk PNG CRC32 and ZIP CRC32 sit at variable
layout offsets, so a fixed-width bit matrix should not invert them.
SQLite may shrink from zero-page sparsity; that is format/sparsity, not
a novel corpus phenomenon. Strong compressors (xz/brotli) are expected
to keep a negative composed gap.
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
from deductive.codecs.gf2_codec import encode_bytes_best_gf2  # noqa: E402
from deductive.datasets.corpora import make_png, make_sqlite_fd, make_zip_stored  # noqa: E402

LARGE_SQLITE_BYTES = 32_768
HYPOTHESIS = (
    "General bit-matrix GF(2) does not invert PNG/ZIP CRCs (variable layout), "
    "so the composed gap vs xz/brotli is negative. SQLite may shrink due to "
    "zeros (seen already on tiny sqlite) but xz still wins — label format/sparsity."
)


def gf2_widths(data: bytes, *, sqlite: bool) -> tuple[int, ...]:
    if sqlite and len(data) >= LARGE_SQLITE_BYTES:
        return (8, 16, 32, 64)
    return (8, 16, 32, 64, 128)


def zip_payload(*, seed: int) -> dict[str, bytes]:
    rng = np.random.default_rng(seed)
    return {
        "rand.bin": rng.integers(0, 256, size=8192, dtype=np.uint8).tobytes(),
        "note.txt": b"tiny stored zip fixture\nline two\n",
    }


def run_one(
    *,
    experiment_id: str,
    dataset_id: str,
    data: bytes,
    seed: int | None,
    category: str,
    sqlite: bool,
    extra_notes: str,
) -> None:
    widths = gf2_widths(data, sqlite=sqlite)
    print(f"{experiment_id}: {len(data)} bytes, widths={widths}")
    rec = run_codec_experiment(
        phase="phase4",
        experiment_id=experiment_id,
        dataset_id=dataset_id,
        data=data,
        seed=seed,
        config={
            "codec": "gf2_best",
            "widths": list(widths),
            "category": category,
            "label": "format_awareness_trap",
        },
        encode_fn=lambda d=data, w=widths: encode_bytes_best_gf2(d, widths=w),
        hypothesis=HYPOTHESIS,
        notes=extra_notes,
    )
    persist(rec, "phase4_formats")
    print_record(rec)


def main() -> int:
    png = make_png(width=48, height=48, seed=801)
    run_one(
        experiment_id="phase4_formats_png_48x48_s801",
        dataset_id="png_48x48_s801",
        data=png,
        seed=801,
        category="png",
        sqlite=False,
        extra_notes=(
            "LABEL: format-awareness / per-chunk CRC32; general GF(2) is not a PNG parser. "
            "Any raw shrink is sparsity in headers/padding, not novelty."
        ),
    )

    zip_bytes = make_zip_stored(zip_payload(seed=803))
    run_one(
        experiment_id="phase4_formats_zip_stored_s803",
        dataset_id="zip_stored_8kib_rand_plus_text_s803",
        data=zip_bytes,
        seed=803,
        category="zip",
        sqlite=False,
        extra_notes=(
            "LABEL: format-awareness / ZIP CRC32 at local+central headers; variable layout. "
            "General GF(2) is not a ZIP parser. Not claimed as novel."
        ),
    )

    sqlite = make_sqlite_fd(n_rows=4000, seed=802)
    run_one(
        experiment_id="phase4_formats_sqlite_fd_n4000_s802",
        dataset_id="sqlite_fd_n4000_c_eq_a_plus_b_s802",
        data=sqlite,
        seed=802,
        category="sqlite",
        sqlite=True,
        extra_notes=(
            "LABEL: format/sparsity (zero pages) and/or FD in a SQLite file. "
            "xz/brotli are expected to win. Not claimed as a general-corpus gap."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
