# ADR-0014: Vreji triages prior-art similarity and IP risk

Status: Accepted
Date: 2026-08-09

## Context

Raveil needs an explicit owner for detecting similarity to published work and
for keeping copyright, license, confidentiality, patent, and standards-related
risk visible before external mechanisms influence implementation. The
Librarian role is named Vreji. Treating Vreji as legal counsel or giving it
authority to clear an implementation would be unsafe; leaving the work
unassigned would allow prior-art and IP checks to disappear between research
and implementation.

## Options considered

- Let each implementer perform informal source checks.
- Give Vreji authority to approve use of external mechanisms.
- Make Vreji the read-only inventory and escalation owner while the Project
  Manager owns canonical integration and qualified experts own legal opinions.

## Decision

Vreji, the read-only Raveil Librarian, owns prior-art and IP-risk triage:

- identify similar mechanisms, claims, terminology, interfaces, and published
  implementations relevant to a proposed Raveil change;
- prefer primary papers, patent publications and official registries,
  standards/licensing notices, and official vendor material over summaries;
- record exact source/version/locator, jurisdictions when known, patent-family
  or standards references when found, rights/access state, and uncertainty;
- distinguish copyright and storage permission from patent licensing and
  freedom to operate;
- preserve contradictory sources, expired or abandoned status only when
  verified, and all `unreviewed` gaps;
- return similarity findings, adoption hazards, missing searches, and a clear
  escalation recommendation to the Project Manager before a related mechanism
  is promoted into an implementation proposal.

Vreji remains read-only. It does not edit canonical records, determine
infringement, issue a legal opinion, declare freedom to operate, approve an
implementation, allocate IDs, accept decisions, conclude experiments, or
change a Gate. `unreviewed` fails closed for claims of clearance, not for
cataloguing or independent clean-room research.

The Project Manager owns repository integration and blocks a material external
mechanism from being labelled cleared until the required technical and, where
appropriate, qualified legal review is recorded. This ADR does not itself
authorize copying source material or implementing any external claim.

## Rationale

Vreji already owns minimal context routing and source disambiguation. Extending
that read-only packet with similarity and IP-risk fields keeps provenance near
source selection without confusing advice with project or legal authority.
Fail-closed escalation is safer than either silent reuse or an automated legal
conclusion.

## Consequences

- Vreji reports a `prior-art/IP` section when external mechanisms, novelty,
  patents, vendor designs, standards, or source reuse are in scope.
- RFC-0003 and its draft catalog can represent these findings, but remain
  Proposed beyond the narrow role boundary accepted here.
- Implementers and Researchers must not interpret a public document, citation,
  expired-looking record, open-source license, or absent search result as an
  implementation license or freedom-to-operate conclusion.
- Legal uncertainty may block a claim of clearance or require redesign, legal
  review, or a clean-room boundary; Vreji only recommends that escalation.

## Verification and supersession

The Vreji agent definition, context-librarian skill, WORKFLOW role description,
and RFC-0003 handoff must preserve the same read-only and non-legal boundary.
A later decision that changes ownership or grants any approval authority must
supersede this ADR.
