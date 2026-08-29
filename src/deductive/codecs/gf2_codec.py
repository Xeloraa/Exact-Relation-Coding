"""GF(2) deductive codec with fully counted relation description.

Container layout (LSB-first bits, then byte padding):

    magic[4] version[8] kind[8]
    n_rows[32] n_cols[32] n_payload_pivots[32]
    flags[8]  (bit0=affine, bit1=ones_is_pivot, bit2=has_prefix;
               ones column is never sent)
    original_nbytes[64] leftover_nbits[32]
    leftover bits (if any)
    prefix_nbits[32] + prefix bits          -- only if flags bit2 (bit-offset codec)
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
    GF2AffineBasis,
    GF2ColumnBasis,
    affine_column_basis,
    column_basis,
    extract_pivot_bits,
    reconstruct,
    reconstruct_affine,
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


def reshape_bits_offset(data: bytes, n_cols: int, offset: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reshape starting `offset` bits in. Returns (matrix, prefix, leftover).

    `prefix` is the `offset` bits skipped before the first row; `leftover` is the
    `< n_cols` bits after the last full row. Together with the matrix they
    reconstruct every bit of `data` in order. offset == 0 gives an empty prefix
    and is equivalent to `reshape_bits`.
    """
    if n_cols <= 0:
        raise ValueError("n_cols must be positive")
    if not (0 <= offset < n_cols):
        raise ValueError("offset must be in [0, n_cols)")
    bits = bits_from_bytes(data)
    prefix = bits[:offset]
    body = bits[offset:]
    n_rows = body.size // n_cols
    used = n_rows * n_cols
    matrix = body[:used].reshape(n_rows, n_cols)
    leftover = body[used:]
    return matrix, prefix, leftover


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
    prefix: np.ndarray | None = None,
    basis: GF2ColumnBasis | None = None,
    affine: bool = False,
) -> Encoded:
    bit = (matrix.astype(np.uint8, copy=False) & 1)
    aff: GF2AffineBasis | None = None
    if affine:
        if basis is not None:
            raise ValueError("explicit homogeneous basis cannot be used with affine=True")
        aff = affine_column_basis(bit)
        n_rows, n_cols = aff.n_rows, aff.n_cols
        n_payload = aff.n_payload_pivots
        n_rel = aff.n_relations
        recovered = aff.recovered_bits()
        notes = "gf2_affine"
    else:
        if basis is None:
            basis = column_basis(bit)
        else:
            if not verify_basis(bit, basis):
                raise ValueError("provided basis does not hold on this matrix")
        n_rows, n_cols = basis.n_rows, basis.n_cols
        n_payload = basis.rank
        n_rel = basis.n_relations
        recovered = basis.recovered_bits()
        notes = "gf2"

    if leftover is None:
        leftover_u8 = np.zeros(0, dtype=np.uint8)
    else:
        leftover_u8 = leftover.astype(np.uint8).reshape(-1) & 1
    if prefix is None:
        prefix_u8 = np.zeros(0, dtype=np.uint8)
    else:
        prefix_u8 = prefix.astype(np.uint8).reshape(-1) & 1
    if original is None:
        if prefix_u8.size:
            raise ValueError("prefix requires an explicit `original`")
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
        have = int(prefix_u8.size + bit.size + leftover_u8.size)
        if have < needed:
            raise ValueError("prefix+matrix+leftover shorter than original")

    if n_rel == 0:
        # Full column rank: relation description cannot omit symbols.
        return encode_passthrough(original)

    w = AccountedWriter()
    write_preamble(w, Kind.GF2)
    w.write_bits("header", n_rows, 32)
    w.write_bits("header", n_cols, 32)
    w.write_bits("header", n_payload, 32)
    flags = 0
    if affine:
        flags |= 1
        if aff is not None and aff.ones_is_pivot:
            flags |= 2
    if prefix_u8.size:
        flags |= 4
    w.write_bits("header", flags, 8)
    w.write_bits("header", len(original), 64)
    w.write_bits("leftover", int(leftover_u8.size), 32)
    w.write_bit_array("leftover", leftover_u8)
    if prefix_u8.size:
        w.write_bits("prefix", int(prefix_u8.size), 32)
        w.write_bit_array("prefix", prefix_u8)

    if affine and aff is not None:
        pivot_cols = np.asarray(aff.real_pivot_indices, dtype=np.int64)
        coeff_matrix = aff.coefficients
    else:
        assert basis is not None
        pivot_cols = np.asarray(basis.pivot_indices, dtype=np.int64)
        coeff_matrix = basis.coefficients

    pivot_mask = np.zeros(n_cols, dtype=np.uint8)
    if pivot_cols.size:
        pivot_mask[pivot_cols] = 1
    w.write_bit_array("relation", pivot_mask)
    w.write_bit_array("relation", np.ascontiguousarray(coeff_matrix.astype(np.uint8) & 1).reshape(-1))

    if affine and aff is not None:
        if aff.n_payload_pivots:
            pivot_bits = np.column_stack([bit[:, p] for p in aff.real_pivot_indices])
        else:
            pivot_bits = np.zeros((n_rows, 0), dtype=np.uint8)
    else:
        pivot_bits = extract_pivot_bits(bit, basis)

    w.write_bit_array("payload", np.ascontiguousarray(pivot_bits.astype(np.uint8) & 1).reshape(-1))

    crc = zlib.crc32(original) & 0xFFFFFFFF
    w.write_bits("crc", crc, 32)
    data, acc = w.finalize()
    encoded = Encoded(
        data=data,
        accounting=acc,
        kind=Kind.GF2,
        n_relations=n_rel,
        n_independent=n_payload,
        recovered_bits=recovered,
        notes=notes,
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
    flags = r.read_bits(8)
    if flags & ~0b111:
        raise ValueError(f"unknown flag bits set: {flags:#010b}")
    affine = bool(flags & 1)
    ones_is_pivot = bool(flags & 2)
    has_prefix = bool(flags & 4)
    orig_len = r.read_bits(64)
    leftover_nbits = r.read_bits(32)
    leftover = r.read_bit_array(leftover_nbits)
    if has_prefix:
        prefix_nbits = r.read_bits(32)
        prefix = r.read_bit_array(prefix_nbits)
    else:
        prefix = np.zeros(0, dtype=np.uint8)
    pivot_mask = r.read_bit_array(n_cols)
    pivot_indices = tuple(int(i) for i in np.flatnonzero(pivot_mask))
    free_indices = tuple(int(i) for i in np.flatnonzero(pivot_mask == 0))
    if len(pivot_indices) != n_pivots:
        raise ValueError("n_pivots does not match pivot mask")
    n_free = n_cols - n_pivots
    coeff_width = n_pivots + (1 if ones_is_pivot else 0)
    coeffs = r.read_bit_array(n_free * coeff_width).reshape(n_free, coeff_width).astype(np.uint8)
    pivot_bits = r.read_bit_array(n_rows * n_pivots).reshape(n_rows, n_pivots).astype(np.uint8)
    if affine:
        aff = GF2AffineBasis(
            n_rows=n_rows,
            n_cols=n_cols,
            real_pivot_indices=pivot_indices,
            free_indices=free_indices,
            ones_is_pivot=ones_is_pivot,
            coefficients=coeffs,
        )
        matrix = reconstruct_affine(n_rows, n_cols, pivot_bits, aff)
    else:
        if ones_is_pivot:
            raise ValueError("ones_is_pivot requires affine flag")
        basis = GF2ColumnBasis(
            n_rows=n_rows,
            n_cols=n_cols,
            pivot_indices=pivot_indices,
            free_indices=free_indices,
            coefficients=coeffs,
        )
        matrix = reconstruct(n_rows, n_cols, pivot_bits, basis)
    parts = [matrix.reshape(-1)]
    if prefix.size:
        parts.insert(0, prefix)
    if leftover.size:
        parts.append(leftover)
    flat = np.concatenate(parts) if len(parts) > 1 else parts[0]
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


def encode_bytes_gf2(data: bytes, n_cols: int, *, affine: bool = False) -> Encoded:
    matrix, leftover = reshape_bits(data, n_cols)
    return encode_gf2_matrix(matrix, original=data, leftover=leftover, affine=affine)


def encode_bytes_gf2_offset(data: bytes, n_cols: int, offset: int, *, affine: bool = False) -> Encoded:
    """GF(2) codec on the bit matrix that starts `offset` bits into `data`.

    offset == 0 is byte-identical to `encode_bytes_gf2`. offset > 0 carries the
    skipped `offset` bits as a counted `prefix` field (flags bit 2).
    """
    matrix, prefix, leftover = reshape_bits_offset(data, n_cols, offset)
    return encode_gf2_matrix(matrix, original=data, leftover=leftover, prefix=prefix, affine=affine)


def encode_bytes_best_gf2_offsets(
    data: bytes,
    width_offsets=((8, None), (16, None), (32, None), (64, None), (128, 8), (256, 8)),
) -> tuple[Encoded, dict]:
    """Detector extension: for each width, try a set of bit phase offsets.

    `width_offsets` is a sequence of `(w, n_offsets)`: `n_offsets=None` sweeps
    every phase `0..w-1`; an integer `k` sweeps `0..k-1` (a coarse sweep for
    wide `w`). Bounded — no nonlinear search. Returns the smallest fully
    accounted container over all `(width, offset, {homogeneous, affine})` plus
    passthrough, and a dict describing the winning config and the sweep size.
    """
    best = encode_passthrough(data)
    best_cfg = {"kind": "passthrough", "width": None, "offset": None, "affine": None}
    tried = errored = 0
    for w, n_off in width_offsets:
        if w <= 0:
            continue
        limit = w if n_off is None else min(w, int(n_off))
        for off in range(limit):
            for affine in (False, True):
                tried += 1
                try:
                    cand = encode_bytes_gf2_offset(data, w, off, affine=affine)
                except Exception:  # noqa: BLE001
                    errored += 1
                    continue
                if len(cand.data) < len(best.data):
                    best = cand
                    best_cfg = {"kind": cand.kind.name, "width": w, "offset": off,
                                "affine": affine}
    info = {**best_cfg, "configs_tried": tried, "configs_errored": errored,
            "width_offsets": [list(t) for t in width_offsets]}
    best.notes = (f"offset-search {best_cfg['kind']} w={best_cfg['width']} "
                  f"off={best_cfg['offset']} affine={best_cfg['affine']} "
                  f"({tried} configs, {errored} errored)")
    return best, info


def encode_bytes_best_gf2(
    data: bytes,
    widths: tuple[int, ...] = (8, 16, 32, 64, 128, 256),
    *,
    strict: bool = False,
) -> Encoded:
    """Try several column widths, homogeneous and affine, plus passthrough.

    A per-config failure is recorded (count + last message) in the returned
    ``Encoded.notes`` rather than silently dropped, so a discovery/verification
    bug cannot hide as a skipped width. With ``strict=True`` any per-config
    exception is re-raised instead of recorded.
    """
    best = encode_passthrough(data)
    best_desc = "passthrough"
    errors: list[str] = []
    for w in widths:
        if w <= 0:
            continue
        for affine in (False, True):
            try:
                cand = encode_bytes_gf2(data, w, affine=affine)
            except Exception as exc:  # noqa: BLE001
                if strict:
                    raise
                errors.append(f"w={w} affine={affine}: {type(exc).__name__}: {exc}")
                continue
            if len(cand.data) < len(best.data):
                best = cand
                best_desc = f"gf2 {'affine' if affine else 'linear'} n_cols={w}"
    note = best_desc
    if errors:
        note += f" | {len(errors)} config(s) errored; last: {errors[-1]}"
    best.notes = note
    return best


def passthrough_size(nbytes: int) -> int:
    """Byte length of a passthrough container for an ``nbytes`` payload.

    Layout is all whole-byte fields: magic(4) version(1) kind(1) len(8) crc(4)
    then the payload verbatim. No bit padding is ever needed.
    """
    return nbytes + 18


def never_worse(data: bytes, candidate: Encoded) -> Encoded:
    """Replace a candidate with passthrough if it is not strictly smaller."""
    if len(candidate.data) < passthrough_size(len(data)):
        return candidate
    return encode_passthrough(data)
