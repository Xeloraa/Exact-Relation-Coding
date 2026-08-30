# Exact-Relation Coding: A Preregistered Test of Whether Discovered Fixed-Width GF(2)/Affine Structure Yields a Composed Lossless-Compression Advantage

**Author(s):** withheld for review — repository: `https://github.com/Xeloraa/deductive-coding`
**Frozen experiment state:** git tag `v1.1-final` (this PDF was generated from
exactly that commit).
**Numerical provenance:** every quantity in this paper is generated from
`results/ledger.json` (122 experiment records) by `scripts/regen_tables.py`;
every inline figure additionally carries a source marker naming the experiment
record and field it is drawn from, verified against the ledger by
`scripts/check_paper_numbers.py`.

**Scope in one sentence.** The negative result concerns *fixed-width,
axis-aligned, GF(2) linear* relations (plus an integer-affine variant used only
for tabular controls, and one bounded bit-phase extension); it is **not** a
test of "algebraic redundancy" in general.

## Abstract

Lossless compressors model a probability for the next symbol and code a
residual. We investigate an alternative pre-pass: automatically *discover* an
exact algebraic relation the data satisfies, transmit a fully counted
description of that relation together with the independent symbols, and let the
decoder reconstruct the determined symbols. We instantiate the pre-pass as a
fixed-width GF(2) column-basis codec (with an integer-affine variant used only
for tabular controls), define a *composed deduction gain*
`G = min_c |c(x)| − min_c |c(D(x))|` over a fixed set of stock compressors `c`
and the accounted container `D(x)`, and preregister a per-file success threshold
before running any natural-corpus experiment. On data engineered to contain an
exact GF(2) linear code the pre-pass removes about half of the size the six
stock baselines achieve (1 MiB code: `G` =
<!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_bytes = 523726 --> bytes,
`G_pct` =
<!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_pct = 0.4994616534154252 -->);
the gain scales with the number of rows while relation description stays
near-constant, and two context-mixing compressors (paq8l, paq8px v216) do not
close it. We then test whether comparable exploitable *exact GF(2)* structure
transfers to public natural corpora.

The preregistered natural corpus is the 12 Silesia members (whole),
enwik8, one SDRBench scientific `float32` field, and one telemetry text file.
On the available 8 GiB machine we ran **8 of the 12 Silesia members whole**
(≤ 10.2 MB); the other four members and whole enwik8 / SDRBench / UCI exceed
memory and were run only at 256 KiB. **Strictly by the preregistration the
hypothesis outcome is therefore inconclusive with respect to the complete
corpus** (the whole-file list is not finished). *Within the achieved coverage*
— 8 whole Silesia members, all 12 members plus enwik8 plus six `float32` fields
plus the telemetry file at 256 KiB, and a bounded bit-phase-offset extension —
the result is a **clean layered negative**: no non-prior-art file produces a
composed gain meeting the threshold; the largest `G_pct` on any natural file is
**+0.09 % (`G_pct` = 0.0009)**, on a passthrough container — a sub-0.1 %
downstream-compressor sensitivity to an 18-byte header, not deduction — and the
offset extension reproduces the phase-0 composed gain to the byte on every file.
Functional-dependency and per-record-CRC32 cases reproduce known techniques and
are labelled as such.

The mechanism is not novel (syndrome source coding; grammar compression; recent
program-synthesis compression). Our contribution is the accounting-complete
codec with an independent shared-nothing verifier, the composed-gain evaluation
discipline with a preregistered threshold, and the empirical finding that blind
fixed-width axis-aligned GF(2) relation discovery does not yield a composed
advantage on the natural corpora and detectors tested. We do **not** claim
natural data contains no exact algebraic redundancy, nor that the general
approach can never help.

**Keywords:** lossless compression, algebraic redundancy, GF(2) linear codes,
functional dependencies, preregistration, negative result, reproducibility.

## 1. Introduction

Redundancy in a byte string is either *statistically predictable* — a good model
assigns the next symbol high probability — or *exactly determined* — some
relation fixes it given other symbols. General-purpose compressors exploit the
first. Whether it is ever worthwhile to explicitly discover and transmit the
second, on arbitrary data, after paying for the description, is an old question
that is periodically revisited.

It carries a known trap. A "win" measured against the payload alone, or against
the transformed container *before* a downstream compressor, routinely evaporates
once the container is itself compressed, because the stock compressor already
captures the same redundancy given a more convenient byte layout. Any honest
test must therefore (i) count every metadata bit inside the container and
(ii) compare *after* a strong downstream compressor. We make that comparison the
primary quantity and fix it, together with a success threshold, in a
git-locked preregistration written before the natural-corpus experiments.

### 1.1 Research questions

We separate five layers and never let one stand in for another; "we found a
relation" (RQ-A) is never reported as a compression result.

* **RQ-A — does exact structure exist?** Does `x` satisfy an exact GF(2)/affine
  relation at a tried bit width and phase?
* **RQ-B — can we discover and represent it?** Is the relation verified on
  *every* row and encoded into a well-formed, fully accounted container?
* **RQ-C — does it reduce total representation cost?** Is the container strictly
  smaller than both a never-worse passthrough and the best stock compressor on
  the raw bytes, *before* any downstream compressor?
* **RQ-D — does the reduction survive a strong downstream compressor?** Is the
  composed gain `G > 0`?
* **RQ-E — does it occur naturally at meaningful scale?** Across the
  preregistered natural corpus, does any non-prior-art file clear the fixed
  threshold?

RQ-A → RQ-B → RQ-C → RQ-D is a strict per-file funnel; RQ-E is the corpus-level
aggregate.

### 1.2 Contributions

1. A GF(2) column-basis lossless codec with an integer-affine variant, a
   bit-exact accounting ledger whose finaliser refuses to emit a container
   whose category bits do not sum to its byte length, and a structural
   never-worse passthrough fallback (§3).
2. The *composed deduction gain* metric and a preregistered per-file threshold,
   as an evaluation discipline for pre-pass compression claims (§2, §4).
3. An independent, shared-nothing decoder and end-to-end composed round-trip
   verification (§5.4).
