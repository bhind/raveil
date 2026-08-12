    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000100
    lw      s2, 0(s0)
    xor     t3, s2, s2
    li      t0, 0x4b1d2e3f
    li      t2, 1
    nop
    beq     t2, t2, redirect_landed
    sw      t0, 0(s0)

redirect_landed:
    lw      t1, 0(s0)
    la      s1, begin_signature
    sw      s2, 4(s1)
    sw      t1, 8(s1)
    bne     t1, s2, fail
    beq     s2, t0, fail

    li      a0, 1
    j       finish

fail:
    li      a0, 3

finish:
    sw      a0, 0(s1)
    fence   rw, rw
    la      t1, tohost
    sd      a0, 0(t1)
    fence   iorw, iorw
1:
    j       1b

    .section .signature,"aw",@progbits
    .align 4
    .globl begin_signature
begin_signature:
    .fill 3, 4, 0
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
