# ADR-0001: Four-plane adaptive Harvard model

Status: Accepted
Date: 2026-08-07

## Context

AI-generated optimization makes normal code/data separation insufficient.
Immutable meaning, installed graph configuration, mutable objects, and learned
history require different write authorities.

## Decision

Separate Program, Graph, Data, and Experience planes. Program contains admitted
semantics and fallback. Graph contains only sealed variants and memory plans.
Data is writable but never executable. Experience accepts restricted
measurement and policy evidence. AI may propose but writes no plane directly.

## Consequences

Sonatine must enforce distinct capabilities and installation paths. Contracts
must identify all four planes. Four-plane hardware enforcement is intended
architecture and is not present in the minimal seed.
