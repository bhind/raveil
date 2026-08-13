    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000100
    la      s1, begin_signature

    li      t0, 0x51a7c0de
    fence   iorw, iorw
    sw      t0, 0(s0)
    fence   iorw, iorw
    lwu     t1, 0(s0)
    fence   iorw, iorw

    sw      t0, 4(s1)
    sw      t1, 8(s1)
    li      a0, 1
    sw      a0, 0(s1)
    fence   rw, rw
    la      t2, tohost
    sd      a0, 0(t2)
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
