"""The independent (shared-nothing) verifier must accept every container the
main codec produces, and its independent accounting re-derivation must match.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from deductive.codecs.gf2_codec import encode_bytes_gf2, encode_gf2_matrix
from deductive.codecs.passthrough import encode_passthrough
from deductive.codecs.tabular_codec import encode_tabular_affine
from deductive.datasets.synthetic import (
    corrupted_gf2_code,
    exact_functional_table,
    gf2_linear_code,
    integer_linear_table,
    mixed_noise_bits,
)

_spec = importlib.util.spec_from_file_location(
    "independent_verify", Path(__file__).resolve().parents[1] / "verification" / "independent_verify.py"
)
iv = importlib.util.module_from_spec(_spec)
sys.modules["independent_verify"] = iv
_spec.loader.exec_module(iv)


def _check(container: bytes, original: bytes):
    r = iv.verify_container(container, hashlib.sha256(original).hexdigest())
    assert r["sha256_ok"], f"reconstruction hash mismatch: {r}"
    assert r["accounting_ok"], f"independent accounting {r['accounting_bits']} != {r['container_bits']}"
    assert r["ok"]


@pytest.mark.parametrize("seed,w", [(1, 16), (2, 32), (902, 64), (7, 128)])
def test_independent_gf2_linear(seed, w):
    ds = gf2_linear_code(n_rows=600, n_info=w // 4, n_parity=w // 4, seed=seed)
    _check(encode_bytes_gf2(ds.data, w).data, ds.data)


@pytest.mark.parametrize("seed", [3, 11, 42])
def test_independent_gf2_affine(seed):
    ds = gf2_linear_code(n_rows=400, n_info=12, n_parity=12, seed=seed)
    _check(encode_bytes_gf2(ds.data, 24, affine=True).data, ds.data)


def test_independent_gf2_affine_offset():
    rng = np.random.default_rng(11)
    info = rng.integers(0, 2, size=(256, 8), dtype=np.uint8)
    parity = np.bitwise_xor.reduce(info, axis=1) ^ 1
    m = np.concatenate([info, parity.reshape(-1, 1)], axis=1)
    enc = encode_gf2_matrix(m, affine=True)
    # decode target is the byte-padded bit string (original was None)
    from deductive.codecs import decode

    _check(enc.data, decode(enc.data))


@pytest.mark.parametrize("n,seed", [(64, 1), (777, 5)])
def test_independent_passthrough(n, seed):
    data = np.random.default_rng(seed).integers(0, 256, n, dtype=np.uint8).tobytes()
    _check(encode_passthrough(data).data, data)


def test_independent_passthrough_via_noise_best():
    ds = mixed_noise_bits(n_rows=128, n_cols=32, seed=9)
    _check(encode_passthrough(ds.data).data, ds.data)


def test_independent_corrupted_still_roundtrips():
    ds = corrupted_gf2_code(n_rows=1024, n_info=32, n_parity=32, seed=433, flip_fraction=1e-3)
    from deductive.codecs.gf2_codec import encode_bytes_best_gf2

    enc = encode_bytes_best_gf2(ds.data, widths=(64, 32))
    from deductive.codecs import decode

    _check(enc.data, decode(enc.data))


@pytest.mark.parametrize("fn", ["affine"])
def test_independent_tabular_affine(fn):
    ft = exact_functional_table(n_rows=150, seed=6, fn=fn)
    tbl = np.frombuffer(ft.data, dtype=np.int64).reshape(150, 3).copy()
    _check(encode_tabular_affine(tbl).data, ft.data)


def test_independent_tabular_intlin():
    ds = integer_linear_table(n_rows=200, seed=5, extra_independent=1)
    tbl = np.frombuffer(ds.data, dtype=np.int64).reshape(200, 4).copy()
    _check(encode_tabular_affine(tbl).data, ds.data)
