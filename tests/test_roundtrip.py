"""Byte-exact encode/decode for every codec kind."""

from __future__ import annotations

import numpy as np

from deductive.codecs import decode, encode_passthrough
from deductive.codecs.gf2_codec import encode_bytes_best_gf2, encode_gf2_matrix, reshape_bits
from deductive.codecs.tabular_codec import encode_tabular_affine, table_to_bytes
from deductive.datasets.synthetic import (
    exact_functional_table,
    gf2_linear_code,
    integer_linear_table,
    mixed_noise_bits,
)


def test_passthrough_roundtrip():
    data = b"hello deductive coding\x00\xff"
    enc = encode_passthrough(data)
    assert decode(enc.data) == data
    assert enc.accounting.total_bytes == len(enc.data)
    assert len(enc.data) > len(data)


def test_gf2_planted_roundtrip():
    ds = gf2_linear_code(n_rows=256, n_info=8, n_parity=8, seed=7)
    n_cols = 16
    matrix, leftover = reshape_bits(ds.data, n_cols)
    enc = encode_gf2_matrix(matrix, original=ds.data, leftover=leftover)
    assert decode(enc.data) == ds.data
    assert enc.n_relations == 8
    assert enc.recovered_bits == 256 * 8


def test_gf2_odd_dimensions_roundtrip():
    rng = np.random.default_rng(3)
    matrix = rng.integers(0, 2, size=(10, 3), dtype=np.uint8)
    matrix[:, 2] = matrix[:, 0] ^ matrix[:, 1]
    enc = encode_gf2_matrix(matrix)
    rec = decode(enc.data)
    # reconstructed bytes contain the matrix bits plus pad leftover
    from deductive.codecs.gf2_codec import bits_from_bytes

    bits = bits_from_bytes(rec)
    assert np.array_equal(bits[:30].reshape(10, 3), matrix)


def test_gf2_best_never_worse_on_noise():
    ds = mixed_noise_bits(n_rows=128, n_cols=32, seed=9)
    enc = encode_bytes_best_gf2(ds.data, widths=(8, 16, 32))
    assert decode(enc.data) == ds.data
    pt = encode_passthrough(ds.data)
    assert len(enc.data) <= len(pt.data)


def test_tabular_affine_roundtrip():
    ds = integer_linear_table(n_rows=200, seed=5, extra_independent=1)
    table = np.frombuffer(ds.data, dtype=np.int64).reshape(200, 4).copy()
    enc = encode_tabular_affine(table)
    assert decode(enc.data) == table_to_bytes(table)
    assert enc.n_relations == 1


def test_affine_fd_roundtrip():
    ds = exact_functional_table(n_rows=150, seed=6, fn="affine")
    table = np.frombuffer(ds.data, dtype=np.int64).reshape(150, 3).copy()
    enc = encode_tabular_affine(table)
    assert decode(enc.data) == ds.data
    assert enc.n_relations == 1
