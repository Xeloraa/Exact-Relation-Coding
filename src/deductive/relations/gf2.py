"""GF(2) linear algebra: rank, column basis, nullspace, reconstruction.

All arithmetic is exact over the field with two elements. Relations are
accepted only if they hold on every row of the dataset.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GF2ColumnBasis:
    """Leftmost column basis plus exact reconstructions of free columns.

    For every free column j, reconstructed[:, j] equals the XOR of the
    pivot columns indicated by coeff_rows[j].
    """

    n_rows: int
    n_cols: int
    pivot_indices: tuple[int, ...]
    free_indices: tuple[int, ...]
    # shape (n_free, n_pivots) over {0,1}
    coefficients: np.ndarray

    @property
    def rank(self) -> int:
        return len(self.pivot_indices)

    @property
    def n_relations(self) -> int:
        return len(self.free_indices)

    def recovered_bits(self) -> int:
        return self.n_rows * self.n_relations


def pack_rows(matrix: np.ndarray) -> tuple[np.ndarray, int]:
    """Pack a (n_rows, n_cols) 0/1 matrix into uint64 words per row."""
    if matrix.ndim != 2:
        raise ValueError("matrix must be 2-D")
    n_rows, n_cols = matrix.shape
    n_words = (n_cols + 63) // 64
    packed = np.zeros((n_rows, n_words), dtype=np.uint64)
    bit = matrix.astype(np.uint8, copy=False)
    for c in range(n_cols):
        word, off = divmod(c, 64)
        packed[:, word] |= bit[:, c].astype(np.uint64) << np.uint64(off)
    return packed, n_cols


def unpack_rows(packed: np.ndarray, n_cols: int) -> np.ndarray:
    n_rows = packed.shape[0]
    out = np.zeros((n_rows, n_cols), dtype=np.uint8)
    for c in range(n_cols):
        word, off = divmod(c, 64)
        out[:, c] = ((packed[:, word] >> np.uint64(off)) & np.uint64(1)).astype(np.uint8)
    return out


def _bit(packed_row: np.ndarray, col: int) -> int:
    word, off = divmod(col, 64)
    return int((packed_row[word] >> np.uint64(off)) & np.uint64(1))


def column_basis(matrix: np.ndarray) -> GF2ColumnBasis:
    """Compute the leftmost column basis of a 0/1 matrix over GF(2).

    Uses Gaussian elimination on a working copy. Pivot columns are the
    unique leftmost independent set. Each free column is expressed as a
    linear combination of pivot columns; the combination is verified
    against the original matrix before being returned.
    """
    if matrix.size == 0:
        return GF2ColumnBasis(0, matrix.shape[1] if matrix.ndim == 2 else 0, (), (), np.zeros((0, 0), dtype=np.uint8))
    bit = (matrix.astype(np.uint8, copy=False) & 1).copy()
    n_rows, n_cols = bit.shape
    packed, _ = pack_rows(bit)
    work = packed.copy()
    pivot_cols: list[int] = []
    pivot_row_for_col: dict[int, int] = {}
    rank = 0
    for col in range(n_cols):
        word, off = divmod(col, 64)
        mask = np.uint64(1) << np.uint64(off)
        col_nonzero = np.flatnonzero((work[rank:, word] & mask) != 0)
        if col_nonzero.size == 0:
            continue
        found = int(col_nonzero[0]) + rank
        if found != rank:
            work[[rank, found]] = work[[found, rank]]
        # eliminate this column from all other rows
        has = (work[:, word] & mask).astype(bool)
        has[rank] = False
        if np.any(has):
            work[has] ^= work[rank]
        pivot_cols.append(col)
        pivot_row_for_col[col] = rank
        rank += 1
        if rank == n_rows:
            break

    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(n_cols) if c not in pivot_set]
    n_piv = len(pivot_cols)
    coeffs = np.zeros((len(free_cols), n_piv), dtype=np.uint8)
    for i, fcol in enumerate(free_cols):
        for j, pcol in enumerate(pivot_cols):
            prow = pivot_row_for_col[pcol]
            coeffs[i, j] = _bit(work[prow], fcol)

    basis = GF2ColumnBasis(
        n_rows=n_rows,
        n_cols=n_cols,
        pivot_indices=tuple(pivot_cols),
        free_indices=tuple(free_cols),
        coefficients=coeffs,
    )
    if not verify_basis(bit, basis):
        raise RuntimeError("GF(2) basis failed verification against the original matrix")
    return basis


def reconstruct(n_rows: int, n_cols: int, pivot_bits: np.ndarray, basis: GF2ColumnBasis) -> np.ndarray:
    """Reconstruct the full 0/1 matrix from pivot column bits and the basis.

    pivot_bits: shape (n_rows, n_pivots)
    """
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


def verify_basis(matrix: np.ndarray, basis: GF2ColumnBasis) -> bool:
    bit = matrix.astype(np.uint8, copy=False) & 1
    if bit.shape != (basis.n_rows, basis.n_cols):
        return False
    if not basis.pivot_indices:
        return bool(np.all(bit == 0))
    pivot_bits = np.column_stack([bit[:, p] for p in basis.pivot_indices])
    rec = reconstruct(basis.n_rows, basis.n_cols, pivot_bits, basis)
    return bool(np.array_equal(rec, bit))


def extract_pivot_bits(matrix: np.ndarray, basis: GF2ColumnBasis) -> np.ndarray:
    bit = matrix.astype(np.uint8, copy=False) & 1
    if not basis.pivot_indices:
        return np.zeros((basis.n_rows, 0), dtype=np.uint8)
    return np.column_stack([bit[:, p] for p in basis.pivot_indices])


def relation_description_bits(basis: GF2ColumnBasis) -> int:
    """Bits required to encode the basis under the canonical v1 layout.

    Layout (excluding container header):
      n_rows: 32
      n_cols: 32
      n_pivots: 32
      pivot mask: n_cols
      coefficients: n_free * n_pivots
    """
    return 32 + 32 + 32 + basis.n_cols + basis.n_relations * basis.rank
