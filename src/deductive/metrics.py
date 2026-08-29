"""Deduction-gap definitions.

Provisional. Do not treat a single formula as the scientific claim; see
docs/theory.md. All sizes are fully accounted byte counts.
"""

from __future__ import annotations

from typing import Iterable

from deductive.results import BaselineSize, ExperimentRecord


def raw_deduction_gap(record: ExperimentRecord) -> int | None:
    """best_statistical_baseline_size - deductive_container_size."""
    return record.deduction_gap_bytes()


def composition_gap(
    baseline_sizes: Iterable[BaselineSize],
    composed: dict[str, dict],
) -> int | None:
    """min |c(raw)| - min |c(deductive_container)| over available compressors c."""
    raw = [b.bytes for b in baseline_sizes if b.available]
    comp = [int(v["bytes"]) for v in composed.values() if v.get("available")]
    if not raw or not comp:
        return None
    return min(raw) - min(comp)


def bits_per_byte_gap(record: ExperimentRecord) -> float | None:
    gap = record.deduction_gap_bytes()
    if gap is None or record.dataset_bytes == 0:
        return None
    return 8.0 * gap / record.dataset_bytes


def overhead_fraction(record: ExperimentRecord) -> float | None:
    total = record.accounting.get("total_bits")
    rel = record.accounting.get("relation_description_bits")
    if not total:
        return None
    return rel / total
