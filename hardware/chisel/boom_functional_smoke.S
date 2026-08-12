    .section .text.init
    .globl _start
_start:
#ifdef BOOM_SERIALIZE_DISPATCH
    li      t0, 8
    csrrs   zero, 0x7c1, t0
    csrr    t1, 0x7c1
    andi    t1, t1, 8
    beqz    t1, 5f
#endif

    li      t0, 0
    li      t1, 1
    li      t2, 17

1:
    add     t0, t0, t1
    addi    t1, t1, 1
    blt     t1, t2, 1b

    la      t3, scratch
    sd      t0, 0(t3)
    ld      t4, 0(t3)
    li      t5, 136
    bne     t4, t5, 2f

    li      a0, 1
    j       3f

2:
    li      a0, 3

    j       3f

5:
    li      a0, 5

3:
    la      t6, tohost
    sd      a0, 0(t6)
    fence
4:
    j       4b

    .section .bss
    .align 3
scratch:
    .dword 0

    .section .tohost,"aw",@progbits
    .align 6
    .globl tohost
tohost:
    .dword 0
    .align 6
    .globl fromhost
fromhost:
    .dword 0
