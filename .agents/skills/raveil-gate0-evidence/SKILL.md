---
name: raveil-gate0-evidence
description: Collect and record Sonatine Gate 0 build, QEMU smoke, debug-symbol, or GDB evidence for EXP-0002. Use when working on T-0001, T-0006, T-0007, T-0008, the RV64 Makefile, or the native macOS/Homebrew Sonatine verification path.
---

# Raveil Gate 0 Evidence

1. Read `docs/guides/SONATINE_MACOS_DEBUGGING.md`, `docs/STATUS.md`,
   `TODO.md`, `docs/ROADMAP.md`, `docs/experiments/EXP-0002-*.md`, and the
   Sonatine Makefile/source relevant to the check.
2. Record platform identity, Git revision, exact tool paths and versions, every
   build/smoke/GDB command, exit status, and the complete raw console log with
   a stable path or hash.
3. For a debug build, keep release flags intact and verify that both
   `.debug_info` and `.debug_line` are present. For GDB, establish the
   command-line remote session and a `kmain` breakpoint before making an
   IDE-attachment claim.
4. Map evidence separately to T-0001 (Docker smoke), T-0006 (debug symbols),
   T-0007 (actual IntelliJ configuration), and T-0008 (native Homebrew build and
   smoke). Update only tasks whose acceptance evidence was actually collected.
5. Update EXP-0002, STATUS, TODO, ROADMAP, and the dated log only with what was
   actually run. Label native QEMU/emulation evidence separately from
   analytical, FPGA, and silicon results.
6. Leave generated build products and local logs ignored. State explicitly
   whether Docker reproduction, clean-clone reproduction, and IDE-driven GDB
   attachment remain unverified.
