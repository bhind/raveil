    .section .text.init
    .globl _start
_start:
#ifdef BOOM_SERIALIZE_DISPATCH
    li      t0, 8
    csrrs   zero, 0x7c1, t0
    csrr    t1, 0x7c1
    andi    t1, t1, 8
    beqz    t1, 1f
#endif

    call    stencil_repeated_main
    bnez    a0, 1f
    li      a0, 1
    j       2f
1:
    li      a0, 3
2:
    la      t0, tohost
    sd      a0, 0(t0)
    fence
3:
    j       3b

    .section .scratchpad.input,"aw",@nobits
    .align 4
    .globl input_words
input_words:
    .space 1296

    .section .scratchpad.signature,"aw",@progbits
    .align 4
    .globl begin_signature
    .globl output_words
begin_signature:
output_words:
    .space 1024
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
