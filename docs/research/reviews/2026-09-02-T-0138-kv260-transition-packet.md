# T-0138 KV260 transition feasibility packet

Status: completed planning packet; implementation not authorized

Date: 2026-09-02

RFC slice: RFC-0004/S01

Evidence class: planning

## Outcome

The smallest credible board path is feasible enough to prepare, but it is not
yet ready for FPGA implementation.  The tentative reference configuration is:

- AMD Kria KV260 starter kit, with the carrier revision recorded before use;
- the vendor-neutral T-0132/S07 `GraphDeviceAxi4LiteTop` RTL export as the only
  Raveil hardware input;
- Vivado ML Standard 2025.1 on a supported Windows 11 x86-64 host;
- a 32-bit PS-to-PL AXI master path to one 16 KiB AXI4-Lite slave window;
- one PS-derived PL clock and one reviewed active-low reset path;
- Ubuntu Server 24.04 LTS arm64 on microSD;
- Linux UIO map 0 at offset zero, with polling only and no IRQ, DMA, coherence,
  `/dev/mem`, kernel module, or XRT requirement; and
- an explicit future UIO transport on the same two-request operator semantics,
  shared admission and independent oracle used by `graph-device run-pair`.

This is a recommendation for the next bounded review, not an accepted board
design.  No absolute address, clock frequency, reset circuit, device-tree
`compatible` value, bitstream format, deployment command, or UIO binding is
assigned here.  Those values must be emitted by and checked against one exact
Vivado design and one exact target image.

Vivado 2025.1 is deliberately preferred over the current 2026.1 release for
this first prototype.  AMD states that 2025.1 ML Standard includes all Kria
devices and does not require a license.  AMD states that 2026.1 requires a
valid license before Vivado starts.  Moving to 2026.1 is therefore a separate
cost and entitlement decision, not a routine upgrade.

## Verified public facts

All links below were accessed on 2026-09-02.  They are references, not copied
source dependencies.