4. A control battery that makes a negative result *informative*: planted
   positive, i.i.d./shuffled/near-relation nulls, a corruption sweep, a
   representation-change false-positive estimate, a metadata-cost check, a
   composition-order check, and a non-aligned-period scope control (§6).
5. A preregistered empirical finding: on 8 whole Silesia members, 20 further
   files at 256 KiB, and a bounded bit-phase-offset extension, blind
   fixed-width axis-aligned GF(2) relation discovery yields **no** composed
   advantage meeting the threshold, robustly to bit phase (§8) — with the
   whole-file list for the full preregistered corpus not yet complete (§8.4).

The mechanism itself is not claimed as novel; see §7.

## 2. Problem definition and the composed metric

Let `x` be the input byte string and `B` a fixed set of lossless stock
compressors (§5.2). Let `E` be a lossless deductive encoder with
`E⁻¹(E(x)) = x`, and write `D(x) = E(x)` for the *container*. `E` emits the
byte-smaller of a relation container (§3) and *passthrough*
(`magic · version · kind · len64 · crc32 · x`, all whole-byte fields, so
`|passthrough(x)| = |x| + 18`), hence `|D(x)| ≤ |x| + 18` always.

```
  raw_best(x)      =  min over c in B, c ran  of  |c(x)|
  composed_best(x) =  min over c in B, c ran  of  |c(D(x))|
  G(x)             =  raw_best(x) - composed_best(x)          (signed bytes)
  G_pct(x)         =  G(x) / raw_best(x)
```

`G(x) > 0` is the event the hypothesis needs. A companion *raw gain*
`raw_best(x) − |D(x)|` (no downstream compressor) is reported to expose the case
where a raw win vanishes under composition. When a compressor fails on one side
only (e.g. `xz` runs out of memory on a large container but not on the raw
bytes), a *matched-codec gain* over the intersection of compressors that ran on
both sides is also recorded; a positive is reportable only if the matched gain
also clears the threshold.

## 3. Method

### 3.1 GF(2) fixed-width column basis

For a bit width `w ∈ {8, 16, 32, 64, 128, 256}`, the bits of `x` are reshaped to
an `⌊8|x|/w⌋ × w` matrix; the `< w` trailing bits are carried verbatim
(`leftover`). Gaussian elimination over GF(2) on packed 64-bit rows computes the
leftmost column basis: the pivot columns are the unique leftmost independent
set, and every free column is expressed as an XOR of pivot columns. The map is
checked against the *original* matrix before use — a discovery bug raises an
error rather than producing a wrong container. Homogeneous and affine
(`[1 | A]`, the all-ones column synthesised at decode and never transmitted)
variants are both tried, and the smallest fully accounted container over all
`(w, variant)` is kept, else passthrough.

### 3.2 Integer affine functional dependencies

For byte strings that parse as an `int64` table, candidate relations
`z = Σ aᵢ xᵢ + b` are solved on a few rows and verified with exact Python
integers on *every* row; coefficients are zig-zag varints, counted. This variant
is used only for synthetic functional-dependency controls; the natural-corpus
experiments use §3.1 exclusively.

### 3.3 Bit-phase-offset extension

The detectors of §3.1–3.2 are *axis-aligned* and reshape from bit 0. As the one
bounded detector-broadening attempt required by the preregistration's kill
criterion, we add a phase sweep: for each width `w`, also reshape starting at
every bit phase `p ∈ {0, …, w−1}` (a coarse `p`-subset for `w ∈ {128, 256}`),
carrying the skipped `p` bits as a counted `prefix` field. This tests whether a
phase-0 negative is a *framing* artifact — a genuine `w`-periodic linear
relation beginning mid-byte is invisible to phase-0 reshaping and recovered at
the right phase (verified: a planted width-24 code with 8 junk bits prepended is
found at `w = 24, p = 8` and missed at phase 0). It is bounded — `Σ w` extra
reshapes, no search over nonlinear forms — and does not attempt a learned
permutation.

### 3.4 Container and bit accounting

The relation container is (LSB-first, then byte padding):

```
magic[4] version[8] kind[8]
n_rows[32] n_cols[32] n_payload_pivots[32]
flags[8]   (bit0 affine, bit1 ones-is-pivot, bit2 has-prefix)
original_nbytes[64] leftover_nbits[32]  leftover bits
prefix_nbits[32] + prefix bits           (only if flags bit2)
pivot_mask[n_cols]
per free column, in index order: coefficients[n_payload_pivots (+1 if affine)]
pivot payload: n_rows · n_payload_pivots bits  (row-major, pivot-column order)
crc32(x)[32]
padding to a whole byte
```

Every emitted bit is attributed by `AccountedWriter` to exactly one of
`{header, relation, payload, leftover, prefix, crc, framing}`. The finaliser
raises unless

```
8·|D(x)|  =  Σ category bits,   framing = (−Σ others) mod 8 ∈ [0, 7].
```

A container with an unaccounted bit cannot be emitted, and a mis-typed category
name still counts toward the total (it lands in an overflow bucket), so the
invariant cannot be defeated by a typo. `crc32(x)` is written and re-checked on
decode; it is not needed for reconstruction, so it makes the deductive container
*larger* (conservative for the hypothesis) and is identical work on the
passthrough side (neutral for `G`).

### 3.5 Decoding

Decode reads the fields in the same order, rebuilds the matrix by
`pivot_bits · coeffsᵀ` over GF(2) (a `uint8` matmul; the low bit of the wrapping
sum is the parity), reattaches the prefix and leftover, truncates to
`original_nbytes`, and checks the CRC and length. The encoder is deterministic
(asserted byte-identical across re-runs for 18 frozen cases).

## 4. Preregistration

`docs/preregistration.md` is git-locked; the commit that adds it is an ancestor
of every natural-corpus result. It fixes, before any natural-corpus number
existed:

* **Meaningful positive, per file:** `G_pct ≥ 0.05` **and** `G ≥ 1024` bytes
  **and** exact round-trip **and** the container is a real deduction
  (`n_relations ≥ 1`, not passthrough) **and** the file is not a format-trick,
  derived-column, or checksum case. The 5 % floor is the midpoint of the
  3–10 % band a compressor-generation change typically achieves; it is a
  relevance threshold, not a measurement-precision limit.
