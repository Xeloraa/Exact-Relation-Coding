"""Experiment result records and compact serialization."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deductive.environment import command_line, git_commit, machine_info


@dataclass
class BaselineSize:
    name: str
    bytes: int
    seconds: float
    available: bool = True
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentRecord:
    experiment_id: str
    phase: str
    dataset_id: str
    dataset_sha256: str
    dataset_bytes: int
    seed: int | None
    config: dict[str, Any]
    codec_kind: str
    n_relations: int
    n_independent: int
    recovered_bits: int
    accounting: dict[str, int]
    total_encoded_bytes: int
    roundtrip_ok: bool
    encode_seconds: float
    decode_seconds: float
    discovery_seconds: float
    baselines: list[BaselineSize] = field(default_factory=list)
    composition: dict[str, Any] = field(default_factory=dict)
    composed_roundtrip: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    hypothesis: str = ""
    verdict: str = ""
    utc_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    git_commit: str = field(default_factory=git_commit)
    command: str = field(default_factory=command_line)
    machine: dict[str, Any] = field(default_factory=machine_info)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def best_baseline_bytes(self) -> int | None:
        avail = [b.bytes for b in self.baselines if b.available]
        return min(avail) if avail else None

    def deduction_gap_bytes(self) -> int | None:
        """best statistical baseline minus fully accounted deductive size.

        Positive means deduction is smaller (a gap in the compressor's favour
        would be negative). This definition is provisional; see docs/theory.md.
        """
        best = self.best_baseline_bytes()
        if best is None:
            return None
        return best - self.total_encoded_bytes

    def composition_gap_bytes(self) -> int | None:
        """min_c |c(raw)| - min_c |c(deductive_container)|, if measured.

        This is G_abs in docs/metric.md S4: positive means the deductive
        pre-pass reduced the size achievable by the strongest available stock
        compressor, after full accounting.
        """
        raw_sizes = [b.bytes for b in self.baselines if b.available]
        composed = []
        for key, val in self.composition.items():
            if not isinstance(val, dict):
                continue
            if val.get("available") is False:
                continue
            n = int(val.get("bytes", -1))
            if n < 0:
                continue
            composed.append(n)
        if not raw_sizes or not composed:
            return None
        return min(raw_sizes) - min(composed)

    def raw_best_bytes(self) -> int | None:
        """min_c |c(raw)| over available baselines (raw_best in metric.md)."""
        return self.best_baseline_bytes()

    def composition_gap_pct(self) -> float | None:
        """G_pct in docs/metric.md S4: G_abs / raw_best, signed fraction."""
        g = self.composition_gap_bytes()
        base = self.raw_best_bytes()
        if g is None or not base:
            return None
        return g / base

    def raw_gap_bytes(self) -> int | None:
        """raw_best - |D(x)|: deduction vs stock compressors with NO composition."""
        base = self.raw_best_bytes()
        if base is None:
            return None
        return base - self.total_encoded_bytes

    # --- matched-codec-set gap: only codecs that ran on BOTH sides ----------
    def _raw_sizes_by_codec(self) -> dict[str, int]:
        return {b.name: b.bytes for b in self.baselines if b.available and b.bytes >= 0}

    def _composed_sizes_by_codec(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for name, val in self.composition.items():
            if isinstance(val, dict) and val.get("available") is not False:
                n = int(val.get("bytes", -1))
                if n >= 0:
                    out[name] = n
        return out

    def available_raw_codecs(self) -> list[str]:
        return sorted(self._raw_sizes_by_codec())

    def available_composed_codecs(self) -> list[str]:
        return sorted(self._composed_sizes_by_codec())

    def codec_sets_match(self) -> bool:
        return self.available_raw_codecs() == self.available_composed_codecs()

    def composition_gap_matched_bytes(self) -> int | None:
        """G_abs restricted to codecs that ran on BOTH raw and container.

        Guards against an asymmetric comparison where e.g. xz9 OOMs on one side
        only. Equals composition_gap_bytes() when codec_sets_match().
        """
        raw = self._raw_sizes_by_codec()
        comp = self._composed_sizes_by_codec()
        common = set(raw) & set(comp)
        if not common:
            return None
        return min(raw[c] for c in common) - min(comp[c] for c in common)

    def composition_gap_matched_pct(self) -> float | None:
        g = self.composition_gap_matched_bytes()
        raw = self._raw_sizes_by_codec()
        comp = self._composed_sizes_by_codec()
        common = set(raw) & set(comp)
        if g is None or not common:
            return None
        base = min(raw[c] for c in common)
        return g / base if base else None

    def composed_roundtrip_ok(self) -> bool | None:
        v = self.composed_roundtrip.get("all_ok")
        return bool(v) if v is not None else None


def write_json(path: Path, record: ExperimentRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.as_dict(), indent=2, default=str) + "\n", encoding="utf-8")


def append_csv(path: Path, record: ExperimentRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "experiment_id": record.experiment_id,
        "phase": record.phase,
        "dataset_id": record.dataset_id,
        "dataset_sha256": record.dataset_sha256,
        "dataset_bytes": record.dataset_bytes,
        "codec_kind": record.codec_kind,
        "n_relations": record.n_relations,
        "n_independent": record.n_independent,
        "recovered_bits": record.recovered_bits,
        "total_encoded_bytes": record.total_encoded_bytes,
        "payload_bits": record.accounting.get("payload_bits"),
        "relation_description_bits": record.accounting.get("relation_description_bits"),
        "header_bits": record.accounting.get("header_bits"),
        "framing_bits": record.accounting.get("framing_bits"),
        "crc_bits": record.accounting.get("crc_bits"),
        "roundtrip_ok": record.roundtrip_ok,
        "encode_seconds": record.encode_seconds,
        "decode_seconds": record.decode_seconds,
        "discovery_seconds": record.discovery_seconds,
        "best_baseline_bytes": record.best_baseline_bytes(),
        "deduction_gap_bytes": record.deduction_gap_bytes(),
        "raw_gap_bytes": record.raw_gap_bytes(),
        "composition_gap_bytes": record.composition_gap_bytes(),
        "composition_gap_pct": record.composition_gap_pct(),
        "composition_gap_matched_bytes": record.composition_gap_matched_bytes(),
        "composition_gap_matched_pct": record.composition_gap_matched_pct(),
        "codec_sets_match": record.codec_sets_match(),
        "composed_roundtrip_ok": record.composed_roundtrip_ok(),
        "verdict": record.verdict,
        "git_commit": record.git_commit,
        "utc_timestamp": record.utc_timestamp,
        "seed": record.seed,
    }
    for b in record.baselines:
        row[f"baseline_{b.name}_bytes"] = b.bytes if b.available else ""
        row[f"baseline_{b.name}_seconds"] = b.seconds if b.available else ""
    write_header = not path.exists()
    fieldnames = list(row.keys())
    if not write_header:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                fieldnames = list(dict.fromkeys(list(reader.fieldnames) + fieldnames))
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def write_summary_json(path: Path, records: list[ExperimentRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "n": len(records),
        "utc_timestamp": datetime.now(timezone.utc).isoformat(),
        "records": [r.as_dict() for r in records],
    }
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
