"""Accounting surface: every transmitted bit is attributed."""

from __future__ import annotations

from deductive.bitstream import AccountedWriter, Accounting, BitReader, BitWriter

__all__ = ["Accounting", "AccountedWriter", "BitReader", "BitWriter"]