| Subject | Official source and revision | Fact used here | Status |
|---|---|---|---|
| Board and intended use | [AMD UG1089 summary](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Summary), rev. 1.4, 2025-06-25 | KV260 combines a non-production K26 SOM, carrier and thermal solution and is an evaluation platform. | verified |
| Included items | [AMD UG1089 box contents](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/What-s-in-the-Box), rev. 1.4 | The kit includes the SOM, thermal solution and carrier; PSU, SD card, peripherals and accessories are excluded. | verified |
| Power | [AMD UG1089 power](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Powering-the-Starter-Kit-and-Power-Budgets), rev. 1.4 | Required input is 12 V, 3 A, center-positive, 2.5 mm ID/5.5 mm OD; AMD lists CUI SMI36-12-V-P6. | verified |
| Physical access | [AMD UG1089 interfaces](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Interfaces), rev. 1.4 | Both carrier revisions expose microSD J11, 1 GbE J10, reset SW2 and integrated USB2 UART/JTAG J4. | verified |
| Initial boot | [AMD UG1089 software getting started](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Software-Getting-Started), rev. 1.4 | AMD directs users to write a starter Linux image to microSD, then power and boot Linux. | verified |
| Target OS | [Canonical Ubuntu for AMD](https://ubuntu.com/download/amd) | Ubuntu Server 24.04 LTS is a 64-bit image listed for KV260/KR260; Canonical also publishes a matching sysroot. | verified |
| Windows image writing | [AMD Kria SD-card preparation](https://xilinx.github.io/kria-apps-docs/kv260/2022.1/linux_boot/ubuntu_22_04/build/html/docs/sdcard.html) | AMD documents Raspberry Pi Imager on Windows, Linux and macOS.  The page is an older flow, so the current Canonical image identity must be recorded separately. | verified with revision caveat |
| Board design flow | [AMD UG1089 Vivado Board Flow](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Vivado-Board-Flow), rev. 1.4 | Vivado board flow supplies K26/KV260 board models, fixed-peripheral configuration and carrier awareness. | verified |
| Windows tool support | [AMD UG973 supported OSes](https://docs.amd.com/r/2025.1-English/ug973-vivado-release-notes-install-license/Supported-Operating-Systems), 2025.1, 2025-05-29 | Vivado 2025.1 supports Windows 11 23H2 and 24H2 on x86-64. | verified |
| 2025.1 device/license tier | [AMD UG973 supported devices](https://docs.amd.com/r/2025.1-English/ug973-vivado-release-notes-install-license/Supported-Devices), 2025.1 | ML Standard includes all Kria devices and does not require a license. | verified |
| 2026.1 license change | [AMD UG973 supported devices and features](https://docs.amd.com/r/en-US/ug973-vivado-release-notes-install-license/Supported-Devices-and-Features), 2026.1, 2026-06-23 | From 2026.1, Vivado uses subscription tiers and requires a valid license to launch. | verified |
| PS-to-PL control path | [AMD PG201 slave interfaces](https://docs.amd.com/r/en-US/pg201-zynq-ultrascale-plus-processing-system/Slave-Interface), v3.5, 2023-06-16 | `M_AXI_HPM0_LPD` and `M_AXI_HPM{0,1}_FPD` are PS masters for PL slaves. | verified |
| 32-bit control convention | [AMD UG1209 embedded design tutorial](https://docs.amd.com/r/en-US/ug1209-embedded-design-tutorial/Connecting-IP-Blocks-to-Create-a-Complete-System), 2026.1 | AMD uses 32-bit `M_AXI_HPM0_LPD` for control registers and requires address assignment in the Vivado Address Editor. | verified example, not a Raveil assignment |
| Dynamic PL package shape | [AMD UG1630 package layout](https://docs.amd.com/r/en-US/ug1630-kria-som-apps-developer-ubuntu/Package-File-System-Unpacking), rev. 1.0, 2023-08-11 | AMD's Ubuntu application layout can include a bitstream, DT overlay and `shell.json`; XCLBIN is optional and tied to XRT-based designs. | verified, exact 24.04 path unverified |
| Load/unload manager | [AMD UG1630 dfx-mgrd](https://docs.amd.com/r/en-US/ug1630-kria-som-apps-developer-ubuntu/dfx-mgrd), rev. 1.0 | `xmutil loadapp`/`unloadapp` call `dfx-mgrd`, which consumes a bitstream, DTBO and `shell.json`. | verified, exact 24.04 availability unverified |
| Custom platform outputs | [AMD XD101 custom Kria platform example](https://docs.amd.com/r/2024.1-English/Vitis-Tutorials-Vitis-Platform-Creation/Custom-Kria-SOM-Platform-Creation-Example), 2024.1 | AMD's custom KV260 example produces an XSA and PL DTBO and can load PL from Linux without rebuilding boot components. | verified example, version compatibility unverified |
| UIO binding | [Linux kernel UIO HOWTO](https://docs.kernel.org/driver-api/uio-howto.html) | A device-tree platform device using `uio_pdrv_genirq` needs an `of_id` module parameter matching its `compatible`; map metadata is exposed in sysfs and `/dev/uioX` is mmapped by userspace. | verified generic Linux behavior |
| Recovery | [AMD UG1089 reset and recovery](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Board-Reset-Firmware-Update-and-Recovery), rev. 1.4 | KV260 has Linux A/B update and Ethernet recovery mechanisms; the board also has a physical reset. | verified, Raveil procedure not yet tested |
| Vendor legal boundary | [AMD UG1089 legal notice](https://docs.amd.com/r/en-US/ug1089-kv260-starter-kit/Please-Read-Important-Legal-Notices) | AMD documentation is informational, subject to change, and does not grant Raveil legal clearance. | verified |

## Exact boundary mapping

| Raveil-owned boundary | Proposed board adapter | What must be frozen by the board task |
|---|---|---|
| `GraphDeviceAxi4LiteTop` raw RTL ports | Package the exported closure behind a Vivado-recognizable AXI4-Lite slave wrapper; do not alter the core. | Wrapper source hash, generated RTL manifest, top name and Vivado version. |
| `aclk` | One PS-derived PL clock shared by the AXI interconnect, wrapper and Raveil top. | Source pin, frequency, clock-domain proof and timing constraint.  No frequency is selected here. |
| active-low asynchronous `aresetn` | One reviewed reset synchronizer/controller driven from the selected PS/PL reset path. | Assertion/deassertion behavior, minimum pulse, reset order, load/unload behavior and recovery test. |
| 32-bit AXI4-Lite address/data and four strobes | A 32-bit PS HPM master through the minimum required interconnect to the Raveil slave. | Exact interface, interconnect blocks, protocol conversion, all connection automation output and source manifests. |
| relative `[0x0000,0x4000)` aperture | One naturally aligned 16 KiB segment assigned in the Vivado Address Editor. | Absolute base and inclusive/exclusive bounds from the XSA/address report.  The base must not enter a Raveil ABI. |
| maximum one outstanding request | Preserve the current target and polling runtime; do not add queues. | AXI protocol check and Linux ordering assumptions. |
| no interrupt port | Poll existing status registers from userspace. | DT node must contain no invented IRQ; UIO kernel configuration and binding must work without adding an IRQ contract. |
| Linux UIO map 0 | DT overlay creates one reviewed platform device and one exactly 0x4000-byte map. | `compatible`, `reg`, address/size cells, overlay hash, boot/load command, `/sys/class/uio/.../maps/map0/{addr,size}` and device major/minor. |
| S08 runtime request admission | Run the existing request-independent arm64 runner unchanged apart from deployment/build packaging. | Compiler/sysroot identity, executable hash, filesystem owner/mode and exact request roots. |
| S10 operator semantics and oracle | The current `run-pair` implementation is simulator-only.  A later explicit UIO transport must preserve the same two Graph/seed pairs, admission and independent outputs/oracles without pretending the simulator command ran hardware. | One bitstream/DTBO/XSA/RTL/runtime identity chain, explicit transport label and byte-equal outputs; label only FPGA functional evidence. |

The wrapper may adapt Vivado interface naming and reset plumbing.  It may not
change register meanings, Graph catalogue, opcodes, request schema, authority,
or output publication semantics.  If Vivado cannot consume the exported RTL
without a semantic edit to the core, the board task is No-Go and returns to
simulation.

## Work split

### Physical owner

The human operator owns every action that accepts a license, changes the
Windows machine, powers hardware, or changes removable/non-volatile media:

1. Report the exact Windows edition, release and x86-64 status.  Windows 11
   23H2 or 24H2 is the currently verified Vivado 2025.1 path.
2. Acquire or inventory the KV260, its carrier revision, a compliant 12 V/3 A
   PSU, microSD, a data-capable USB cable for J4, and Ethernet.  Do not publish
   serial numbers or account data.
3. Download the exact Ubuntu Server 24.04 KV260 image through Canonical, record
   its filename and published digest, and flash it with Raspberry Pi Imager.
4. Boot with UART visible, capture the board model, kernel, image/package
   versions, free storage and recovery state, and confirm SSH access.
5. Review and personally accept any AMD/Xilinx installer and tool EULAs.  An
   agent must not click through them or use the operator's credentials.
6. Install Vivado ML Standard 2025.1 with K26/KV260 device and board support
   only after the host-version and storage checks pass.
7. Run the eventual signed-off programming/load, reset, unload and recovery
   procedure while retaining the raw terminal transcript.

### Jitro and repository agents

Agents may proceed without another acknowledgement only within an approved,
non-incident task packet:

1. Re-export and verify the current T-0132/S07 RTL bundle from the exact main
   revision; never reconstruct it from an old T-0112 branch.
2. Draft a repository-owned thin AXI wrapper and batch-mode Vivado project only
   after a new ADR-0039 Project Manager/legal disposition authorizes the board
   slice.
3. Make every generated output disposable and bind Vivado version, board file,
   Tcl, wrapper, source RTL, XSA, bitstream, DTBO and address report hashes.
4. Generate, but do not silently deploy, a minimal overlay for the exact 16 KiB
   segment and validate it before presenting the operator command.
5. Build the unchanged Linux runner either on the board or from the published
   Canonical sysroot, then verify executable identity on target.
6. Supply one scripted preflight, one load/unload/recovery script and one
   explicitly UIO-backed two-request command with S10-equivalent semantics.
   Fail before device access on any identity drift.
7. Store only non-sensitive evidence.  Account tokens, serial numbers, absolute
   home paths and accepted-license files stay outside the repository.

## Go/No-Go checks for the implementation task

The next board task is Ready only when checks 1--7 have evidence.  FPGA
functional promotion additionally requires checks 8--12.

1. **Board identity:** KV260 and carrier revision are known; supply, cooling,
   microSD, USB UART/JTAG and Ethernet are inventoried.
2. **Host support:** the Windows release is supported by Vivado 2025.1 and the
   host has sufficient local resources.  Otherwise No-Go pending a supported
   host; do not upgrade to 2026.1 implicitly.
3. **License:** the operator has accepted the applicable 2025.1 EULAs and ML
   Standard/Kria availability is confirmed.  Any 2026.1 use requires a
   separately recorded entitlement/cost decision.
4. **Boot baseline:** the exact Ubuntu 24.04 image and digest are recorded, the
   board boots, UART and SSH work, and recovery instructions are accessible.
5. **Target capability:** installed kernel/package evidence shows an available
   FPGA manager/deployment path and a usable UIO configuration.  An older
   tutorial is not enough.
6. **Source boundary:** S07 export verifies from current main and all vendor
   board files or scripts have source, revision, license and notice metadata.
7. **Authority:** Project Manager and qualified legal review explicitly permit
   the exact board wrapper/tool inputs under ADR-0039.  This packet is not that
   permission.
8. **Design closure:** batch Vivado synthesis, implementation and bitstream
   generation complete with no unreviewed source substitution; reports are
   retained but are not yet performance claims.
9. **Address/reset closure:** XSA/address report proves one aligned 16 KiB
   segment; clock/reset and load/unload sequences pass bounded tests.
10. **Linux closure:** DTBO identity matches the bitstream design and sysfs
    exposes exactly one 0x4000-byte UIO map at the recorded base.
11. **Functional closure:** the two S10 requests complete on one loaded design,
    both outputs are byte-equal to their independent oracles, and malformed
    admission fails before MMIO.
12. **Recovery closure:** unload/reload and one controlled reset return to a
    known state without publishing stale output.  Failed attempts remain
    evidence.

Any missing item is `pause` or `No-Go`, never permission to weaken the existing
contract.  Timing closure, utilization, latency, throughput, energy and CPU
comparison require separately preregistered experiments after functional
closure.

## Open gaps retained

- The physical owner's exact Windows release, machine resources and installed
  AMD tools are unknown.
- No KV260 carrier revision, inventory or board access is recorded.
- Ubuntu 24.04's exact `fpga-manager-xlnx`, `dfx-mgrd`/`xmutil` and
  `uio_pdrv_genirq` availability has not been observed on the target.
- The exact deployment route for a non-XRT Raveil bitstream on the current
  Ubuntu image is unselected.  The older UG1630 application package and XD101
  custom-platform flow are candidates, not authority.
- The absolute address, PL clock frequency, reset controller, device-tree
  `compatible`, bitstream/DTBO identities and recovery commands are unassigned.
- No official source currently proves that the emitted raw SystemVerilog is
  synthesizable as-is in Vivado; only the board task can test that.
- External board files, vendor scripts and generated tool output still require
  exact license/notice and provenance review before reuse or publication.

## Non-claims

This packet records planning evidence only.  It does not claim a working
KV260, FPGA execution, Linux UIO success, synthesis, timing closure, resource
fit, speed, energy, commercial readiness, production suitability, novelty,
patentability, non-infringement, freedom to operate, ASIC behavior or silicon
behavior.
