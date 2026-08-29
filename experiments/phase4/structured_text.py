"""Phase 4: structured text with an exact integer FD (format+FD trap).

JSON `sum = x+y` and log `total = n*2` are exact at the *parsed* level.
They are generated in memory only (not written as corpus files). GF(2) on
UTF-8 bytes is not that relation; gzip/xz are expected to crush the text.
A raw GF(2) shrink, if any, is labeled as not a composed win.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
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
from deductive.results import ExperimentRecord  # noqa: E402

N_ROWS = 2000
WIDTHS = (8, 16, 32, 64)
JSON_SEED = 801
LOG_SEED = 802
HYPOTHESIS = (
    "gzip/xz crush this structured text; composed gap negative. "
    "Any GF(2) raw shrink is not a composed win (format+FD trap)."
)


def make_json_fd(*, n: int, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        x = int(rng.integers(0, 10_000))
        y = int(rng.integers(0, 10_000))
        rows.append({"id": i + 1, "x": x, "y": y, "sum": x + y})
    return json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def make_log_fd(*, n: int, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    base = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)
    lines = []
    for i in range(n):
        ts = (base + timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        n_val = int(rng.integers(0, 10_000))
        total = n_val * 2
        lines.append(f"ts={ts} level=INFO n={n_val} total={total}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def label_trap(record: ExperimentRecord) -> None:
    parts = [record.notes] if record.notes else []
    parts.append(
        "LABEL: format+FD trap; exact integer FD lives in parsed JSON/log text, not GF(2) on UTF-8."
    )
    if record.total_encoded_bytes < record.dataset_bytes:
        parts.append("LABEL: GF2 raw shrink is not a composed win.")
    record.notes = " ".join(parts)


def run_one(
    *,
    experiment_id: str,
    dataset_id: str,
    data: bytes,
    seed: int,
    extra_notes: str,
) -> ExperimentRecord:
    rec = run_codec_experiment(
        phase="phase4_structured",
        experiment_id=experiment_id,
        dataset_id=dataset_id,
        data=data,
        seed=seed,
        config={
            "codec": "gf2_best",
            "widths": list(WIDTHS),
            "n_rows": N_ROWS,
            "label": "format_FD_trap_structured_text",
        },
        encode_fn=lambda d=data: encode_bytes_best_gf2(d, widths=WIDTHS),
        hypothesis=HYPOTHESIS,
        notes=extra_notes,
    )
    label_trap(rec)
    persist(rec, "phase4_structured")
    print_record(rec)
    return rec


def main() -> int:
    json_bytes = make_json_fd(n=N_ROWS, seed=JSON_SEED)
    log_bytes = make_log_fd(n=N_ROWS, seed=LOG_SEED)

    rec_json = run_one(
        experiment_id="phase4_structured_json_fd_n2000",
        dataset_id=f"json_array_fd_n{N_ROWS}_s{JSON_SEED}",
        data=json_bytes,
        seed=JSON_SEED,
        extra_notes="in-memory JSON array; sum=x+y; not a corpus file",
    )
    rec_log = run_one(
        experiment_id="phase4_structured_log_fd_n2000",
        dataset_id=f"log_lines_fd_n{N_ROWS}_s{LOG_SEED}",
        data=log_bytes,
        seed=LOG_SEED,
        extra_notes="in-memory log lines; total=n*2 (weak FD); not a corpus file",
    )
    for rec in (rec_json, rec_log):
        print(
            f"NUMBERS {rec.experiment_id}: "
            f"raw={rec.dataset_bytes} DEDC={rec.total_encoded_bytes} "
            f"best_stat={rec.best_baseline_bytes()} "
            f"raw_gap={rec.deduction_gap_bytes()} "
            f"comp_gap={rec.composition_gap_bytes()} "
            f"rels={rec.n_relations} kind={rec.codec_kind} "
            f"roundtrip={rec.roundtrip_ok} sha256={rec.dataset_sha256}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
