"""Regenerate every paper table from results/ledger.json.

Writes paper/results_tables.md. The paper body includes/references this file;
no experimental number in the paper is hand-typed. scripts/check_paper_numbers.py
fails CI if this output is stale relative to the ledger, or if a number in the
paper prose is not backed by a `<!-- src: ... -->` marker that resolves here.

    python scripts/build_ledger.py && python scripts/regen_tables.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results" / "ledger.json"
OUT = ROOT / "paper" / "results_tables.md"


def load() -> list[dict]:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def by_id(rows):
    return {r["experiment_id"]: r for r in rows}


def _g(r, k, default="—"):
    v = r.get(k)
    return default if v is None else v


def _pct(r, k):
    v = r.get(k)
    return "—" if v is None else f"{v*100:+.2f}%"


def tbl(header, rows):
    line = "| " + " | ".join(header) + " |"
    sep = "| " + " | ".join("---" for _ in header) + " |"
    body = ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join([line, sep, *body])


def section_controls(rows):
    out = ["## Controls\n"]
    want = [r for r in rows if r["phase"] == "controls"]
    hdr = ["experiment", "kind", "rels", "raw_best", "container", "composed_best",
           "G_abs", "G_pct", "matched G_abs", "codec sets match", "round-trip", "composed RT", "acct ok"]
    body = []
    for r in sorted(want, key=lambda r: r["experiment_id"]):
        body.append([
            r["experiment_id"].replace("control_", ""),
            r["codec_kind"], _g(r, "n_relations"),
            _g(r, "raw_best_bytes"), _g(r, "container_bytes"), _g(r, "composed_best_bytes"),
            _g(r, "composition_gap_bytes"), _pct(r, "composition_gap_pct"),
            _g(r, "composition_gap_matched_bytes"), _g(r, "codec_sets_match"),
            _g(r, "roundtrip_ok"), _g(r, "composed_roundtrip_ok"), _g(r, "accounting_ok"),
        ])
    out.append(tbl(hdr, body))
    return "\n".join(out)


def section_planted(rows):
    out = ["\n## Planted GF(2) — scaling and mixer baselines\n"]
    scaling = [r for r in rows if r["phase"] in ("phase1", "phase4", "phase0")
               and "gf2" in (r["dataset_id"] or "") and r["codec_kind"] == "GF2"]
    hdr = ["experiment", "dataset_bytes", "rels", "container", "raw_best", "composed_best",
           "G_abs", "G_pct", "relation_bits", "round-trip"]
    body = []
    for r in sorted(scaling, key=lambda r: (r["dataset_bytes"] or 0)):
        body.append([
            r["experiment_id"], _g(r, "dataset_bytes"), _g(r, "n_relations"), _g(r, "container_bytes"),
            _g(r, "raw_best_bytes"), _g(r, "composed_best_bytes"),
            _g(r, "composition_gap_bytes"), _pct(r, "composition_gap_pct"),
            _g(r, "relation_description_bits"), _g(r, "roundtrip_ok"),
        ])
    out.append(tbl(hdr, body))

    paq = [r for r in rows if r["phase"] == "phase4_paq"]
    if paq:
        out.append("\n### Context-mixing baselines on a 10 KiB planted code\n")
        out.append("Values as recorded in each `results/phase4_paq/*.json` `config` block "
                   "(paq run externally; not part of `B`).")
        hdr2 = ["experiment", "note"]
        out.append(tbl(hdr2, [[r["experiment_id"], (r.get("config") or "")[:90]] for r in paq]))
    return "\n".join(out)


def section_natural(rows):
    out = ["\n## Natural corpora\n"]
    whole = [r for r in rows if r["phase"] == "natural"]
    sl = [r for r in rows if r["phase"] == "natural_slice"]
    hdr = ["dataset_id", "bytes", "sha256[:12]", "kind", "rels", "container",
           "raw_best", "composed_best", "G_abs", "G_pct", "A", "B", "C",
           "round-trip", "composed RT", "acct ok"]

    def rowfmt(r):
        # A/B/C recomputed from ledger fields (discoverable / reduces repr / survives composition)
        A = (r.get("n_relations") or 0) >= 1
        rg = r.get("raw_gap_bytes")
        B = (r.get("container_bytes") is not None and r.get("dataset_bytes") is not None
             and r["container_bytes"] < r["dataset_bytes"] + 18 and rg is not None and rg > 0)
        C = (r.get("composition_gap_bytes") or -1) > 0
        return [
            r["dataset_id"], _g(r, "dataset_bytes"), (r.get("dataset_sha256") or "")[:12],
            r["codec_kind"], _g(r, "n_relations"), _g(r, "container_bytes"),
            _g(r, "raw_best_bytes"), _g(r, "composed_best_bytes"),
            _g(r, "composition_gap_bytes"), _pct(r, "composition_gap_pct"),
            int(A), int(B), int(C), _g(r, "roundtrip_ok"), _g(r, "composed_roundtrip_ok"),
            _g(r, "accounting_ok"),
        ]

    if whole:
        out.append("### Whole-file (pre-registered answer)\n")
        out.append(tbl(hdr, [rowfmt(r) for r in sorted(whole, key=lambda r: r["dataset_id"])]))
        out.append(f"\nWhole-file experiments run: {len(whole)} of the pre-registered corpus list. "
                   "Remaining rows PENDING a >=32 GiB machine (docs/environment_constraints.md).")
    if sl:
        out.append("\n### Dev-machine feasibility slices (provenance only, NOT the pre-registered answer)\n")
        out.append(tbl(hdr, [rowfmt(r) for r in sorted(sl, key=lambda r: r["dataset_id"])]))
    return "\n".join(out)


def section_priorart(rows):
    out = ["\n## Prior-art sanity cases (labelled; never counted toward the hypothesis)\n"]
    pa = [r for r in rows if "priorart" in (r["experiment_id"] or "")
          or r["phase"] == "phase3" and "crc" in (r["dataset_id"] or "")]
    hdr = ["experiment", "kind", "rels", "raw_best", "container", "composed_best", "G_abs", "G_pct", "label"]
    body = []
    for r in sorted(pa, key=lambda r: r["experiment_id"]):
        cfg = json.loads(r["config"]) if isinstance(r.get("config"), str) else (r.get("config") or {})
        body.append([
            r["experiment_id"], r["codec_kind"], _g(r, "n_relations"),
            _g(r, "raw_best_bytes"), _g(r, "container_bytes"), _g(r, "composed_best_bytes"),
            _g(r, "composition_gap_bytes"), _pct(r, "composition_gap_pct"),
            cfg.get("label", "prior_art"),
        ])
    out.append(tbl(hdr, body))
    return "\n".join(out)


def main() -> int:
    rows = load()
    parts = [
        "# Generated results tables",
        "",
        "Auto-generated by `scripts/regen_tables.py` from `results/ledger.json`.",
        "Do not edit by hand. Regenerate: "
        "`python scripts/build_ledger.py && python scripts/regen_tables.py`.",
        f"\nLedger rows: {len(rows)}. "
        f"Accounting failures: {sum(1 for r in rows if r.get('accounting_ok') is False)}. "
        f"Round-trip failures: {sum(1 for r in rows if r.get('roundtrip_ok') is False)}. "
        f"Composed round-trip failures: {sum(1 for r in rows if r.get('composed_roundtrip_ok') is False)}.",
        "",
        section_controls(rows),
        section_planted(rows),
        section_natural(rows),
        section_priorart(rows),
        "",
    ]
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
