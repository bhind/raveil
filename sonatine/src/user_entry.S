.section .text
.align 2
.global user_enter
user_enter:
  addi sp, sp, -128
  sd ra, 0(sp)
  sd s0, 8(sp)
  sd s1, 16(sp)
  sd s2, 24(sp)
  sd s3, 32(sp)
  sd s4, 40(sp)
  sd s5, 48(sp)
  sd s6, 56(sp)
  sd s7, 64(sp)
  sd s8, 72(sp)
  sd s9, 80(sp)
  sd s10, 88(sp)
  sd s11, 96(sp)
  sd gp, 104(sp)
  sd tp, 112(sp)
  csrw mscratch, sp
  csrw mepc, a0
  csrr t0, mstatus
  li t1, ~(3 << 11)
  and t0, t0, t1
  csrw mstatus, t0
  mv sp, a1
  mret
.global user_kernel_return
user_kernel_return:
  ld ra, 0(sp)
  ld s0, 8(sp)
  ld s1, 16(sp)
  ld s2, 24(sp)
  ld s3, 32(sp)
  ld s4, 40(sp)
  ld s5, 48(sp)
  ld s6, 56(sp)
  ld s7, 64(sp)
  ld s8, 72(sp)
  ld s9, 80(sp)
  ld s10, 88(sp)
  ld s11, 96(sp)
  ld gp, 104(sp)
  ld tp, 112(sp)
  addi sp, sp, 128
  ret

.align 2
.global user_trap_entry
user_trap_entry:
  csrrw sp, mscratch, sp
  addi sp, sp, -32
  sd ra, 0(sp)
  sd a0, 8(sp)
  sd a7, 16(sp)
  csrr a0, mcause
  csrr a1, mepc
  ld a2, 8(sp)
  ld a3, 16(sp)
  call user_trap_dispatch
  li t0, 1
  beq a0, t0, 1f
  csrw mepc, a0
  ld ra, 0(sp)
  ld a0, 8(sp)
  ld a7, 16(sp)
  addi sp, sp, 32
  csrrw sp, mscratch, sp
  mret
1:
  la t0, user_kernel_return
  csrw mepc, t0
  csrr t0, mstatus
  li t1, (3 << 11)
  or t0, t0, t1
  csrw mstatus, t0
  addi sp, sp, 32
  mret

.section .rodata.user,"a"
.align 2
.global user_payload_start
user_payload_start:
  li a7, 1
  li a0, 'U'
  ecall
  li a0, '-'
  ecall
  li a0, 'm'
  ecall
  li a0, 'o'
  ecall
  li a0, 'd'
  ecall
  li a0, 'e'
  ecall
  li a0, '\n'
  ecall
  li a7, 2
  ecall
  j .
.global user_fault_payload_start
user_fault_payload_start:
  li ra, -1
  li s0, -1
  li s1, -1
  li s2, -1
  li s3, -1
  li s4, -1
  li s5, -1
  li s6, -1
  li s7, -1
  li s8, -1
  li s9, -1
  li s10, -1
  li s11, -1
  li t2, -1
  li t3, -1
  li t4, -1
  li t5, -1
  li t6, -1
  li a0, -1
  li a1, -1
  li a2, -1
  li a3, -1
  li a4, -1
  li a5, -1
  li a6, -1
  li a7, -1
  li gp, -1
  li tp, -1
  unimp
  j .
.global user_shell_payload_start
user_shell_payload_start:
  # s7 is an eight-byte little-endian command buffer. s8 is its length,
  # s9 is the overflow flag, and s10 remembers a preceding CR.
  li s7, 0
  li s8, 0
  li s9, 0
  li s10, 0
20:
  mv a0, s0
  li a1, 1
  li a7, 10
  ecall
