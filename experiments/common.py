"""Shared experiment helpers: hash, time, round-trip, record, write."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Callable

from deductive.baselines import composition_sizes, run_baselines, verify_composed_roundtrip
from deductive.codecs import Encoded, decode
from deductive.results import ExperimentRecord, append_csv, write_json


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def roundtrip(data: bytes, encoded: bytes) -> bool:
    return decode(encoded) == data


def run_codec_experiment(
    *,
    phase: str,
    experiment_id: str,
    dataset_id: str,
    data: bytes,
    seed: int | None,
    config: dict[str, Any],
    encode_fn: Callable[[], Encoded],
    hypothesis: str,
    notes: str = "",
    skip_slow_baselines: bool = False,
) -> ExperimentRecord:
    t0 = time.perf_counter()
    encoded = encode_fn()
    discovery_and_encode = time.perf_counter() - t0
    t1 = time.perf_counter()
    ok = roundtrip(data, encoded.data)
    decode_s = time.perf_counter() - t1
    if not ok:
        raise AssertionError(f"round-trip failed for {experiment_id}")

    baselines = run_baselines(data, skip_slow=skip_slow_baselines)
    composition = composition_sizes(encoded.data)
    composed_roundtrip = verify_composed_roundtrip(data, encoded.data, decode)

    record = ExperimentRecord(
        experiment_id=experiment_id,
        phase=phase,
        dataset_id=dataset_id,
        dataset_sha256=sha256_hex(data),
        dataset_bytes=len(data),
        seed=seed,
        config=config,
        codec_kind=encoded.kind.name if hasattr(encoded.kind, "name") else str(encoded.kind),
        n_relations=encoded.n_relations,
        n_independent=encoded.n_independent,
        recovered_bits=encoded.recovered_bits,
        accounting=encoded.accounting.as_dict(),
        total_encoded_bytes=len(encoded.data),
        roundtrip_ok=ok,
        encode_seconds=discovery_and_encode,
        decode_seconds=decode_s,
        discovery_seconds=discovery_and_encode,
        baselines=baselines,
        composition=composition,
        composed_roundtrip=composed_roundtrip,
        notes=notes or encoded.notes,
        hypothesis=hypothesis,
    )
    record.verdict = _verdict(record)
    if composed_roundtrip.get("all_ok") is not True and composed_roundtrip.get("n_codecs_checked", 0):
        record.verdict = "FAIL_COMPOSED_ROUNDTRIP " + record.verdict
    return record


def _verdict(record: ExperimentRecord) -> str:
    if not record.roundtrip_ok:
        return "FAIL_ROUNDTRIP"
    gap = record.deduction_gap_bytes()
    cgap = record.composition_gap_bytes()
    parts = []
    if gap is None:
        parts.append("no_baseline")
    elif gap > 0:
        parts.append(f"raw_gap+{gap}")
    elif gap < 0:
        parts.append(f"raw_gap{gap}")
    else:
        parts.append("raw_gap0")
    if record.codec_kind == "PASSTHROUGH" or record.n_relations == 0:
        parts.append("no_deduction")
        if cgap:
            parts.append(f"header_perturbation{cgap:+d}")
        return " ".join(parts)
    if cgap is None:
        parts.append("no_composition")
    elif cgap > 0:
        parts.append(f"comp_gap+{cgap}")
    elif cgap < 0:
        parts.append(f"comp_gap{cgap}")
    else:
        parts.append("comp_gap0")
    return " ".join(parts)


def persist(record: ExperimentRecord, phase: str) -> None:
    out_dir = RESULTS / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{record.experiment_id}.json", record)
    append_csv(out_dir / "summary.csv", record)


def print_record(record: ExperimentRecord) -> None:
    best = record.best_baseline_bytes()
    print(
        f"{record.experiment_id}: raw={record.dataset_bytes} "
        f"deductive={record.total_encoded_bytes} "
        f"best_stat={best} "
        f"gap={record.deduction_gap_bytes()} "
        f"comp_gap={record.composition_gap_bytes()} "
        f"rels={record.n_relations} "
        f"roundtrip={record.roundtrip_ok} "
        f"kind={record.codec_kind} "
        f"| {record.verdict}"
    )
