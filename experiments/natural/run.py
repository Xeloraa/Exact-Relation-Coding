"""Natural-corpus campaign runner (docs/preregistration.md corpus list).

Modes:
  --mode slice  (default)  largest-feasible prefix for the current machine;
                           every row is labelled prefix=<bytes> / prefix_reason.
  --mode whole             whole files; for the heavy-sweep machine (>=32 GiB).

For each corpus item it separates the three claims (docs/protocol.md S1):
  A discoverable          n_relations >= 1
  B reduces representation |D(x)| < passthrough  AND  raw_gap > 0
  C survives composition   G_abs > 0
and evaluates the FIXED meaningful-positive threshold
(docs/preregistration.md S3): C and G_pct >= 0.05 and G_abs >= 1024 and
round-trip and not-passthrough and not-prior-art.

Writes results/natural/<id>.json and a consolidated results/natural/verdicts.json.
Nothing here changes a size, a baseline, or the threshold.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (SRC, ROOT / "experiments"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import (  # noqa: E402
    encode_bytes_best_gf2,
    passthrough_size,
)
from deductive.datasets import corpora as C  # noqa: E402

# whole-file results are the pre-registered answer; slice results are dev-machine
# provenance only and live in a separate phase / separate manifest ids.
PHASE_WHOLE = "natural"
PHASE_SLICE = "natural_slice"
PREREG_G_PCT = 0.05
PREREG_G_ABS = 1024

SILESIA = C.SILESIA_MEMBERS
PRIOR_ART_IDS: set[str] = set()  # natural corpora are never prior-art here


def corpus_items(mode: str, slice_bytes: int):
    """Yield (experiment_id, dataset_id, category, data|None, note)."""
    n = None if mode == "whole" else slice_bytes

    for m in SILESIA:
        data, note = (
            C.load_silesia_member_whole(m) if mode == "whole"
            else C.load_silesia_member_prefix(m, n_bytes=slice_bytes)
        )
        yield f"nat_silesia_{m}", f"silesia_{m}", "silesia", data, note

    e_data, e_note = C.load_enwik8_prefix(n_bytes=(1 << 40) if mode == "whole" else slice_bytes)
    yield "nat_enwik8", "enwik8", "text", e_data, e_note

    for field in ("vx.f32", "vy.f32", "vz.f32", "xx.f32", "yy.f32", "zz.f32"):
        data, note = C.load_sdrbench_field("exaalt-2869440", field)
        if data is not None and n is not None:
            data = data[: n - (n % 4)]
            note += f" [prefix {len(data)}]"
        yield f"nat_sdrbench_exaalt_{field.split('.')[0]}", f"sdrbench_exaalt2869440_{field}", "scientific_f32", data, note

    up_text, up_note = C.load_uci_household_power_text(n)
    yield "nat_uci_household_power_text", "uci_household_power_text", "telemetry_text", up_text, up_note


def evaluate(rec, data_len: int) -> dict:
    g_abs = rec.composition_gap_bytes()
    g_pct = rec.composition_gap_pct()
    g_abs_m = rec.composition_gap_matched_bytes()
    g_pct_m = rec.composition_gap_matched_pct()
    raw_gap = rec.raw_gap_bytes()
    is_pt = rec.codec_kind == "PASSTHROUGH" or rec.n_relations == 0
    claim_A = rec.n_relations >= 1
    claim_B = (rec.total_encoded_bytes < passthrough_size(data_len)) and (raw_gap is not None and raw_gap > 0)
    claim_C = g_abs is not None and g_abs > 0
    # locked definition (docs/preregistration.md S3) -- do not add conditions here
    meaningful = bool(
        claim_C
        and g_pct is not None and g_pct >= PREREG_G_PCT
        and g_abs is not None and g_abs >= PREREG_G_ABS
        and rec.roundtrip_ok
        and not is_pt
        and rec.dataset_id not in PRIOR_ART_IDS
    )
    # extra VALIDITY gates a reportable positive must also clear (not a redefinition)
    crt = rec.composed_roundtrip_ok()
    matched_ok = (
        g_pct_m is not None and g_pct_m >= PREREG_G_PCT
        and g_abs_m is not None and g_abs_m >= PREREG_G_ABS
    )
    reportable = bool(meaningful and crt is True and (rec.codec_sets_match() or matched_ok))
    return {
        "experiment_id": rec.experiment_id,
        "dataset_id": rec.dataset_id,
        "dataset_sha256": rec.dataset_sha256,
        "dataset_bytes": rec.dataset_bytes,
        "codec_kind": rec.codec_kind,
        "n_relations": rec.n_relations,
        "recovered_bits": rec.recovered_bits,
        "encoded_bytes": rec.total_encoded_bytes,
        "raw_best_bytes": rec.raw_best_bytes(),
        "raw_gap_bytes": raw_gap,
        "G_abs_bytes": g_abs,
        "G_pct": g_pct,
        "G_abs_matched_bytes": g_abs_m,
        "G_pct_matched": g_pct_m,
        "codec_sets_match": rec.codec_sets_match(),
        "available_raw_codecs": rec.available_raw_codecs(),
        "available_composed_codecs": rec.available_composed_codecs(),
        "roundtrip_ok": rec.roundtrip_ok,
        "composed_roundtrip_ok": crt,
        "claim_A_discoverable": claim_A,
        "claim_B_reduces_representation": claim_B,
        "claim_C_survives_composition": claim_C,
        "meaningful_positive_prereg": meaningful,
        "reportable_positive": reportable,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("slice", "whole"), default="slice")
    ap.add_argument("--slice-bytes", type=int, default=262_144)
    ap.add_argument("--widths", type=int, nargs="+", default=[8, 16, 32, 64, 128, 256])
    ap.add_argument("--only", type=str, nargs="+", default=None,
                    help="substring filter on experiment id (e.g. --only silesia_dickens); "
                         "lets a resource-limited machine run corpora one at a time")
    args = ap.parse_args(argv)

    is_slice = args.mode == "slice"
    phase = PHASE_SLICE if is_slice else PHASE_WHOLE
    slice_note = "dev_machine_feasibility_slice" if is_slice else "whole_file"
    id_suffix = f"@slice{args.slice_bytes}" if is_slice else ""
    verdicts = []
    for exp_id, ds_id, category, data, note in corpus_items(args.mode, args.slice_bytes):
        if args.only and not any(tok in exp_id for tok in args.only):
            continue
        exp_id = exp_id + ("_slice" if is_slice else "")
        ds_id = ds_id + id_suffix
        if data is None:
            print(f"SKIP {exp_id}: {note}")
            verdicts.append({"experiment_id": exp_id, "dataset_id": ds_id, "skipped": note})
            continue
        try:
            C.pin_or_verify(ds_id, data, source=note,
                            extra={"category": category, "acquisition_mode": args.mode})
        except RuntimeError as exc:
            print(f"ABORT {exp_id}: {exc}")
            return 3

        cfg = {
            "codec": "gf2_best",
            "widths": args.widths,
            "category": category,
            "acquisition": slice_note,
        }
        if is_slice:
            cfg["prefix"] = len(data)
            cfg["prefix_reason"] = slice_note

        try:
            rec = run_codec_experiment(
                phase=phase,
                experiment_id=exp_id,
                dataset_id=ds_id,
                data=data,
                seed=None,
                config=cfg,
                encode_fn=lambda d=data: encode_bytes_best_gf2(d, widths=tuple(args.widths)),
                hypothesis=(
                    "Blind GF(2) fixed-width discovery on this corpus yields a "
                    "composed size reduction after full accounting (docs/metric.md)."
                ),
                notes=f"{note} | acquisition={slice_note}",
            )
        except MemoryError:
            print(f"MEMORYERROR {exp_id} at {len(data)} B on this machine")
            verdicts.append({
                "experiment_id": exp_id, "dataset_id": ds_id, "dataset_bytes": len(data),
                "error": "MemoryError", "prefix_reason": "MemoryError_on_dev_machine",
            })
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {exp_id}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            verdicts.append({"experiment_id": exp_id, "dataset_id": ds_id, "error": f"{type(exc).__name__}: {exc}"})
            continue

        persist(rec, phase)
        print_record(rec)
        v = evaluate(rec, len(data))
        v["acquisition_mode"] = args.mode
        v["prefix_reason"] = None if args.mode == "whole" else slice_note
        verdicts.append(v)

    out = ROOT / "results" / phase / "verdicts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": args.mode,
        "prereg_threshold": {"G_pct_min": PREREG_G_PCT, "G_abs_min_bytes": PREREG_G_ABS},
        "verdicts": verdicts,
    }
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    scored = [v for v in verdicts if "meaningful_positive_prereg" in v]
    positives = [v for v in scored if v["meaningful_positive_prereg"]]
    print("\n--- natural-corpus summary ---")
    print(f"mode={args.mode}  items scored={len(scored)}  meaningful positives={len(positives)}")
    for v in scored:
        print(
            f"  {v['dataset_id']:34s} kind={v['codec_kind']:11s} rels={v['n_relations']:>4d} "
            f"G_abs={v['G_abs_bytes']} G_pct={v['G_pct']:.4f} "
            f"A={int(v['claim_A_discoverable'])} B={int(v['claim_B_reduces_representation'])} "
            f"C={int(v['claim_C_survives_composition'])} pos={int(v['meaningful_positive_prereg'])}"
            if v["G_pct"] is not None else f"  {v['dataset_id']:34s} (no baseline)"
        )
    if args.mode == "slice":
        print("\nNOTE: slice mode. These are dev-machine feasibility slices, NOT whole-file "
              "results, and do NOT settle the pre-registered question (docs/preregistration.md S4).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
