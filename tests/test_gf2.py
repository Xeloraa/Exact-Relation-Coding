"""GF(2) discovery and reconstruction."""

from __future__ import annotations

import numpy as np
import pytest

from deductive.relations.gf2 import affine_column_basis, column_basis, reconstruct, verify_basis


def test_planted_parity_rank():
    rng = np.random.default_rng(0)
    n, k, p = 200, 8, 4
    info = rng.integers(0, 2, size=(n, k), dtype=np.uint8)
    parity = np.column_stack(
        [
            info[:, 0] ^ info[:, 1] ^ info[:, 2],
            info[:, 3] ^ info[:, 4],
            np.bitwise_xor.reduce(info, axis=1),
            info[:, 7],
        ]
    )
    matrix = np.concatenate([info, parity], axis=1)
    basis = column_basis(matrix)
    assert basis.rank == k
    assert basis.n_relations == p
    assert verify_basis(matrix, basis)


def test_all_zero_matrix():
    m = np.zeros((10, 5), dtype=np.uint8)
    basis = column_basis(m)
    assert basis.rank == 0
    assert basis.n_relations == 5
    rec = reconstruct(10, 5, np.zeros((10, 0), dtype=np.uint8), basis)
    assert np.array_equal(rec, m)


def test_full_rank_random():
    rng = np.random.default_rng(1)
    m = rng.integers(0, 2, size=(64, 8), dtype=np.uint8)
    # almost surely full rank
    basis = column_basis(m)
    assert basis.rank == 8
    assert basis.n_relations == 0
    assert verify_basis(m, basis)


def test_identity():
    m = np.eye(7, dtype=np.uint8)
    basis = column_basis(m)
    assert basis.rank == 7
    assert verify_basis(m, basis)


@pytest.mark.parametrize("n_cols", [1, 7, 8, 9, 64, 65])
def test_wide_and_narrow(n_cols):
    rng = np.random.default_rng(n_cols + 3)
    info = rng.integers(0, 2, size=(40, max(1, n_cols // 2)), dtype=np.uint8)
    if n_cols == info.shape[1]:
        m = info
    else:
        extra = n_cols - info.shape[1]
        dep = np.zeros((40, extra), dtype=np.uint8)
        for j in range(extra):
            dep[:, j] = info[:, j % info.shape[1]]
        m = np.concatenate([info, dep], axis=1)
    basis = column_basis(m)
    assert verify_basis(m, basis)
    assert basis.rank <= min(m.shape)


def test_affine_recovers_constant_offset():
    rng = np.random.default_rng(4)
    info = rng.integers(0, 2, size=(80, 5), dtype=np.uint8)
    parity = np.bitwise_xor.reduce(info, axis=1) ^ 1
    matrix = np.concatenate([info, parity.reshape(-1, 1)], axis=1)
    lin = column_basis(matrix)
    aff = affine_column_basis(matrix)
    assert lin.n_relations == 0
    assert aff.n_relations == 1
    assert aff.ones_is_pivot

