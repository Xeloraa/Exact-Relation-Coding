# Exact-Relation Coding: A Preregistered Test of Whether Discovered Algebraic Structure Yields a Composed Lossless-Compression Advantage

**Author(s):** withheld for review — repository: `https://github.com/Xeloraa/deductive-coding`
**Version:** experiment state tagged `v0.3-submission`.
**Artifact:** all numbers in this paper are generated from `results/ledger.json`
(122 experiment records) by `scripts/regen_tables.py`; every inline figure
carries a source marker naming the experiment record and field it comes from,
verified against the ledger by `scripts/check_paper_numbers.py`.

## Abstract

Lossless compressors model a probability for the next symbol and code a
residual. We investigate an alternative pre-pass: automatically *discover* an
exact algebraic relation the data satisfies, transmit a fully counted
description of that relation together with the independent symbols, and let the
decoder reconstruct the determined symbols. We formalise the pre-pass as a
GF(2) column-basis codec (with an integer-affine variant for tables), define a
*composed deduction gain* `G = min_c |c(x)| - min_c |c(D(x))|` over a fixed set
of stock compressors `c` and the accounted container `D(x)`, and preregister a
per-file success threshold before running any natural-corpus experiment. On
data engineered to contain an exact GF(2) linear code the pre-pass removes about
half of the size the six stock baselines achieve
(1 MiB code: `G` <!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_bytes = 523726 --> bytes,
`G_pct` <!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_pct = 0.4994616534154252 -->),
the gain scales with the number of rows while relation description stays
near-constant, and two context-mixing compressors (paq8l, paq8px v216) do not
close it. We then test whether comparable exploitable structure transfers to
public natural corpora: 8 of 12 whole Silesia members (the largest an 8 GiB
machine completes), all 12 Silesia members plus an enwik8 prefix plus six
scientific `float32` fields plus a telemetry text file at 256 KiB, and a bounded
bit-phase-offset extension of the detector. Under the preregistered protocol,
**no natural file produces a composed gain meeting the threshold**; the maximum
observed `G_pct` over 122 records is `+0.0009` (a passthrough header artifact),
and the offset extension reproduces the phase-0 composed gain to the byte on
every file. Functional-dependency and per-record-CRC32 cases reproduce known
techniques and are labelled as such. The mechanism is not novel (grammar
compression; syndrome coding; recent program-synthesis compression). Our
contribution is the accounting-complete codec with an independent verifier, the
composed-gain evaluation discipline, and the preregistered empirical finding
that blind axis-aligned exact-relation discovery does not yield a composed
advantage on the corpora and detectors tested. We do **not** claim natural data
contains no algebraic redundancy, nor that the approach can never help.

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
   axis-aligned exact-relation discovery yields **no** composed advantage
   meeting the threshold, robustly to bit phase (§5).

The mechanism itself is not claimed as novel; see §7.

## 2. Problem definition and the composed metric

Let `x` be the input byte string and `B` a fixed set of lossless stock
compressors (§5.2). Let `E` be a lossless deductive encoder with
`E^{-1}(E(x)) = x`, and write `D(x) = E(x)` for the *container*. `E` emits the
byte-smaller of a relation container (§3) and *passthrough*
(`magic · version · kind · len64 · crc32 · x`, all whole-byte fields, so
`|passthrough(x)| = |x| + 18`), hence `|D(x)| ≤ |x| + 18` always.

