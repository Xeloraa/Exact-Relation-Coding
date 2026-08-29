"""Freeze current deductive-codec output bytes as an equivalence reference.

Run BEFORE any codec-internal refactor:

    python tests/_gen_codec_reference.py

Writes tests/data/codec_reference.json. For each deterministic case it records
the SHA-256 and length of encode(x).data (plus full hex for small cases), the
accounting bit total, and the SHA-256 of decode(encode(x)) -- the object a
correct codec must still reconstruct. tests/test_codec_equivalence.py then
asserts a refactored codec reproduces the container bytes exactly and decodes
to the same reconstruction. Regenerate only for an intended format change,
and say so in the commit.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

from deductive.codecs import decode  # noqa: E402
from deductive.codecs.gf2_codec import (  # noqa: E402
    encode_bytes_best_gf2,
    encode_bytes_gf2,
    encode_gf2_matrix,
)
from deductive.codecs.passthrough import encode_passthrough  # noqa: E402
from deductive.codecs.tabular_codec import encode_tabular_affine  # noqa: E402
from deductive.datasets.synthetic import (  # noqa: E402
    exact_functional_table,
    gf2_linear_code,
    integer_linear_table,
    mixed_noise_bits,
    near_relation_bits,
)

OUT = ROOT / "tests" / "data" / "codec_reference.json"
FULL_HEX_MAX = 4096


def cases():
    """Yield (name, make) where make() -> Encoded. Deterministic, no I/O."""
    yield "pt_ascii", lambda: encode_passthrough(b"hello deductive coding\x00\xff")
    yield "pt_1k_zeros", lambda: encode_passthrough(bytes(1024))
    yield "pt_prng", lambda: encode_passthrough(
        np.random.default_rng(1).integers(0, 256, 777, dtype=np.uint8).tobytes()
    )

    for (nr, ni, npar, seed, w) in [
        (256, 8, 8, 7, 16),
        (128, 16, 16, 11, 32),
        (1280, 32, 32, 902, 64),
        (512, 24, 8, 33, 32),
    ]:
        ds = gf2_linear_code(n_rows=nr, n_info=ni, n_parity=npar, seed=seed)
        yield (
            f"gf2_fixed_n{nr}_i{ni}_p{npar}_s{seed}_w{w}",
            lambda ds=ds, w=w: encode_bytes_gf2(ds.data, w),
        )

    ds = gf2_linear_code(n_rows=400, n_info=12, n_parity=12, seed=5)
    yield "gf2_affine_fixed_n400_s5_w24", lambda ds=ds: encode_bytes_gf2(ds.data, 24, affine=True)

    # bit-phase-offset codec (flags bit2, `prefix` field). Added 2026-08-29
    # with the detector-scope extension; the phase-0 cases above are unchanged.
    from deductive.codecs.gf2_codec import encode_bytes_gf2_offset  # noqa: PLC0415
    ds = gf2_linear_code(n_rows=700, n_info=16, n_parity=16, seed=13)
    for _off in (1, 7, 19):
        yield (f"gf2_offset_n700_s13_w32_off{_off}",
               lambda ds=ds, _o=_off: encode_bytes_gf2_offset(ds.data, 32, _o))

    def _affine_offset():
        rng = np.random.default_rng(11)
        info = rng.integers(0, 2, size=(256, 8), dtype=np.uint8)
        parity = np.bitwise_xor.reduce(info, axis=1) ^ 1
        m = np.concatenate([info, parity.reshape(-1, 1)], axis=1)
        return encode_gf2_matrix(m, affine=True)

    yield "gf2_affine_offset_n256", _affine_offset

    ds = gf2_linear_code(n_rows=600, n_info=20, n_parity=20, seed=41)
    yield "best_planted_n600_s41", lambda ds=ds: encode_bytes_best_gf2(ds.data)
    ds = mixed_noise_bits(n_rows=128, n_cols=32, seed=9)
    yield "best_noise_n128_s9", lambda ds=ds: encode_bytes_best_gf2(ds.data, widths=(8, 16, 32))
    ds = near_relation_bits(n_rows=128, n_info=8, seed=3, n_flips=1)
    yield "best_near_relation_s3", lambda ds=ds: encode_bytes_best_gf2(ds.data, widths=(9, 8, 16))

    def _odd():
        rng = np.random.default_rng(3)
        m = rng.integers(0, 2, size=(10, 3), dtype=np.uint8)
        m[:, 2] = m[:, 0] ^ m[:, 1]
        return encode_gf2_matrix(m)

    yield "gf2_odd_10x3", _odd

    ds = integer_linear_table(n_rows=200, seed=5, extra_independent=1)
    tbl = np.frombuffer(ds.data, dtype=np.int64).reshape(200, 4).copy()
    yield "tab_intlin_n200_s5", lambda tbl=tbl: encode_tabular_affine(tbl)
    ds = exact_functional_table(n_rows=150, seed=6, fn="affine")
    tbl = np.frombuffer(ds.data, dtype=np.int64).reshape(150, 3).copy()
    yield "tab_affine_fd_n150_s6", lambda tbl=tbl: encode_tabular_affine(tbl)


def _digest(data: bytes) -> dict:
    d = {"sha256": hashlib.sha256(data).hexdigest(), "len": len(data)}
    if len(data) <= FULL_HEX_MAX:
        d["hex"] = data.hex()
    return d


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-new", action="store_true",
                    help="keep existing frozen entries; only add cases not already present "
                         "(use when appending cases without disturbing pre-vectorisation hashes)")
    args = ap.parse_args()

    ref = {"_meta": {"full_hex_max": FULL_HEX_MAX}}
    if args.only_new and OUT.is_file():
        ref = json.loads(OUT.read_text(encoding="utf-8"))
    timings = []
    added = 0
    for name, make in cases():
        if args.only_new and name in ref:
            continue
        t0 = time.perf_counter()
        enc = make()
        enc_s = time.perf_counter() - t0
        t1 = time.perf_counter()
        recon = decode(enc.data)
        dec_s = time.perf_counter() - t1
        entry = _digest(enc.data)
        entry["accounting_total_bits"] = int(enc.accounting.total_bits)
        entry["reconstruction_sha256"] = hashlib.sha256(recon).hexdigest()
        entry["reconstruction_len"] = len(recon)
        ref[name] = entry
        added += 1
        timings.append((name, len(enc.data), enc_s, dec_s))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ref, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT} with {len(ref) - 1} cases ({added} (re)generated)")
    for name, nbytes, es, dsec in timings:
        print(f"  {name:34s} {nbytes:>9d} B  enc {es:>7.3f}s  dec {dsec:>7.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