* **Hypothesis outcome:** *positive* iff ≥ 1 non-prior-art corpus meets the
  per-file threshold and reproduces within ±10 %; *negative* iff none does while
  the positive, null, and prior-art controls all behave as designed;
  *inconclusive* if a control fails or resource limits prevent running enough of
  the corpus list.
* **Kill criterion (three conjuncts):** negative on the full corpus list;
  **and** one bounded detector-broadening attempt moves no natural file above
  threshold; **and** the strongest executed context mixer does not itself close
  the planted-GF(2) gap. Its status is tracked in `docs/kill_criterion_status.md`.

Post-lock changes are limited to engineering that cannot move a reported size
(codec vectorisation guarded by byte-exact equivalence tests, result-file schema
additions, plotting). Baselines, presets, accounting rules, and thresholds are
frozen.

## 5. Experimental protocol

### 5.1 Datasets and corpus coverage

The preregistered natural corpus is: the 12 Silesia members (whole files);
enwik8 (first 10⁸ bytes); ≥ 1 SDRBench scientific `float32` field; and the UCI
Individual Household Electric Power Consumption text. The scientific and
telemetry corpora were named in the lock, before any loader output was
inspected, because they are the canonical public datasets for "exact
cross-field structure is plausible here" — not because they produced a
favourable number.

| id | obtained | SHA-256 pinned | run as |
| --- | --- | --- | --- |
| `silesia_{dickens,xml,ooffice,reymont,sao,x-ray,mr,osdb}` | `silesia.zip` (Mahoney mirror) | yes | **whole** (5.3–10.2 MB) |
| `silesia_{samba,nci,webster,mozilla}` | same | yes | 256 KiB prefix only |
| `enwik8` | `enwik8.zip` | yes | 256 KiB prefix only |
| `sdrbench_exaalt2869440_{vx,vy,vz,xx,yy,zz}.f32` | SDRBench EXAALT bundle (Globus HTTPS), tar-verified | yes | 256 KiB prefix (fields are 11.5 MB whole) |
| `uci_household_power_text` | UCI ML Repository #235 | yes | 256 KiB prefix only |

Every corpus is pinned by SHA-256 in `results/corpus_manifest.json`; a changed
hash aborts the run. No corpus has been dropped for being unfavourable; the four
Silesia members not run whole are the *largest*, not the most inconvenient
(§8). Prefixes are labelled as such and live in a separate result phase; they
are never presented as whole-file results.

**Train/test separation.** The discovery step reads only the file it encodes;
there is no learned model, no shared parameters across files, and no held-out
tuning set. The only quantities fixed across all files are the six bit widths,
the six stock compressors, and the preregistered threshold. Synthetic data is
generated from documented integer seeds.

### 5.2 Baselines

`B = {gzip −9 (mtime 0), zlib −9, bz2 −9, xz −9 (FORMAT_XZ), zstd −19,
brotli −11}`, all deterministic; versions recorded per record (`zstandard`
0.25.0, `brotli` 1.2.0, stdlib otherwise; Python 3.13.6). A compressor that
raises `MemoryError` or times out is recorded unavailable with the exception and
excluded from the `min`; the available set is reported per record.

Two context-mixing compressors — paq8l (`-3`, `-8`) and paq8px v216 (`-4`,
`-8`) — are applied **only** to the planted-GF(2) positive control, to test
whether the mechanism's advantage there is a genuine blind spot of the strongest
statistical compressors we could run. cmix (needs 20–32 GiB, no memory level)
and nncp (needs a GPU) could not be run on the available hardware; the paper
writes "the strongest context-mixing compressors we could run", never "state of
the art".

### 5.3 Independent verification

`verification/independent_verify.py` shares no code with the encoder or the
main decoder: its own bit reader, its own container parse, a plain-Python XOR /
integer reconstruction, and an independent re-derivation of the accounting from
parsed field sizes. It checks the full chain
`raw → encode → container → compress → decompress → independent-decode → raw`,
asserting SHA-256 equality and the `8·|D| = Σ categories` invariant on the
independently parsed field sizes. It reconstructs all four container kinds in a
self-test; the CI suite exercises it over 21 parametrised cases (offsets 0–31,
all container kinds, the composed compress/decompress chain, and a
phase-shifted planted code it must recover); and it was run once on the whole
10 MB `silesia_dickens` container. Separately, the *primary* decoder's composed
round-trip `E⁻¹(c⁻¹(c(D(x)))) = x` is checked for every stock compressor on
every one of the 122 ledger records — 0 failures.

### 5.4 Reproducibility harness

`scripts/reproduce.py` runs, in order: `pytest` (636 tests on the frozen state:
byte-equivalence, randomised property tests, independent verifier), the verifier
self-test, the controls, the natural-corpus slice sweep, the offset-extension
sweep, the legacy phase experiments, then `build_ledger.py` → `regen_tables.py`
→ `make_figures.py` → `check_paper_numbers.py` → `independent_verify.py
--ledger`. Every step returns 0 on the reported state. Every experiment JSON
records dataset SHA-256, seeds, config, the seven accounting categories,
container size, round-trip and composed round-trip status, every baseline
`(name, bytes, seconds, available)`, every composition size, `G`, `G_pct`, the
raw gain, a UTC timestamp, the git commit (with a `-dirty` marker if the tree
was not clean), and machine info.

## 6. Controls

All gate assertions pass (`experiments/controls/run.py`; full numbers in
`paper/results_tables.md`).

