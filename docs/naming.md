# Naming

## The problem with "Deductive Coding"

The phrase is already used for two unrelated things:

1. **Qualitative research methodology** — "deductive coding" is coding
   interview / survey text against a predefined codebook. This is the dominant
   meaning in a literature search and is an unavoidable collision.
2. **Semantic / lossy compression (2026)** — "Rate-Distortion Theory for
   Deductive Sources" and "Semantic Rate-Distortion: Deductive Compression and
   Closure Fidelity" (arXiv 2604.11204 / 2604.15698) use "deductive
   compression" for lossy coding of knowledge bases under a proof system. That
   is an adjacent field publishing under the same term now.

Using "Deductive Coding" for a byte-exact lossless method invites confusion with
both.

## Chosen name

**Exact-Relation Coding** — descriptive, unclaimed, and precise about the two
things that define the method:

- *exact*: only relations that hold on every row / every bit-column are used; no
  probabilistic prediction, no near-relations without counted exceptions;
- *relation*: the structure discovered is an algebraic relation (a GF(2) column
  basis, or an integer affine functional dependency), not a learned model.

No acronym is promoted (the obvious ones — ERC, ERD, ERP, XRC — all already
mean other things). Write it out.

The **metric** keeps its descriptive name: the *composed deduction gain*
`G_abs = raw_best - composed_best` (`docs/metric.md`). "Deduction gain" as a
plain-English description of "bytes saved by omitting deducible symbols" is not
a claimed term and does not collide.

## What is NOT renamed

- The container magic bytes are `DEDC` (4 bytes, in every artifact). Changing
  them would invalidate every existing result artifact and the frozen codec
  equivalence reference for zero scientific gain. They are treated as an opaque
  format tag; `docs/audit.md` and `verification/independent_verify.py` assert
  they match `deductive.__init__.MAGIC`.
- The Python package path is `src/deductive/`. A source-tree rename is pure
  churn with test-suite risk and no bearing on any measurement. It is legacy;
  imports read `from deductive... import ...` and that is fine.

## Positioning relative to prior art (see docs/prior_art.md)

Exact-Relation Coding does **not** claim the general idea of
"discover exact structure → transmit a reconstruction recipe → beat general
compressors after accounting" as novel. That idea is present in grammar
compression, in syndrome-source-coding (Ancheta 1976), and — with a real 2026
composed win on model checkpoints — in Brevis (program synthesis for tensor
compression). The contribution here is narrow and empirical: a **prior-free,
axis-aligned GF(2)/affine** relation family, with a bit-exact ledger and a
**pre-registered composed-gain test on public corpora**, and the finding of
where that family does and does not produce a composed gain.
