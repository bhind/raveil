    .section .text.init
    .globl _start
_start:
    li      s0, 0x08000100
    la      s1, begin_signature

    lwu     t0, 0(s0)
    sw      t0, 4(s1)

    li      a0, 1
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
    .fill 2, 4, 0
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
