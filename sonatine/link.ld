OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY {
  RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 128M
}

SECTIONS {
  . = ORIGIN(RAM);

  .text : ALIGN(4) {
    KEEP(*(.text.init))
    KEEP(*(.text.trap))
    *(.text .text.*)
  } > RAM

  .rodata : ALIGN(8) {
    *(.rodata .rodata.*)
  } > RAM

  .data : ALIGN(8) {
    *(.data .data.*)
  } > RAM

  .bss : ALIGN(16) {
    __bss_start = .;
    *(.bss .bss.* COMMON)
    __bss_end = .;
  } > RAM

  . = ALIGN(4096);
  __kernel_end = .;
  __memory_end = ORIGIN(RAM) + LENGTH(RAM);

  /DISCARD/ : {
    *(.eh_frame .eh_frame.*)
    *(.comment)
  }
}
