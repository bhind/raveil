# T-0203: A single-board path with zero initial incremental spend

Date: 2026-09-27. Issue276. ADR-0105. Evidence: planning, host-functional tests,
and reproducible RTL generation only; no FPGA execution or performance result.

## Scope correction

The unstarted T-0203 SHIP-only proposal is superseded by the owner's explicit
hardware/budget direction. Its private draft remains provenance, not adopted
architecture. Earlier Project registration was automatically rejected for
unclear authority. The later explicit direction and budget facts permitted the
revised packet and normal queue registration. No rejected operation was bypassed.

## Reuse and missing work

| Existing and checked | Still missing |
|---|---|
| Owned GraphDeviceAxi4LiteTop, source-bound export, 16-KiB ABI | One board wrapper, PS/PL wiring, clock/reset, constraints, address report |
| Linux UIO runner, admission, independent oracle, no-open KV260 preflight | Vivado synthesis/implementation, XSA, bitstream, matching DT overlay |
| Reproducible export and host-fixture tests | Board ownership, boot, deployment/recovery, real two-request execution |

Preflight cannot prove the design before it exists: its UIO check runs after
a matching overlay exposes the device. Do not require a UIO device merely to
begin host inventory or design preparation. Likewise a host-fixture success is
not a board success. Current editable simulation operations exceed the sealed
UIO contract; do not promise all of them on the first board image.

ADR-0105 explicitly remaps T-0138's authority/check sequence: checks1–6 are
retained at the stage where they can actually be observed, scoped PM authority
for check7 is supplied without waiving provenance or targeted legal review,
and checks8–12 still govern real design/functional/recovery acceptance.

## Cost and host decision

Owner facts: MacBook and Windows PC only; no FPGA; monthly spending room is
described as a few tens of thousands of yen, with Codex already USD100/month.
The exact remaining hardware budget is unknown. Spend zero now; do not treat
recurring software expense as permission for another subscription or assume
this month's money can cover a kit.

On September27, [DigiKey Japan's SK-KV260-G listing](https://www.digikey.jp/ja/products/detail/amd/SK-KV260-G/13985269)
shows JPY47,224 excluding tax / JPY51,946.40 including tax. This is a reference
listing, not a reserved quote or an order. PSU, microSD and data cables are
additional; use a provisional JPY60,000–70,000 all-in planning envelope,
excluding a new PC, instrument and shipping variations. That envelope is an
estimate, not an approved budget. Buying over a savings period or borrowing is
preferable to creating recurring charges. Defer power instrumentation until
latency/function measurements justify it.

[AMD UG973 2025.1 supported devices](https://docs.amd.com/r/2025.1-English/ug973-vivado-release-notes-install-license/Supported-Devices)
includes Kria in ML Standard and states no Standard license is required.
[Its supported OS list](https://docs.amd.com/r/2025.1-English/ug973-vivado-release-notes-install-license/Supported-Operating-Systems)
requires x86-64 and includes Windows11 23H2/24H2 and specified Linux versions.
Therefore reuse the Windows PC if its actual version/resources qualify; the
observed Mac is Darwin arm64 and is not the native Vivado target. No tool
installation/EULA or upgrade is inferred. Retain 2025.1 as the bounded candidate;
verify storage/RAM for the exact K26 design before installation.

KV260 is provisionally favored for integration effort, not because it is the
cheapest FPGA. A cheaper bare FPGA would need a different host transport and
possibly a different toolchain, so unit price alone is insufficient. No board
is selected irreversibly until budget, tool availability and source fit are known.

## First outcome and measurement path

1. Current owned RTL export and host validation, with no purchase.
2. T-0188/#194 host inventory: Windows release, architecture, RAM/free disk,
   existing tools; actual board/accessory and target observations stay pending.
3. T-0189/#195 exact design preparation, vendor closure and deployment packet;
   then one reviewed board acquisition and owner-run functional bring-up.
4. One loaded image executes the admitted two-request pair and recovery; extend
   to three genuinely different supported graphs before a generality claim.
5. A separate frozen experiment measures an optimized C CPU baseline, FPGA
   core cycles, staging/installation and complete latency across reuse counts.
   Include failures, jitter, resource utilization and clock closure. Expand
   workload size only through a reviewed contract change. Do not report a
   tiny bring-up fixture as proof of useful application acceleration.

The first application target is repeated bounded sensor/image integer
processing. Actual representative input provenance and a practical output
requirement remain to be pinned before performance comparison. Full LLM serving,
affine F16 optimization, custom ISA and multi-board scaling are not prerequisites.

Compare the same work and precision on the board CPU and FPGA; a host Mac
comparison is a separately labelled system experiment. CPU code must be compiled
and reasonably optimized, not Python-oracle execution used as a weak baseline.
Count both cold and reuse cases; keep transfer/validation cost visible. A loss
identifies the next engineering bottleneck rather than invalidating the prototype.

## Verified prerequisite refresh

At source main1c8e24d on macOS26.6.2 arm64/Python3.14.6, sixteen existing tests
passed across kv260_preflight, graph_device_axi4lite_export and
graph_device_dynamic_uio. Expected negative child processes printed admission
errors; the suite returned0. These are host fixtures, not FPGA runs.

The existing cached linux/amd64 image
`sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c`
ran offline under the local Docker host. The export script generated RTL twice,
required identical manifests, finalized it and verified it again. Source hash:
`cd75644eec01c145d80c710efc2b08434105ea007729950a08ef4a191ab7e366`.
RTL manifest hash:
`0af26da2283283b7ab58a7d09f28807ccac2c4e42fc7d3d08708f3dc5a524627`.
Export log hash:
`05f69bc222bd2791c8c3527db60d49be7e612cad1f459c79fa241e18d0e82257`.

Raw bundle/log: ignored `artifacts/research/T-0203/axi-rtl` and `export.log`
in the clean task clone. The receipt deliberately says board/base unassigned
and performance not measured. This does not prove Vivado synthesis or fit.

## Successor ownership

Reuse the real existing T-0188/#194 and T-0189/#195 items rather than creating
duplicate board tasks. Their earlier authority checklists require an ADR-0105
addendum and staged acceptance: host-only progress is useful while a board is
unowned. The immediate next deliverable is a safe Windows inventory command
and a source-bound handoff for vendor synthesis; no paid resource is needed.

## No-install Windows inventory for T-0188

Run in an ordinary PowerShell terminal on the existing Windows PC. This reads
OS/resources and discovers an existing Vivado command; it installs nothing and
collects no serial, user, account or machine-name fields. A missing Vivado is
normal. Do not paste unrelated terminal output or license files.

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID,Size,FreeSpace
Get-Command vivado -ErrorAction SilentlyContinue | Select-Object Name
```

Exact K26 resource needs remain to be checked against the selected tool and
design; this command does not certify host readiness. It is supplied but has
not been run on the Windows machine in this session.
