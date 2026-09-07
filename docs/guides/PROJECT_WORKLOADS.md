# Project workload examples

Status: T-0177 host-functional examples

These repository-authored fixtures exercise the existing bounded Command
Graph through the normal project workspace. They contain synthetic data only.
Copy a fixture before running it so the repository remains unchanged:

```sh
cp -R examples/project-workloads/log-summary /tmp/raveil-log-summary
mkdir /tmp/raveil-log-summary/runs
python3 -m raveil project show log-summary --project /tmp/raveil-log-summary
python3 -m raveil project run log-summary --project /tmp/raveil-log-summary --backend native

cp -R examples/project-workloads/duplicate-inventory /tmp/raveil-duplicate-inventory
mkdir /tmp/raveil-duplicate-inventory/runs
python3 -m raveil project run duplicate-inventory \
  --project /tmp/raveil-duplicate-inventory --backend native
```

`log-summary` selects and sorts ERROR lines. Its expected result is
`expected/errors.txt`. Add an ERROR line to `inputs/events.log`, run it again,
and compare the two IDs with `project diff`; the first run retains its original
input and output snapshot.

`duplicate-inventory` sorts a small inventory and removes duplicate lines. Its
expected result is `expected/unique.txt`. This is an inventory normalization
example, not a claim about filesystem discovery or general data processing.

For the failure path, run `missing-input` in the copied log project. The absent
`inputs/missing.log` produces a retained failed run with no published output.
The fixtures add no tools, grammar, executor behavior, project schema, init
sample, customer data, performance evidence, isolation, or hardware support.
