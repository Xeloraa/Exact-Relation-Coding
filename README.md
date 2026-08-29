# Deductive Coding

Research repository for a single question:

> How much redundancy in real datasets is **exactly deductively recoverable** from other information, rather than merely statistically predictable?

**Deductive Coding** means: discover exact relations that the data satisfies, transmit a fully counted description of those relations plus the independent information, and reconstruct determined symbols. A determined symbol is *not* free unless the decoder can derive it from information already transmitted.

This is a research instrument, not a product. Positive results are not the goal. The goal is a result that survives hostile accounting.

Repository: https://github.com/Xeloraa/deductive-coding

## Status

Phase 0–3 have been run. Planted GF(2) shows a large **composed** deduction gap against gzip/zstd/xz/brotli. Null tests do not invent savings. This repo's own source/docs do **not** show a composed gap. Affine derived-column wins and CRC32-record wins are recorded and labeled as established techniques (FD elimination; checksum inversion), not as novelty.

See `docs/results.md`. The project is not killed; it is also not a real-corpus success.

Derived-column elimination in databases is **established prior art**. This project does not claim that idea. See `docs/prior_art.md`.

## Absolute accounting rule

```
total_encoded_size =
    payload_bits
    + relation_description_bits
    + model/structure description
    + headers
    + framing
    + CRC / side information
    + any other information required for exact decoding
```

Every experiment requires `decode(encode(x)) == x` byte-for-byte.

## Reproduce

Python 3.11+ (developed on 3.13).

```text
pip install -e ".[dev]"
python -m pytest
python experiments/phase0/run.py
python experiments/phase1/run.py
python experiments/phase2/run.py
```

Or:

```text
python scripts/run_all.py
```

Results are written under `results/phase*/` as JSON plus a summary CSV. Large datasets are not committed.

## Layout

```text
src/deductive/     codec, discovery, accounting
tests/             round-trip and null tests
experiments/       phase runners
results/           compact measured artifacts
docs/              log, methodology, theory, prior art, results
```

## What would count as success

A fully accounted, byte-exact encoding whose size is smaller than strong general-purpose compressors **and** remains smaller after composition (`deduction then gzip/zstd/xz/brotli` versus those compressors alone) on data that is not just a known format trick or a database derived column.

If that gap is approximately zero on natural data, that is a valid negative result.

## License

MIT. See `LICENSE`.
