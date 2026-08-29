"""Control battery for the natural-corpus campaign.

Consolidates the null / positive / degradation / prior-art checks that make a
NEGATIVE natural-corpus result *informative* (the pipeline demonstrably finds
exact structure when it is present, and never invents a saving when it is not).

Gates (see docs/protocol.md S5, docs/preregistration.md S4):

  positive : planted GF(2)          -> G_pct >= 0.30, round-trip ok
  null     : iid bits / shuffled / 1-flip near-relation
                                    -> passthrough, |G_abs| <= 64
  sweep    : planted, flip fraction phi in {0, 1e-4, 1e-3, 1e-2, 5e-2}
                                    -> G_abs monotone non-increasing in phi,
                                       never below -64 (never-worse holds)
  prior-art: affine FD, CRC32 records
                                    -> recorded, labelled, NOT gated

Exit code 0 iff every gate passes. Runs entirely on synthetic data; feasible
on the development machine.
"""

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
from deductive.codecs import decode  # noqa: E402
from deductive.codecs.gf2_codec import (  # noqa: E402
    encode_bytes_best_gf2,
    encode_gf2_matrix,
    passthrough_size,
    reshape_bits,
)
from deductive.codecs.tabular_codec import bytes_to_table, encode_tabular_affine  # noqa: E402
from deductive.baselines import compress_named, decompress_named  # noqa: E402
from deductive.datasets.synthetic import (  # noqa: E402
    corrupted_gf2_code,
    exact_functional_table,
    gf2_linear_code,
    mixed_noise_bits,
    near_relation_bits,
    shuffled_bits,
)

PHASE = "controls"


def _raw_best(rec) -> int | None:
    return rec.best_baseline_bytes()


def _g_abs(rec) -> int | None:
    return rec.composition_gap_bytes()


def _g_pct(rec) -> float | None:
    g, base = _g_abs(rec), _raw_best(rec)
    if g is None or not base:
        return None
    return g / base


def _fixed_gf2(data: bytes, n_cols: int, *, affine: bool = False):
    def _enc():
        m, lo = reshape_bits(data, n_cols)
        return encode_gf2_matrix(m, original=data, leftover=lo, affine=affine)

    return _enc


def crc_records(*, n_records: int, payload_len: int, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_records):
        p = rng.integers(0, 256, size=payload_len, dtype=np.uint8).tobytes()
        out.append(p + (zlib.crc32(p) & 0xFFFFFFFF).to_bytes(4, "little"))
    return b"".join(out)


