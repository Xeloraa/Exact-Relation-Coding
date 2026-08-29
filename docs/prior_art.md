# Prior-art audit

Living document. If the central mechanism is already substantially implemented with honest accounting on general corpora, stop claiming novelty and either redefine or kill the project.

Last audit pass: 2026-08-29.

## Verdict so far

**Do not claim novelty for:** dropping a table column that is an exact function of others and storing the formula.

That idea is occupied (database patents, Corra, and a 2026 derived-column pre-pass). This repository still has a distinct *question*: whether automatically discovered **exact** relations, including GF(2) linear structure on general byte strings, produce a **composed** deduction gap against strong general-purpose compressors after full description cost — and whether that gap exists outside format-aware and FD-shaped data.

Real-corpus composition results exist and are negative for GF(2) on general bytes (this repo, enwik8, stdlib, all twelve Silesia prefixes, PNG/ZIP, structured JSON/logs). Novelty of the *research question* is still possible for other exact-relation families; novelty of FD elimination is not.

## Close work

### Derived-column / functional-dependency compression

| Work | Mechanism | Data | Discovery? | Description cost transmitted? | Deductive reconstruct? | Arbitrary corpora? | Corpus-level deduction measure? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US 8,150,888 (SAP / related FD elimination) | Detect FDs among columns; drop dependents | Database tables | Yes (schema/data) | Implicit in remaining schema | Reconstruct column from FD | No (tables) | No |
| Corra (2024) | Horizontal diff vs reference columns; outliers stored | Columnar / TPC-H, Taxi, DMV | Partial; auto-detect called future work | Encoding scheme is the description | Reconstruct via diffs, not always exact FD drop | No (columns) | No |
| Wolpe (2026) Zenodo derived-column pre-pass | Exact arithmetic FD discovery; drop column; store formula | Columnar / CTU-13 NetFlow | Yes | Yes (formula); claims never-worse | Yes, byte-exact | No (columnar) | Compression delta vs columnar baseline |
| This repo | GF(2) basis + integer affine (+ later families); counted container | Synthetic now; general bytes intended | Yes, verified | Yes, bit-level ledger | Yes | That is the question | Provisional `deduction_gap_*` |

Wolpe 2026 explicitly disclaims novelty of FD elimination and cites Corra. Any win this project gets on CSV/SQLite/NetFlow-style tables must be **labeled as FD elimination**, not as a new phenomenon.

### Format-aware recompression

**Precomp** (Schnaader): finds deflate/zlib/gzip/JPEG/… streams, decompresses, stores reconstruction data, recompresses. Deductive in the sense of inverting a known codec; not general relation discovery. Wins on PDF/ZIP/PNG are format engineering. If we rediscover CRCs, lengths, or deflate, label it as such.

Related: preflate, packJPG, specialized PNG/WebP recompressors, PAQ file-type detectors.

### Slepian–Wolf / syndrome coding

Distributed source coding: correlated sources encoded separately, jointly decoded. Linear codes over GF(2) map a source to a syndrome `s = H x`. The decoder uses **side information** `y` (another source) plus the syndrome. Correlation model is typically assumed, not discovered from a single corpus with description cost on the same channel. Asymptotic, often not zero-error for finite `n`.

Related but not the same problem: DISCUS, LDPC/turbo SW codes. We are not doing distributed encoding of two separately observed sources.

### Algebraic / constraint / mechanism compression

- Schmidt, “Lossless data compression using constraint propagation”: LP-style bounds on samples, then encode a residual relative to a limited predictor. Statistical residual coding with constraints, not exact symbol omission.
- MeLLoC (NeurIPS 2024): learn PDE-like operators on scientific floats; store sparse source/boundary + residual. Domain-specific, not general byte corpora; residual still encoded.
- Grammar compression / SLPs (Kieffer–Yang, Rytter, …): the string is the unique yield of a grammar. Universal in a finite-state sense. Relations are concatenative, not GF(2) or integer affine. Description cost is the grammar, which *is* counted in the literature.
- Knowledge compilation / probabilistic circuits / MRFs: typically probabilistic, not exact reconstruction for lossless byte coding of arbitrary files.

### Invariant mining

Daikon-style dynamic invariant detection finds likely program invariants. Not a compressor; false invariants are expected. We require exact, verified relations and a transmitted description.

### PAQ / cmix

Context mixing with many specialized models (including some format-aware transforms). They *statistically* exploit structure, sometimes with hard-coded transforms. They do not emit a standalone verified relation basis whose description cost is isolated. Composition experiments against zstd/xz are the practical stand-in until PAQ/cmix binaries are available here. If a later PAQ run absorbs the entire planted-GF(2) gap, that is strong evidence against a deduction gap relative to the strongest statistical mixers.

