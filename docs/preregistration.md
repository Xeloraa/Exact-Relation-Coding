# Pre-registration — natural-corpus deduction gap

**Locked:** 2026-08-29. This file is frozen before the whole-file / scientific /
telemetry experiments are run. Thresholds here **must not be changed after seeing
results**. If a definition turns out to be wrong, the fix is a new dated
pre-registration file plus an explicit note in the paper that the original
criterion was not met and why the revision is not post-hoc tuning.

Commit that locks this file: recorded in git history as the commit that adds
`docs/preregistration.md`. All experiment JSON written after that commit carries
a `git_commit` field that is a descendant of it.

## 1. Question under test

> Do automatically discovered, exactly reconstructable algebraic relations
> (GF(2) linear column relations at fixed bit widths; integer affine functional
> dependencies on parsed tables) contain compression-relevant redundancy in
> real-world data that **survives full description cost and composition** with
> the strongest lossless compressors we can run?

The claim to be adjudicated is **narrow and scoped**. A negative result is a
statement about the enumerated detector families `D`, corpora `C`, and baselines
`B` in `docs/protocol.md` — never a claim that natural data contains no algebraic
redundancy.

## 2. Fixed definitions (see docs/metric.md for the formal statement)

For a byte string `x`, let `B` be the fixed baseline compressor set, `D(x)` the
fully accounted deductive container (or passthrough if that is not strictly
smaller), and

```
raw_best(x)      = min_{c in B} |c(x)|
composed_best(x) = min_{c in B} |c(D(x))|
G_abs(x)         = raw_best(x) - composed_best(x)          # bytes, signed
G_pct(x)         = G_abs(x) / raw_best(x)                  # fraction, signed
```

`G_abs` / `G_pct` are the **composed gain**. Positive means the deductive
pre-pass left the strongest baseline with less total work to do, after every
bit of relation description, header, framing, padding, CRC and leftover was
counted inside `D(x)`.

## 3. Meaningful positive — per dataset (FIXED)

A dataset `x` counts as a **meaningful deductive composed gain** iff **all** of:

1. `G_pct(x) >= 0.05` (composed gain at least 5% of the strongest baseline), **and**
2. `G_abs(x) >= 1024` bytes (absolute floor; tiny inputs cannot qualify on noise), **and**
3. round-trip holds: `decode(encode(x)) == x` byte-for-byte, **and**
4. real deduction occurred: the container is not passthrough and `n_relations >= 1`
   and `recovered_bits >= 1`, **and**
5. `x` is **not** a known format-trick, derived-column FD table, or checksum
   record set. Those are prior-art sanity checks (Section 6); they are reported
   separately and **never** count toward the hypothesis.

Rationale for 5%: composed gains below ~3–5% are within the range routinely
obtained by a compressor version bump or a parameter change, and would not
justify a new mechanism. 5% is the midpoint of the 3–10% band identified in the
prior-art audit and is locked here before the numbers exist.

## 4. Hypothesis-level outcome (FIXED)

- **POSITIVE** — at least one dataset on the pre-registered corpus list
  (Section 5), excluding the Section 6 prior-art cases, meets every condition in
  Section 3, **and** the result independently reproduces: a from-scratch re-run
  (fresh process; different machine *or* different RNG seed for any stochastic
  step; identical corpus bytes verified by SHA-256) yields `G_abs` within ±10%
  of the first run.

- **NEGATIVE** — no dataset on the pre-registered corpus list (excluding
  Section 6) meets Section 3, across the detector families and baselines in
  `docs/protocol.md`, **and** the validity gates all hold:
  - positive control passes: planted GF(2) shows `G_pct >= 0.30` on the seeded
    linear codes, so the pipeline demonstrably finds and exploits exact linear
    structure when it is present;
  - null controls pass: on i.i.d. bits, shuffled planted codes, and a
    single-flip near-relation, `D(x)` is passthrough and `G_abs <= 0` up to
    header perturbation (|G_abs| <= 64 bytes);
  - FD / CRC sanity cases behave as documented prior art (Section 6);
  - every reported dataset has `roundtrip_ok = true`.

- **INCONCLUSIVE** — a validity gate fails, or resource limits prevent running
  enough of the pre-registered corpus to make a NEGATIVE defensible, or an
  unresolved round-trip failure remains.

## 5. Pre-registered corpus list (FIXED)

Whole-file wherever the running machine permits; where it does not, a documented
largest-feasible prefix, with the limitation recorded in the result JSON and in
`docs/environment_constraints.md`. Prefixes are **not** silently substituted:
each affected row is labelled `prefix` with the byte count and reason.

| id | corpus | category | plausible exact structure? |
| --- | --- | --- | --- |
| `silesia/*` (12 members) | Silesia corpus, whole files | text / source / exec / binary / image | low (baseline expectation: negative) |
| `enwik8` | first 10^8 bytes of English Wikipedia dump | natural-language text | low |
| `sdrbench/*` | ≥1 SDRBench scientific field, IEEE-754 float32 arrays | scientific numeric | **plausible** (inter-field / inter-bit-plane linear relations) |
| `uci_household_power` | UCI Individual Household Electric Power Consumption | telemetry / columnar | **plausible** (documented inter-column relation; approximate → also a real-data corrupted-structure case) |

The scientific and telemetry corpora are chosen **before** seeing any result,
because they are the canonical public datasets for "exact cross-field structure
is plausible here", not because they produced a favourable number. Whatever they
yield is reported.

Any corpus that is downloaded, attempted, and then excluded must be listed in
`docs/protocol.md` with the reason (e.g. licence, size, unreadable format) — no
silent drops.

## 6. Prior-art sanity checks (reported, never counted as hypothesis support)

- integer affine derived column `C = aA + bB + c` (FD elimination — occupied)
- per-record CRC32 (checksum inversion — occupied)
- SQLite / PNG / ZIP whole-file bit matrix (format-awareness trap — occupied)

These exist to show the pipeline finds exact structure when it is genuinely
present. Positive composed gains here are expected and are **not** evidence for
the hypothesis.

## 7. Kill criterion (permanent freeze of the hypothesis)

Freeze Deductive Coding as a general-purpose compression research direction if
**all three** hold:

1. **NEGATIVE** (Section 4) is obtained on the full pre-registered corpus list; **and**
2. one bounded detector-broadening attempt — at least one materially larger
   relation family beyond axis-aligned fixed-width GF(2)/affine (candidates:
   searched record width; GF(2) with a searched/learned column permutation;
   low-degree polynomial relations over GF(2) or the integers) — moves **no**
   pre-registered natural dataset above the Section 3 threshold; **and**
3. the strongest context-mixing baseline actually executed does **not** itself
   absorb the planted-GF(2) composed gain (confirming the mechanism's only
   demonstrated advantage is a real statistical-compressor blind spot, so a
   natural-data negative is a statement about the data, not a weak baseline).

If (1) holds but (2) is not attempted, the outcome is **"negative,
detector-scoped"**: report it, freeze this detector, and leave the broader
question explicitly open as a single named follow-up. Do not claim the general
question is closed.

A NEGATIVE result never proves absence. Every negative conclusion in the paper
is written as scoped to `(D, C, B)`.

## 8. What is NOT pre-registered

Engineering that cannot affect a size comparison: codec vectorisation for speed
(guarded by byte-exact equivalence tests), result-file schema additions,
plotting. These may change after this date. Anything that can move a reported
size — baseline set, presets, accounting rules, thresholds — may not.
