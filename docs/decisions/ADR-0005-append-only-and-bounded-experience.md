# ADR-0005: Append-only evidence plus bounded online Experience

Status: Accepted
Date: 2026-08-07

## Context

Scanning an unbounded history online cannot scale. Compressing all evidence into
model weights loses auditability, rare failures, lineage, and decision
boundaries.

## Decision

Retain immutable append-only cold evidence while limiting the Experience that
participates in online retrieval. Consolidation must preserve useful tails,
negative transfer, ranking reversals, uncertainty, and lineage rather than only
average cases.

## Consequences

Cold storage can grow independently of hot-path cost. Consolidation and aging
remain research questions. The current JSONL plus bounded Python list is a
baseline, not the final database or retrieval system.
