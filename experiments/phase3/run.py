"""Phase 3: in-repo corpora and format-awareness traps.

Does not download copyrighted datasets. Uses this repository's own text
as a source-code sample, plus generated tabular FD data labeled as such.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_bytes_best_gf2  # noqa: E402
from deductive.codecs.tabular_codec import bytes_to_table, encode_tabular_affine  # noqa: E402
from deductive.datasets.synthetic import exact_functional_table  # noqa: E402


def repo_text_corpus() -> bytes:
    chunks: list[bytes] = []
    for folder in ("src", "tests", "docs", "experiments"):
        root = ROOT / folder
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".py", ".md"}:
                continue
            chunks.append(path.read_bytes())
            chunks.append(b"\n")
    return b"".join(chunks)


def main() -> int:
    text = repo_text_corpus()
    rec = run_codec_experiment(
        phase="phase3",
        experiment_id="phase3_repo_source_md",
        dataset_id="repo_src_tests_docs_experiments",
        data=text,
        seed=None,
        config={"codec": "gf2_best", "widths": [8, 16, 32, 64, 128]},
        encode_fn=lambda d=text: encode_bytes_best_gf2(d, widths=(8, 16, 32, 64, 128)),
        hypothesis=(
            "Source/docs in this repo: if GF(2) deduction has a composed gap "
            "on ordinary text, that is evidence beyond planted codes. A loss "
            "is evidence that strong compressors already capture this data."
        ),
        notes="in-repo text; not a public corpus",
    )
    persist(rec, "phase3")
    print_record(rec)

    fd = exact_functional_table(n_rows=32768, seed=501, fn="affine")
    rec = run_codec_experiment(
        phase="phase3",
        experiment_id="phase3_fd_affine_32k_labeled_prior_art",
        dataset_id=fd.dataset_id,
        data=fd.data,
        seed=501,
        config={"codec": "tabular_affine", "label": "FD_elimination_prior_art", "n_rows": 32768},
        encode_fn=lambda d=fd.data: encode_tabular_affine(bytes_to_table(d, 3)),
        hypothesis=(
            "Larger affine table: composition win is derived-column elimination "
            "(prior art), not a general byte-corpus deduction gap."
        ),
        notes="LABEL: functional-dependency column elimination; not claimed as novel",
    )
    persist(rec, "phase3")
    print_record(rec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
