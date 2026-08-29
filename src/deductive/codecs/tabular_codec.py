"""Tabular affine codec: drop exact integer affine columns.

Independent columns are stored as little-endian int64. Relations are stored
as (z, x, y_or_none, a, b, c) with zigzag varints. Every field is counted.

If the fully accounted encoding is not smaller than passthrough of the
raw int64 blob, passthrough is used.
"""

from __future__ import annotations

import zlib

import numpy as np

from deductive.bitstream import AccountedWriter, BitReader
from deductive.codecs.container import Kind, read_preamble, write_preamble
from deductive.codecs.passthrough import Encoded, encode_passthrough
from deductive.relations.integer_linear import (
    AffineRelation,
    apply_relations,
    discover_affine_relations,
)


def table_to_bytes(table: np.ndarray) -> bytes:
    """Canonical raw representation: row-major little-endian int64."""
    arr = np.asarray(table, dtype=np.int64)
    return arr.tobytes(order="C")


def bytes_to_table(data: bytes, n_cols: int) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.int64)
    if arr.size % n_cols != 0:
        raise ValueError("byte length is not a multiple of n_cols * 8")
    return arr.reshape(-1, n_cols).copy()


def _zigzag(n: int) -> int:
    n = int(n)
    return (n << 1) if n >= 0 else ((-n) << 1) - 1


def _unzigzag(n: int) -> int:
    n = int(n)
    return (n >> 1) if (n & 1) == 0 else -((n + 1) >> 1)


def _write_varint(w: AccountedWriter, category: str, n: int) -> None:
    if n < 0:
        raise ValueError("varint must be non-negative")
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            w.write_bits(category, byte | 0x80, 8)
        else:
            w.write_bits(category, byte, 8)
            break


def _read_varint(r: BitReader) -> int:
    shift = 0
    n = 0
    while True:
        b = r.read_bits(8)
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n
        shift += 7
        if shift > 70:
            raise ValueError("varint too long")


def encode_tabular_affine(table: np.ndarray, *, discover: bool = True) -> Encoded:
    arr = np.asarray(table, dtype=np.int64)
    raw = table_to_bytes(arr)
    if discover:
        independent, relations = discover_affine_relations(arr)
    else:
        independent, relations = list(range(arr.shape[1])), []

    n_rows, n_cols = arr.shape
    w = AccountedWriter()
    write_preamble(w, Kind.TABULAR_AFFINE)
    w.write_bits("header", n_rows, 32)
    w.write_bits("header", n_cols, 32)
    w.write_bits("header", len(independent), 16)
    w.write_bits("header", len(relations), 16)
    for idx in independent:
        w.write_bits("relation", idx, 16)
    for rel in relations:
        w.write_bits("relation", rel.z_col, 16)
        w.write_bits("relation", rel.x_col, 16)
        has_y = 0 if rel.y_col is None else 1
        w.write_bits("relation", has_y, 1)
        if rel.y_col is not None:
            w.write_bits("relation", rel.y_col, 16)
        for coeff in (rel.a, rel.b, rel.c):
            _write_varint(w, "relation", _zigzag(int(coeff)))

    payload = table_to_bytes(arr[:, independent]) if independent else b""
    w.write_bits("header", len(payload), 64)
    w.write_bytes("payload", payload)
    crc = zlib.crc32(raw) & 0xFFFFFFFF
    w.write_bits("crc", crc, 32)
    data, acc = w.finalize()
    recovered = n_rows * 64 * len(relations)
    encoded = Encoded(
        data=data,
        accounting=acc,
        kind=Kind.TABULAR_AFFINE,
        n_relations=len(relations),
        n_independent=len(independent),
        recovered_bits=recovered,
        notes="tabular_affine",
    )
    pt = encode_passthrough(raw)
    if len(encoded.data) < len(pt.data):
        return encoded
    pt.notes = "passthrough (affine not smaller after overhead)"
    return pt


def decode_tabular_affine(data: bytes) -> bytes:
    r = BitReader(data)
    kind = read_preamble(r)
    if kind != Kind.TABULAR_AFFINE:
        raise ValueError(f"expected tabular_affine, got {kind}")
    n_rows = r.read_bits(32)
    n_cols = r.read_bits(32)
    n_ind = r.read_bits(16)
    n_rel = r.read_bits(16)
    independent = [r.read_bits(16) for _ in range(n_ind)]
    relations: list[AffineRelation] = []
    for _ in range(n_rel):
        z_col = r.read_bits(16)
        x_col = r.read_bits(16)
        has_y = r.read_bits(1)
        y_col = r.read_bits(16) if has_y else None
        a = _unzigzag(_read_varint(r))
        b = _unzigzag(_read_varint(r))
        c = _unzigzag(_read_varint(r))
        relations.append(AffineRelation(z_col=z_col, x_col=x_col, y_col=y_col, a=a, b=b, c=c))
    payload_len = r.read_bits(64)
    payload = r.read_bytes(payload_len)
    crc = r.read_bits(32)
    if independent:
        ind_table = bytes_to_table(payload, len(independent))
        if ind_table.shape[0] != n_rows:
            raise ValueError("independent row count mismatch")
        values = {independent[i]: ind_table[:, i] for i in range(len(independent))}
    else:
        values = {}
    rec = apply_relations(values, relations, n_rows, n_cols)
    rec_i64 = np.empty((n_rows, n_cols), dtype=np.int64)
    for j in range(n_cols):
        rec_i64[:, j] = [int(v) for v in rec[:, j]]
    raw = table_to_bytes(rec_i64)
    if (zlib.crc32(raw) & 0xFFFFFFFF) != crc:
        raise ValueError("CRC mismatch")
    return raw