### ECC as compression

Using a parity-check matrix to compress a source that is a noisy codeword is the syndrome-coding idea again. Compression of *arbitrary* data by discovering that it lies in an unknown linear code is closer to this project, and is only useful if the code description is cheaper than the omitted parity bits.

### Lossless scientific compressors

FPZIP, FPC, SPDP, error-bounded SZ/ZFP (lossy if unbounded). Predictors + residuals. Exact linear relations on integers/bits are a different slice.

## Redefine-or-kill trigger

Kill or narrow the novelty claim if we find a general-purpose tool that:

1. discovers exact relations on arbitrary bytes (not only known formats or declared schemas);
2. transmits the relation description;
3. reconstructs deductively with byte-exact decode;
4. reports composed size vs xz/zstd/PAQ.

FD-only tools do **not** trip this trigger for the GF(2)-on-bytes question. They **do** trip it for “we invented derived-column compression.”

## 2026-08-29 (audit pass 2) — closest new work

### Brevis: "Lossless Tensor Compression as Program Synthesis" (arXiv 2608.02162, Aug 2026)

The nearest thing to this project's *mechanism* that also reports a real
composed win.

| axis | Brevis | this repo |
| --- | --- | --- |
| what is discovered | a self-contained **DSL program** (reversible operators: repeated regions, strides, float-field splits) that reconstructs the tensor bit-exactly | a GF(2) column basis / integer affine relation set |
| discovery method | bounded A* search guided by a **production prior learned from a sample of similar tensors** | blind Gaussian elimination / affine solve on the single input, no prior |
| data | neural-network checkpoints (language / audio / image models) | arbitrary byte corpora |
| accounting | archive is self-contained and executed for decode; measured vs zstd/gzip and vs ZipNN/DFloat11 | bit-level ledger; measured vs `B` and (planted only) paq8l/paq8px |
| result | **+30.87%** smaller than general compressors on 2.13 TB of checkpoints | large composed gap on *planted* GF(2); **no** composed gain on the natural corpora tested |

**Effect on our claims.** Brevis shows the general idea — discover exact
structure, transmit a reconstruction recipe, beat general compressors after full
accounting — is alive in 2026 and *can* win **on a favourable domain**
(checkpoints are dense with exact structure: repeats, low rank, quantisation
grids). It does **not** occupy "blind GF(2)/affine discovery on arbitrary
bytes": different relation family (DSL programs vs linear algebra), and it
relies on a learned prior over a tensor population rather than single-input
blind discovery. It *does* mean our novelty statement must be narrow: we do not
claim "exact-structure discovery as a lossless pre-pass" as new (Brevis; and
grammar compression long before). We study one specific, prior-free,
axis-aligned linear family and report where it does and does not yield a
composed gain.

### Syndrome-source-coding — the pure idea is ~50 years old

Ancheta, "Syndrome-source-coding and its universal generalization" (IEEE T-IT,
1976): treat the source as an error pattern, transmit its syndrome `Hx` under a
linear code; if the source is a coset leader it decompresses exactly. "In the
absence of side information a Slepian–Wolf coder becomes an entropy coder."
So compressing a *single* source by exploiting that it lies near a known linear
code is classical. The only axis on which this project is not already covered is
**discovering** the code from the data with its description cost charged on the
same channel — a thin distinction, and one that only matters if that discovery
yields a composed gain on data nobody hand-picked. Our measurements say it does
not, on the corpora tested.

### Other 2024–2026 points (do not change the verdict)

- **TICC: Transparent Inter-Column Compression** (2017); **US 8,700,579**
  "data compression in a relational database"; **anisotropic columnar
  compression** (US 11,562,085): more inter-column / FD-shaped compression prior
  art. Reinforces: FD / derived-column elimination is thoroughly occupied.
- **Inexact FD with stored exceptions** (RSSI / Infobright-style data packs;
  restated in recent DB-compression patents): "store the relation plus the
  exceptional records." This is exactly what a rigorous *approximate*-relation
  extension of this project would be — already prior art; our corruption sweep
  and the UCI approximate relation are framed accordingly, not as novelty.
- **2026 AIT Data Compression Challenge** (arXiv 2606.17712): 117 compressors;
  the standard reversible-preprocessing toolbox is enumerated (BWT, MTF, RLE,
  delta, BCJ, YCoCg-R, wavelet lifting, dictionary/text filters). Blind
  algebraic-relation discovery is **not** in it — consistent with "not a
  known-useful pre-pass", i.e. a negative here is unsurprising, not novel.
