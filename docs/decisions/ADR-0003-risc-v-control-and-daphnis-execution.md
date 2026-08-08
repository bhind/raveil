# ADR-0003: RISC-V control/fallback plus Daphnis execution

Status: Accepted
Date: 2026-08-07

## Context

Forcing boot, exceptions, irregular control, and all memory behavior into a
graph fabric is impractical. Conversely, a sequential load/store ISA can force
hardware to rediscover known dependencies in structured repeated work.

## Decision

Retain RISC-V permanently for boot, control, admission, capabilities, recovery,
trusted baseline, cold code, and irregular dynamic work. Connect Daphnis as an
implementation plane through owned object/job/completion contracts.

RISC-V does not define Daphnis-native machine code. Daphnis is not fixed to
classic VLIW, and total OoO elimination is not claimed. Static, elastic, stream,
and hybrid organizations remain measurement choices.

## Consequences

Dynamic islands and fallback are first-class. The control core's OoO size and
the native Daphnis contract remain unresolved.
