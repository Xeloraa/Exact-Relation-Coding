# Exact-Relation Coding

*(formerly "Deductive Coding" — renamed to avoid the qualitative-research and
2026 semantic-compression senses of that term; see `docs/naming.md`. The Python
package path `src/deductive/` and the `DEDC` container magic are kept as legacy.)*

Research repository for a single question:

> How much redundancy in real datasets is **exactly deductively recoverable** from other information, rather than merely statistically predictable?

**Deductive Coding** means: discover exact relations that the data satisfies, transmit a fully counted description of those relations plus the independent information, and reconstruct determined symbols. A determined symbol is *not* free unless the decoder can derive it from information already transmitted.

This is a research instrument, not a product. Positive results are not the goal. The goal is a result that survives hostile accounting.

Repository: https://github.com/Xeloraa/deductive-coding

## Status

**Publication-quality campaign in progress.** The methodology is now locked and
hardware-independent work is done; the whole-file / full-baseline sweep is
deferred to a higher-memory machine.

- `docs/preregistration.md` — **git-locked** meaningful-positive threshold
  (composed gain ≥ 5% of the strongest baseline **and** ≥ 1024 B, round-trip
  exact, real deduction, non-prior-art corpus) and permanent kill criterion,
  fixed before the natural-corpus runs.
- `docs/metric.md` — formal composed-gain metric over the full post-downstream
  representation. `docs/protocol.md` — protocol, the RQ-A/B/C claim separation,
  corpora, baselines. `docs/environment_constraints.md` — why cmix/nncp and
  whole-file corpora need a bigger machine.
- `experiments/controls/run.py` — positive / null / corruption-sweep / labelled
  prior-art battery, all gates **pass** (`results/controls/`).
- `experiments/natural/run.py` — pre-registered corpus list (12 whole Silesia +
  enwik8 + 6 SDRBench EXAALT f32 fields + UCI household power). Dev-machine
  **feasibility slices** only so far (`results/natural_slice/`, 256 KiB
  prefixes): 20/20 round-trip ok, 0 meaningful positives. **Not the answer** —
  `--mode whole` on a ≥ 32 GiB machine is required (`docs/preregistration.md` §4).
- `scripts/reproduce.py` — one command: pytest+equivalence+properties+independent
  verifier → downloads → controls → natural → phases → ledger → paper tables →
  number check → ledger verify; writes `results/REPRODUCE.md`.
- `docs/audit.md` — from-scratch adversarial implementation audit (findings
  A1–A7 fixed; correction C1). `docs/adversarial_review.md` — every credible
  reviewer objection with disposition. `docs/statistics.md` — why conventional
  statistics mostly do not apply here and what is reported instead.
- `verification/independent_verify.py` — shared-nothing second decoder +
  independent accounting re-derivation (run in CI and over the ledger).
- `results/ledger.{json,csv}` — one row per experiment, every quantity;
  **0** accounting / round-trip / composed-round-trip failures across 95 rows.
- `paper/deductive-coding.md` — full 24-section technical paper; inline numbers
  ledger-checked; Results §15.2 and the §21 verdict `PENDING` the whole-file
  sweep. `paper/results_tables.md` — generated, no hand-typed numbers.

**One clean whole natural file is done:** Silesia `dickens` (10.19 MB) —
GF(2) finds 25 relations, container is larger than raw, `G_abs` ≈ −2.6 MB
(−94%), round-trip + composed round-trip + independent decode all pass.
Every other whole-file corpus is deferred (dev machine tops out ~10 MB
foreground; `docs/environment_constraints.md`).

Prior established results unchanged: planted GF(2) shows a large **composed**
deduction gap against gzip/zstd/xz/brotli, paq8l `-3`/`-8`, and paq8px v216
`-4`/`-8`, scaling with rows. Null tests invent no savings. Silesia *prefixes*,
enwik8, stdlib, PNG/ZIP, structured JSON/log text show **no** composed gap.
Affine derived-column and CRC32-record wins are labelled established techniques
(FD elimination; checksum inversion), not novelty. See `docs/results.md`.

Current verdict: **INCONCLUSIVE by the pre-registration** until the whole-file
sweep exists. The project is not killed and is not a real-corpus success.

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
python experiments/phase3/run.py
python experiments/phase4/run.py
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