```
raw_best(x)      = min_{c ∈ B, c ran}  |c(x)|
composed_best(x) = min_{c ∈ B, c ran}  |c(D(x))|
G(x)             = raw_best(x) − composed_best(x)          (signed bytes)
G_pct(x)         = G(x) / raw_best(x)
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

`verification/independent_verify.py` shares no code with the encoder or the main
decoder: its own bit reader, its own container parse, a plain-Python XOR / integer
reconstruction, and an independent re-derivation of the accounting from parsed
field sizes. For every reported result it checks the full chain
`raw → encode → container → compress → decompress → independent-decode → raw`
and asserts SHA-256 equality and the accounting invariant. It reconstructs all
four container kinds in a self-test, runs in CI over 21 parametrised cases, and
was run on the 10 MB `silesia_dickens` container. The primary decoder's own
composed round-trip is also checked for every stock compressor.

### 5.4 Reproducibility harness

`scripts/reproduce.py` runs, in order: `pytest` (630 tests: equivalence,
randomised property tests, independent verifier), the verifier self-test, the
controls, the natural-corpus slice sweep, the offset-extension sweep, the legacy
phase experiments, then `build_ledger.py → regen_tables.py → make_figures.py →
check_paper_numbers.py → independent_verify.py --ledger`. All ten steps return 0
on the reported state. Every experiment JSON records dataset SHA-256, seeds,
config, the seven accounting categories, container size, round-trip and composed
round-trip status, every baseline `(name, bytes, seconds, available)`, every
composition size, `G`, `G_pct`, the raw gain, a UTC timestamp, the git commit
(with a `-dirty` marker if the tree was not clean), and machine info.

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
and beat a general-purpose compressor after counting the recipe — is not new.

* **Syndrome source coding** (Ancheta, 1976; and its universal generalisation).
  Treat the source as an error pattern and transmit its syndrome `Hx` under a
  linear code; a coset-leader source decompresses exactly. "In the absence of
  side information a Slepian–Wolf coder is an entropy coder." Compressing a
  single source by exploiting linear-code membership is classical; what is not
  classical is *discovering* the code from one input with description cost
  charged on the same channel — a thin distinction.
* **Grammar-based compression** (Kieffer–Yang; SEQUITUR; Re-Pair). The string is
  the unique yield of a grammar whose description cost is counted; structure is
  concatenative rather than linear-algebraic.
* **Functional-dependency / derived-column elimination.** US 8,150,888; Corra
  (2024); Wolpe (2026); TICC (2017); anisotropic columnar compression
  (US 11,562,085); Infobright-style inexact-FD-with-stored-exceptions. This
  space is thoroughly occupied for relational tables. Our affine-FD and CRC
  results are labelled as reproductions of it and are excluded from RQ-E.
* **Format-aware recompression.** Precomp, preflate, packJPG invert known
  codecs and drop reconstructible checksums; our PNG/ZIP/SQLite behaviour is the
  predicted format-awareness trap, not a counterexample.
* **Program-synthesis compression.** Brevis (2026) synthesises a self-contained
  DSL program that reconstructs a tensor bit-exactly and reports a real composed
  win on model checkpoints — a favourable domain dense with repeats, low rank
  and quantisation grids, searched with a rich language guided by a learned
  prior. This is a strong recent instance of the general idea; it does not
  occupy blind GF(2)/affine discovery on arbitrary bytes.
* **Low GF(2)-rank / Boolean matrix factorisation** (Fomin et al.; F_p-matrix
  factorisation). A change of basis to expose binary rank deficiency; NP-hard in
  general, and the exact case is the special case our column basis computes at a
  fixed width.
* **Invariant mining** (Daikon and successors). Templated discovery of
  equalities and affine relations among program variables; not a compressor and
  false-positive-prone.

**Our contribution, stated narrowly.** (i) An accounting-complete, never-worse
GF(2)/affine relation codec with an independent shared-nothing verifier;
(ii) the composed deduction-gain metric with a preregistered per-file threshold
as an evaluation discipline for pre-pass compression claims; (iii) a
preregistered empirical measurement — with a bounded phase-offset extension — of
whether blind axis-aligned exact-relation discovery produces a composed
advantage on public natural corpora, finding that it does not, on the corpora
and detectors tested. We do not claim any of (i)–(iii) is "first" in a stronger
sense than this.

## 8. Results

### 8.1 Mechanism validation (planted GF(2))

On random GF(2) linear codes — `k` information columns and `k` exact parity
columns — the pre-pass behaves exactly as designed. The relation description is
a constant of the code (1 088 bits for `k = 32`,
<!-- src: phase1_gf2_n65536_k64_p64_s14 / relation_description_bits = 4224 --> bits for
`k = 64`), independent of the number of rows, so the composed gain grows with
`n_rows`: `G_pct` rises from `+32.3 %` at 256 bytes to
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
| `dickens` | <!-- src: nat_silesia_dickens / dataset_bytes = 10192446 --> | GF2 | <!-- src: nat_silesia_dickens / n_relations = 25 --> | <!-- src: nat_silesia_dickens / raw_best_bytes = 2799520 --> | <!-- src: nat_silesia_dickens / composition_gap_bytes = -2645016 --> | −94.5 % |
| `x-ray` | <!-- src: nat_silesia_x-ray / dataset_bytes = 8474240 --> | GF2 | <!-- src: nat_silesia_x-ray / n_relations = 58 --> | <!-- src: nat_silesia_x-ray / raw_best_bytes = 4051112 --> | <!-- src: nat_silesia_x-ray / composition_gap_bytes = -1907747 --> | −47.1 % |
| `xml` | <!-- src: nat_silesia_xml / dataset_bytes = 5345280 --> | GF2 | <!-- src: nat_silesia_xml / n_relations = 21 --> | <!-- src: nat_silesia_xml / raw_best_bytes = 430390 --> | <!-- src: nat_silesia_xml / composition_gap_bytes = -1299038 --> | −301.8 % |

The relations found on text/XML are the "high bit of a mostly-ASCII byte is
zero" bit-plane and similar; brotli and bzip2 already exploit this from the raw
byte order. The other five members admit no exact relation at any tried width
and fall to passthrough, with `|G| ≤ 6 408` bytes (`|G_pct| ≤ 0.15 %`), i.e.
downstream-compressor sensitivity to an 18-byte header, not deduction.

**256 KiB files (20).** Same pattern: 0 meaningful positives (Table B.4). Where
GF(2) finds relations (`float32` fields, XML, text, telemetry) the composed gain
is large-negative (`−4.8 %` to `−302 %`); where it does not, `|G_pct| < 0.3 %`.
Across all 122 records the maximum `G_pct` is `+0.09 %`
(`silesia_sao` at 256 KiB, a passthrough container), far below the 5 % floor and
excluded anyway as passthrough.

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

* Positive, null, prior-art, and scope controls all behave as designed.
* No non-prior-art natural file meets the per-file threshold, on 8 whole
  Silesia members, 20 files at 256 KiB, and the phase-offset extension.
* Four of the twelve Silesia members, and the whole enwik8 / SDRBench / UCI
  files, could not be run whole on the available 8 GiB machine (§9).

By the letter of the preregistration this is **inconclusive for the full corpus
list** (the four large members are not yet run whole). For the coverage
achieved it is a **clean, layered negative**: on natural data, exact structure
is often present (RQ-A) and discoverable (RQ-B), and on no tested file does it
reduce the representation (RQ-C) or survive composition (RQ-D), robustly to bit
phase.

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
  files at 256 KiB plus the phase-offset extension — the composed deduction gain
  is at most `+0.09 %` and is negative on every file where a real relation is
  found. The redundancy the detector locates in natural data is real but
  trivial (constant bit-planes, ASCII structure) and is already captured by
  stock compressors from the raw byte order.

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
| the compressed container does not decode back | `raw → encode → compress → decompress → decode → raw` checked with both the primary and the independent decoder for every codec; 0 failures over 122 records |
| the width × variant `min` inflates results | representation-change null: 0 spurious gains on 40 i.i.d. inputs; never-worse guard caps the downside at passthrough |
| the negative is a framing / bit-phase artifact | bounded phase-offset extension on all 20 files: `G` equals the phase-0 value to the byte |
| a prefix is passed off as a whole file | separate result phase, separate manifest keys, `prefix` reason on every row |
| the corpus was chosen after seeing results | corpus list git-locked before any loader output; every file SHA-256-pinned; a changed hash aborts |
| numbers were transcribed by hand | all tables generated from `results/ledger.json`; inline figures carry markers checked by `check_paper_numbers.py` |

## 11. Limitations

* **Detector scope.** Axis-aligned fixed-width GF(2) plus integer affine,
  extended once to every bit phase. A negative is scoped to these families; the
  non-aligned-period control shows exact structure at a period not among the
  tried widths is missed by construction.
* **Whole-file coverage.** 8 of 12 Silesia members run whole (≤ 10.2 MB); the
  four largest (21–51 MB) and whole enwik8 / SDRBench / UCI need more than 8 GiB
  RAM than the development machine has. Every 256 KiB slice, every whole file
  run, and the offset extension agree, so the *conclusion* is consistent, but
  the pre-registered protocol is *not complete* for the full list.
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

We asked whether automatically discovered exact algebraic relations can provide
an additional source of lossless compression that survives full description cost
and composition with a strong downstream compressor. We built an
accounting-complete GF(2)/affine relation codec, an independent verifier, and a
composed-gain metric, and we preregistered the evaluation. The mechanism is
validated on deliberately structured data: it recovers planted GF(2) codes and
converts them into a composed size reduction of up to `+49.95 %` that scales
with data size and is not closed by two context-mixing compressors. Under the
preregistered protocol, the analogous exploitable structure does **not** appear
on the natural corpora tested — 8 whole Silesia members, 20 further files at
256 KiB, and a bounded bit-phase-offset extension all yield no composed gain
meeting the threshold, with a maximum observed `G_pct` of `+0.0009`. The
functional-dependency and CRC cases reproduce known techniques. The mechanism is
not novel; the contribution is the accounting discipline, the composed
evaluation, the controlled validation, and the preregistered empirical finding.
The result is a scoped negative, not a refutation of the idea: it establishes
that a blind, prior-free, axis-aligned linear detector does not expose a
composed advantage on general byte corpora, and it makes explicit what a future
positive would have to establish.

## 13. Reproducibility

Environment: Windows 11 (10.0.22631), 4 logical cores, 8 GiB RAM; Python 3.13.6;
numpy 2.2.6; zstandard 0.25.0; brotli 1.2.0. Corpora are not committed (licence
and size); acquisition is scripted and SHA-256-pinned, and a changed hash
aborts.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q                       # 630 tests
python verification/independent_verify.py --self-test

python experiments/controls/run.py        # exit 0 == all gates pass
python experiments/natural/run.py  --mode whole        # >= 32 GiB machine: the full answer
python experiments/natural/run.py  --mode whole --only silesia_xml   # one file at a time (8 GiB ok to ~10 MB)
python experiments/offset/run.py   --mode slice        # bit-phase-offset extension

python scripts/build_ledger.py && python scripts/regen_tables.py && python scripts/make_figures.py
python scripts/check_paper_numbers.py
python verification/independent_verify.py --ledger results/ledger.json

python scripts/reproduce.py --mode whole --offset-whole   # everything, big machine
```