| control | construction | result |
| --- | --- | --- |
| positive: planted GF(2), 3 seeds | random info + exact parity columns | `G_pct` <!-- src: control_positive_gf2_n1280_k32_p32_s902 / composition_gap_pct = 0.48311206559937525 -->, +49.5 %, +49.7 %; round-trip exact |
| null: i.i.d. bits / shuffled planted / 1-flip near-relation | — | passthrough; `\|G\| ≤ 19` bytes |
| corruption sweep, flip fraction `φ ∈ {0, 10⁻⁴, 10⁻³, 10⁻², 5·10⁻²}` | planted code, `φ·n_rows·n_parity` parity cells flipped | `G` decreases monotonically 16 213 → 13 238 → 1 402 → −18 → −18; never below −64 |
| representation-change null | 40 i.i.d. inputs through the full width × variant `min` | 0 containers beat passthrough; 0 composed gains > 64 bytes |
| metadata-cost | null input; planted input | null overhead = exactly 18 bytes; planted container bits = Σ categories to the bit |
| composition-order | planted container through `decompress(compress(·))` for five codecs | primary decoder inverts every time |
| non-aligned period, `w = 48` | exact 48-bit-period linear code | default widths → passthrough (`G` <!-- src: control_nonaligned_period_w48 / composition_gap_bytes = -18 -->); adding width 48 → 24 relations, round-trip exact |
| prior art: affine FD / per-record CRC32 | derived column / CRC records | `G` = +37 880 / +16 209 bytes, **labelled** FD elimination / checksum inversion; not counted toward RQ-E |

The corruption sweep and the non-aligned-period control together bound the
scope of a negative: the method degrades gracefully as exact structure is
broken, and it is blind to exact structure whose period is not among the tried
widths (visible once the width is added).

## 7. Related work and novelty

The general idea — discover exact structure, transmit a reconstruction recipe,
and beat a general-purpose compressor after counting the recipe — is not new,
and we claim no novelty for it. Bracketed keys refer to §14.

* **Syndrome source coding** [Ancheta 1976]. Treat the source as an error
  pattern and transmit its syndrome `Hx` under a linear code; a coset-leader
  source decompresses exactly, and with no side information the coder is an
  entropy coder. Compressing a single source by exploiting linear-code
  membership is classical. What is not standard is *discovering* the code from
  one input with its description cost charged on the same channel — a thin
  distinction, and the axis on which our codec differs from classical syndrome
  coding.
* **Grammar-based compression** [Nevill-Manning & Witten 1997; Larsson & Moffat
  2000; Kieffer & Yang 2000]. The string is the unique yield of a grammar whose
  description cost is counted; structure is concatenative rather than
  linear-algebraic.
* **Functional-dependency / derived-column elimination** [US 8,150,888;
  US 8,700,579; Liu et al. 2017 (TICC); Liu et al. 2024 (Corra);
  US 11,562,085]. Detect that a column is an exact function of others, drop it,
  and store the function; extensions store exceptions for inexact dependencies.
  This space is thoroughly occupied for relational tables. Our affine-FD and
  per-record-CRC32 results are labelled as reproductions of it and are excluded
  from RQ-E.
* **Format-aware recompression** [Schnaader, *Precomp*; preflate; packJPG].
  Invert a known embedded codec and drop reconstructible checksums; our
  PNG/ZIP/SQLite behaviour is the predicted format-awareness trap, not a
  counterexample.
* **Program-synthesis compression** [Shi et al. 2026 (Brevis)]. Synthesise a
  self-contained DSL program that reconstructs a tensor bit-exactly; reports a
  real composed win on neural-network checkpoints — a favourable domain dense
  with repeats, low rank and quantisation grids, searched with a rich language
  guided by a learned prior. A strong recent instance of the general idea; it
  does not address blind fixed-width GF(2) discovery on arbitrary bytes.
* **Low GF(2)-rank / binary matrix factorisation** [Fomin et al. 2018]. A change
  of basis to expose binary rank deficiency; NP-hard in general, and the *exact*
  case is the special case our column basis computes at a fixed width.
* **Invariant mining** [Ernst et al. 2007 (Daikon)]. Templated dynamic discovery
  of equalities and affine relations among program variables; not a compressor,
  and it reports *likely* invariants (false positives expected), whereas we
  accept a relation only after verifying it on every row.

**Our contribution, stated narrowly.** (i) An accounting-complete, never-worse
fixed-width GF(2) (plus tabular-affine) relation codec whose emitted bits are
exhaustively categorised, with an independent shared-nothing verifier and
end-to-end composed round-trip checks; (ii) the composed deduction-gain metric
with a git-locked preregistered per-file threshold, offered as an evaluation
discipline for pre-pass compression claims; (iii) a preregistered empirical
measurement — with a bounded bit-phase-offset extension — of whether blind
fixed-width axis-aligned GF(2) relation discovery produces a composed advantage
on public natural corpora, finding that it does not, within the coverage tested.
We do not claim any of (i)–(iii) is "first" in a stronger sense than this.

## 8. Results

### 8.1 Mechanism validation (planted GF(2))

On random GF(2) linear codes — `k` information columns and `k` exact parity
columns — the pre-pass behaves exactly as designed. The relation description is
a constant of the code (1,088 bits for `k = 32`;
<!-- src: phase1_gf2_n65536_k64_p64_s14 / relation_description_bits = 4224 --> bits for
`k = 64`), independent of the number of rows, so the composed gain grows with
the row count: `G_pct` rises from
<!-- src: phase0_gf2_tiny / composition_gap_pct = 0.3230769230769231 --> at 256 bytes
to
<!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_pct = 0.4994616534154252 -->
at 1 MiB (Fig. 1; Table B.2). Every case round-trips, and the independent
verifier agrees.

Context mixers do not close this gap. On a 10 KiB code (seed 902), the best
stock compressor leaves `+4 949` bytes recoverable by deduction; paq8l `-8`
compresses the raw bytes to 10 321 and the container to 5 347 (a mixer-relative
gap of `+4 974`), and paq8px v216 `-8` to 10 261 and 5 288 (`+4 973`). Raising
the mixer memory level changes the gap by `< 6` bytes. The planted-GF(2)
composed gain is therefore not an artifact of weak baselines; it is a blind spot
of these statistical compressors on this bitstream. This is a statement about
those compressors on that input, not a theorem about statistical models in
general.

### 8.2 Natural corpora (RQ-C, RQ-D, RQ-E)

**Whole files (8 of 12 Silesia members).** No file meets the threshold
(Table B.3). Three members admit GF(2) relations at a tried width but the
container is *larger* than the best stock compressor's output, so RQ-C already
fails; composition then makes it worse:

