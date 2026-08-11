# ADR-0036: Command graphs compile a bounded shell subset before general shell compatibility

Status: Accepted
Date: 2026-08-11

## Context

T-0099 makes the Native CLI usable inside one workspace, but its filesystem
commands and existing GEMM graph loop are separate. Merely launching the GEMM
microbenchmark from a shell does not evaluate whether graph compilation and
execution help ordinary host work. Conversely, accepting arbitrary shell text
would introduce ambient executables, expansion, mutation, and authority before
T-0100 provides an enforceable sandbox.

## Options considered

- retain the workspace shell only and benchmark the existing GEMM graph;
- pass arbitrary input to the host shell and infer a graph from observation;
- define an owned safe shell subset, compile it to a versioned command DAG,
  and compare baseline and graph execution on preregistered workloads.

## Decision

T-0101 takes the third option. It adds a separate `CommandGraphProgram`
lineage rather than pretending tensor `GraphProgram` nodes are shell
processes. A parser accepts documented built-ins and allowlisted OSS
file-processing tools with explicit arguments, pipelines, guarded sequencing,
bounded redirection, and independent fan-out. It emits nodes, typed file or
stream dependencies, declared reads and writes, and deterministic identities.
The executor invokes tools with direct argv and a controlled environment; it
never uses `shell=True`.

Every benchmark runs an equivalent direct baseline first, verifies stdout,
declared output hashes, exit status, and failure propagation, and only then
compares graph construction, execution-only, and end-to-end timing under
EXP-0004. Sequential, pipeline, and parallel-fan-out workloads remain distinct.
Graph scheduling may not claim a win against a deliberately weaker baseline;
the exact baseline semantics and concurrency must be reported.

## Rationale

This makes Graph Compiler and Executor behavior visible in work a normal user
recognizes while preserving bounded authority and falsifiable comparison. It
also exposes graph overhead and negative results instead of presuming that
small commands benefit.

## Consequences

T-0101 is not a POSIX shell, GNU compatibility layer, or hostile-code sandbox.
No arbitrary executable lookup, command substitution, ambient environment,
globbing, append, background jobs, interactive programs, or network tools enter
the first slice. Existing GEMM graph schemas and validation remain unchanged.
Additional tools or grammar require explicit tests and authority review.

The executable v1 grammar uses `|||` as an owned bounded join-fanout operator:
independent branches share the same maximum concurrency and a following `&&`
node depends on every branch. It is deliberately not POSIX `&` backgrounding.
The graph records sanitized `system://` tool locators plus binary hashes and
keeps host absolute executable paths private to the runtime adapter.

## Verification and supersession

Acceptance requires parser rejection tests, exact baseline/graph differential
tests, node-failure and rollback tests, deterministic artifact round trips, a
human CLI transcript, and EXP-0004 raw evidence. A future general shell or
untrusted-workload boundary must supersede this ADR rather than silently widen
the allowlist.
