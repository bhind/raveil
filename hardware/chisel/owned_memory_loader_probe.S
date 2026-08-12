    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000000
    li      s1, 0x08010000
    la      s2, begin_signature

    /* Observe the aligned SimTSI/FESVR PT_LOAD read/write before CPU data access. */
    fence   iorw, iorw
    lw      t0, 4(s1)
    sw      t0, 4(s2)
    li      t1, 2
    bne     t0, t1, fail
    lw      t0, 8(s1)
    sw      t0, 8(s2)
    bne     t0, t1, fail
    lw      t0, 0x58(s1)
    sw      t0, 12(s2)
    bnez    t0, fail
    lw      t0, 0x5c(s1)
    sw      t0, 16(s2)
    bnez    t0, fail
    lw      t0, 0x60(s1)
    sw      t0, 20(s2)
    bne     t0, t1, fail
    lw      t0, 0x64(s1)
    sw      t0, 24(s2)
    bne     t0, t1, fail
    lw      t0, 0x78(s1)
    sw      t0, 28(s2)
    bnez    t0, fail
    lw      t0, 0x7c(s1)
    sw      t0, 32(s2)
    bnez    t0, fail
    lw      t0, 0x80(s1)
    sw      t0, 36(s2)
    bne     t0, t1, fail
    lw      t0, 0x84(s1)
    sw      t0, 40(s2)
    bne     t0, t1, fail
    lw      t2, 0x68(s1)
    sw      t2, 44(s2)
    li      t3, 8192
    bgeu    t2, t3, fail
    lw      t2, 0x6c(s1)
    sw      t2, 48(s2)
    bgeu    t2, t3, fail
    lw      t0, 0x70(s1)
    sw      t0, 52(s2)
    bnez    t0, fail
    lw      t0, 0x74(s1)
    sw      t0, 56(s2)
    bnez    t0, fail

    /* The CPU read must see the loader payload and add one tagged request. */
    lw      t0, 0(s0)
    fence   iorw, iorw
    sw      t0, 60(s2)
    li      t1, 0x6c6f6164
    bne     t0, t1, fail

    lw      t0, 4(s1)
    sw      t0, 64(s2)
    li      t1, 3
    bne     t0, t1, fail
    lw      t0, 8(s1)
    sw      t0, 68(s2)
    bne     t0, t1, fail
    lw      t0, 0x58(s1)
    sw      t0, 72(s2)
    li      t1, 1
    bne     t0, t1, fail
    lw      t0, 0x5c(s1)
    sw      t0, 76(s2)
    bne     t0, t1, fail
    li      t1, 2
    lw      t0, 0x60(s1)
    sw      t0, 80(s2)
    bne     t0, t1, fail
    lw      t0, 0x64(s1)
    sw      t0, 84(s2)
    bne     t0, t1, fail
    li      t1, 1
    lw      t0, 0x78(s1)
    sw      t0, 88(s2)
    bne     t0, t1, fail
    lw      t0, 0x7c(s1)
    sw      t0, 92(s2)
    bne     t0, t1, fail
    li      t1, 2
    lw      t0, 0x80(s1)
    sw      t0, 96(s2)
    bne     t0, t1, fail
    lw      t0, 0x84(s1)
    sw      t0, 100(s2)
    bne     t0, t1, fail

    lw      s3, 0x50(s1)
    sw      s3, 120(s2)
    lw      s4, 0x54(s1)
    sw      s4, 124(s2)
    lw      t0, 0x88(s1)
    sw      t0, 104(s2)
    bltu    t0, s3, fail
    bgeu    t0, s4, fail
    lw      t0, 0x8c(s1)
    sw      t0, 108(s2)
    bltu    t0, s3, fail
    bgeu    t0, s4, fail
    lw      t0, 0x90(s1)
    sw      t0, 112(s2)
    bnez    t0, fail
    lw      t0, 0x94(s1)
    sw      t0, 116(s2)
    bnez    t0, fail
    lw      t0, 0(s1)
    sw      t0, 128(s2)
    bnez    t0, fail

    li      a0, 1
    j       finish

fail:
    li      a0, 3

finish:
    sw      a0, 0(s2)
    fence   rw, rw
    la      t0, tohost
    sd      a0, 0(t0)
    fence   iorw, iorw
1:
    j       1b

    .section .loader_probe,"a",@progbits
    .align 2
    .globl loader_probe_payload
loader_probe_payload:
    .word 0x6c6f6164

    .section .signature,"aw",@progbits
    .align 4
    .globl begin_signature
begin_signature:
    .fill 33, 4, 0
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
