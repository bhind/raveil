    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000000
    li      s1, 0x08010000
    la      s2, begin_signature

    lw      t0, 0(s1)
    sw      t0, 4(s2)
    bnez    t0, fail_phase_reset

    li      t0, 0x11223344
    sw      t0, 0(s0)
    fence   iorw, iorw
    lw      t1, 0(s0)
    sw      t1, 8(s2)
    bne     t0, t1, fail_data

    li      t2, 0xaa
    sb      t2, 1(s0)
    li      t2, 0x55
    sb      t2, 3(s0)
    fence   iorw, iorw
    lw      t1, 0(s0)
    sw      t1, 12(s2)
    li      t0, 0x5522aa44
    bne     t0, t1, fail_partial

    li      t0, 2
    sw      t0, 0(s1)
    fence   iorw, iorw
    lw      t1, 0(s0)
    li      t2, 0xcafebabe
    sw      t2, 4(s0)
    fence   iorw, iorw
    lwu     t3, 4(s0)
    sw      t3, 16(s2)
    bne     t2, t3, fail_execution

    fence   iorw, iorw
    lw      s5, 0(s1)
    lw      s6, 4(s1)
    lw      s7, 8(s1)
    lw      a1, 0x10(s1)
    lw      a2, 0x14(s1)
    lw      a3, 0x20(s1)
    lw      a4, 0x24(s1)
    lw      s3, 0x50(s1)
    lw      s4, 0x54(s1)
    lw      a7, 0x58(s1)
    lw      t0, 0x5c(s1)
    lw      t1, 0x60(s1)
    lw      t2, 0x64(s1)
    lw      t3, 0x68(s1)
    lw      t4, 0x6c(s1)
    lw      t5, 0x70(s1)
    lw      t6, 0x74(s1)
    sw      s5, 20(s2)
    sw      s6, 24(s2)
    sw      s7, 28(s2)
    sw      a1, 32(s2)
    sw      a2, 36(s2)
    sw      a3, 40(s2)
    sw      a4, 44(s2)
    sw      s3, 48(s2)
    sw      s4, 52(s2)
    sw      a7, 56(s2)
    sw      t0, 60(s2)
    sw      t1, 64(s2)
    sw      t2, 68(s2)
    sw      t3, 72(s2)
    sw      t4, 76(s2)
    sw      t5, 80(s2)
    sw      t6, 84(s2)

    li      a5, 2
    bne     s5, a5, fail_phase
    li      a5, 8
    bne     s6, a5, fail_accepted
    bne     s7, a5, fail_completed
    li      a5, 2
    bne     a1, a5, fail_install_read
    li      a5, 3
    bne     a2, a5, fail_install_write
    li      a5, 2
    bne     a3, a5, fail_execution_read
    li      a5, 1
    bne     a4, a5, fail_execution_write
    li      a5, 8
    bne     a7, a5, fail_expected_accepted
    bne     t0, a5, fail_expected_completed
    bnez    t1, fail_unexpected_accepted
    bnez    t2, fail_unexpected_completed
    bltu    t3, s3, fail_source_range
    bgeu    t3, s4, fail_source_range
    bltu    t4, s3, fail_source_range
    bgeu    t4, s4, fail_source_range
    li      a5, 2
    bne     t5, a5, fail_source_phase
    bne     t6, a5, fail_source_phase

    li      a0, 1
    j       finish

fail_phase_reset:
    li      a0, 3
    j       finish
fail_data:
    li      a0, 5
    j       finish
fail_partial:
    li      a0, 7
    j       finish
fail_execution:
    li      a0, 9
    j       finish
fail_phase:
    li      a0, 11
    j       finish
fail_accepted:
    li      a0, 13
    j       finish
fail_completed:
    li      a0, 15
    j       finish
fail_install_read:
    li      a0, 17
    j       finish
fail_install_write:
    li      a0, 19
    j       finish
fail_execution_read:
    li      a0, 21
    j       finish
fail_execution_write:
    li      a0, 23
    j       finish
fail_expected_accepted:
    li      a0, 25
    j       finish
fail_expected_completed:
    li      a0, 27
    j       finish
fail_unexpected_accepted:
    li      a0, 29
    j       finish
fail_unexpected_completed:
    li      a0, 31
    j       finish
fail_source_range:
    li      a0, 33
    j       finish
fail_source_phase:
    li      a0, 35

finish:
    sw      a0, 0(s2)
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
    .fill 22, 4, 0
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
