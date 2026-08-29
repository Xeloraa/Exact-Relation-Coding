"""GF(2) deductive codec with fully counted relation description.

Container layout (LSB-first bits, then byte padding):

    magic[4] version[8] kind[8]
    n_rows[32] n_cols[32] n_pivots[32]
    original_nbytes[64] leftover_nbits[8]
    leftover bits (if any)
    pivot_mask[n_cols]
    for each free column in increasing index:
        coefficients[n_pivots]
    pivot payload: n_rows * n_pivots bits (row-major, pivot-column order)
    crc32 of the original byte string [32]
    padding to a whole byte

Dependent bits are omitted from the payload. They are free only because
the decoder already has the pivot bits and the coefficient matrix.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

import numpy as np

from deductive.bitstream import AccountedWriter, BitReader
from deductive.codecs.container import Kind, read_preamble, write_preamble
from deductive.codecs.passthrough import Encoded, encode_passthrough
from deductive.relations.gf2 import (
    GF2ColumnBasis,
    column_basis,
    extract_pivot_bits,
    reconstruct,
    verify_basis,
)


def bits_from_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = np.unpackbits(arr, bitorder="little")
    return bits.astype(np.uint8)


def bytes_from_bits(bits: np.ndarray) -> bytes:
    if bits.size % 8 != 0:
        raise ValueError("bit length must be a multiple of 8")
    packed = np.packbits(bits.astype(np.uint8), bitorder="little")
    return packed.tobytes()


def reshape_bits(data: bytes, n_cols: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (n_rows, n_cols) matrix and leftover bits (length < n_cols)."""
    if n_cols <= 0:
        raise ValueError("n_cols must be positive")
    bits = bits_from_bytes(data)
    n_bits = bits.size
    n_rows = n_bits // n_cols
    used = n_rows * n_cols
    matrix = bits[:used].reshape(n_rows, n_cols)
    leftover = bits[used:]
    return matrix, leftover


@dataclass
class GF2EncodeChoice:
    n_cols: int
    encoded: Encoded
    basis: GF2ColumnBasis


def encode_gf2_matrix(
    matrix: np.ndarray,
    *,
    original: bytes | None = None,
    leftover: np.ndarray | None = None,
    basis: GF2ColumnBasis | None = None,
) -> Encoded:
    bit = (matrix.astype(np.uint8, copy=False) & 1)
    if basis is None:
        basis = column_basis(bit)
    else:
        if not verify_basis(bit, basis):
            raise ValueError("provided basis does not hold on this matrix")
    if leftover is None:
        leftover_u8 = np.zeros(0, dtype=np.uint8)
    else:
        leftover_u8 = leftover.astype(np.uint8).reshape(-1) & 1
    if original is None:
        if leftover_u8.size:
            flat = np.concatenate([bit.reshape(-1), leftover_u8])
        else:
            flat = bit.reshape(-1).copy()
        if flat.size % 8 != 0:
            pad = 8 - (flat.size % 8)
            leftover_u8 = np.concatenate([leftover_u8, np.zeros(pad, dtype=np.uint8)])
            flat = np.concatenate([bit.reshape(-1), leftover_u8])
        original = bytes_from_bits(flat)
    else:
        needed = len(original) * 8
        have = int(bit.size + leftover_u8.size)
        if have < needed:
            raise ValueError("matrix+leftover shorter than original")

    w = AccountedWriter()
    write_preamble(w, Kind.GF2)
    w.write_bits("header", basis.n_rows, 32)
    w.write_bits("header", basis.n_cols, 32)
    w.write_bits("header", basis.rank, 32)
    w.write_bits("header", len(original), 64)
    w.write_bits("leftover", int(leftover_u8.size), 32)
    for b in leftover_u8.tolist():
        w.write_bits("leftover", int(b) & 1, 1)

    pivot_set = set(basis.pivot_indices)
    for c in range(basis.n_cols):
        w.write_bits("relation", 1 if c in pivot_set else 0, 1)

    for i in range(basis.n_relations):
        for j in range(basis.rank):
            w.write_bits("relation", int(basis.coefficients[i, j]) & 1, 1)

    pivot_bits = extract_pivot_bits(bit, basis)
    n_rows = basis.n_rows
    for r in range(n_rows):
        for j in range(basis.rank):
            w.write_bits("payload", int(pivot_bits[r, j]) & 1, 1)

    crc = zlib.crc32(original) & 0xFFFFFFFF
    w.write_bits("crc", crc, 32)
    data, acc = w.finalize()
    encoded = Encoded(
        data=data,
        accounting=acc,
        kind=Kind.GF2,
        n_relations=basis.n_relations,
        n_independent=basis.rank,
        recovered_bits=basis.recovered_bits(),
        notes="gf2",
    )
    return never_worse(original, encoded)


