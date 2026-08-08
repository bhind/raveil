---
name: raveil-context-librarian
description: Build the smallest authoritative Raveil reading packet for a task before implementation or review. Use when a Raveil request is broad, unfamiliar, crosses code and project records, risks loading many Markdown files, or asks what context should be read first. Route by executable source-of-truth order and return precise paths, symbols, headings, and exclusions; do not decide facts or edit files.
---

# Raveil Context Librarian

Produce a reading packet, not a project summary.

## Route

1. Inspect `git status --short`, `AGENTS.md`, and the routing table in
   `docs/README.md`. Do not preload every linked record.
2. Run `python3 .agents/skills/raveil-context-librarian/scripts/route_context.py
   --query "<task terms>"` to rank likely files without injecting their full
   contents into context.
3. Inspect file headings, matching lines, executable symbols, and nearby tests.
   Read whole files only when they are short or their sections cannot be safely
   separated.
4. Apply the authority order: code/tests, STATUS, accepted ADRs, ARCHITECTURE,
   ROADMAP/TODO, logs. Ignore `docs/history/` and `docs/archive/` unless the task
   explicitly asks for provenance.
5. Return a packet with:
   - **must read**: path plus symbol/heading or narrow line span and why;
   - **read if triggered**: the condition that makes each item relevant;
   - **skip**: tempting but irrelevant records and why;
   - **record context**: likely T-ID, gate, ADR/RFC/EXP, labelled provisional;
   - **conflicts/gaps**: disagreements or missing authority for the primary to
     verify.

Keep the packet under 400 words unless the caller requests a deeper map. Never
make a gate decision, allocate an identifier, accept an ADR, conclude an EXP,
or substitute the packet for the primary agent's required source reads.

## Handoff boundary

The librarian is read-only. The primary agent reads the selected authoritative
sections itself before editing and owns task classification, integration,
verification, and record updates.