| member | bytes | kind | rels | `raw_best` | `G` (bytes) | `G_pct` |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `dickens` | <!-- src: nat_silesia_dickens / dataset_bytes = 10192446 --> | GF2 | <!-- src: nat_silesia_dickens / n_relations = 25 --> | <!-- src: nat_silesia_dickens / raw_best_bytes = 2799520 --> | <!-- src: nat_silesia_dickens / composition_gap_bytes = -2645016 --> | −94.48 % |
| `x-ray` | <!-- src: nat_silesia_x-ray / dataset_bytes = 8474240 --> | GF2 | <!-- src: nat_silesia_x-ray / n_relations = 58 --> | <!-- src: nat_silesia_x-ray / raw_best_bytes = 4051112 --> | <!-- src: nat_silesia_x-ray / composition_gap_bytes = -1907747 --> | −47.09 % |
| `xml` | <!-- src: nat_silesia_xml / dataset_bytes = 5345280 --> | GF2 | <!-- src: nat_silesia_xml / n_relations = 21 --> | <!-- src: nat_silesia_xml / raw_best_bytes = 430390 --> | <!-- src: nat_silesia_xml / composition_gap_bytes = -1299038 --> | −301.83 % |

The relations found on text/XML are the "high bit of a mostly-ASCII byte is
zero" bit-plane and similar; brotli and bzip2 already exploit this from the raw
byte order. The other five members admit no exact relation at any tried width
and fall to passthrough, with `|G| ≤ 6 408` bytes (`|G_pct| ≤ 0.15 %`), i.e.
downstream-compressor sensitivity to an 18-byte header, not deduction.

**256 KiB files (20).** Same pattern: 0 meaningful positives (Table B.4). Where
GF(2) finds relations (`float32` fields, XML, text, telemetry) the composed gain
is large-negative (−4.8 % to −302 %); where it does not, `|G_pct| < 0.3 %`. The
single largest positive `G_pct` on any natural-corpus record — whole files, 256
KiB files, and the offset extension together — is
**<!-- src: nat_silesia_sao_slice / composition_gap_pct = 0.0008833922261484099 -->**
(`G_pct` = 0.0009), on the 256 KiB prefix of `silesia_sao`, whose container is *passthrough*
(`n_relations = 0`). This is downstream-compressor sensitivity to the 18-byte
passthrough header, not deduction; it is two orders of magnitude below the 5 %
floor and is excluded from the hypothesis in any case because it is not a real
deduction. (The `+49.95 %` maximum over all 122 records is the planted
positive control, §8.1.)

**Bit-phase-offset extension (20 files).** For every file the offset-search
composed gain equals the phase-0 value **to the byte** (Table B.5); no bit phase
improves on phase 0 by more than header perturbation, and 0 files cross the
threshold. The axis-aligned negative is robust to bit phase; it is not an
artifact of reshaping from bit 0. This is the one bounded detector-broadening
attempt the kill criterion requires, and it does not rescue the hypothesis.

### 8.3 Prior-art sanity cases

An integer affine derived column (`C = 3A + 5B + 7`, 8 192 rows) yields
`G` = +37 880 bytes and a per-record IEEE CRC32 set yields `G` = +16 209 bytes
(affine) / +15 701 bytes (homogeneous). These are labelled reproductions of
functional-dependency elimination and checksum inversion respectively and are
**not** counted toward RQ-E.

### 8.4 Verdict under the preregistered protocol

**Coverage against the full preregistered corpus.**

| preregistered item | preregistered "run as" | actually run |
| --- | --- | --- |
| Silesia — 12 members | whole files | 8 whole (`dickens, xml, ooffice, reymont, sao, x-ray, mr, osdb`, ≤ 10.2 MB); 4 (`samba, nci, webster, mozilla`, 21–51 MB) at 256 KiB only |
| enwik8 | first 10⁸ bytes | 256 KiB prefix only |
| ≥ 1 SDRBench `float32` field | whole field | six EXAALT fields at 256 KiB only |
| UCI household-power text | whole file | 256 KiB prefix only |
| bit-phase-offset extension | — | all 20 files at 256 KiB |

* The positive, null, prior-art, and scope controls all behave as designed.
* No non-prior-art natural file meets the per-file threshold, on the 8 whole
  Silesia members, the 20 files at 256 KiB, or the phase-offset extension.
* The whole-file runs for four Silesia members and for whole enwik8 / SDRBench /
  UCI exceed the 8 GiB development machine and were **not executed** (§9, §11).

**Verdict: inconclusive with respect to the complete preregistered corpus; a
clean negative within the achieved coverage.** Strictly, the preregistration's
"negative" outcome requires the full whole-file list, which was not completed,
so the formal hypothesis outcome is *inconclusive*. Within what was run, the
result is an unambiguous **layered negative**: on natural data, exact GF(2)
structure is often present (RQ-A) and discoverable (RQ-B), and on **no** tested
file — at 256 KiB or whole, at any bit phase — does it reduce the representation
(RQ-C) or survive composition (RQ-D). Every 256 KiB result and every whole-file
result that could be run agree, so the four missing whole-file runs are the only
gap between "inconclusive" and "negative".

## 9. Discussion

### 9.1 What is established

* The codec recovers and exploits exact GF(2) linear structure when it is
  deliberately present: complete round-trip, complete accounting, a composed
  gain up to `+49.95 %` that scales with rows, independently verified end to
  end, and not closed by paq8l or paq8px v216.
* The controls establish that this behaviour is not a false positive of the
  width × variant search (0 spurious gains on 40 i.i.d. inputs), that metadata
  is fully counted (null overhead is exactly the 18-byte passthrough header),
  and that the pipeline degrades gracefully as structure is corrupted.
* On the natural corpora *actually measured* — 8 whole Silesia members plus 20
  files at 256 KiB plus the phase-offset extension — the largest positive
  composed gain on any file is +0.09 % (on a passthrough container, i.e. header
  perturbation), and `G_pct` is strongly negative on every file where a real
  GF(2) relation is found. The redundancy the detector locates in natural data
  is real but trivial (a constant high bit-plane, ASCII structure) and is
  already captured by the stock compressors from the raw byte order.

### 9.2 What is not established

