# RFC-0003: Reference catalog and collaborative research synthesis

Status: Proposed
Date: 2026-08-09

## Problem

Raveil research memos link primary papers and vendor material, but the tree has
no canonical way to identify the exact version consulted, record access and
redistribution constraints, detect corrections or retractions, or connect a
project-authored synopsis and atomic claim back to an exact source location.
Links alone are too mutable, while committing third-party PDFs or copied
abstracts would create provenance, copyright, and access-control risks.

The repository also needs a collaboration boundary. A Librarian can locate and
disambiguate sources, and a Researcher can synthesize them, but neither role may
turn literature into a Raveil fact, decision, experiment result, or Gate claim.

## Proposed design

### Canonical metadata, non-authoritative synthesis

Track bibliographic identity and provenance in
`docs/references/catalog.json`, using the versioned
`raveil.references/v1-draft` schema. The catalog is canonical only for what
source, version, locator, access class, and rights assessment Raveil recorded.
It is not authority for the truth of a source claim.

Each work is classified before annotation. Research papers may carry a
`raveil_authored_abstract`; manuals, product documentation, vendor
presentations, talks, patents, and similar material instead carry a
`raveil_authored_prior_art_note`. A prior-art note records why the item was
consulted and possible counterevidence. It is not a paper abstract, an adoption
recommendation, or permission to implement the described mechanism.

Each work has a stable work-level key. Versions remain separate and carry the
DOI, arXiv version, publisher document revision, canonical URL, publication and
access dates, correction/retraction state, rights assessment, and optional
content hash and size. A changed version is appended; it does not silently
replace the version previously cited.

A `raveil_authored_abstract` is a short project synopsis of a research paper,
labelled as such and
linked to its basis claims, including when those claims are explicitly draft
memo-derived claims awaiting a primary-source locator. It is never called or represented as the source's
abstract. The catalog does not copy a full source abstract. A short quotation,
when essential, must carry an exact locator and word count and remain within a
conservative aggregate limit of 25 quoted words from one source within one
tracked Markdown record or one catalog entry, pending legal review.

### Claim cards

External support for a retained design, comparison, or research claim is
represented as an atomic claim card with:

- a stable claim ID and one Raveil-authored paraphrase;
- kind: method, author-reported result, limitation, hypothesis, counterevidence,
  or Raveil inference;
- source role: primary, secondary discovery, or secondary context;
- exact source version and page, section, figure, table, timestamp, or other
  locator;
- conditions such as workload, hardware, population, metric, baseline, and
  units where applicable;
- uncertainty and correction/retraction status;
- explicit non-claims, especially what the source does not establish for
  Raveil.

ADR, RFC, EXP, and research-memo prose may cite the work/version and claim ID.
Strong external claims require a primary-source locator. A URL or a secondary
summary alone is insufficient for promotion. Incompatible claims remain
separate and linked as a conflict; they are not averaged or silently resolved.

### Collaborative handoff

1. The Project Manager fixes scope, T-ID, acceptance criteria, and the files
   that may change.
2. Vreji, the Librarian, returns a read-only packet of candidate primary sources,
   stable identifiers, available exact locators, version ambiguity, rights
   gaps, technical similarity, patent-family or standards references when
   found, adoption hazards, and sources to skip. It does not decide what a
   source proves, whether infringement exists, or whether implementation is
   legally cleared.
3. The Researcher reads the selected versions and writes a dated,
   non-authoritative memo containing Raveil-authored abstracts, claim cards,
   counterevidence, uncertainty, non-claims, and recommendations.
   Its tracked output remains under `docs/research/reviews/` as constrained by
   the repository role definition.
4. The Project Manager checks each promoted locator and integrates only the
   bibliographic/provenance fields into the canonical catalog. Decisions go to
   ADRs, unresolved design to RFC/OPEN_QUESTIONS, measurements to EXP, and
   implementation facts to code/tests and STATUS.
5. A later reviewer samples promoted claims from catalog entry to exact source
   location. Missing version, locator, rights status, or visible contradiction
   keeps the item draft or unverified.

### Storage and rights

Git tracks metadata, project-authored paraphrases, access dates, rights
assessments, and hashes. It does not track third-party PDFs by default.

