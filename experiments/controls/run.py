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
from deductive.codecs.gf2_codec import encode_bytes_best_gf2, encode_gf2_matrix, reshape_bits  # noqa: E402
from deductive.codecs.tabular_codec import bytes_to_table, encode_tabular_affine  # noqa: E402
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
