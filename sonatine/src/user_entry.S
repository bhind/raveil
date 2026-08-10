.section .text
.align 2
.global user_enter
user_enter:
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
  beqz a0, 2f
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
  ld ra, 0(sp)
  addi sp, sp, 32
  mret
2:
  j 2b

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
.global user_payload_end
user_payload_end:
