    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000000
    li      s1, 0x08010000
    la      s2, begin_signature

    li      t1, 32768
1:
    lw      t0, 0x84(s1)
    bnez    t0, 2f
    addi    t1, t1, -1
    bnez    t1, 1b
    li      a0, 3
    j       finish
2:
    fence   iorw, iorw
    lw      t0, 0x00(s1)
    sw      t0, 4(s2)
    lw      t0, 0x04(s1)
    sw      t0, 8(s2)
    lw      t0, 0x08(s1)
    sw      t0, 12(s2)
    lw      t0, 0x58(s1)
    sw      t0, 16(s2)
    lw      t0, 0x5c(s1)
    sw      t0, 20(s2)
    lw      t0, 0x60(s1)
    sw      t0, 24(s2)
    lw      t0, 0x64(s1)
    sw      t0, 28(s2)
    lw      t0, 0x78(s1)
    sw      t0, 32(s2)
    lw      t0, 0x7c(s1)
    sw      t0, 36(s2)
    lw      t0, 0x80(s1)
    sw      t0, 40(s2)
    lw      t0, 0x84(s1)
    sw      t0, 44(s2)
    lw      t0, 0x68(s1)
    sw      t0, 48(s2)
    lw      t0, 0x6c(s1)
    sw      t0, 52(s2)
    lw      t0, 0x70(s1)
    sw      t0, 56(s2)
    lw      t0, 0x74(s1)
    sw      t0, 60(s2)
    lw      t0, 0x98(s1)
    sw      t0, 64(s2)
    lw      t0, 0x9c(s1)
    sw      t0, 68(s2)
    lw      t0, 0xa0(s1)
    sw      t0, 72(s2)
    lw      t0, 0xa4(s1)
    sw      t0, 76(s2)

    lbu     t0, 0(s0)
    sw      t0, 80(s2)
    li      t1, 0xa5
    bne     t0, t1, fail_payload
    fence   iorw, iorw

    lw      t0, 0x04(s1)
    sw      t0, 84(s2)
    lw      t0, 0x08(s1)
    sw      t0, 88(s2)
    lw      t0, 0x58(s1)
    sw      t0, 92(s2)
    lw      t0, 0x5c(s1)
    sw      t0, 96(s2)
    lw      t0, 0x60(s1)
    sw      t0, 100(s2)
    lw      t0, 0x64(s1)
    sw      t0, 104(s2)
    lw      t0, 0x78(s1)
    sw      t0, 108(s2)
    lw      t0, 0x7c(s1)
    sw      t0, 112(s2)
    lw      t0, 0x80(s1)
    sw      t0, 116(s2)
    lw      t0, 0x84(s1)
    sw      t0, 120(s2)
    lw      t0, 0x88(s1)
    sw      t0, 124(s2)
    lw      t0, 0x8c(s1)
    sw      t0, 128(s2)
    lw      t0, 0x90(s1)
    sw      t0, 132(s2)
    lw      t0, 0x94(s1)
    sw      t0, 136(s2)
    lw      t0, 0x98(s1)
    sw      t0, 140(s2)
    lw      t0, 0x9c(s1)
    sw      t0, 144(s2)

    li      a0, 1
    j       finish
fail_payload:
    li      a0, 5
finish:
    sw      a0, 0(s2)
    fence   rw, rw
    la      t0, tohost
    sd      a0, 0(t0)
    fence   iorw, iorw
3:
    j       3b

    .section .signature,"aw",@progbits
    .align 4
    .globl begin_signature
begin_signature:
    .fill 37, 4, 0
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