def decode_gf2(data: bytes) -> bytes:
    r = BitReader(data)
    kind = read_preamble(r)
    if kind != Kind.GF2:
        raise ValueError(f"expected gf2, got {kind}")
    n_rows = r.read_bits(32)
    n_cols = r.read_bits(32)
    n_pivots = r.read_bits(32)
    orig_len = r.read_bits(64)
    leftover_nbits = r.read_bits(32)
    leftover = np.array([r.read_bits(1) for _ in range(leftover_nbits)], dtype=np.uint8)
    pivot_mask = [r.read_bits(1) for _ in range(n_cols)]
    pivot_indices = tuple(i for i, b in enumerate(pivot_mask) if b)
    free_indices = tuple(i for i, b in enumerate(pivot_mask) if not b)
    if len(pivot_indices) != n_pivots:
        raise ValueError("n_pivots does not match pivot mask")
    n_free = n_cols - n_pivots
    coeffs = np.zeros((n_free, n_pivots), dtype=np.uint8)
    for i in range(n_free):
        for j in range(n_pivots):
            coeffs[i, j] = r.read_bits(1)
    pivot_bits = np.zeros((n_rows, n_pivots), dtype=np.uint8)
    for row in range(n_rows):
        for j in range(n_pivots):
            pivot_bits[row, j] = r.read_bits(1)
    basis = GF2ColumnBasis(
        n_rows=n_rows,
        n_cols=n_cols,
        pivot_indices=pivot_indices,
        free_indices=free_indices,
        coefficients=coeffs,
    )
    matrix = reconstruct(n_rows, n_cols, pivot_bits, basis)
    flat = matrix.reshape(-1)
    if leftover.size:
        flat = np.concatenate([flat, leftover])
    # original may have included pad bits to byte-align a synthetic matrix
    if orig_len == 0:
        rec = b""
    else:
        needed_bits = orig_len * 8
        if flat.size < needed_bits:
            raise ValueError("not enough reconstructed bits")
        rec = bytes_from_bits(flat[:needed_bits])
    crc = r.read_bits(32)
    if (zlib.crc32(rec) & 0xFFFFFFFF) != crc:
        raise ValueError("CRC mismatch")
    if len(rec) != orig_len:
        raise ValueError("length mismatch")
    return rec


def encode_bytes_gf2(data: bytes, n_cols: int) -> Encoded:
    matrix, leftover = reshape_bits(data, n_cols)
    return encode_gf2_matrix(matrix, original=data, leftover=leftover)


def encode_bytes_best_gf2(
    data: bytes,
    widths: tuple[int, ...] = (8, 16, 32, 64, 128, 256),
) -> Encoded:
    """Try several column widths plus passthrough; keep the smallest total."""
    best = encode_passthrough(data)
    for w in widths:
        if w <= 0:
            continue
        try:
            cand = encode_bytes_gf2(data, w)
        except Exception:
            continue
        if len(cand.data) < len(best.data):
            best = cand
            best.notes = f"gf2 n_cols={w}"
    return best


def never_worse(data: bytes, candidate: Encoded) -> Encoded:
    """Replace a candidate with passthrough if it is not strictly smaller."""
    pt = encode_passthrough(data)
    if len(candidate.data) < len(pt.data):
        return candidate
    return pt
