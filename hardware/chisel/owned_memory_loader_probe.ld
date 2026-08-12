OUTPUT_ARCH("riscv")
ENTRY(_start)

PHDRS
{
  probe PT_LOAD FLAGS(6);
  text PT_LOAD FLAGS(5);
  data PT_LOAD FLAGS(6);
}

SECTIONS
{
  . = 0x08000000;
  .loader_probe : { KEEP(*(.loader_probe)) } :probe

  . = 0x80000000;
  .text : { *(.text.init) *(.text .text.*) } :text
  .rodata : { *(.rodata .rodata.*) } :text
  .data : { *(.data .data.*) } :data
  .bss : { *(.bss .bss.*) *(COMMON) } :data
  .signature : { *(.signature) } :data
  . = ALIGN(64);
  .tohost : { *(.tohost) } :data
}
