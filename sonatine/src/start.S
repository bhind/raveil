.section .text.init
.align 2
.global _start
_start:
  /* QEMU passes hartid in a0. v0 keeps exactly one authority hart. */
  bnez a0, .Lpark
  la sp, __boot_stack_top
  la t0, __bss_start
  la t1, __bss_end
.Lbss:
  bgeu t0, t1, .Lbss_done
  sd zero, 0(t0)
  addi t0, t0, 8
  j .Lbss
.Lbss_done:
  call kmain

.Lpark:
  wfi
  j .Lpark

.section .bss.stack,"aw",@nobits
.align 12
.global __boot_stack_bottom
__boot_stack_bottom:
  .space 16384
.global __boot_stack_top
__boot_stack_top:
