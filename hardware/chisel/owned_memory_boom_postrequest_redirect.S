    .section .text.init
    .globl _start
_start:
    li      s0, 0x80010000
    la      s1, begin_signature

    li      s2, 0x682513da
    sw      s2, 0(s0)
    fence   rw, rw
    lwu     s2, 0(s0)
    sw      s2, 4(s1)
    fence   iorw, iorw

    li      t0, -1
    li      t1, 3
    divu    t2, t0, t1
    xor     t2, t2, t2
    bne     t2, zero, wrong_path_load
    j       redirect_landed
wrong_path_load:
    lwu     t4, 0(s0)
    addi    t5, t4, 1

redirect_landed:
    lwu     s3, 0(s0)
    sw      s3, 8(s1)
    bne     s2, s3, fail

    li      a0, 1
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
