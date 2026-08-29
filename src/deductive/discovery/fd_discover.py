"""Blind functional-dependency discovery entry point."""

from __future__ import annotations

import numpy as np

from deductive.relations.functional import MapDependency, discover_low_cardinality_maps


def discover_functional_maps(table: np.ndarray) -> list[MapDependency]:
    return discover_low_cardinality_maps(table)
