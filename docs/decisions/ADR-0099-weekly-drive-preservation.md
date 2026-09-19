# ADR-0099: Batch ordinary Drive preservation weekly

Status: Accepted
Date: 2026-09-19

## Context

The owner requested Drive saves approximately once weekly and resumed delivery.
Temporary evidence loss still requires immediate persistent local retention.

## Decision

PM batches pending bundles once weekly, normally before Saturday Sprint Review
(Asia/Tokyo), not after each run or task. No new bundles means no transfer.
The successful 2026-09-19 batch covers the current week. Exceptions require
explicit owner direction, not automatic per-task upload.

Every run still saves evidence immediately in persistent ignored local storage
and verifies identities. Label pending bundles local-only. Keep immutable copy,
download verification and marker-last completion; never sync-delete or amend
old bundles. Authentication failures leave the batch pending. Do not delete
local evidence after transfer merely because remote verification succeeded.

Independent delivery and technical review continue between batches. Research
promotion that requires remote durability waits for successful verification.
ADR-0009 and ADR-0050 integrity and promotion requirements are unchanged;
this decision clarifies timing only. No background scheduler is installed:
the existing weekly Sprint operating loop owns execution and its receipt.

## Consequences

Fewer transfer/authentication interruptions, with approximately a week of
local-only exposure. Local disk failure can lose pending evidence; this is
not remotely durable evidence until the weekly batch is verified.