Only an original whose storage is explicitly permitted may be placed under the
ignored `artifacts/reference-library/<work-key>/<version>/` tree or an approved
access-controlled external store. Record its source URL, capture time, exact
bytes, SHA-256, size, and permission basis. Free access is not treated as
redistribution permission. Paywalled, proprietary, NDA, DRM-protected, or
rights-unknown material remains metadata-only unless a governing agreement
explicitly permits controlled storage. Credentials, cookies, tokens, personal
account data, absolute machine paths, and unauthorized copies never enter Git
or public research bundles.

Copyright, license, confidentiality, and patent risk are separate checks. The
right to read, quote, store, or redistribute a document does not establish
freedom to implement claims that may be covered by a patent. Publication as
prior art also does not itself grant a patent license. Before a mechanism from
an external source becomes an implementation proposal, record whether a patent
search was performed, known patent-family or standards-licensing references,
the intended jurisdictions and use, and whether qualified legal review is
required. `unreviewed` is fail-closed: the item may remain research context but
must not be labelled cleared, safe to adopt, or free to operate.

This catalog is an engineering provenance tool, not a legal opinion, patent
search, or freedom-to-operate determination.

### Validation

An offline `check_references` tool is proposed to validate schema version,
unique keys and claim IDs, dates, supported roles and states, work/version
links, exact-locator presence for promoted claims, quote word counts, rights
fields, source/annotation-type compatibility, patent-review status, hashes and
sizes, and references from tracked Markdown.

An optional networked `verify_references` tool may check DOI, arXiv, publisher
URLs, and correction/retraction notices before an RFC/ADR decision, EXP plan or
report, or public release. It emits reviewable differences and never rewrites
canonical metadata automatically.

### Draft migration

Start with the nine primary-source links already present in the T-0052
Experience-generalization and RFC-0001 industry-prior-art reviews. The initial
catalog intentionally records missing authors, versions, exact paper locators,
rights, and correction status as unverified. Existing memo prose supplies only
clearly labelled Raveil-authored draft synopses; it is not promoted to verified
source-level claim cards until the primary versions are checked.

Apply locator-backed claim cards prospectively to new or materially revised
ADR/RFC/EXP records. Do not mechanically rewrite all historical records.

## Alternatives

- Markdown-only bibliography: easy to edit but weak for uniqueness, version,
  rights, and link validation.
- BibTeX alone: useful for conventional papers but insufficient for vendor
  whitepapers, talks, correction state, access class, and claim cards.
- YAML: readable, but it introduces a parser dependency in the current
  standard-library-only validation path.
- Commit all PDFs: rejected because access does not imply redistribution rights
  and repository history makes later removal incomplete.
- Reuse sealed experiment bundles: rejected because experimental evidence and
  third-party literature have different authority, rights, and retention
  boundaries.
- Copy publisher abstracts: rejected as the default; stable locators plus
  original Raveil paraphrase are sufficient for the proposed workflow.

## Safety and authority boundaries

Literature can motivate a hypothesis, define prior art, or provide a comparison
method. It cannot demonstrate Raveil implementation, performance, safety,
reproducibility, or Gate completion. Researcher and Librarian output remains
advice. The Project Manager owns canonical integration, but an accepted ADR or
sealed EXP is still required for decisions and measurements.

Retractions, corrections, unavailable sources, and contradictory evidence are
preserved. A hash proves byte identity only; it does not prove a correct
version, legal possession, source truth, or applicability to Raveil.

## Experiments required

No performance experiment is required to evaluate the metadata workflow. A
small documentation pilot should migrate the existing nine sources, exercise
one source with multiple versions, one vendor page without a stable revision,
one corrected or retracted-state transition, and one claim-card audit before
the schema or workflow is accepted.

## Open questions

- Which exact fields and enum values survive the documentation pilot?
- Should claim cards live inside the catalog, in per-work annotation files, or
  only in dated research memos with catalog back-links?
- What evidence is sufficient for a redistribution-rights assessment?
- Which changes require a qualified patent or freedom-to-operate review, and
  who may record a status beyond `unreviewed`?
- Which controlled external store, operator, retention period, and access audit
  apply when contractual storage is permitted?
- Which registries are consulted for corrections and retractions, and at what
  review milestones?
- How are exact locators normalized for HTML pages, videos, datasets, standards,
  and software releases?
- Should offline validation join `scripts/ci-local.sh`, the record checker, or
  remain a separate command until the draft schema stabilizes?
