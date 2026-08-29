from __future__ import annotations

from deductive.datasets.synthetic import (
    SyntheticDataset,
    exact_functional_table,
    gf2_linear_code,
    integer_linear_table,
    mixed_noise_bits,
    mixed_noise_table,
    near_relation_bits,
    shuffled_bits,
)
from deductive.datasets.corpora import (
    builtin_corpora,
    load_enwik8_prefix,
    local_pe_sample,
    make_csv_fd,
    make_png,
    make_sqlite_fd,
    make_zip_stored,
    python_stdlib_sample,
)

__all__ = [
    "SyntheticDataset",
    "gf2_linear_code",
    "exact_functional_table",
    "integer_linear_table",
    "mixed_noise_bits",
    "mixed_noise_table",
    "near_relation_bits",
    "shuffled_bits",
    "builtin_corpora",
    "make_png",
    "make_zip_stored",
    "make_csv_fd",
    "make_sqlite_fd",
    "python_stdlib_sample",
    "local_pe_sample",
    "load_enwik8_prefix",
]
