"""Exact integer affine relation discovery.

Searches for relations of the form

    z = a x + b y + c

with exact integer arithmetic. A relation is accepted only if it holds on
every row. Coefficients are not assumed; they are recovered from the data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AffineRelation:
    """z_col = a * x_col + b * y_col + c, with y_col optional (b=0)."""

    z_col: int
    x_col: int
    y_col: int | None
    a: int
    b: int
    c: int

    def evaluate(self, x: int, y: int = 0) -> int:
        return self.a * x + self.b * y + self.c

    def holds(self, table: np.ndarray) -> bool:
        x = table[:, self.x_col]
        z = table[:, self.z_col]
        if self.y_col is None:
            pred = self.a * x + self.c
        else:
            pred = self.a * x + self.b * table[:, self.y_col] + self.c
        return bool(np.all(pred == z))


def _as_object_ints(table: np.ndarray) -> np.ndarray:
    """Python ints so large intermediate values do not wrap."""
    if table.dtype == object:
        return table
    return table.astype(object)


def _univariate_from_two_points(x0: int, z0: int, x1: int, z1: int) -> tuple[int, int] | None:
    dx = x1 - x0
    dz = z1 - z0
    if dx == 0:
        return None
    if dz % dx != 0:
        return None
    a = dz // dx
    c = z0 - a * x0
    return a, c


def discover_univariate(table: np.ndarray, z_col: int, x_col: int) -> AffineRelation | None:
    n = table.shape[0]
    if n == 0:
        return None
    x = table[:, x_col]
    z = table[:, z_col]
    # Find two rows with distinct x.
    x0 = int(x[0])
    z0 = int(z[0])
    x1 = z1 = None
    for i in range(1, n):
        if int(x[i]) != x0:
            x1 = int(x[i])
            z1 = int(z[i])
            break
    if x1 is None:
        # x is constant: z must be constant, then a=0, c=z
        if not all(int(z[i]) == z0 for i in range(n)):
            return None
        rel = AffineRelation(z_col=z_col, x_col=x_col, y_col=None, a=0, b=0, c=z0)
        return rel if rel.holds(table) else None
    pair = _univariate_from_two_points(x0, z0, x1, z1)
    if pair is None:
        return None
    a, c = pair
    rel = AffineRelation(z_col=z_col, x_col=x_col, y_col=None, a=a, b=0, c=c)
    return rel if rel.holds(table) else None


def _solve_bivariate_three_rows(
    rows: list[tuple[int, int, int]],
) -> tuple[int, int, int] | None:
    """Solve a x + b y + c = z on three rows. Return integer (a,b,c) or None."""
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = rows
    # Eliminate c: (x_i-x0) a + (y_i-y0) b = z_i - z0
    dx1, dy1, dz1 = x1 - x0, y1 - y0, z1 - z0
    dx2, dy2, dz2 = x2 - x0, y2 - y0, z2 - z0
    det = dx1 * dy2 - dy1 * dx2
    if det == 0:
        return None
    # Cramer's rule; require exact integers
    numa = dz1 * dy2 - dy1 * dz2
    numb = dx1 * dz2 - dz1 * dx2
    if numa % det != 0 or numb % det != 0:
        return None
    a = numa // det
    b = numb // det
    c = z0 - a * x0 - b * y0
    return a, b, c


def discover_bivariate(table: np.ndarray, z_col: int, x_col: int, y_col: int) -> AffineRelation | None:
    n = table.shape[0]
    if n < 1:
        return None
    pts: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for i in range(n):
        xy = (int(table[i, x_col]), int(table[i, y_col]))
        if xy in seen:
            continue
        seen.add(xy)
        pts.append((xy[0], xy[1], int(table[i, z_col])))
        if len(pts) >= 8:
            break
    if len(pts) == 1:
        x0, y0, z0 = pts[0]
        rel = AffineRelation(z_col=z_col, x_col=x_col, y_col=y_col, a=0, b=0, c=z0)
        return rel if rel.holds(table) else None
    if len(pts) == 2:
        # Degenerate: try univariate in x or y, or fail.
        uni = discover_univariate(table, z_col, x_col)
        if uni is not None:
            return AffineRelation(z_col=z_col, x_col=x_col, y_col=y_col, a=uni.a, b=0, c=uni.c) if uni.holds(table) else None
        uni = discover_univariate(table, z_col, y_col)
        if uni is not None:
            return AffineRelation(z_col=z_col, x_col=y_col, y_col=None, a=uni.a, b=0, c=uni.c)
        return None
    # Try several triples in case the first three are linearly dependent in (x,y).
    for i in range(len(pts) - 2):
        for j in range(i + 1, len(pts) - 1):
            for k in range(j + 1, min(j + 4, len(pts))):
                sol = _solve_bivariate_three_rows([pts[i], pts[j], pts[k]])
                if sol is None:
                    continue
                a, b, c = sol
                rel = AffineRelation(z_col=z_col, x_col=x_col, y_col=y_col, a=a, b=b, c=c)
                if rel.holds(table):
                    return rel
    return None


def discover_affine_relations(table: np.ndarray) -> tuple[list[int], list[AffineRelation]]:
    """Find an acyclic set of exact affine relations.

    Targets are considered from right to left so that leftmost columns are
    preferred as independent when a later column is determined by earlier
    ones. A column may be dependent even if it appears first in the table.
    """
    if table.ndim != 2:
        raise ValueError("table must be 2-D")
    tbl = _as_object_ints(table)
    n_cols = tbl.shape[1]
    independent: list[int] = list(range(n_cols))
    relations: list[AffineRelation] = []
    changed = True
    while changed:
        changed = False
        for j in sorted(independent, reverse=True):
            sources = [c for c in independent if c != j]
            found: AffineRelation | None = None
            for i in sources:
                found = discover_univariate(tbl, j, i)
                if found is not None:
                    break
            if found is None and len(sources) >= 2:
                for a_i in range(len(sources)):
                    for b_i in range(a_i + 1, len(sources)):
                        found = discover_bivariate(tbl, j, sources[a_i], sources[b_i])
                        if found is not None:
                            break
                    if found is not None:
                        break
            if found is not None:
                relations.append(found)
                independent.remove(j)
                changed = True
                break
    independent.sort()
    relations.sort(key=lambda r: r.z_col)
    return independent, relations


def apply_relations(
    independent_values: dict[int, np.ndarray],
    relations: list[AffineRelation],
    n_rows: int,
    n_cols: int,
) -> np.ndarray:
    out = np.empty((n_rows, n_cols), dtype=object)
    known = set(independent_values)
    for idx, col in independent_values.items():
        out[:, idx] = col
    remaining = list(relations)
    while remaining:
        progress = False
        for rel in remaining:
            srcs = {rel.x_col}
            if rel.y_col is not None:
                srcs.add(rel.y_col)
            if not srcs <= known:
                continue
            x = out[:, rel.x_col]
            if rel.y_col is None:
                out[:, rel.z_col] = [rel.a * int(v) + rel.c for v in x]
            else:
                y = out[:, rel.y_col]
                out[:, rel.z_col] = [
                    rel.a * int(xv) + rel.b * int(yv) + rel.c for xv, yv in zip(x, y)
                ]
            known.add(rel.z_col)
            remaining.remove(rel)
            progress = True
            break
        if not progress:
            raise ValueError("cyclic or incomplete affine relations")
    return out
