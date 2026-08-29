"""Bit-exact writers and readers with per-category accounting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


def _mask(nbits: int) -> int:
    if nbits >= 64:
        return (1 << nbits) - 1
    return (1 << nbits) - 1


class BitWriter:
    """LSB-first bit packer. Every written bit is counted."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self._acc = 0
        self._acc_bits = 0
        self.nbits = 0

    def write_bits(self, value: int, nbits: int) -> None:
        if nbits < 0:
            raise ValueError("nbits must be non-negative")
        if nbits == 0:
            return
        if value < 0:
            raise ValueError("value must be non-negative")
        remaining = int(value) & _mask(nbits)
        left = nbits
        while left:
            take = min(8 - self._acc_bits, left)
            self._acc |= (remaining & ((1 << take) - 1)) << self._acc_bits
            self._acc_bits += take
            remaining >>= take
            left -= take
            self.nbits += take
            if self._acc_bits == 8:
                self._buf.append(self._acc)
                self._acc = 0
                self._acc_bits = 0

    def write_bytes(self, data: bytes) -> None:
        for b in data:
            self.write_bits(b, 8)

    def pad_to_byte(self) -> int:
        if self._acc_bits == 0:
            return 0
        pad = 8 - self._acc_bits
        self.write_bits(0, pad)
        return pad

    def tobytes(self) -> bytes:
        pad_writer = BitWriter()
        pad_writer._buf = bytearray(self._buf)
        pad_writer._acc = self._acc
        pad_writer._acc_bits = self._acc_bits
        pad_writer.nbits = self.nbits
        pad_writer.pad_to_byte()
        return bytes(pad_writer._buf)

    def finalize(self) -> tuple[bytes, int]:
        """Return packed bytes and the number of padding bits added."""
        pad = 0
        if self._acc_bits:
            pad = 8 - self._acc_bits
            self.write_bits(0, pad)
        return bytes(self._buf), pad


class BitReader:
    """LSB-first bit reader matching BitWriter."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos_bits = 0
        self.nbits_total = len(data) * 8

    def remaining_bits(self) -> int:
        return self.nbits_total - self._pos_bits

    def read_bits(self, nbits: int) -> int:
        if nbits < 0:
            raise ValueError("nbits must be non-negative")
        if nbits == 0:
            return 0
        if self._pos_bits + nbits > self.nbits_total:
            raise ValueError("unexpected end of bitstream")
        value = 0
        shift = 0
        left = nbits
        while left:
            byte_index = self._pos_bits // 8
            bit_index = self._pos_bits % 8
            take = min(8 - bit_index, left)
            chunk = (self._data[byte_index] >> bit_index) & ((1 << take) - 1)
            value |= chunk << shift
            shift += take
            left -= take
            self._pos_bits += take
        return value

    def read_bytes(self, nbytes: int) -> bytes:
        return bytes(self.read_bits(8) for _ in range(nbytes))

    def align_byte(self) -> int:
        rem = self._pos_bits % 8
        if rem == 0:
            return 0
        pad = 8 - rem
        self.read_bits(pad)
        return pad


@dataclass
class Accounting:
    """Complete transmitted-size ledger. Nothing is silently excluded."""

    payload_bits: int = 0
    relation_description_bits: int = 0
    header_bits: int = 0
    framing_bits: int = 0
    crc_bits: int = 0
    leftover_bits: int = 0
    other_sideinfo_bits: int = 0
    extra: dict[str, int] = field(default_factory=dict)

    def add(self, category: str, nbits: int) -> None:
        if nbits < 0:
            raise ValueError("nbits must be non-negative")
        if category == "payload":
            self.payload_bits += nbits
        elif category == "relation":
            self.relation_description_bits += nbits
        elif category == "header":
            self.header_bits += nbits
        elif category == "framing":
            self.framing_bits += nbits
        elif category == "crc":
            self.crc_bits += nbits
        elif category == "leftover":
            self.leftover_bits += nbits
        elif category == "sideinfo":
            self.other_sideinfo_bits += nbits
        else:
            self.extra[category] = self.extra.get(category, 0) + nbits

    @property
    def total_bits(self) -> int:
        return (
            self.payload_bits
            + self.relation_description_bits
            + self.header_bits
            + self.framing_bits
            + self.crc_bits
            + self.leftover_bits
            + self.other_sideinfo_bits
            + sum(self.extra.values())
        )

    @property
    def total_bytes(self) -> int:
        return (self.total_bits + 7) // 8

    def as_dict(self) -> dict[str, int]:
        out = {
            "payload_bits": self.payload_bits,
            "relation_description_bits": self.relation_description_bits,
            "header_bits": self.header_bits,
            "framing_bits": self.framing_bits,
            "crc_bits": self.crc_bits,
            "leftover_bits": self.leftover_bits,
            "other_sideinfo_bits": self.other_sideinfo_bits,
            "total_bits": self.total_bits,
            "total_bytes": self.total_bytes,
        }
        if self.extra:
            out["extra"] = dict(self.extra)
        return out


class AccountedWriter:
    """BitWriter that attributes every bit to an accounting category."""

    def __init__(self) -> None:
        self.writer = BitWriter()
        self.accounting = Accounting()

    def write_bits(self, category: str, value: int, nbits: int) -> None:
        self.accounting.add(category, nbits)
        self.writer.write_bits(value, nbits)

    def write_bytes(self, category: str, data: bytes) -> None:
        self.accounting.add(category, 8 * len(data))
        self.writer.write_bytes(data)

    def finalize(self) -> tuple[bytes, Accounting]:
        data, pad = self.writer.finalize()
        if pad:
            self.accounting.add("framing", pad)
        if len(data) * 8 != self.accounting.total_bits:
            raise RuntimeError(
                f"accounting mismatch: {len(data)*8} packed bits vs "
                f"{self.accounting.total_bits} accounted bits"
            )
        return data, self.accounting


def bits_to_bytes_ceil(nbits: int) -> int:
    return (nbits + 7) // 8


def merge_accounting(parts: Mapping[str, int]) -> Accounting:
    acc = Accounting()
    for k, v in parts.items():
        acc.add(k, int(v))
    return acc