* **Not** that natural data contains no exact algebraic redundancy. We tested
  two specific relation families (axis-aligned fixed-width GF(2), integer affine
  on parsed tables), extended once to arbitrary bit phase, on one public
  benchmark corpus plus one scientific dataset (six correlated fields) plus one
  telemetry file. A materially different family — non-axis-aligned linear via a
  searched or learned column permutation, or low-degree polynomial relations —
  is untested.
* **Not** that the approach can never improve compression. Program-synthesis
  compression demonstrates a real composed win on a favourable domain (model
  checkpoints). Our negative concerns blind, prior-free, axis-aligned linear
  discovery on general byte corpora.
* **Not** that the method is universally inferior to existing compressors: on
  its target structure it wins decisively, and the never-worse guard makes it,
  by construction, at most 18 bytes worse than passthrough on any input.

### 9.3 Why the negative is informative

The mechanism is validated: when exact linear structure exists it is found and
turned into a real, composition-surviving size reduction. The informative
content is that the *analogous* structure a blind axis-aligned detector locates
in natural byte corpora is (i) already modelled by stock compressors and
(ii) too cheap-to-describe-relative-to-what-it-recovers to survive its own
metadata, let alone composition. Establishing a positive on natural data would
require either a corpus with genuine exact cross-field structure that stock
compressors miss (the FD/CRC cases show what that looks like, and they are prior
art), or a detector family expressive enough to find non-trivial structure at
acceptable description cost — the direction future work would have to take, and
the one the preregistered kill criterion names.

## 10. Threats to validity

| threat | mitigation |
| --- | --- |
| encoder and decoder share a bug | independent shared-nothing decoder + independent accounting re-derivation, in CI and on the 10 MB `dickens` container |
| vectorised primitives are wrong | 400 randomised bit-I/O trials vs a per-bit reference; 60 `reconstruct` trials vs a per-column XOR reference; 18 byte-frozen container cases |
| a container has unaccounted bits | finaliser refuses to emit it; independently re-derived by the second decoder |
| the downstream comparison is unfair (a codec fails on one side) | matched-codec gain over the intersection; both available-codec sets recorded; a reportable positive needs matched sets |
| the compressed container does not decode back | the *primary* decoder's `raw → encode → compress → decompress → decode → raw` is checked for every stock codec on all 122 records (0 failures); the *independent* shared-nothing decoder runs the same chain on the 21 CI cases and on the whole 10 MB `dickens` container |
| the width × variant `min` inflates results | representation-change null: 0 spurious gains on 40 i.i.d. inputs; never-worse guard caps the downside at passthrough |
| the negative is a framing / bit-phase artifact | bounded phase-offset extension on all 20 files: `G` equals the phase-0 value to the byte |
| a prefix is passed off as a whole file | separate result phase, separate manifest keys, `prefix` reason on every row |
| the corpus was chosen after seeing results | corpus list git-locked before any loader output; every file SHA-256-pinned; a changed hash aborts |
| numbers were transcribed by hand | all tables generated from `results/ledger.json`; inline figures carry markers checked by `check_paper_numbers.py` |

## 11. Limitations

* **Detector scope.** Fixed-width, axis-aligned GF(2) linear relations (widths
  8–256), plus an integer-affine variant used only for tabular controls, plus
  one bounded bit-phase-offset extension. The negative is scoped to these
  families only; it is not a test of algebraic redundancy in general. The
  non-aligned-period control shows exact structure at a period not among the
  tried widths is missed by construction. Non-axis-aligned linear relations
  (via a searched or learned column permutation) and low-degree polynomial
  relations are untested.
* **Whole-file coverage — the principal limitation.** 8 of the 12 preregistered
  whole Silesia members were run whole (≤ 10.2 MB). The four largest members
  (`samba, nci, webster, mozilla`, 21–51 MB) and whole enwik8 / SDRBench / UCI
  exceed the 8 GiB development machine and were run only at 256 KiB. Every
  256 KiB result, every whole-file result that could be run, and the offset
  extension agree, so the *direction* of the finding is consistent — but by the
  preregistration the whole-file list is **not complete**, so the formal
  hypothesis outcome is *inconclusive with respect to the full corpus* (§8.4).
  Completing those runs on a ≈ 32 GiB machine is the one outstanding task.
* **Baseline ceiling.** cmix and nncp were not run (hardware). The
  planted-GF(2) result with paq8l/paq8px bounds — but does not eliminate — the
  possibility that a stronger mixer would absorb the planted gap; it says
  nothing about the natural-corpus negative, which does not depend on baseline
  strength.
* **Corpus breadth.** Four corpus classes; the scientific class is one
  molecular-dynamics dataset whose six fields are one simulation (effective
  n ≈ 1–2). A broader scientific and telemetry sweep is future work.
* **Statistics.** The measurements are deterministic; there is no random
  sampling from a defined population, so no inferential confidence interval or
  p-value is claimed. The file is the unit of analysis and the headline is a
  per-file maximum `G_pct` against the fixed threshold.

## 12. Conclusion

We asked whether automatically discovered exact GF(2)/affine relations can
provide an additional source of lossless compression that survives full
description cost and composition with a strong downstream compressor. We built a
fixed-width GF(2) relation codec with exhaustive bit accounting, an independent
shared-nothing verifier, and a composed-gain metric, and we preregistered the
evaluation. The mechanism is validated on deliberately structured data: it
recovers planted GF(2) codes and converts them into a composed size reduction of
up to +49.95 % that scales with data size and is not closed by two
context-mixing compressors.

For the natural-corpus test, the available 8 GiB machine could run only 8 of the
12 preregistered whole Silesia members; the other four members and whole enwik8
/ SDRBench / UCI were run only at 256 KiB. **Strictly by the preregistration the
hypothesis outcome is therefore inconclusive with respect to the complete
corpus; within the achieved coverage the result is a clean layered negative.**
No non-prior-art file — 8 whole Silesia members, 20 files at 256 KiB, and the
bit-phase-offset extension — yields a composed gain meeting the threshold; the
largest positive `G_pct` on any natural file is +0.09 %, on a passthrough
container. The functional-dependency and CRC cases reproduce known techniques.

