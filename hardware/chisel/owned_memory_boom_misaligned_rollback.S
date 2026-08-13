    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000100
    la      s1, begin_signature
    la      t0, trap_handler
    csrw    mtvec, t0

    lw      s2, 0(s0)
    sw      s2, 4(s1)
    fence   iorw, iorw

exception_load:
    lw      t1, 1(s0)

exception_return:
    lw      s3, 0(s0)
    sw      s3, 8(s1)
    bne     s2, s3, fail
    lw      t0, 20(s1)
    li      t1, 1
    bne     t0, t1, fail
    lw      t0, 12(s1)
    li      t1, 4
    bne     t0, t1, fail
    lw      t0, 16(s1)
    li      t1, 0x08000101
    bne     t0, t1, fail

    li      a0, 1
    j       finish

trap_handler:
    csrr    t0, mcause
    csrr    t1, mtval
    sw      t0, 12(s1)
    sw      t1, 16(s1)
    lw      t2, 20(s1)
    addi    t2, t2, 1
    sw      t2, 20(s1)
    li      t2, 4
    bne     t0, t2, trap_fail
    li      t2, 0x08000101
    bne     t1, t2, trap_fail
    csrr    t3, mepc
    la      t4, exception_load
    bne     t3, t4, trap_fail
    addi    t3, t3, 4
    csrw    mepc, t3
    mret

trap_fail:
    li      a0, 5
    j       finish

fail:
    li      a0, 3

finish:
    sw      a0, 0(s1)
    fence   rw, rw
    la      t0, tohost
    sd      a0, 0(t0)
    fence   iorw, iorw
1:
    j       1b

    .section .signature,"aw",@progbits
    .align 4
    .globl begin_signature
begin_signature:
    .fill 6, 4, 0
    .globl end_signature
end_signature:

    .section .tohost,"aw",@progbits
    .align 6
    .globl tohost
tohost:
    .dword 0
    .align 6
    .globl fromhost
fromhost:
    .dword 0
