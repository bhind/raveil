# T-0191 OpenASIP feasibility spike

This directory is an experiment-private adapter scaffold for exact OpenASIP
v2.2. It does not vendor OpenASIP or grant it Raveil execution, effect, or
publication authority.

## Cancellation request

The authorized simulator entrypoint accepts `--cancel-file PATH`. Create that
file to request cancellation; once observed, the request is latched for the
invocation even if the file is removed. Use a separate path for each run.
This is an operator control for the local experiment, not multi-user isolation.
The existing `--cancel-before-start` option remains available.

An interrupted candidate must not publish results or invoke CPU fallback.
If owned-process cleanup cannot be verified, the lifecycle returns an
unpublished failure instead of reporting successful cancellation. Do not infer
Docker/compiler/simulator termination from the absence of a result alone.
If Docker create fails before returning a valid ID, ownership is uncertain.
The runner denies publication and leaves reconciliation to the operator; it
does not remove a container by guessed or generated name. An orphaned container
may remain in this error case.

### Cleanup and retry

After a successful cancellation witness, no cleanup is necessary: the checker
has verified absence of its exact owned container. Preserve every evidence
directory, including failed attempts. Retry with a new nonexistent evidence
directory and a new cancellation-file path; never reuse a sealed directory.

If creation returned no verified ID, do not delete by name or run Docker prune.
Use `docker ps -a --no-trunc` for read-only inventory, then
`docker inspect <full-container-id>` for a suspected container. Names alone
are not ownership evidence. Correlate image, creation time, command and mounts
with the failed invocation. If ownership cannot be established, retain the
container and escalate to the operator; no automatic removal or retry is safe.
Only after the operator confirms the exact full ID belongs to this invocation,
use `docker stop --time 2 <full-container-id>` and
`docker rm <full-container-id>`, then verify absence with
`docker container ls -aq --no-trunc --filter id=<full-container-id>`.
Never target other containers. Resume the explicit simulate command with a new
evidence directory only after uncertainty is resolved.

For an ordinary failed run whose owned-container cleanup succeeded, retry:

```sh
sh experiments/openasip/run_three_programs.sh --simulate --evidence-dir <new-persistent-directory>
python3 experiments/openasip/verify_evidence.py run <new-persistent-directory>
```

An accepted CPU fallback is not simulator success: require backend
`openasip-ttasim` and strict evidence verification for this feasibility task.

Reproduce the bounded real-process cancellation checks with the existing pinned
image (no image build or pull):

```sh
python3 experiments/openasip/check_cancellation.py oacc
python3 experiments/openasip/check_cancellation.py ttasim
```

The witness observes a numeric PID plus target executable before requesting
cancellation, checks the unpublished receipt and container absence, and
excludes ttasim's load-only probe. It verifies process lifecycle only, not
simulated instruction progress or performance. Missing observation is a failure.

The first boundary is `./run_three_programs.sh --preflight`. It performs only
static identity and independent-oracle calculations: it does not compile or
execute the C inputs and does not start Docker. The separate explicit
`--host-check` path compiles and executes the three sealed, bounded C inputs
with a cleared environment. The pinned Linux image and hardened explicit
`--simulate` path are present. The default command remains fail-closed.
Simulator output begins unpublished; `lifecycle.py` owns oracle admission,
cancellation, fallback and publication. Its public accepted receipts are fixed
projections of reviewed results plus a canonical private-receipt SHA-256; raw
argv, host paths, platform identity and arbitrary candidate fields remain
private. An optional private evidence directory
retains TPEFs, disassembly and raw logs with a marker-last receipt.
`verify_evidence.py` rehashes the exact run or RTL file set and rejects missing,
extra, symlinked, corrupted or authority-inconsistent evidence.
`generate_rtl.py --output DIR` separately generates and seals the exact
fixed-ADF VHDL tree. It records raw and timestamp-normalized identities because
OpenASIP writes generated-on comments into two RF files. Its host duration is a
diagnostic configuration-tool observation, not a device or PPA result.

The three C inputs deliberately differ in operation topology and memory use:

- `neighborhood.c` reads a two-dimensional cross neighbourhood;
- `elementwise.c` performs independent multiply/add chains; and
- `reduction.c` folds an array through one accumulator.

`oracle.py` is an independent Python calculation of the three expected
unsigned-32 result words. These sources are Raveil-owned test inputs. OpenASIP
source and binaries remain outside the repository.

Evidence from this directory is Host Functional external-simulator evidence
only. It is not RTL, FPGA, ASIC, silicon, performance, patent/FTO, adoption, or
T-0044 gate evidence.
