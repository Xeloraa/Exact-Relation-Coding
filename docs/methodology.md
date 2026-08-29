# Methodology

## Hypothesis

There exist datasets, including some natural ones, whose redundancy is an *exact* relation the decoder can reconstruct, and for which transmitting the relation plus independent symbols is cheaper than what strong statistical compressors achieve on the raw bytes — after every bit of description, header, CRC, and padding is counted.

The hypothesis is empirical. It can fail because:

1. discovery finds nothing exact;
2. relation description costs more than the recovered symbols;
3. strong compressors already exploit the same structure;
4. composition (`deduce` then `xz`) erases the gap;
5. apparent wins are format-specific engineering (CRC, lengths, indexes).

## Accounting

`AccountedWriter` attributes every written bit to a category. Finalize pads to a whole byte and counts padding as framing. The packed length in bits must equal `accounting.total_bits`.

CRC32 of the original byte string is stored and counted. It is not required for reconstruction of a trusted stream; it is included because a real container needs integrity and this project forbids hidden metadata.

Passthrough is the never-worse fallback: original bytes plus counted header and CRC. A candidate encoding is not reported as a win unless it is strictly smaller than this fallback **and** compared against gzip, zlib, bz2, xz, zstd, and brotli on the same raw bytes.

## Discovery

### GF(2)

The data is viewed as a 0/1 matrix. Gaussian elimination computes the leftmost column basis. Each free column is expressed as an XOR of pivot columns. The map is verified on the original matrix before encoding. Planted relations are not passed to the codec.

Column width for byte strings is a hypothesis: the encoder may try several widths and keep the smallest fully accounted container, including passthrough.

### Integer affine

Relations `z = a x + b y + c` are recovered from the table by solving on a few distinct rows and verifying every row with Python integers (no wrap). Search is order-independent: a determined column is dropped even if it appears first. Coefficients are encoded as zigzag varints and counted as relation description.

### Functional maps

Exact maps `(sources) -> z` are detectable, but a lookup table is transmitted only if used, and its cost is counted. Low-cardinality maps can be cheaper than a column; high-cardinality maps are not.

## Round-trip

`decode(encode(x)) == x` is asserted in unit tests and in every experiment runner. Failure aborts the experiment.

## Baselines

Python stdlib: gzip-9, zlib-9, bz2-9, lzma/xz preset 9.
Optional packages: zstandard-19, brotli quality 11.

Missing compressors are recorded as unavailable, not omitted.

## Composition

The deductive container is itself compressed with each baseline. The **composition gap** is

```text
min_c |c(raw)| - min_c |c(deductive_container)|
```

over available compressors `c`. This is the primary test of whether deduction exposes structure statistical codecs leave unused.

## Reproducibility

Each `ExperimentRecord` stores UTC time, git commit, dataset SHA-256, byte length, seed, config, command line, machine info, package versions, accounting breakdown, baseline sizes and runtimes, composition sizes, and round-trip status.

Synthetic data is generated from documented seeds. Large corpora are not stored in git; download instructions live in `src/deductive/datasets/corpora.py` and `docs/results.md`.

## What we refuse to claim

Autoregressive models **can** represent parity distributions. An experiment in which a sequential predictor fails to compress XOR bits is evidence about *that predictor, that order, and that compute budget*, not about a mathematical impossibility. See `docs/theory.md`.