The mechanism is not novel; the contribution is the accounting discipline, the
composed evaluation, the controlled validation, and the scoped empirical
finding. This is a precise negative, not a refutation of the idea: it
establishes that a blind, fixed-width, axis-aligned GF(2) detector does not
expose a composed advantage on the natural corpora tested, it identifies the
four whole-file runs that separate "inconclusive" from "negative" for the full
preregistered corpus, and it states what a future positive would need — either a
corpus with exact cross-field structure that stock compressors miss, or a
detector family expressive enough to find non-trivial structure at acceptable
description cost.

## 13. Reproducibility

**Frozen state.** Everything in this paper corresponds to git tag `v1.1-final`.
**Environment used:** Windows 11 (build 10.0.22631), 4 logical cores, 8 GiB RAM;
Python 3.13.6; numpy 2.2.6, zstandard 0.25.0, brotli 1.2.0 (the rest of `B` is
the Python standard library). Corpora are not committed (licence and size);
acquisition is scripted and SHA-256-pinned in `results/corpus_manifest.json`,
and a changed hash aborts the run.

*Headline reproduction — any 8 GiB machine, ~10 min:*

```bash
python -m pip install -e ".[dev]"
python -m pytest -q                                   # 636 tests -> all pass
                                                     #   (incl. 21 independent-verifier cases +
                                                     #    randomised property tests + byte-equivalence)
python verification/independent_verify.py --self-test # -> SELF-TEST: PASS  (all 4 container kinds)
python experiments/controls/run.py                    # -> CONTROLS: PASS (exit 0)
python scripts/build_ledger.py                        # -> 122 records, 0 failures
python scripts/regen_tables.py && python scripts/make_figures.py
python scripts/check_paper_numbers.py                 # -> PAPER-NUMBER CHECK: PASS (20 markers)
python scripts/build_pdf.py                           # -> paper/exact-relation-coding.pdf
```

Expected: controls pass; planted GF(2) shows the +32–50 % composed gains of
Table B.2; the checker verifies every inline marker against the ledger.

*Natural-corpus reproduction (the headline test) — 8 GiB machine:*

```bash
python experiments/natural/run.py --mode whole --only silesia_xml   # 8 GiB ok up to ~10 MB
python experiments/offset/run.py  --mode slice                      # offset extension, ~15 min
```

These reproduce exactly the 8 whole Silesia members (Table B.3) and the 20-file
offset extension (Table B.5): **0 files meet the threshold; largest natural
`G_pct` = +0.09 %.**

*Complete preregistered corpus — needs > 8 GiB (≈ 32 GiB) RAM:*

```bash
python scripts/reproduce.py --mode whole --offset-whole
```

This additionally runs `samba, nci, webster, mozilla` whole, whole enwik8,
whole SDRBench fields, and whole UCI — the whole-file runs the present paper
could not execute, and that separate its "inconclusive" from a full "negative".

A re-run on the frozen state reproduces every size, gain, and verdict exactly;
only timings and timestamps differ.
`docs/preregistration.md` (locked), `docs/audit.md` (implementation audit and
corrections C1–C2), `docs/prior_art.md`, `docs/statistics.md`,
`docs/kill_criterion_status.md`, and `docs/venue_assessment.md` accompany the
manuscript.

## 14. References

1. T. Ancheta. "Syndrome-source-coding and its universal generalization."
   *IEEE Transactions on Information Theory*, 22(4):432–436, July 1976.
2. C. G. Nevill-Manning and I. H. Witten. "Identifying hierarchical structure in
   sequences: A linear-time algorithm." *Journal of Artificial Intelligence
   Research*, 7:67–82, 1997. (SEQUITUR)
3. N. J. Larsson and A. Moffat. "Off-line dictionary-based compression."
   *Proceedings of the IEEE*, 88(11):1722–1732, 2000. (Re-Pair)
4. J. C. Kieffer and E.-H. Yang. "Grammar-based codes: A new class of universal
   lossless source codes." *IEEE Transactions on Information Theory*,
   46(3):737–754, 2000.
5. J.-P. Dittrich. "Automatic elimination of functional dependencies between
   columns." US Patent 8,150,888 B2, 2012.
6. "Method and system for data compression in a relational database."
   US Patent 8,700,579 B2, 2014.
7. H. Liu, Y. Ji, J. Xiao, H. Tan, Q. Luo, and L. M. Ni. "TICC: Transparent
   Inter-Column Compression for Column-Oriented Database Systems."
   *Proc. ACM CIKM*, 2017. DOI 10.1145/3132847.3133077.
8. H. Liu, M. Stoian, A. van Renen, and A. Kipf. "Corra: Correlation-Aware
   Column Compression." *VLDB 2024 Workshop on Cloud Databases (CloudDB)*, 2024.
   arXiv:2403.17229.
9. "Anisotropic compression as applied to columnar storage formats."
   US Patent 11,562,085 B2, 2023.
10. C. Schnaader. *Precomp* — precompressor for deflate/bzip2/PNG/PDF/GIF/JPEG
    streams. Software, `https://github.com/schnaader/precomp-cpp`. See also
    *preflate* (`https://github.com/deus-libri/preflate`) and *packJPG*.
11. J. Shi et al. "Lossless Tensor Compression as Program Synthesis." arXiv
    preprint arXiv:2608.02162, 2026. (Brevis)
12. F. V. Fomin, P. A. Golovach, F. Panolan, and S. Saurabh. "Parameterized
    Low-Rank Binary Matrix Approximation." arXiv:1803.06102, 2018.
13. M. D. Ernst, J. H. Perkins, P. J. Guo, S. McCamant, C. Pacheco, M. S.
    Tschantz, and C. Xiao. "The Daikon system for dynamic detection of likely
    invariants." *Science of Computer Programming*, 69(1–3):35–45, 2007.

---

## Appendix A — Figures

FIGURE::fig_planted_scaling

*Figure 1. Planted GF(2) codes: composed gain `G` (bytes) versus input size,
log–log. The gain scales approximately with the number of rows because the
relation description is a constant of the code. The two low points are a
single-flip near-relation control and an affine-parity control.*

FIGURE::fig_natural_gpct

