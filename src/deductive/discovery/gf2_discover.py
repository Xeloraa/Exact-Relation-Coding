"""Blind GF(2) discovery entry point."""

from __future__ import annotations

import numpy as np

from deductive.relations.gf2 import GF2ColumnBasis, column_basis


def discover_gf2_relations(matrix: np.ndarray) -> GF2ColumnBasis:
    """Discover a verified leftmost column basis. No planted relations are used."""
    return column_basis(matrix)