- **StateSMix** (Mamba/SSM + sparse n-gram mixing, 2026), **Nacrith** (ensemble
  context mixing, 2026), **"Lossless data compression by large models"**
  (Nat. Mach. Intell., 2025): the statistical frontier keeps moving; none was
  run here. The paper says "the strongest context-mixing compressors we could
  run (paq8l, paq8px v216)" and nothing stronger.

## Search log

- 2026-08-29: constraint-based compression; Corra; Wolpe FD pre-pass; US 8,150,888; precomp; Slepian–Wolf; MeLLoC; grammar compression; PAQ mixing; Daikon. No tool found that states a corpus-level deduction gap for general bytes with GF(2) discovery and full accounting.
- 2026-08-29 (pass 2): Brevis (tensor program synthesis, 2608.02162); Ancheta syndrome-source-coding (1976) + universal generalisation; TICC; US 8,700,579; anisotropic columnar compression; 2026 AIT challenge preprocessing survey; StateSMix / Nacrith / LLM-as-compressor. Verdict unchanged: the *general* idea is not novel (Brevis, grammar compression, syndrome coding); the specific prior-free axis-aligned GF(2)/affine family with full accounting and a pre-registered composed test on public corpora is the contribution, and it is a **negative** on every natural corpus measured. FD elimination and CRC inversion remain occupied.
- 2026-08-29: PNG/ZIP/gzip CRC32 (PNG spec, zlib `crc32`, precomp); SQLite pager / unused-page zeros vs columnar FD. Same verdict: FD elimination occupied; CRC inversion occupied; live question remains a composed gap on arbitrary bytes.
- 2026-08-29: local PATH, Program Files, user folders, and this repo — no `paq8px` / `zpaq` / `cmix` / `bsc` on PATH. `paq8l.exe` was later obtained from mattmahoney.net `paq8l.zip` (gitignored). 10 KiB planted GF(2): `-3` paq(raw)=10299 vs DEDC 5291; `-8` paq(raw)=10321 vs DEDC 5291. Mixer does not absorb XOR at either level.
- 2026-08-29: `paq8px.exe` v216 from github.com/hxim/paq8px Releases (gitignored). Same 10 KiB planted GF(2): `-4` paq(raw)=10262 vs paq(DEDC)=5289 (gap +4973); `-8` 10261 vs 5288 (gap +4973). Current mixer does not absorb XOR. Still no cmix.

## 2026-08-29 — CRC32, PNG vs GF(2), SQLite pager

**CRC inversion is occupied.** PNG chunk CRCs (ISO 3309 / ITU-T V.42 CRC-32 over type+data; PNG specification), gzip trailers, and ZIP local/central CRC-32 of uncompressed payload are published checksums. zlib’s `crc32` is the usual implementation. Precomp (and format-aware PNG/ZIP recompressors) already invert known streams and drop reconstructible CRCs. A per-record CRC32 that a blind affine GF(2) basis recovers is the same checksum, not a new phenomenon. Label it format-aware; do not cite it as novelty on “real files.”

**Parsing PNG is not a whole-file GF(2) matrix.** Chunk layout, `IHDR`/`IDAT`/`IEND`, per-chunk CRC fields, and deflate-inside-`IDAT` are a typed parse plus a known codec. Precomp-style wins on PNG/ZIP/gzip are that parse. Treating the entire file as bit-columns and discovering a GF(2) basis is a different mechanism: no chunk grammar, no zlib stream finder. Even if both omit CRC bits, the description is not “we parsed PNG.” Rediscovering CRCs, lengths, or deflate by either route stays labeled occupied.

**SQLite pager zeros are not columnar FD.** The SQLite file is a header plus fixed-size pages (pager). Unused page bytes and never-written pages are typically zero. A GF(2) pass that collapses that sparsity is format structure; xz already encodes long zero runs. Columnar FD elimination (drop a table column that is an exact function of others; Corra / US 8,150,888 / Wolpe 2026) is a schema-shaped relation on *cells*, not pager slack. A SQLite raw-size shrink that then loses on composition is a format-awareness trap, not derived-column compression and not a general-byte deduction gap.

**Phase 4 measurement (2026-08-29):** whole-file GF(2) on generated PNG 48×48, stored ZIP, and a 4000-row SQLite FD file was passthrough (`n_relations==0`). Composed gaps were negative (header perturbation or xz/brotli on the raw file). That is the predicted format-awareness trap, not a counterexample to occupancy of CRC inversion / pager sparsity.

**Verdict unchanged.** FD elimination occupied. CRC inversion occupied. The live question is still whether discovered exact relations on *arbitrary* bytes yield a composed deduction gap after full description cost, outside format-aware and FD-shaped data.
