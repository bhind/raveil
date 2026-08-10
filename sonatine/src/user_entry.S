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
3:
  mv a0, s0
  li a1, 1
  li a7, 10
  ecall
4:
  mv a0, s0
  li a7, 11
  ecall
  li t0, -3
  beq a0, t0, 4b
  li t0, 'i'
  beq a0, t0, 5f
  li t0, 's'
  beq a0, t0, 6f
  li t0, 'c'
  beq a0, t0, 7f
  li t0, 't'
  beq a0, t0, 8f
  li t0, 'f'
  beq a0, t0, 15f
  li t0, 'x'
  beq a0, t0, 9f
  j 4b
5:
  mv a0, s0
  li a1, 2
  li a7, 10
  ecall
  j 3b
6:
  mv a0, s0
  li a1, 3
  li a7, 10
  ecall
  li ra, -1
  li gp, -1
  li tp, -1
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
  li t0, 100000000
10:
  addi t0, t0, -1
  bnez t0, 10b
  li t1, -1
  li a2, 1
  bne ra, t1, 13f
  li a2, 3
  bne gp, t1, 13f
  li a2, 4
  bne tp, t1, 13f
  li a2, 23
  bne s7, t1, 13f
  li a2, 24
  bne s8, t1, 13f
  li a2, 25
  bne s9, t1, 13f
  li a2, 26
  bne s10, t1, 13f
  li a2, 27
  bne s11, t1, 13f
  li a2, 7
  bne t2, t1, 13f
  li a2, 28
  bne t3, t1, 13f
  li a2, 29
  bne t4, t1, 13f
  li a2, 30
  bne t5, t1, 13f
  li a2, 31
  bne t6, t1, 13f
  li a2, -1
  bne a0, t1, 14f
  bne a1, t1, 14f
  bne a2, t1, 14f
  bne a3, t1, 14f
  bne a4, t1, 14f
  bne a5, t1, 14f
  bne a6, t1, 14f
  bne a7, t1, 14f
  mv a0, s0
  li a1, 10
  li a7, 10
  ecall
  mv a0, s0
  li a1, 4
  li a7, 10
  ecall
  j 3b
7:
  li a0, 0xdead
  li a1, 1
  li a7, 16
  ecall
  bnez a0, 12f
  mv a0, s3
  li a1, 2
  li a7, 16
  ecall
  bnez a0, 12f
  mv a0, s4
  li a1, 3
  li a7, 16
  ecall
  bnez a0, 12f
  mv a0, s2
  li a1, 83
  li a7, 13
  ecall
  bnez a0, 12f
  mv a0, s2
  li a7, 14
  ecall
  li t0, 83
  bne a0, t0, 12f
  mv a0, s0
  li a1, 8
  li a7, 10
  ecall
  j 3b
8:
  mv a0, s1
  li a7, 12
  ecall
  mv a0, s0
  li a1, 9
  li a7, 10
  ecall
  j 3b
9:
  li a7, 15
  ecall
  j .
15:
  mv a0, s5
  li a1, 1
  li a7, 17
  ecall
  li t0, 'h'
  bne a0, t0, 12f
  mv a0, s5
  li a1, (88 << 24) | 1
  li a7, 18
  ecall
  li t0, -1
  bne a0, t0, 12f
  mv a0, s6
  li a1, (82 << 24) | 2
  li a7, 18
  ecall
  li t0, -1
  bne a0, t0, 12f
  mv a0, s5
  li a1, (82 << 24) | 2
  li a7, 18
  ecall
  bnez a0, 12f
  mv a0, s5
  li a1, 2
  li a7, 17
  ecall
  li t0, 'R'
  bne a0, t0, 12f
  mv a0, s0
  li a1, 13
  li a7, 10
  ecall
  j 3b
12:
  unimp
  j .
13:
  mv a3, t2
  mv a0, s0
  li a1, 11
  li a7, 10
  ecall
  j 12b
14:
  mv a0, s0
  li a1, 12
  li a7, 10
  ecall
  j 12b
.global user_payload_end
user_payload_end:
