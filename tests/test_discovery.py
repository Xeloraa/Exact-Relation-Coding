"""Blind discovery: relations are verified, not assumed."""

from __future__ import annotations

import numpy as np

from deductive.relations.functional import is_function_of
from deductive.relations.gf2 import column_basis
from deductive.relations.integer_linear import discover_affine_relations


def test_affine_discovers_regardless_of_column_order():
    rng = np.random.default_rng(0)
    x = rng.integers(-1000, 1000, size=80)
    y = rng.integers(-1000, 1000, size=80)
    z = 2 * x + 3 * y + 5
    for order in ((0, 1, 2), (2, 0, 1), (1, 2, 0)):
        cols = [x, y, z]
        table = np.column_stack([cols[i] for i in order])
        ind, rels = discover_affine_relations(table)
        assert len(rels) == 1
        assert rels[0].holds(table)
        assert len(ind) == 2


def test_no_affine_on_independent_columns():
    rng = np.random.default_rng(1)
    table = rng.integers(-(2**20), 2**20, size=(200, 3))
    ind, rels = discover_affine_relations(table)
    assert rels == []
    assert ind == [0, 1, 2]


def test_gf2_does_not_accept_near_relation():
    rng = np.random.default_rng(2)
    info = rng.integers(0, 2, size=(100, 4), dtype=np.uint8)
    parity = np.bitwise_xor.reduce(info, axis=1, keepdims=True)
    parity[0, 0] ^= 1
    matrix = np.concatenate([info, parity], axis=1)
    basis = column_basis(matrix)
    assert basis.rank == 5
    assert basis.n_relations == 0


def test_functional_map_detects_sum():
    table = np.array([[1, 2, 3], [4, 5, 9], [10, 20, 30]], dtype=np.int64)
    assert is_function_of(table, 2, (0, 1))
    noisy = np.array([[1, 2, 3], [1, 2, 4]], dtype=np.int64)
    assert not is_function_of(noisy, 2, (0, 1))
