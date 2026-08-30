# Publishing this artifact

**Status:** the research is frozen at git tag **`v1.1-final`** (commit
`1216ef6`), pushed to `origin`. The manuscript PDF, its source, the figures, the
experiment ledger, the pre-registration, the verifier, and the reproduction
scripts are all in that tag (see the checklist at the bottom).

An automated agent prepared this repository for publication but **could not
publish it**: this environment has no authorised connection to Zenodo (or OSF,
figshare, DataCite), no GitHub CLI, and no GitHub API token. The steps below are
what a human with the accounts needs to do. They take about ten minutes and do
not change any scientific result.

`CITATION.cff` and `.zenodo.json` are filled in except for **author identity**,
which is deliberately left as the placeholder `Xeloraa` (the repository's
existing public handle). Replace it with your real name — and optionally an
ORCID — **before** you mint a DOI if you want the record under your real
identity. Do not let a tool guess this.

---

## 1. GitHub Release (canonical code record)

1. Go to `https://github.com/Xeloraa/deductive-coding/releases/new`.
2. **Choose a tag:** select the existing `v1.1-final` (do **not** create a new
   one; do not move it).
3. **Release title:** `v1.1-final — Exact-Relation Coding (frozen research artifact)`
4. **Description:** paste the body of the annotated tag message
   (`git show -s --format=%B v1.1-final`), or a short summary plus a link to
   `paper/exact-relation-coding.pdf`.
5. **Attach binaries:** upload `paper/exact-relation-coding.pdf` so the PDF is
   downloadable directly from the release page.
6. Leave "Set as the latest release" checked. Publish.

GitHub automatically attaches `Source code (zip)` and `(tar.gz)` snapshots of
the tag.

## 2. Zenodo record + DOI (permanent research record)

**Option A — Zenodo ↔ GitHub integration (recommended; keeps future releases in
sync):**

1. Sign in at `https://zenodo.org` (or create an account; you can log in with
   GitHub or ORCID).
2. `https://zenodo.org/account/settings/github/` → find
   `Xeloraa/deductive-coding` → toggle it **ON**.
3. Back on GitHub, either publish a *new* release, or delete and re-publish the
   `v1.1-final` release (the webhook fires on release creation). Zenodo ingests
   the release tarball, reads `.zenodo.json` for metadata, and issues a DOI
   (a version DOI plus a concept DOI that always resolves to the latest).
4. On the Zenodo record page, confirm:
   - **Upload type:** Publication → Preprint.
   - **Creators:** your real name / ORCID (fix the placeholder if you have not).
   - **License:** MIT.
   - **Description** and **keywords** came from `.zenodo.json` — verify they read
     correctly, especially that it says the complete pre-registered corpus was
     **not** executed and the outcome is *inconclusive for the full corpus, a
     clean layered negative within the achieved coverage*.
   - **Related identifier:** the GitHub URL should be listed.
5. Optionally also upload `paper/exact-relation-coding.pdf` as an extra file so
   the PDF is a first-class download on the record (the tarball already contains
   it).
6. Publish. Zenodo DOIs are permanent and the files become immutable.

**Option B — manual Zenodo upload (no GitHub link):**

1. `https://zenodo.org/uploads/new`.
2. Upload:
   - `paper/exact-relation-coding.pdf` (the manuscript),
   - a source archive: `git archive --format=zip -o exact-relation-coding-v1.1-final.zip v1.1-final`
     (this is the exact frozen tree: paper source + HTML, figures, ledger,
     pre-registration, verifier, reproduction scripts, corpus manifest, README).
3. Fill metadata from `.zenodo.json` (Zenodo does not read it on manual upload):
   title, version `v1.1-final`, Publication → Preprint, MIT, keywords, the
   description, and a *Related identifier* → `isSupplementedBy` →
   `https://github.com/Xeloraa/deductive-coding/tree/v1.1-final`.
4. Set **Creators** to your real identity.
5. Publish.

## 3. After publishing

- Add the DOI badge / citation to `README.md` and to `CITATION.cff`
  (`doi:` field and a `preferred-citation`).
- If you used Option A, the concept DOI is the one to cite in the paper.

---

## Frozen-artifact checklist (all present in `v1.1-final`)

| item | path |
| --- | --- |
| final PDF | `paper/exact-relation-coding.pdf` |
| Markdown source | `paper/exact-relation-coding.md` |
| HTML source | `paper/exact-relation-coding.html` |
| generated tables | `paper/results_tables.md` |
| figures | `paper/figures/fig_planted_scaling.svg`, `paper/figures/fig_natural_gpct.svg` |
| results ledger | `results/ledger.json`, `results/ledger.csv` |
| per-experiment records | `results/**/*.json` |
| pre-registration (git-locked) | `docs/preregistration.md` |
| verification scripts | `verification/independent_verify.py` |
| reproduction scripts | `scripts/reproduce.py`, `scripts/build_ledger.py`, `scripts/regen_tables.py`, `scripts/make_figures.py`, `scripts/check_paper_numbers.py`, `scripts/build_pdf.py` |
| corpus manifest | `results/corpus_manifest.json` |
| reproduction instructions | `README.md` (see also manuscript §13) |
| supporting docs | `docs/audit.md`, `docs/prior_art.md`, `docs/statistics.md`, `docs/kill_criterion_status.md`, `docs/venue_assessment.md`, `docs/protocol.md`, `docs/environment_constraints.md`, `docs/submission_gap_audit.md`, `docs/naming.md` |
| final tag / commit | `v1.1-final` → `1216ef6` |

`CITATION.cff` and `.zenodo.json` were added on `master` *after* `v1.1-final`
(publication metadata only, no science). If you want them inside the archived
snapshot, either publish the Zenodo record from `master` HEAD instead of the
tag, or move the tag yourself.
