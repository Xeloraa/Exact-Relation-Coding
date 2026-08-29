"""Aggregate every results/**/*.json ExperimentRecord into one master ledger.

Outputs:
  results/ledger.json  - list of flat records, one per experiment
  results/ledger.csv   - same, spreadsheet form

Every number the paper reports must be traceable to a row here. No manual
transcription: scripts/regen_tables.py builds the paper tables from this file
and scripts/check_paper_numbers.py checks the paper against it.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

# ExperimentRecord JSONs only; skip aggregates / manifests.
SKIP_NAMES = {"verdicts.json", "corpus_manifest.json", "ledger.json", "REPRODUCE.md"}


def _baseline_map(rec: dict) -> dict[str, int]:
    out = {}
    for b in rec.get("baselines", []):
        if b.get("available"):
            out[b["name"]] = b["bytes"]
    return out


def _composed_map(rec: dict) -> dict[str, int]:
    out = {}
    for name, v in (rec.get("composition") or {}).items():
        if isinstance(v, dict) and v.get("available") is not False and int(v.get("bytes", -1)) >= 0:
            out[name] = int(v["bytes"])
    return out


def _acc(rec: dict) -> dict:
    return rec.get("accounting", {}) or {}


def flatten(rec: dict, path: Path) -> dict:
    acc = _acc(rec)
    raw_sizes = _baseline_map(rec)
    comp_sizes = _composed_map(rec)
    raw_best = min(raw_sizes.values()) if raw_sizes else None
    comp_best = min(comp_sizes.values()) if comp_sizes else None
    common = set(raw_sizes) & set(comp_sizes)
    g_abs = (raw_best - comp_best) if (raw_best is not None and comp_best is not None) else None
    g_matched = (
        min(raw_sizes[c] for c in common) - min(comp_sizes[c] for c in common)
        if common else None
    )
    enc = rec.get("total_encoded_bytes")
    raw = rec.get("dataset_bytes")
    meta_bits = (
        acc.get("relation_description_bits", 0) + acc.get("header_bits", 0)
        + acc.get("framing_bits", 0) + acc.get("crc_bits", 0) + acc.get("leftover_bits", 0)
    )
    cr = rec.get("composed_roundtrip", {}) or {}
    return {
        "experiment_id": rec.get("experiment_id"),
        "phase": rec.get("phase"),
        "result_file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "dataset_id": rec.get("dataset_id"),
        "dataset_sha256": rec.get("dataset_sha256"),
        "dataset_bytes": raw,
        "seed": rec.get("seed"),
        "git_commit": rec.get("git_commit"),
        "utc_timestamp": rec.get("utc_timestamp"),
        "config": json.dumps(rec.get("config", {}), sort_keys=True),
        "codec_kind": rec.get("codec_kind"),
        "n_relations": rec.get("n_relations"),
        "n_independent": rec.get("n_independent"),
        "recovered_bits": rec.get("recovered_bits"),
        "container_bytes": enc,
        "payload_bits": acc.get("payload_bits"),
        "relation_description_bits": acc.get("relation_description_bits"),
        "header_bits": acc.get("header_bits"),
        "framing_bits": acc.get("framing_bits"),
        "crc_bits": acc.get("crc_bits"),
        "leftover_bits": acc.get("leftover_bits"),
        "metadata_bits_total": meta_bits,
        "accounting_total_bits": acc.get("total_bits"),
        "accounting_ok": (acc.get("total_bits") == (enc * 8)) if enc is not None else None,
        "raw_best_bytes": raw_best,
        "composed_best_bytes": comp_best,
        "composition_gap_bytes": g_abs,
        "composition_gap_pct": (g_abs / raw_best) if (g_abs is not None and raw_best) else None,
        "composition_gap_matched_bytes": g_matched,
        "codec_sets_match": sorted(raw_sizes) == sorted(comp_sizes),
        "available_raw_codecs": ",".join(sorted(raw_sizes)),
        "available_composed_codecs": ",".join(sorted(comp_sizes)),
        "raw_gap_bytes": (raw_best - enc) if (raw_best is not None and enc is not None) else None,
        "roundtrip_ok": rec.get("roundtrip_ok"),
        "composed_roundtrip_mode": cr.get("mode"),
        "composed_roundtrip_ok": cr.get("all_ok"),
        "composed_roundtrip_n_checked": cr.get("n_codecs_checked"),
        "verdict": rec.get("verdict"),
        "package_versions": json.dumps((rec.get("machine", {}) or {}).get("package_versions", {}), sort_keys=True),
        "platform": (rec.get("machine", {}) or {}).get("platform"),
        **{f"baseline_{k}": v for k, v in raw_sizes.items()},
        **{f"composed_{k}": v for k, v in comp_sizes.items()},
    }


def main() -> int:
    rows = []
    for path in sorted(RESULTS.rglob("*.json")):
        if path.name in SKIP_NAMES:
            continue
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"skip {path}: {exc}")
            continue
        if "experiment_id" not in rec or "accounting" not in rec:
            continue
        rows.append(flatten(rec, path))

    rows.sort(key=lambda r: (r["phase"] or "", r["experiment_id"] or ""))
    (RESULTS / "ledger.json").write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")

    fieldnames: list[str] = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with (RESULTS / "ledger.csv").open("w", newline="", encoding="utf-8") as f:
        wtr = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        wtr.writeheader()
        wtr.writerows(rows)

    n_acc_bad = sum(1 for r in rows if r["accounting_ok"] is False)
    n_rt_bad = sum(1 for r in rows if r["roundtrip_ok"] is False)
    n_crt_bad = sum(1 for r in rows if r["composed_roundtrip_ok"] is False)
    print(f"ledger: {len(rows)} experiments -> results/ledger.{{json,csv}}")
    print(f"  accounting failures: {n_acc_bad}")
    print(f"  round-trip failures: {n_rt_bad}")
    print(f"  composed round-trip failures: {n_crt_bad}")
    return 1 if (n_acc_bad or n_rt_bad or n_crt_bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
