from __future__ import annotations

from deductive.codecs.container import Kind
from deductive.codecs.gf2_codec import decode_gf2, encode_bytes_best_gf2, encode_gf2_matrix
from deductive.codecs.passthrough import Encoded, decode_passthrough, encode_passthrough
from deductive.codecs.tabular_codec import decode_tabular_affine, encode_tabular_affine
from deductive.bitstream import BitReader
from deductive.codecs.container import read_preamble


def decode(data: bytes) -> bytes:
    kind = read_preamble(BitReader(data))
    if kind == Kind.PASSTHROUGH:
        return decode_passthrough(data)
    if kind == Kind.GF2:
        return decode_gf2(data)
    if kind == Kind.TABULAR_AFFINE:
        return decode_tabular_affine(data)
    raise ValueError(f"unknown kind {kind}")


__all__ = [
    "Kind",
    "Encoded",
    "encode_passthrough",
    "encode_gf2_matrix",
    "encode_bytes_best_gf2",
    "encode_tabular_affine",
    "decode",
    "decode_passthrough",
    "decode_gf2",
    "decode_tabular_affine",
]
