"""Randomised property tests for the correctness-critical primitives.

These target the places a silent bug could inflate or deflate a measured gain:
the vectorised bit I/O, the vectorised GF(2) reconstruction, and the column
basis itself. Each is checked against an independent slow reference over many
random trials and shapes, including awkward alignments and wide bases.
"""

from __future__ import annotations

import numpy as np
import pytest

from deductive.bitstream import BitReader, BitWriter
from deductive.relations.gf2 import (
    GF2ColumnBasis,
    column_basis,
    reconstruct,
    verify_basis,
)

RNG = np.random.default_rng(20260829)


# --- bit I/O: write_bit_array / read_bit_array == the per-bit loop ---------

@pytest.mark.parametrize("trial", range(200))
def test_write_bit_array_matches_per_bit_loop(trial):
    n_pre = int(RNG.integers(0, 20))          # bits written one-at-a-time first
    n_arr = int(RNG.integers(0, 500))         # then a bulk array
    n_post = int(RNG.integers(0, 20))
    pre = RNG.integers(0, 2, n_pre, dtype=np.uint8)
    arr = RNG.integers(0, 2, n_arr, dtype=np.uint8)
    post = RNG.integers(0, 2, n_post, dtype=np.uint8)

    ref = BitWriter()
    for b in pre:
        ref.write_bits(int(b), 1)
    for b in arr:
        ref.write_bits(int(b), 1)
    for b in post:
        ref.write_bits(int(b), 1)
    ref_bytes, _ = ref.finalize()

    fast = BitWriter()
    for b in pre:
        fast.write_bits(int(b), 1)
    fast.write_bit_array(arr)
    for b in post:
        fast.write_bits(int(b), 1)
    fast_bytes, _ = fast.finalize()

    assert fast_bytes == ref_bytes
    assert fast.nbits == ref.nbits


@pytest.mark.parametrize("trial", range(200))
def test_read_bit_array_matches_per_bit_loop(trial):
    n_total = int(RNG.integers(1, 400))
    payload = RNG.integers(0, 256, (n_total + 7) // 8, dtype=np.uint8).tobytes()
    skip = int(RNG.integers(0, min(16, n_total)))
    take = int(RNG.integers(0, n_total - skip + 1))

    r1 = BitReader(payload)
    for _ in range(skip):
        r1.read_bits(1)
    ref = np.array([r1.read_bits(1) for _ in range(take)], dtype=np.uint8)

    r2 = BitReader(payload)
    for _ in range(skip):
        r2.read_bits(1)
    fast = r2.read_bit_array(take)

    assert np.array_equal(fast, ref)
    assert r1._pos_bits == r2._pos_bits


# --- GF(2) reconstruct: matmul path == the per-column XOR reference --------

def _reconstruct_reference(n_rows, n_cols, pivot_bits, basis):
    out = np.zeros((n_rows, n_cols), dtype=np.uint8)
    for j, p in enumerate(basis.pivot_indices):
        out[:, p] = pivot_bits[:, j] & 1
    for i, f in enumerate(basis.free_indices):
        acc = np.zeros(n_rows, dtype=np.uint8)
        for j in range(len(basis.pivot_indices)):
            if basis.coefficients[i, j]:
                acc ^= out[:, basis.pivot_indices[j]]
        out[:, f] = acc
    return out


@pytest.mark.parametrize("trial", range(60))
def test_reconstruct_matches_xor_reference(trial):
    n_rows = int(RNG.integers(1, 400))
    n_piv = int(RNG.integers(1, 130))          # up to a wide basis
    n_free = int(RNG.integers(0, 40))
    n_cols = n_piv + n_free
    perm = RNG.permutation(n_cols)
    pivot_indices = tuple(sorted(int(x) for x in perm[:n_piv]))
    free_indices = tuple(sorted(int(x) for x in perm[n_piv:]))
    coeffs = RNG.integers(0, 2, (n_free, n_piv), dtype=np.uint8)
    basis = GF2ColumnBasis(n_rows, n_cols, pivot_indices, free_indices, coeffs)
    pivot_bits = RNG.integers(0, 2, (n_rows, n_piv), dtype=np.uint8)

    fast = reconstruct(n_rows, n_cols, pivot_bits, basis)
    ref = _reconstruct_reference(n_rows, n_cols, pivot_bits, basis)
    assert np.array_equal(fast, ref)


# --- column_basis: finds exactly the planted rank deficiency --------------

@pytest.mark.parametrize("trial", range(40))
def test_column_basis_recovers_planted_relations(trial):
    n_rows = int(RNG.integers(80, 400))
    n_info = int(RNG.integers(2, 24))
    n_parity = int(RNG.integers(1, 16))
    # make the info block itself full column rank so rank == n_info exactly
    while True:
        info = RNG.integers(0, 2, (n_rows, n_info), dtype=np.uint8)
        if column_basis(info).rank == n_info:
            break
    masks = RNG.integers(0, 2, (n_parity, n_info), dtype=np.uint8)
    masks[masks.sum(axis=1) == 0, 0] = 1
    parity = (info @ masks.T) & 1
    matrix = np.concatenate([info, parity], axis=1).astype(np.uint8)

    basis = column_basis(matrix)
    assert verify_basis(matrix, basis)                       # relations hold on every row
    assert basis.rank == n_info                              # info columns are the pivots
    assert basis.n_relations == n_parity                     # exactly the planted parities are free
    assert set(basis.free_indices) == set(range(n_info, n_info + n_parity))


@pytest.mark.parametrize("trial", range(20))
def test_column_basis_full_rank_on_random(trial):
    # tall random 0/1 matrix, few columns: full column rank almost surely
    n_rows = int(RNG.integers(200, 600))
    n_cols = int(RNG.integers(2, 24))
    m = RNG.integers(0, 2, (n_rows, n_cols), dtype=np.uint8)
    basis = column_basis(m)
    assert verify_basis(m, basis)
    # if it did find a relation it must be exact (verify_basis already checked)
