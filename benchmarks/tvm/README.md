# Gate 1 Apache TVM environment

The Gate 1 adapter uses the official Apache TVM macOS arm64 wheel in an ignored,
isolated virtual environment. The tracked lock pins the TVM FFI ABI because the
package's open-ended lower bound otherwise selected a newer dylib that did not
export the symbol required by the TVM 0.25.0.post1 wheel.

```sh
RAVEIL_TVM_VENV=/absolute/path/outside/repository/raveil-tvm-venv
python3 -m venv "$RAVEIL_TVM_VENV"
"$RAVEIL_TVM_VENV/bin/python" -m pip install \
  --disable-pip-version-check -r benchmarks/tvm/requirements.lock
"$RAVEIL_TVM_VENV/bin/python" -c \
  'import tvm; print(tvm.__version__)'
```

Run TVM experiment commands with the repo-external venv's Python. The venv stays
outside the repository and generated MetaSchedule databases remain ignored
research artifacts; the sealed
run bundle records the resolved manifest, lock file, TVM version, schedules,
measurements, and hashes.

Primary upstream references: the Apache TVM
[installation guide](https://tvm.apache.org/docs/install/index.html),
[MetaSchedule documentation](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/meta_schedule.html),
and the official `apache-tvm` package published under Apache-2.0.
