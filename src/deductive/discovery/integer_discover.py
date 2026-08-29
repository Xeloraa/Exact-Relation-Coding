"""Blind integer-linear discovery entry point."""

from __future__ import annotations

import numpy as np

from deductive.relations.integer_linear import AffineRelation, discover_affine_relations


def discover_integer_affine(table: np.ndarray) -> tuple[list[int], list[AffineRelation]]:
    return discover_affine_relations(table)
