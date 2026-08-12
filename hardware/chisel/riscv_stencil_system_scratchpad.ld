OUTPUT_ARCH("riscv")
ENTRY(_start)

PHDRS
{
  text PT_LOAD FLAGS(5);
  data PT_LOAD FLAGS(6);
  scratchpad PT_LOAD FLAGS(6);
}

SECTIONS
{
  . = 0x80000000;
  .text : { *(.text.init) *(.text .text.*) } :text
  .rodata : { *(.rodata .rodata.*) } :text
  .data : { *(.data .data.*) } :data
  .bss : { *(.bss .bss.*) *(COMMON) } :data
  . = ALIGN(64);
  .tohost : { *(.tohost) } :data

  . = 0x08000000;
  .scratchpad (NOLOAD) : { *(.scratchpad.input) } :scratchpad
  .scratchpad_signature : { *(.scratchpad.signature) } :scratchpad
}

ASSERT(SIZEOF(.scratchpad) + SIZEOF(.scratchpad_signature) <= 64K,
       "RFC-0005 functional buffers exceed the system scratchpad")
