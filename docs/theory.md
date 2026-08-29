# Theory notes

## Deductive vs statistical coding

Statistical lossless coding assigns a probability to the next symbol and encodes a residual. Deductive coding, as studied here, is not a better probability. It is an exact reconstruction:

```text
ordinary:   predict x_i  →  encode residual / code according to p(x_i | context)
deductive:  derive x_i from a relation that already determines it  →  encode nothing for x_i
```

Nothing is free. The relation, the independent symbols, headers, framing, and integrity checks are transmitted. The decoder reconstructs `x_i` only from that message.

## Relation description is information

A basis of GF(2) relations on `m` columns of rank `k` costs on the order of `m + (m-k) k` bits under the canonical v1 layout (pivot mask plus coefficient matrix), plus a constant header. Recovered payload is `(m-k) n` bits for `n` rows. Net saving requires `n` large enough that recovered bits exceed description and container overhead.

Random matrices with `n < m` have nontrivial kernel for dimensional reasons. Encoding the kernel then reconstituting columns does not compress: the coefficients *are* the data. The never-worse rule must fall back to passthrough.

## Provisional deduction gap

For a byte string `X`:

```text
deduction_gap_raw(X) = min_c |c(X)| - |D(X)|
```

where `c` ranges over available statistical compressors and `D(X)` is the fully accounted deductive container (or passthrough if larger).

```text
deduction_gap_composed(X) = min_c |c(X)| - min_c |c(D(X))|
```

The composed quantity is the one that answers the research question. A raw win that vanishes under xz means the statistical codec already captures the redundancy when given a more convenient arrangement, or that the container is simply easier to compress for boring reasons (zeros, leftover structure).

Other useful cuts: recovered bits, relation-description bits, overhead fraction, bits/byte.

These definitions are provisional. They will be changed if experiments show they mislead (for example if `D` expands incompressible data just enough that `c(D)` is worse while `D` itself is slightly smaller).

## Parity and autoregressive models

Do **not** claim: “autoregressive models cannot represent parity.”

Distinctions:

1. **Representational capability.** A sufficiently expressive conditional model `p(x_i | x_<i)` can put mass 1 on the correct parity bit when the relevant bits are in the context.
2. **Conditional entropy under an ordering.** If the parity bit is encoded *before* the bits that determine it, `H(parity | prefix)` is not zero. Order matters.
3. **Computational tractability.** Computing XOR over a long unordered set is cheap; learning it from next-token prediction with a finite context or a particular architecture may be hard.
4. **Predictor capacity.** A small context mixer may fail to implement the exact function even though some larger model would.
5. **Exact deductive reconstruction.** Once the relation is known and the independent bits are present, the parity bit is determined with zero residual. That is a different coding strategy, not a proof that probability models cannot have the same information.

An experiment that shows gzip/zstd/xz failing to squeeze planted XOR bits is evidence about *those compressors on that bitstream*, which is exactly the comparison we need. It is not a theorem about neural sequence models.

## Exactness

A relation is used only if it holds on every row (or every bit column). Near-relations with a single flipped symbol are rejected. Residual/exception coding is allowed later only if exceptions are fully counted.

## Novelty boundary

Functional-dependency column elimination is prior art. The live question is whether a general, automatically discovered deductive layer yields a composed gap on arbitrary byte corpora, not only on tables with named derived columns. If experiments show wins only on FD-shaped tables, the project must say so and not rebrand database compression.
