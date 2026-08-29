# Prior-art audit

Living document. If the central mechanism is already substantially implemented with honest accounting on general corpora, stop claiming novelty and either redefine or kill the project.

Last audit pass: 2026-08-29.

## Verdict so far

**Do not claim novelty for:** dropping a table column that is an exact function of others and storing the formula.

That idea is occupied (database patents, Corra, and a 2026 derived-column pre-pass). This repository still has a distinct *question*: whether automatically discovered **exact** relations, including GF(2) linear structure on general byte strings, produce a **composed** deduction gap against strong general-purpose compressors after full description cost — and whether that gap exists outside format-aware and FD-shaped data.

Until real-corpus composition results exist, novelty of the *research question* is possible; novelty of FD elimination is not.

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

## Search log

- 2026-08-29: constraint-based compression; Corra; Wolpe FD pre-pass; US 8,150,888; precomp; Slepian–Wolf; MeLLoC; grammar compression; PAQ mixing; Daikon. No tool found that states a corpus-level deduction gap for general bytes with GF(2) discovery and full accounting.
- 2026-08-29: PNG/ZIP/gzip CRC32 (PNG spec, zlib `crc32`, precomp); SQLite pager / unused-page zeros vs columnar FD. Same verdict: FD elimination occupied; CRC inversion occupied; live question remains a composed gap on arbitrary bytes.
- 2026-08-29: local PATH, Program Files, user folders, and this repo — no `paq8px` / `zpaq` / `cmix` / `bsc` on PATH. `paq8l.exe` was later obtained from mattmahoney.net `paq8l.zip` (gitignored). Level `-3` on 10 KiB planted GF(2): paq(raw)=10299 vs DEDC 5291; mixer does not absorb XOR.

## 2026-08-29 — CRC32, PNG vs GF(2), SQLite pager

**CRC inversion is occupied.** PNG chunk CRCs (ISO 3309 / ITU-T V.42 CRC-32 over type+data; PNG specification), gzip trailers, and ZIP local/central CRC-32 of uncompressed payload are published checksums. zlib’s `crc32` is the usual implementation. Precomp (and format-aware PNG/ZIP recompressors) already invert known streams and drop reconstructible CRCs. A per-record CRC32 that a blind affine GF(2) basis recovers is the same checksum, not a new phenomenon. Label it format-aware; do not cite it as novelty on “real files.”

**Parsing PNG is not a whole-file GF(2) matrix.** Chunk layout, `IHDR`/`IDAT`/`IEND`, per-chunk CRC fields, and deflate-inside-`IDAT` are a typed parse plus a known codec. Precomp-style wins on PNG/ZIP/gzip are that parse. Treating the entire file as bit-columns and discovering a GF(2) basis is a different mechanism: no chunk grammar, no zlib stream finder. Even if both omit CRC bits, the description is not “we parsed PNG.” Rediscovering CRCs, lengths, or deflate by either route stays labeled occupied.

**SQLite pager zeros are not columnar FD.** The SQLite file is a header plus fixed-size pages (pager). Unused page bytes and never-written pages are typically zero. A GF(2) pass that collapses that sparsity is format structure; xz already encodes long zero runs. Columnar FD elimination (drop a table column that is an exact function of others; Corra / US 8,150,888 / Wolpe 2026) is a schema-shaped relation on *cells*, not pager slack. A SQLite raw-size shrink that then loses on composition is a format-awareness trap, not derived-column compression and not a general-byte deduction gap.

**Phase 4 measurement (2026-08-29):** whole-file GF(2) on generated PNG 48×48, stored ZIP, and a 4000-row SQLite FD file was passthrough (`n_relations==0`). Composed gaps were negative (header perturbation or xz/brotli on the raw file). That is the predicted format-awareness trap, not a counterexample to occupancy of CRC inversion / pager sparsity.

**Verdict unchanged.** FD elimination occupied. CRC inversion occupied. The live question is still whether discovered exact relations on *arbitrary* bytes yield a composed deduction gap after full description cost, outside format-aware and FD-shaped data.