def main() -> int:
    failures: list[str] = []

    # ---- positive control: planted GF(2) --------------------------------------
    pos_cfgs = [
        dict(n_rows=1280, n_info=32, n_parity=32, seed=902),
        dict(n_rows=4096, n_info=32, n_parity=32, seed=12),
        dict(n_rows=8192, n_info=48, n_parity=48, seed=777),
    ]
    for cfg in pos_cfgs:
        ds = gf2_linear_code(**cfg)
        n_cols = cfg["n_info"] + cfg["n_parity"]
        rec = run_codec_experiment(
            phase=PHASE,
            experiment_id=f"control_positive_{ds.dataset_id}",
            dataset_id=ds.dataset_id,
            data=ds.data,
            seed=cfg["seed"],
            config={**cfg, "control": "positive", "codec": "gf2", "n_cols": n_cols},
            encode_fn=_fixed_gf2(ds.data, n_cols),
            hypothesis="Planted exact GF(2) code: composed gain must be large and round-trip exact.",
        )
        persist(rec, PHASE)
        print_record(rec)
        gp = _g_pct(rec)
        if not rec.roundtrip_ok:
            failures.append(f"positive {ds.dataset_id}: round-trip failed")
        if gp is None or gp < 0.30:
            failures.append(f"positive {ds.dataset_id}: G_pct={gp} < 0.30")

    # ---- null controls ------------------------------------------------------
    nulls = []
    nb = mixed_noise_bits(n_rows=8192, n_cols=64, seed=41)
    nulls.append(("iid_bits", nb.data, lambda d=nb.data: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64))))
    planted = gf2_linear_code(n_rows=4096, n_info=16, n_parity=16, seed=61)
    shuf = shuffled_bits(planted, seed=62)
    nulls.append(("shuffled_planted", shuf.data, lambda d=shuf.data: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64))))
    near = near_relation_bits(n_rows=4096, n_info=16, seed=51, n_flips=1)
    nulls.append(("near_relation_1flip", near.data, _fixed_gf2(near.data, 17)))

    for tag, data, enc_fn in nulls:
        rec = run_codec_experiment(
            phase=PHASE,
            experiment_id=f"control_null_{tag}",
            dataset_id=tag,
            data=data,
            seed=None,
            config={"control": "null", "tag": tag},
            encode_fn=enc_fn,
            hypothesis="No exact global relation: container must fall back to passthrough, no invented saving.",
        )
        persist(rec, PHASE)
        print_record(rec)
        g = _g_abs(rec)
        is_pt = rec.codec_kind == "PASSTHROUGH" or rec.n_relations == 0
        if not is_pt:
            failures.append(f"null {tag}: not passthrough (kind={rec.codec_kind}, rels={rec.n_relations})")
        if g is None or abs(g) > 64:
            failures.append(f"null {tag}: |G_abs|={g} > 64 (invented/absorbed saving)")

    # ---- degradation sweep -----------------------------------------------
    sweep_phis = [0.0, 1e-4, 1e-3, 1e-2, 5e-2]
    sweep_pts: list[tuple[float, int | None]] = []
    for phi in sweep_phis:
        ds = corrupted_gf2_code(n_rows=4096, n_info=32, n_parity=32, seed=433, flip_fraction=phi)
        n_cols = 64
        rec = run_codec_experiment(
            phase=PHASE,
            experiment_id=f"control_sweep_phi{phi:g}",
            dataset_id=ds.dataset_id,
            data=ds.data,
            seed=433,
            config={"control": "degradation", "flip_fraction": phi, "n_cols": n_cols,
                    "n_flipped": ds.meta["n_flipped"]},
            encode_fn=lambda d=ds.data: encode_bytes_best_gf2(d, widths=(64, 32, 128)),
            hypothesis="As exact structure is broken, composed gain must fall toward 0, never below -64.",
        )
        persist(rec, PHASE)
        print_record(rec)
        g = _g_abs(rec)
        sweep_pts.append((phi, g))
        if g is not None and g < -64:
            failures.append(f"sweep phi={phi:g}: G_abs={g} < -64 (never-worse violated)")

    known = [g for _, g in sweep_pts if g is not None]
    for a, b in zip(known, known[1:]):
        if b > a + 64:  # allow small non-monotone noise, but not a rise
            failures.append(f"sweep not non-increasing: {a} -> {b}")
            break

    # ---- prior-art sanity (recorded, NOT gated) --------------------------
    fd = exact_functional_table(n_rows=8192, seed=21, fn="affine")
    rec = run_codec_experiment(
        phase=PHASE,
        experiment_id="control_priorart_affine_fd",
        dataset_id=fd.dataset_id,
        data=fd.data,
        seed=21,
        config={"control": "prior_art", "label": "FD_elimination", "prior_art": True},
        encode_fn=lambda d=fd.data: encode_tabular_affine(bytes_to_table(d, 3)),
        hypothesis="Derived-column FD elimination. Any composed gain here is PRIOR ART, not hypothesis support.",
        notes="LABEL: functional-dependency elimination (Corra / US 8,150,888 / Wolpe 2026)",
    )
    persist(rec, PHASE)
    print_record(rec)

    crc = crc_records(n_records=4096, payload_len=4, seed=777)
    n_cols = 64
    m, lo = reshape_bits(crc, n_cols)
    rec = run_codec_experiment(
        phase=PHASE,
        experiment_id="control_priorart_crc32_affine",
        dataset_id=f"crc32_n4096_p4_s777",
        data=crc,
        seed=777,
        config={"control": "prior_art", "label": "checksum_inversion", "prior_art": True, "n_cols": n_cols},
        encode_fn=lambda: encode_gf2_matrix(m, original=crc, leftover=lo, affine=True),
        hypothesis="Per-record CRC32 is affine over GF(2). Any composed gain here is PRIOR ART (checksum inversion).",
        notes="LABEL: checksum inversion; not novel",
    )
    persist(rec, PHASE)
    print_record(rec)

    # ---- representation-change null: false-positive rate of the 12-way min ----
    # If the min over {6 widths x 2 variants x passthrough} could "get lucky" on
    # structureless input, we would see the container beat passthrough, or a
    # composed gain above header noise. Run many independent i.i.d. inputs.
    import numpy as _np

    fp_container_beats_pt = 0
    fp_composed_gain = 0
    n_rand = 40
    worst_cgap = 0
    for s in range(n_rand):
        rng = _np.random.default_rng(9000 + s)
        blob = rng.integers(0, 256, size=8192, dtype=_np.uint8).tobytes()
        enc = encode_bytes_best_gf2(blob, widths=(8, 16, 32, 64, 128, 256))
        if len(enc.data) < passthrough_size(len(blob)):
            fp_container_beats_pt += 1
        raw_best = min(len(compress_named(blob, c)) for c in ("gzip9", "bz2_9", "xz9", "brotli11"))
        comp_best = min(len(compress_named(enc.data, c)) for c in ("gzip9", "bz2_9", "xz9", "brotli11"))
        cgap = raw_best - comp_best
        worst_cgap = max(worst_cgap, cgap)
        if cgap > 64:
            fp_composed_gain += 1
    rt_ok = decode(encode_bytes_best_gf2(
        _np.random.default_rng(1).integers(0, 256, 4096, dtype=_np.uint8).tobytes()).data)
    print(
        f"control_repr_change_null: n={n_rand} iid inputs | "
        f"container<passthrough: {fp_container_beats_pt} | composed_gain>64B: {fp_composed_gain} | "
        f"worst composed gain {worst_cgap} B"
    )
    if fp_container_beats_pt or fp_composed_gain:
        failures.append(
            f"repr-change null: {fp_container_beats_pt} container wins / {fp_composed_gain} composed gains "
            f"on {n_rand} structureless inputs (12-way min false positive)"
        )

    # ---- metadata-cost control: metadata is exactly what accounting says -----
    # On a null input the only overhead is the 18-byte passthrough header/crc;
    # on a positive, container == payload + relation + header + crc + framing to
    # the bit (enforced by finalize()), re-checked here from the JSON.
    null_blob = _np.random.default_rng(4242).integers(0, 256, 8192, dtype=_np.uint8).tobytes()
    null_enc = encode_bytes_best_gf2(null_blob)
    meta_only = len(null_enc.data) - len(null_blob)
    print(f"control_metadata_cost: null container - raw = {meta_only} B (expect 18, passthrough header+crc)")
    if meta_only != 18:
        failures.append(f"metadata-cost: null overhead {meta_only} != 18 B")
    pos_ds = gf2_linear_code(n_rows=2048, n_info=32, n_parity=32, seed=555)
    pm, plo = reshape_bits(pos_ds.data, 64)
    pos_enc = encode_gf2_matrix(pm, original=pos_ds.data, leftover=plo)
    a = pos_enc.accounting
    parts = (a.payload_bits + a.relation_description_bits + a.header_bits
             + a.crc_bits + a.framing_bits + a.leftover_bits + a.other_sideinfo_bits)
    meta_share = (a.relation_description_bits + a.header_bits + a.crc_bits
                  + a.framing_bits + a.leftover_bits) / (len(pos_enc.data) * 8)
    print(f"control_metadata_cost: positive container bits {len(pos_enc.data)*8} == sum(categories) {parts}"
          f" | metadata share {meta_share:.4%}")
    if parts != len(pos_enc.data) * 8:
        failures.append(f"metadata-cost: category sum {parts} != container bits {len(pos_enc.data)*8}")

    # ---- framing control: every control container is byte-closed -------------
    for exp_json in sorted((ROOT_RESULTS := (ROOT / "results" / PHASE)).glob("*.json")):
        try:
            dd = json.loads(exp_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        acc = dd.get("accounting", {})
        fr = acc.get("framing_bits")
        tb = acc.get("total_bits")
        if fr is None or tb is None:
            continue
        if not (0 <= fr <= 7):
            failures.append(f"framing: {exp_json.name} framing_bits={fr} not in [0,7]")
        if tb % 8 != 0:
            failures.append(f"framing: {exp_json.name} total_bits={tb} not byte-aligned")

    # ---- composition-order control: explicit, both directions ---------------
    order_ds = gf2_linear_code(n_rows=1280, n_info=32, n_parity=32, seed=902)
    om, olo = reshape_bits(order_ds.data, 64)
    oc = encode_gf2_matrix(om, original=order_ds.data, leftover=olo).data
    order_ok = True
    for c in ("gzip9", "bz2_9", "xz9", "zstd19", "brotli11"):
        back = decompress_named(compress_named(oc, c), c)
        if back != oc or decode(back) != order_ds.data:
            order_ok = False
            failures.append(f"composition-order: {c} decode(decompress(compress(D)))!=x")
    print(f"control_composition_order: decode after decompress-after-compress OK for all codecs: {order_ok}")

    # ---- non-aligned period: exact structure the tried widths cannot see ----
    # Plant a linear code with a 48-bit record period and serialise row-major.
    # The structure is real (rank-deficient in the width-48 view) but 48 is not
    # among the default widths {8,16,32,64,128,256} and no default width aligns
    # to a 48-bit period, so fixed-width discovery falls to passthrough. Run it
    # BOTH ways to prove the structure exists and is only a framing miss.
    import numpy as _np2  # local alias

    W = 48
    rng = _np2.random.default_rng(71)
    n_rows_p = 6000
    info = rng.integers(0, 2, (n_rows_p, W // 2), dtype=_np2.uint8)
    masks = rng.integers(0, 2, (W // 2, W // 2), dtype=_np2.uint8)
    masks[masks.sum(1) == 0, 0] = 1
    parity = (info @ masks.T) & 1
    mat = _np2.concatenate([info, parity], axis=1).astype(_np2.uint8)          # (n_rows_p, 48)
    naligned = _np2.packbits(mat.reshape(-1), bitorder="little").tobytes()      # 6 bytes/row

    enc_default = encode_bytes_best_gf2(naligned, widths=(8, 16, 32, 64, 128, 256))
    enc_with48 = encode_bytes_best_gf2(naligned, widths=(48, 96, 8, 16, 32, 64))
    ok_default_pt = (enc_default.kind.name == "PASSTHROUGH")
    ok_48_finds = (enc_with48.kind.name == "GF2" and enc_with48.n_relations >= 1)
    rt = decode(enc_default.data) == naligned and decode(enc_with48.data) == naligned
    print(
        f"control_nonaligned_period (W=48): default-widths kind={enc_default.kind.name} "
        f"rels={enc_default.n_relations} (expect PASSTHROUGH); "
        f"with-48 kind={enc_with48.kind.name} rels={enc_with48.n_relations} "
        f"container {len(enc_with48.data)} vs raw {len(naligned)}; round-trip={rt}"
    )
    if not ok_default_pt:
        failures.append(f"nonaligned-period: default widths did NOT fall to passthrough "
                        f"(kind={enc_default.kind.name}, rels={enc_default.n_relations})")
    if not ok_48_finds:
        failures.append("nonaligned-period: width-48 discovery failed to find the planted structure "
                        "(the control is only meaningful if the structure is real)")
    if not rt:
        failures.append("nonaligned-period: round-trip failed")
    # record it as a proper experiment via the default (missed) path
    rec = run_codec_experiment(
        phase=PHASE,
        experiment_id="control_nonaligned_period_w48",
        dataset_id="nonaligned_period_w48_s71",
        data=naligned,
        seed=71,
        config={"control": "scope_axis_aligned", "record_period_bits": W,
                "tried_widths": [8, 16, 32, 64, 128, 256],
                "note": "structure is real at width 48/96; not among tried widths"},
        encode_fn=lambda d=naligned: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64, 128, 256)),
        hypothesis="Exact linear structure at a non-power-of-two record period is invisible to fixed-width discovery.",
        notes="SCOPE CONTROL: a negative from these widths does not rule out structure at other periods",
    )
    persist(rec, PHASE)
    print_record(rec)

    # ---- verdict ---------------------------------------------------------
    print("\n--- control sweep G_abs by flip fraction ---")
    for phi, g in sweep_pts:
        print(f"  phi={phi:<7g} G_abs={g}")
    print("\n--- gate result ---")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        print("CONTROLS: FAIL")
        return 1
    print("CONTROLS: PASS (positive, null, and degradation gates all hold)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