*Figure 2. Natural corpus: per-file composed gain `G_pct` for the whole files
(blue), the 256 KiB slices (light blue), and the bit-phase-offset extension
(red), with the zero line and the preregistered `+5 %` threshold (dashed).
Every point is far below the threshold. Three points sit fractionally to the
right of zero — `sao` (`G_pct` = +0.0009), `reymont`, `mr` — all with
passthrough containers (`n_relations = 0`); these are sub-0.1 %
downstream-compressor reactions to the 18-byte passthrough header, not
deduction. Points where a real relation was found are all strongly negative.*

## Appendix B — Key results tables

The complete auto-generated tables — **B.1** controls, **B.2** planted scaling +
context-mixer baseline, **B.3** whole natural, **B.4** 256 KiB natural,
**B.5** bit-phase offset, **B.6** prior-art sanity — are in
`paper/results_tables.md`, produced from `results/ledger.json` (122 records;
0 accounting, round-trip, or composed round-trip failures). Every row traces to
a JSON record under `results/` carrying its dataset hash, git commit,
configuration, compressor versions, and verification status. The control numbers
(B.1) appear in §6 and the prior-art numbers (B.6) in §8.3; the remaining four
tables are reproduced below.

**B.2 (extract) — planted GF(2): the mechanism scales**

| input bytes | relations | container | `raw_best` | `G` (bytes) | `G_pct` | relation bits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 256 | 8 | 172 | 260 | +84 | +32.31 % | 80 |
| 4,096 | 16 | 2,118 | 4,100 | +1,978 | +48.24 % | 288 |
| 32,768 | 32 | 16,554 | 32,772 | +16,214 | +49.48 % | 1,088 |
| 102,400 | 32 | 51,371 | 102,405 | +51,030 | +49.83 % | 1,088 |
| 256,000 | 32 | 128,171 | 256,005 | +127,829 | +49.93 % | 1,088 |
| 1,048,576 | 64 | 524,850 | 1,048,581 | +523,726 | +49.95 % | 4,224 |

**B.3 — whole natural files (8 of 12 Silesia members)**

| member | bytes | kind | rels | `raw_best` | container | `G` (bytes) | `G_pct` | round-trip |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | :---: |
| `xml` | 5,345,280 | GF2 | 21 | 430,390 | 4,907,484 | −1,299,038 | −301.83 % | ✓ |
| `ooffice` | 6,152,192 | passthrough | 0 | 2,426,816 | 6,152,210 | −188 | ≈ 0 | ✓ |
| `reymont` | 6,627,202 | passthrough | 0 | 1,246,230 | 6,627,220 | +217 | ≈ 0 | ✓ |
| `sao` | 7,251,944 | passthrough | 0 | 4,415,072 | 7,251,962 | −6,408 | −0.15 % | ✓ |
| `x-ray` | 8,474,240 | GF2 | 58 | 4,051,112 | 6,555,798 | −1,907,747 | −47.09 % | ✓ |
| `mr` | 9,970,564 | passthrough | 0 | 2,441,280 | 9,970,582 | +857 | ≈ 0 | ✓ |
| `osdb` | 10,085,684 | passthrough | 0 | 2,802,792 | 10,085,702 | −25 | ≈ 0 | ✓ |
| `dickens` | 10,192,446 | GF2 | 25 | 2,799,520 | 9,197,882 | −2,645,016 | −94.48 % | ✓ |

**B.4 — 256 KiB natural files (all 20; phase-0 detector).** Every input is
262,144 bytes. "pass" = passthrough container (`n_relations = 0`).

| file | kind | rels | `raw_best` | `G` (bytes) | `G_pct` |
| --- | --- | ---: | ---: | ---: | ---: |
| `exaalt/vx.f32` | GF2 | 3 | 226,805 | −10,819 | −4.8 % |
| `exaalt/vy.f32` | GF2 | 3 | 226,808 | −10,816 | −4.8 % |
| `exaalt/vz.f32` | GF2 | 3 | 226,655 | −10,969 | −4.8 % |
| `exaalt/xx.f32` | GF2 | 3 | 224,585 | −11,576 | −5.2 % |
| `exaalt/yy.f32` | GF2 | 29 | 187,128 | −44,290 | −23.7 % |
| `exaalt/zz.f32` | GF2 | 3 | 215,238 | −22,336 | −10.4 % |
| `silesia_dickens` | GF2 | 31 | 77,252 | −47,827 | −61.9 % |
| `silesia_nci` | GF2 | 1 | 14,563 | −11,065 | −76.0 % |
| `silesia_reymont` | GF2 | 1 | 53,158 | −24,988 | −47.0 % |
| `silesia_webster` | GF2 | 1 | 62,139 | −37,157 | −59.8 % |
| `silesia_x-ray` | GF2 | 58 | 129,632 | −57,729 | −44.5 % |
| `silesia_xml` | GF2 | 1 | 11,559 | −17,365 | −150.2 % |
| `uci_household_power_text` | GF2 | 60 | 28,160 | −29,828 | −105.9 % |
| `enwik8` | pass | 0 | 73,306 | −39 | ≈ 0 |
| `silesia_mozilla` | pass | 0 | 111,811 | −54 | ≈ 0 |
| `silesia_mr` | pass | 0 | 55,898 | −119 | ≈ 0 |
| `silesia_ooffice` | pass | 0 | 123,528 | −16 | ≈ 0 |
| `silesia_osdb` | pass | 0 | 82,475 | −19 | ≈ 0 |
| `silesia_samba` | pass | 0 | 153,153 | −45 | ≈ 0 |
| `silesia_sao` | pass | 0 | 167,536 | +148 | +0.09 % |

Every GF(2) container is strongly composition-negative; every passthrough
container is within header noise. Round-trip and composed round-trip hold for
all 20 (Table in `results_tables.md`).

**B.5 (summary) — bit-phase-offset extension (20 files, 256 KiB).** For every
file the offset-search `G` equals the corresponding phase-0 `G` in the table
above **to the byte**; 0 files cross the `+5 %` threshold; 0 files improve on
phase 0 by more than header perturbation. The fixed-width axis-aligned negative
is robust to bit phase.
