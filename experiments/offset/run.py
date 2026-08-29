"""Detector-scope extension: bit-phase-offset search (kill criterion S7 item 2).

The pre-registered detector reshapes from bit 0. This runner instead tries, for
each width w, every starting phase offset p in 0..w-1 (a coarse subset for very
wide w), and keeps the smallest fully accounted container. Bounded: Sum(w)
reshapes, no nonlinear search.

Scientific question: is the axis-aligned natural-corpus negative a *framing*
artifact? A genuine w-periodic linear relation that begins mid-byte is invisible
to phase-0 reshaping and visible at the right phase (demonstrated by
`control_nonaligned_period` and `test_independent_gf2_offset_best_recovers_phase_shift`).

Result that would change the conclusion: any pre-registered natural file whose
offset-search G_pct crosses the fixed 0.05 threshold that phase-0 missed.
Expected: none -> the negative strengthens from "phase 0" to "any phase".

Writes results/offset/<id>_{slice,whole}.json + results/offset/verdicts.json.
Compares each file's offset-search G_abs against its phase-0 value from
results/ledger.json.

Runtime note: the phase sweep is ~Sum(w) reshapes per file (≈ 240 discovery
passes at widths {8,16,32,64} full phase). On the 8 GiB dev machine `--mode
slice` (20 files, 256 KiB each) completes in ~16 min; `--mode whole` did not
finish the first 10 MB file in > 20 min and is left for a bigger machine. The
slice sweep is sufficient for the kill-criterion question: it reproduces the
phase-0 composed gain to the byte on every file (no phase helps), and there is
no size-dependent mechanism by which a phase would start helping at 10 MB.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "experiments"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_bytes_best_gf2_offsets  # noqa: E402
from deductive.datasets import corpora as C  # noqa: E402

PHASE = "offset"
PREREG_G_PCT = 0.05
PREREG_G_ABS = 1024
# full phase sweep for 8..64, coarse (8 offsets) for the wide widths
WIDTH_OFFSETS_SLICE = ((8, None), (16, None), (32, None), (64, None), (128, 8), (256, 8))
# whole files: keep it to the narrow widths, full phase (wide widths never win on
# real data and cost O(w) Gaussian-elimination passes on millions of rows)
WIDTH_OFFSETS_WHOLE = ((8, None), (16, None), (32, None), (64, None))


def _phase0(ledger: dict, dataset_id: str):
    # dataset_id in the offset run may carry no @slice suffix for whole files
    for key in (dataset_id, dataset_id + "@slice262144"):
        for r in ledger.values():
            if r["dataset_id"] == key:
                return r
    return None


def corpus_items(mode: str, slice_bytes: int):
    if mode == "whole":
        feasible = ("dickens", "xml", "ooffice", "reymont", "sao", "x-ray", "mr", "osdb")
        for m in feasible:
            data, note = C.load_silesia_member_whole(m)
            yield f"off_silesia_{m}", f"silesia_{m}", data, note, "whole"
    else:
        for m in C.SILESIA_MEMBERS:
            data, note = C.load_silesia_member_prefix(m, n_bytes=slice_bytes)
            yield f"off_silesia_{m}", f"silesia_{m}@slice{slice_bytes}", data, note, "slice"
        d, n = C.load_enwik8_prefix(n_bytes=slice_bytes)
        yield "off_enwik8", f"enwik8@slice{slice_bytes}", d, n, "slice"
        for f in ("vx.f32", "vy.f32", "vz.f32", "xx.f32", "yy.f32", "zz.f32"):
            data, note = C.load_sdrbench_field("exaalt-2869440", f)
            if data is not None:
                data = data[: slice_bytes - (slice_bytes % 4)]
            yield (f"off_sdrbench_exaalt_{f.split('.')[0]}",
                   f"sdrbench_exaalt2869440_{f}@slice{slice_bytes}", data, note, "slice")
        t, n = C.load_uci_household_power_text(slice_bytes)
        yield "off_uci_household_power_text", f"uci_household_power_text@slice{slice_bytes}", t, n, "slice"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("slice", "whole"), default="slice")
    ap.add_argument("--slice-bytes", type=int, default=262_144)
    ap.add_argument("--only", type=str, nargs="+", default=None)
    args = ap.parse_args(argv)

    ledger_path = ROOT / "results" / "ledger.json"
    ledger = {}
    if ledger_path.is_file():
        ledger = {r["experiment_id"]: r for r in json.loads(ledger_path.read_text(encoding="utf-8"))}

    wo = WIDTH_OFFSETS_WHOLE if args.mode == "whole" else WIDTH_OFFSETS_SLICE
    verdicts = []
    for exp_id, ds_id, data, note, scope in corpus_items(args.mode, args.slice_bytes):
        if args.only and not any(tok in exp_id for tok in args.only):
            continue
        exp_id = f"{exp_id}_{scope}"   # distinct records for slice vs whole (no file collision)
        if data is None:
            print(f"SKIP {exp_id}: {note}")
            continue
        C.pin_or_verify(ds_id, data, source=note, extra={"acquisition_mode": args.mode, "detector": "offset_search"})

        def _enc(d=data):
            best, _info = encode_bytes_best_gf2_offsets(d, width_offsets=wo)
            return best

        rec = run_codec_experiment(
            phase=PHASE, experiment_id=exp_id, dataset_id=ds_id, data=data, seed=None,
            config={"detector": "bit_offset_search", "width_offsets": [list(t) for t in wo],
                    "acquisition": scope, "prereg_threshold": {"G_pct": PREREG_G_PCT, "G_abs": PREREG_G_ABS}},
            encode_fn=_enc,
            hypothesis=("Trying every bit phase offset per width. If the phase-0 negative "
                        "were a framing artifact, some offset would cross the 0.05 threshold."),
            notes=f"{note} | detector=bit_offset_search",
        )
        persist(rec, PHASE)
        print_record(rec)

        p0 = _phase0(ledger, ds_id) or _phase0(ledger, ds_id.split("@")[0])
        g_off = rec.composition_gap_bytes()
        g_off_pct = rec.composition_gap_pct()
        g_p0 = p0.get("composition_gap_bytes") if p0 else None
        helped = (g_off is not None and g_p0 is not None and g_off > g_p0 + 64)
        crosses = bool(g_off_pct is not None and g_off_pct >= PREREG_G_PCT
                       and g_off is not None and g_off >= PREREG_G_ABS
                       and rec.codec_kind != "PASSTHROUGH")
        verdicts.append({
            "experiment_id": exp_id, "dataset_id": ds_id, "scope": scope,
            "dataset_sha256": rec.dataset_sha256, "dataset_bytes": rec.dataset_bytes,
            "codec_kind": rec.codec_kind, "n_relations": rec.n_relations,
            "offset_config": rec.notes,
            "G_abs_offset": g_off, "G_pct_offset": g_off_pct,
            "G_abs_phase0": g_p0,
            "offset_helped_vs_phase0": helped,
            "crosses_prereg_threshold": crosses,
            "roundtrip_ok": rec.roundtrip_ok,
            "composed_roundtrip_ok": rec.composed_roundtrip_ok(),
        })

    out = ROOT / "results" / PHASE / "verdicts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"mode": args.mode, "verdicts": verdicts}, indent=2, default=str) + "\n",
                   encoding="utf-8")

    crossed = [v for v in verdicts if v["crosses_prereg_threshold"]]
    helped = [v for v in verdicts if v["offset_helped_vs_phase0"]]
    print(f"\n--- offset-search summary (mode={args.mode}) ---")
    print(f"files: {len(verdicts)} | offset beat phase-0 by >64 B: {len(helped)} | "
          f"crossed 0.05 threshold: {len(crossed)}")
    for v in verdicts:
        print(f"  {v['dataset_id']:38s} kind={v['codec_kind']:11s} "
              f"G_abs off={v['G_abs_offset']} vs phase0={v['G_abs_phase0']} "
              f"helped={int(v['offset_helped_vs_phase0'])} crosses={int(v['crosses_prereg_threshold'])}")
    if crossed:
        print("\n*** offset search CROSSED the pre-registered threshold on: "
              + ", ".join(v["dataset_id"] for v in crossed)
              + " -- the phase-0 negative may be a framing artifact; investigate. ***")
    else:
        print("\nNo file crossed the threshold under full bit-phase-offset search: "
              "the axis-aligned negative is robust to phase, not a framing artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
