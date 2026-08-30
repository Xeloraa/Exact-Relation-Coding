# Exact-Relation Coding

*(formerly "Deductive Coding" — renamed to avoid the qualitative-research and
2026 semantic-compression senses of that term; see `docs/naming.md`. The Python
package path `src/deductive/` and the `DEDC` container magic are kept as legacy.)*

Research repository for a single question:

> How much redundancy in real datasets is **exactly deductively recoverable** from other information, rather than merely statistically predictable?

**Deductive Coding** means: discover exact relations that the data satisfies, transmit a fully counted description of those relations plus the independent information, and reconstruct determined symbols. A determined symbol is *not* free unless the decoder can derive it from information already transmitted.

This is a research instrument, not a product. Positive results are not the goal. The goal is a result that survives hostile accounting.

**Frozen research artifact:** git tag [`v1.1-final`](https://github.com/Xeloraa/deductive-coding/releases/tag/v1.1-final)
(commit `1216ef6`). The paper is `paper/exact-relation-coding.pdf`. To create a
GitHub Release and a Zenodo DOI from this tag, follow `PUBLISHING.md`;
`CITATION.cff` and `.zenodo.json` hold the archive metadata (author identity is
a placeholder pending the real name/ORCID). No DOI has been minted yet.

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
- `experiments/natural/run.py` — pre-registered corpus list (12 Silesia + enwik8
  + 6 SDRBench EXAALT f32 fields + UCI household power). **8 of 12 Silesia
  members run whole** (`results/natural/`, ≤ 10 MB — the dev-machine ceiling);
  all 12 + enwik8 + 6 float fields + telemetry as ≥ 256 KiB prefixes
  (`results/natural_slice/`). **0 meaningful positives on any of them.** The 4
  largest Silesia members + whole enwik8/SDRBench/UCI need > 8 GiB
  (`docs/environment_constraints.md`); `--mode whole` runs them unchanged.
- `experiments/offset/run.py` — bit-phase-offset detector extension (the kill
  criterion's one bounded broadening attempt): every width × every bit phase.
  Run on every natural file — **0 threshold crossings**, no file beats phase-0
  by more than header noise. The axis-aligned negative is phase-robust.
  `docs/kill_criterion_status.md`.
- `scripts/reproduce.py` — one command: pytest+equivalence+properties+independent
  verifier → downloads → controls → natural → offset → phases → ledger → tables
  → figures → number check → ledger verify; writes `results/REPRODUCE.md`.
- `docs/audit.md` — adversarial implementation audit (A1–A9 fixed; correction
  C1). `docs/adversarial_review.md` — every credible reviewer objection + the
  13 canonical ones, each resolved / narrowed / disclosed.
  `docs/submission_gap_audit.md` — the REQ/REC/OPT/NO checklist.
  `docs/venue_assessment.md` — honest venue call (**B**: workshop /
  negative-results / preprint). `docs/statistics.md` — RQ-A..E layer reporting.
- `verification/independent_verify.py` — shared-nothing second decoder +
  independent accounting re-derivation + `verify_composed` (full
  `raw→encode→compress→decompress→decode→raw` chain).
- `results/ledger.{json,csv}` — one row per experiment; **0** accounting /
  round-trip / composed-round-trip failures.
- **`paper/exact-relation-coding.pdf`** — the finished manuscript (17 pp, A4),
  frozen at tag **`v1.1-final`**. Source: `paper/exact-relation-coding.md`
  (+ `results_tables.md`, `figures/*.svg`, all generated). Rebuild:
  `python scripts/make_figures.py && python scripts/build_pdf.py` (headless
  Chromium). Every inline figure carries a source marker verified against
  `results/ledger.json` by `scripts/check_paper_numbers.py`.
  Result in one line: **inconclusive w.r.t. the complete preregistered corpus
  (4 large whole-file runs need > 8 GiB), a clean layered negative within the
  achieved coverage** (8 whole Silesia members + 20 files at 256 KiB + a
  bit-phase-offset extension; largest natural `G_pct` = +0.09 %, on a
  passthrough container).

**Whole natural files done (8/12 Silesia):** 3 find GF(2) relations
(`dickens` −94 %, `x-ray` −47 %, `xml` −303 %) and 5 fall to passthrough
(header noise). Every one is round-trip + composed round-trip verified; none
is a meaningful positive. The bit-phase-offset extension changes nothing.

Prior established results unchanged: planted GF(2) shows a large **composed**
deduction gap against gzip/zstd/xz/brotli, paq8l `-3`/`-8`, and paq8px v216
`-4`/`-8`, scaling with rows. Null tests invent no savings. Silesia *prefixes*,
enwik8, stdlib, PNG/ZIP, structured JSON/log text show **no** composed gap.
Affine derived-column and CRC32-record wins are labelled established techniques
(FD elimination; checksum inversion), not novelty. See `docs/results.md`.

Current verdict: **INCONCLUSIVE-for-the-full-list by the pre-registration**
(4 giant Silesia members + whole enwik8/SDRBench/UCI need > 8 GiB), while the
coverage achieved — 8/12 Silesia whole + 12 slices + 6 float fields + telemetry
+ the bit-phase-offset extension — is a clean, layered **NEGATIVE**
(structure exists → is discoverable → still does not reduce the representation).
Venue: **B** (workshop / negative-results / preprint); `docs/venue_assessment.md`.
The mechanism itself is not novel (`docs/prior_art.md`).

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