On the reported state every step returns 0; a re-run reproduces every size,
gain, and verdict exactly, with only timings and timestamps differing.
`docs/preregistration.md` (locked), `docs/audit.md` (implementation audit and
corrections C1–C2), `docs/prior_art.md`, `docs/statistics.md`,
`docs/kill_criterion_status.md`, and `docs/venue_assessment.md` accompany the
manuscript.

---

## Appendix A — Figures

FIGURE::fig_planted_scaling

*Figure 1. Planted GF(2) codes: composed gain `G` (bytes) versus input size,
log–log. The gain scales approximately with the number of rows because the
relation description is a constant of the code. The two low points are a
single-flip near-relation control and an affine-parity control.*

FIGURE::fig_natural_gpct

*Figure 2. Natural corpus: per-file `G_pct` for the whole files, the 256 KiB
slices, and the bit-phase-offset extension, with the zero line and the
preregistered `+5 %` threshold. Every point is at or below zero.*

## Appendix B — Key results tables

The complete tables (**B.1** controls, **B.2** planted scaling + context-mixer
baseline, **B.3** whole natural, **B.4** 256 KiB natural, **B.5** bit-phase
offset, **B.6** prior art) are auto-generated in `paper/results_tables.md` from
`results/ledger.json` (122 records; 0 accounting, round-trip, or composed
round-trip failures). Every row traces to a JSON record under `results/`
carrying its dataset hash, git commit, configuration, compressor versions, and
verification status. The three most load-bearing are reproduced here.

