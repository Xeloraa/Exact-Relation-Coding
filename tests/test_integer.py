"""Integer affine discovery and codec."""

from __future__ import annotations

import numpy as np

from deductive.codecs import decode
from deductive.codecs.tabular_codec import encode_tabular_affine
from deductive.relations.integer_linear import discover_affine_relations


def test_univariate_affine():
    x = np.arange(20, dtype=np.int64)
    y = 7 * x - 3
    table = np.column_stack([x, y])
    ind, rels = discover_affine_relations(table)
    assert len(rels) == 1
    assert rels[0].a == 7 and rels[0].c == -3
    assert ind == [0]


def test_bivariate_and_codec_smaller():
    rng = np.random.default_rng(8)
    x = rng.integers(-(2**20), 2**20, size=500, dtype=np.int64)
    y = rng.integers(-(2**20), 2**20, size=500, dtype=np.int64)
    z = 4 * x - y + 11
    table = np.column_stack([x, y, z])
    enc = encode_tabular_affine(table)
    assert decode(enc.data) == table.tobytes(order="C")
    assert enc.n_relations == 1
    assert len(enc.data) < table.nbytes + 16