21:
  mv a0, s0
  li a7, 11
  ecall
  li t0, -3
  beq a0, t0, 21b
  mv t6, a0
  # ETX is an operator interrupt. Route it through the same capability- and
  # current-task-checked shutdown syscall as the explicit `exit` command.
  li t0, 0x03
  beq t6, t0, 36f
  li t0, '\r'
  beq t6, t0, 25f
  li t0, '\n'
  bne t6, t0, 22f
  bnez s10, 24f
  j 26f
22:
  li s10, 0
  li t0, '\b'
  beq t6, t0, 23f
  li t0, 0x7f
  beq t6, t0, 23f
  li t0, 0x20
  bltu t6, t0, 21b
  li t0, 0x7f
  bgeu t6, t0, 21b
  li t0, 8
  bgeu s8, t0, 29f
  slli t1, s8, 3
  sll t2, t6, t1
  or s7, s7, t2
  addi s8, s8, 1
  mv a0, s0
  mv a1, t6
  li a7, 19
  ecall
  j 21b
23:
  bnez s9, 21b
  beqz s8, 21b
  addi s8, s8, -1
  slli t1, s8, 3
  li t0, 1
  sll t0, t0, t1
  addi t0, t0, -1
  and s7, s7, t0
  mv a0, s0
  li a1, '\b'
  li a7, 19
  ecall
  mv a0, s0
  li a1, ' '
  li a7, 19
  ecall
  mv a0, s0
  li a1, '\b'
  li a7, 19
  ecall
  j 21b
24:
  li s10, 0
  j 21b
25:
  li s10, 1
26:
  mv a0, s0
  li a1, '\n'
  li a7, 19
  ecall
  bnez s9, 30f
  beqz s8, 39f
  li t0, 0x706c6568
  beq s7, t0, 31f
  li t0, 0x6f666e69
  beq s7, t0, 32f
  li t0, 0x736b636974
  beq s7, t0, 33f
  li t0, 0x637069
  beq s7, t0, 34f
  li t0, 0x7366
  beq s7, t0, 35f
  li t0, 0x736c
  beq s7, t0, 42f
  li t0, 0x746163
  beq s7, t0, 43f
  li t0, 0x6f686365
  beq s7, t0, 44f
  li t0, 0x6574697277
  beq s7, t0, 45f
  li t0, 0x74617473
  beq s7, t0, 46f
  li t0, 0x73626f6a
  beq s7, t0, 47f
  li t0, 0x6e7572
  beq s7, t0, 48f
  li t0, 0x6c65636e6163
  beq s7, t0, 49f
  li t0, 0x746c75736572
  beq s7, t0, 50f
  li t0, 0x74697865
  beq s7, t0, 36f
  li t0, 0x74736574666c6573
  beq s7, t0, 37f
  mv a0, s0
  li a1, 6
  li a7, 10
  ecall
  j 39f
29:
  li s9, 1
  j 21b
30:
  mv a0, s0
  li a1, 5
  li a7, 10
  ecall
  j 39f
31:
  mv a0, s0
  li a1, 2
  li a7, 10
  ecall
  j 39f
32:
  mv a0, s0
  li a1, 3
  li a7, 10
  ecall
  j 39f
33:
  mv a0, s1
  li a7, 12
  ecall
  mv a0, s0
  li a1, 9
  li a7, 10
  ecall
  j 39f
34:
  mv a0, s2
  li a1, 83
  li a7, 13
  ecall
  bnez a0, 38f
  mv a0, s2
  li a7, 14
  ecall
  li t0, 83
  bne a0, t0, 38f
  mv a0, s0
  li a1, 8
  li a7, 10
  ecall
  j 39f
35:
  mv a0, s5
  li a1, 1
  li a7, 17
  ecall
  li t0, 'h'
  bne a0, t0, 38f
  mv a0, s5
  li a1, (88 << 24) | 1
  li a7, 18
  ecall
  li t0, -1
  bne a0, t0, 38f
  mv a0, s6
  li a1, (82 << 24) | 2
  li a7, 18
  ecall
  li t0, -1
  bne a0, t0, 38f
  mv a0, s5
  li a1, (82 << 24) | 2
  li a7, 18
  ecall
  bnez a0, 38f
  mv a0, s5
  li a1, 2
  li a7, 17
  ecall
  li t0, 'R'
  bne a0, t0, 38f
  mv a0, s0
  li a1, 13
  li a7, 10
  ecall
  j 39f
