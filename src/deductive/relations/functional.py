"""Exact functional-dependency discovery for tabular columns.

A column z is a function of columns S if equal S-tuples imply equal z.
The decoder can reconstruct z from a transmitted lookup table only if that
table is itself transmitted. The table cost is counted in full.

This is not claimed as novel (see docs/prior_art.md). It exists so the
research question can be tested honestly on synthetic FD data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MapDependency:
    z_col: int
    source_cols: tuple[int, ...]
    # keys are tuples of source values; values are z
    mapping: dict[tuple[int, ...], int]

    def table_entries(self) -> int:
        return len(self.mapping)


def is_function_of(table: np.ndarray, z_col: int, source_cols: tuple[int, ...]) -> bool:
    seen: dict[tuple[int, ...], int] = {}
    for row in table:
        key = tuple(int(row[c]) for c in source_cols)
        val = int(row[z_col])
        prev = seen.get(key)
        if prev is None:
            seen[key] = val
        elif prev != val:
            return False
    return True


def extract_map(table: np.ndarray, z_col: int, source_cols: tuple[int, ...]) -> MapDependency | None:
    if not is_function_of(table, z_col, source_cols):
        return None
    mapping: dict[tuple[int, ...], int] = {}
    for row in table:
        key = tuple(int(row[c]) for c in source_cols)
        mapping[key] = int(row[z_col])
    return MapDependency(z_col=z_col, source_cols=source_cols, mapping=mapping)


def mapping_cost_bits(dep: MapDependency, value_bits: int, key_bits_per_col: list[int]) -> int:
    """Honest description cost of a lookup table.

    Each entry stores the source key and the z value. No sharing is assumed.
    """
    key_bits = sum(key_bits_per_col)
    n = dep.table_entries()
    # store n, then n records
    return 32 + n * (key_bits + value_bits)


def discover_low_cardinality_maps(
    table: np.ndarray,
    *,
    max_sources: int = 2,
    max_map_entries: int | None = None,
) -> list[MapDependency]:
    """Greedy: later columns as maps of earlier independent columns.

    A map is kept only if it is an exact function. Callers must still
    compare mapping_cost_bits against storing the column raw.
    """
    n_rows, n_cols = table.shape
    if max_map_entries is None:
        max_map_entries = max(1, n_rows // 2)
    independent: list[int] = []
    deps: list[MapDependency] = []
    for j in range(n_cols):
        found: MapDependency | None = None
        # unary
        for i in independent:
            if is_function_of(table, j, (i,)):
                dep = extract_map(table, j, (i,))
                if dep is not None and dep.table_entries() <= max_map_entries:
                    found = dep
                    break
        if found is None and max_sources >= 2:
            for a in range(len(independent)):
                for b in range(a + 1, len(independent)):
                    src = (independent[a], independent[b])
                    if is_function_of(table, j, src):
                        dep = extract_map(table, j, src)
                        if dep is not None and dep.table_entries() <= max_map_entries:
                            found = dep
                            break
                if found is not None:
                    break
        if found is not None:
            deps.append(found)
        else:
            independent.append(j)
    return deps
