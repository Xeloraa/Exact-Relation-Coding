# Venue assessment

Honest self-assessment of where Exact-Relation Coding can be submitted, after
the publication-grade hardening + evidence-completion passes. Not "the repo is
polished, therefore A".

## What the evidence now is

- **Mechanism (H1):** planted GF(2) codes — large composed gain
  (`G_pct` ≈ 0.48–0.50), scales with rows, description near-constant,
  independently verified end-to-end, not absorbed by paq8l / paq8px v216.
  *Solid.*
- **Natural data (H2 / RQ-E):** 8 of 12 Silesia members whole (up to ~10 MB);
  all 12 + enwik8 prefix + 6 SDRBench float32 fields + UCI household power as
  ≥ 256 KiB prefixes; plus a bounded bit-phase-offset extension of the detector.
  **0 files clear the pre-registered threshold; max per-file `G_pct` < 0.**
  The offset extension does not change this. *Consistent, strong negative — but
  the 4 largest Silesia members (21–51 MB) and whole enwik8 / SDRBench / UCI
  were not runnable on the available hardware.*
- **Controls:** positive / null / corruption sweep / representation-change
  false-positive / metadata-cost / composition-order / non-aligned-period —
  all gates pass. *Exceptionally thorough for this kind of study.*
- **Methodology:** bit-exact ledger with a hard invariant, structural
  never-worse, pre-registration git-locked before results, independent
  shared-nothing decoder incl. the composed chain, all paper numbers generated
  from a machine-readable ledger. *Above the norm for the area.*
- **Novelty:** the general mechanism is **not novel** (grammar compression;
  syndrome-source-coding 1976; Brevis 2026 program-synthesis tensor
  compression). The contribution is the scoped, pre-registered empirical
  evaluation + the methodology.

## Grade

### Not A (a serious compression/main venue, e.g. DCC full paper)

Two gaps a strong PC would hold against it, neither cosmetic:

1. **Coverage.** Whole-file results stop at ~10 MB. `samba`/`nci`/`webster`/
   `mozilla` (21–51 MB), whole enwik8, whole SDRBench fields, whole UCI — the
   pre-registered list — are prefix-only, on hardware grounds. A DCC reviewer
   expects the headline corpus run whole. (Every slice + the 8 whole files +
   the offset extension agree, so the *conclusion* is not in doubt; the
   *completeness of the pre-registered protocol* is.)
2. **Contribution size.** A carefully-scoped negative on a non-novel,
   deliberately-narrow (axis-aligned linear, + one bounded phase extension)
   mechanism, on ~4 corpus categories with one scientific and one telemetry
   dataset each, is a real result but a *small* one for a main track. The
   methodology is arguably the larger contribution and would need to be framed
   as such.

### B — strong workshop / negative-results / preprint. **This is the honest grade.**

- A negative-results or reproducibility track, a compression workshop, or an
  arXiv preprint fits the evidence exactly: pre-registered, fully accounted,
  independently verified, a clean layered negative (structure exists → is
  discoverable → still does not reduce the representation → and this is robust
  to bit phase), with the mechanism validated on planted sources and the
  prior-art position stated plainly.
- To move from B toward A: run the 4 giant Silesia members + whole enwik8 +
  whole SDRBench fields on a ≥ 32 GiB machine (`scripts/reproduce.py --mode
  whole`), and add cmix on the planted control. The infrastructure is done;
  this is compute, not design. If those come back negative (expected), the
  coverage objection is closed and the paper is a defensible full
  negative-results submission — still likely a workshop/short-paper rather than
  a main track, on contribution-size grounds.

### Not C (technically excellent artifact, evidence insufficient for submission)

The evidence is now sufficient for a B-grade submission: the mechanism works
where its target structure exists, the natural-corpus negative is broad
(8 whole + 12 slices + 6 float fields + telemetry + offset extension) and
layered, the controls rule out the obvious artifacts, and independent
verification closes the implementation-doubt objection.

## Recommendation

Submit as a **workshop / negative-results / preprint** paper now, framed as
"we investigate whether automatically discovered exact algebraic relations
provide a compositional advantage for lossless compression; the mechanism
succeeds on planted algebraic sources and the measured natural-corpus evidence
does not show a corresponding composed advantage, robustly across bit phase".
Pursue the ≥ 32 GiB whole-file run + cmix as the single revision that would
support a stronger venue.
