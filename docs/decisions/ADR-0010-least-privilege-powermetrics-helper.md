# ADR-0010: Gate 1 uses a least-privilege powermetrics helper

Status: Accepted
Date: 2026-08-08

## Context

The full fixed-C manifest has 3,600 candidate measurements. Direct
`powermetrics` requires superuser privilege, while an interactive `sudo -v`
step prevents unattended execution and couples the run to a terminal ticket.
Running Python or the benchmark as root would enlarge the trusted boundary and
allow repository-controlled code to execute with system authority.

## Decision

Raveil invokes `sudo -n /usr/local/libexec/raveil-powermetrics`. The installed
helper is a reviewed, root-owned C binary. It accepts only sample rate 20..1000
ms and sample count 1 or -1, clears the environment, fixes all powermetrics
samplers and output arguments, and directly executes
`/usr/bin/powermetrics`. It contains no shell or general command facility.

A narrowly scoped sudoers entry grants `NOPASSWD` only to that helper. Python,
native C candidates, compilation, analysis, bundle handling, rclone, and Git
remain under the ordinary user. Raveil fails closed if the helper is missing,
user-writable, unauthorized, returns invalid telemetry, or cannot satisfy the
thermal/sample contract.

Each environment signature records helper version and installed-binary
SHA-256. Each energy bundle preserves the reviewed helper source. A standalone
manifest-aware preflight verifies the boundary without creating a RUN-ID.

## Rejected alternatives

- Run the experiment as root: rejects the authority boundary.
- Grant `NOPASSWD` directly to unrestricted powermetrics: allows options beyond
  the registered measurement contract.
- Use a setuid helper: creates a broader, harder-to-audit privilege mechanism.
- Use MetricKit: its aggregated reporting is not candidate-window energy
  evidence.
- Drop energy measurement: cannot satisfy Gate 1.

## Consequences

One reviewed installation and sudoers edit still require administrator
authority. Thereafter, preflight and full runs can execute without a password
or cached sudo ticket. Updating the helper requires a new reviewed source
version, binary reinstall, and environment-signature hash; it must never be
updated in place during a run.