**B.2 (extract) — planted GF(2): the mechanism scales**

| input bytes | relations | container | `raw_best` | `G` (bytes) | `G_pct` | relation bits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 256 | 8 | 172 | 260 | +84 | +32.3 % | 80 |
| 4,096 | 16 | 2,118 | 4,100 | +1,978 | +48.2 % | 288 |
| 32,768 | 32 | 16,554 | 32,772 | +16,214 | +49.5 % | 1,088 |
| 102,400 | 32 | 51,371 | 102,405 | +51,030 | +49.8 % | 1,088 |
| 256,000 | 32 | 128,171 | 256,005 | +127,829 | +49.9 % | 1,088 |
| 1,048,576 | 64 | 524,850 | 1,048,581 | +523,726 | +49.95 % | 4,224 |

**B.3 — whole natural files (8 of 12 Silesia members)**

| member | bytes | kind | rels | `raw_best` | container | `G` (bytes) | `G_pct` | round-trip |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `xml` | 5,345,280 | GF2 | 21 | 430,390 | 4,907,484 | −1,299,038 | −301.8 % | ✓ |
| `ooffice` | 6,152,192 | passthrough | 0 | 2,426,816 | 6,152,210 | −188 | −0.0 % | ✓ |
| `reymont` | 6,627,202 | passthrough | 0 | 1,246,230 | 6,627,220 | +217 | +0.0 % | ✓ |
| `sao` | 7,251,944 | passthrough | 0 | 4,415,072 | 7,251,962 | −6,408 | −0.15 % | ✓ |
| `x-ray` | 8,474,240 | GF2 | 58 | 4,051,112 | 6,555,798 | −1,907,747 | −47.1 % | ✓ |
| `mr` | 9,970,564 | passthrough | 0 | 2,441,280 | 9,970,582 | +857 | +0.0 % | ✓ |
| `osdb` | 10,085,684 | passthrough | 0 | 2,802,792 | 10,085,702 | −25 | −0.0 % | ✓ |
| `dickens` | 10,192,446 | GF2 | 25 | 2,799,520 | 9,197,882 | −2,645,016 | −94.5 % | ✓ |

**B.5 (summary) — bit-phase-offset extension (20 files, 256 KiB).** For every
file the offset-search `G` equals the phase-0 `G` to the byte; 0 files cross the
`+5 %` threshold; 0 files improve on phase 0 by more than header perturbation.
The axis-aligned negative is robust to bit phase.