36:
  li a7, 15
  ecall
  j .
37:
  # Smoke-only register/capability diagnostic; the command buffer remains in
  # callee-saved registers throughout real timer preemption.
  li ra, -1
  li gp, -1
  li tp, -1
  li t2, -1
  li t3, -1
  li t4, -1
  li t5, -1
  li t6, -1
  li a0, -1
  li a1, -1
  li a2, -1
  li a3, -1
  li a4, -1
  li a5, -1
  li a6, -1
  li a7, -1
  li t0, 100000000
10:
  addi t0, t0, -1
  bnez t0, 10b
  li t1, -1
  li a2, 1
  bne ra, t1, 40f
  li a2, 3
  bne gp, t1, 40f
  li a2, 4
  bne tp, t1, 40f
  li a2, 7
  bne t2, t1, 40f
  li a2, 28
  bne t3, t1, 40f
  li a2, 29
  bne t4, t1, 40f
  li a2, 30
  bne t5, t1, 40f
  li a2, 31
  bne t6, t1, 40f
  li a2, -1
  bne a0, t1, 41f
  bne a1, t1, 41f
  bne a2, t1, 41f
  bne a3, t1, 41f
  bne a4, t1, 41f
  bne a5, t1, 41f
  bne a6, t1, 41f
  bne a7, t1, 41f
  mv a0, s0
  li a1, 10
  li a7, 10
  ecall
  mv a0, s0
  li a1, 4
  li a7, 10
  ecall
  # Preserve the existing kernel-derived denial evidence.
  li a0, 0xdead
  li a1, 1
  li a7, 16
  ecall
  bnez a0, 38f
  mv a0, s3
  li a1, 2
  li a7, 16
  ecall
  bnez a0, 38f
  mv a0, s4
  li a1, 3
  li a7, 16
  ecall
  bnez a0, 38f
  # A console grant alone cannot invoke the demo broker.
  mv a0, s0
  li a1, 3
  li a2, 0
  li a7, 20
  ecall
  li t0, 1
  bne a0, t0, 38f
  j 39f
38:
  unimp
  j .
39:
  li s7, 0
  li s8, 0
  li s9, 0
  j 20b
40:
  mv a3, t2
  mv a0, s0
  li a1, 11
  li a7, 10
  ecall
  j 38b
41:
  mv a0, s0
  li a1, 12
  li a7, 10
  ecall
  j 38b
42:
  mv a0, s0
  li a1, 1
  mv a2, s11
  li a7, 20
  ecall
  j 39b
43:
  mv a0, s0
  li a1, 2
  mv a2, s11
  li a7, 20
  ecall
  j 39b
44:
  mv a0, s0
  li a1, 3
  mv a2, s11
  li a7, 20
  ecall
  j 39b
45:
  mv a0, s0
  li a1, 4
  mv a2, s11
  li a7, 20
  ecall
  j 39b
46:
  mv a0, s0
  li a1, 5
  mv a2, s11
  li a7, 20
  ecall
  j 39b
47:
  mv a0, s0
  li a1, 6
  mv a2, s11
  li a7, 20
  ecall
  j 39b
48:
  mv a0, s0
  li a1, 7
  mv a2, s11
  li a7, 20
  ecall
  j 39b
49:
  mv a0, s0
  li a1, 8
  mv a2, s11
  li a7, 20
  ecall
  j 39b
50:
  mv a0, s0
  li a1, 9
  mv a2, s11
  li a7, 20
  ecall
  j 39b
.global user_payload_end
user_payload_end:
