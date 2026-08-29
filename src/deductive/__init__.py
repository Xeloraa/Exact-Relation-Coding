"""Deductive Coding research prototype.

This package implements lossless codecs that discover exact relations,
transmit independent symbols plus a fully accounted relation description,
and reconstruct determined symbols. Nothing is treated as free unless the
decoder can derive it from already-transmitted information.
"""

from __future__ import annotations

__version__ = "0.1.0"

MAGIC = b"DEDC"
FORMAT_VERSION = 1
