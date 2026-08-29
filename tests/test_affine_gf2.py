"""Affine GF(2): implicit ones column vs homogeneous discovery."""

from __future__ import annotations

import zlib

import numpy as np

from deductive.codecs import decode, encode_passthrough
from deductive.codecs.gf2_codec import bits_from_bytes, encode_gf2_matrix, reshape_bits
from deductive.datasets.synthetic import gf2_linear_code
from deductive.relations.gf2 import affine_column_basis, column_basis


def _crc_records_matrix(n_records: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = np.zeros((n_records, 64), dtype=np.uint8)
    for i in range(n_records):
        payload = rng.integers(0, 256, size=4, dtype=np.uint8).tobytes()
        crc = (zlib.crc32(payload) & 0xFFFFFFFF).to_bytes(4, "little")
        rec = payload + crc
        bits = np.unpackbits(np.frombuffer(rec, dtype=np.uint8), bitorder="little")
        rows[i] = bits
    return rows


def test_affine_offset_parity_ones_is_pivot():
    rng = np.random.default_rng(4)
    info = rng.integers(0, 2, size=(80, 5), dtype=np.uint8)
    parity = np.bitwise_xor.reduce(info, axis=1) ^ 1
    matrix = np.concatenate([info, parity.reshape(-1, 1)], axis=1)
    lin = column_basis(matrix)
    aff = affine_column_basis(matrix)
    assert lin.n_relations == 0
    assert aff.n_relations == 1
    assert aff.ones_is_pivot


def test_crc32_homogeneous_vs_affine_relation_count():
    matrix = _crc_records_matrix(200, seed=7)
    lin = column_basis(matrix)
    aff = affine_column_basis(matrix)
    assert lin.n_relations == 31
    assert aff.n_relations == 32
    assert aff.ones_is_pivot


def test_crc32_affine_encode_roundtrip_beats_passthrough():
    n = 256
    matrix = _crc_records_matrix(n, seed=11)
    enc = encode_gf2_matrix(matrix, affine=True)
    rec = decode(enc.data)
    bits = bits_from_bytes(rec)
    assert np.array_equal(bits[: matrix.size].reshape(matrix.shape), matrix)
    assert enc.n_relations == 32
    pt = encode_passthrough(rec)
    assert len(enc.data) < len(pt.data)


def test_homogeneous_still_finds_linear_parity():
    ds = gf2_linear_code(n_rows=256, n_info=8, n_parity=8, seed=7)
    matrix, leftover = reshape_bits(ds.data, 16)
    enc = encode_gf2_matrix(matrix, original=ds.data, leftover=leftover, affine=False)
    assert decode(enc.data) == ds.data
    assert enc.n_relations == 8
