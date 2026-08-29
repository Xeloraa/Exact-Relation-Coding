"""Adversarial nulls: no invented net savings."""

from __future__ import annotations

from deductive.codecs import encode_passthrough
from deductive.codecs.gf2_codec import encode_bytes_best_gf2, never_worse
from deductive.codecs.tabular_codec import encode_tabular_affine, bytes_to_table
from deductive.datasets.synthetic import mixed_noise_bits, mixed_noise_table, near_relation_bits


def test_iid_bits_not_smaller_than_passthrough():
    ds = mixed_noise_bits(n_rows=256, n_cols=32, seed=99)
    enc = encode_bytes_best_gf2(ds.data, widths=(8, 16, 32))
    pt = encode_passthrough(ds.data)
    assert len(enc.data) <= len(pt.data)
    # Deductive container must not beat raw by more than it can justify;
    # for iid bits, it should not beat passthrough, and passthrough is larger than raw.
    assert len(enc.data) >= len(ds.data)


def test_near_relation_not_treated_as_exact_saving():
    ds = near_relation_bits(n_rows=128, n_info=8, seed=3, n_flips=1)
    from deductive.codecs.gf2_codec import encode_gf2_matrix, reshape_bits

    matrix, leftover = reshape_bits(ds.data, 9)
    enc = encode_gf2_matrix(matrix, original=ds.data, leftover=leftover)
    assert enc.n_relations == 0
    guarded = never_worse(ds.data, enc)
    pt = encode_passthrough(ds.data)
    assert len(guarded.data) == len(pt.data)


def test_random_table_no_affine_relations():
    ds = mixed_noise_table(n_rows=100, n_cols=3, seed=4)
    table = bytes_to_table(ds.data, 3)
    enc = encode_tabular_affine(table)
    assert enc.n_relations == 0
