#include "console.h"

#include <stdbool.h>

#include "platform.h"

#define UART_RHR 0u
#define UART_THR 0u
#define UART_LSR 5u
#define UART_LSR_DATA_READY 0x01u
#define UART_LSR_TX_IDLE 0x20u

static volatile uint8_t *const uart = (volatile uint8_t *)QEMU_UART0_BASE;

void console_init(void) {
  /* QEMU's virt 16550 is initialized sufficiently for polled I/O. */
}

void console_putc(char value) {
  while ((uart[UART_LSR] & UART_LSR_TX_IDLE) == 0u) {
    cpu_relax();
  }
  uart[UART_THR] = (uint8_t)value;
}

char console_getc(void) {
  while ((uart[UART_LSR] & UART_LSR_DATA_READY) == 0u) {
    cpu_relax();
  }
  return (char)uart[UART_RHR];
}

bool console_try_getc(char *value) {
  if ((uart[UART_LSR] & UART_LSR_DATA_READY) == 0u) {
    return false;
  }
  *value = (char)uart[UART_RHR];
  return true;
}

void console_write(const char *text) {
  while (*text != '\0') {
    if (*text == '\n') {
      console_putc('\r');
    }
    console_putc(*text++);
  }
}

void console_write_dec(uint64_t value) {
  char digits[21];
  size_t count = 0;
  if (value == 0u) {
    console_putc('0');
    return;
  }
  while (value != 0u) {
    digits[count++] = (char)('0' + (value % 10u));
    value /= 10u;
  }
  while (count != 0u) {
    console_putc(digits[--count]);
  }
}

void console_write_hex(uint64_t value) {
  static const char digits[] = "0123456789abcdef";
  console_write("0x");
  bool emitted = false;
  for (int shift = 60; shift >= 0; shift -= 4) {
    const uint8_t digit = (uint8_t)((value >> (uint32_t)shift) & 0x0fu);
    if (digit != 0u || emitted || shift == 0) {
      console_putc(digits[digit]);
      emitted = true;
    }
  }
}

size_t console_readline(char *buffer, size_t capacity) {
  size_t length = 0;
  if (capacity == 0u) {
    return 0u;
  }
  for (;;) {
    if ((uart[UART_LSR] & UART_LSR_DATA_READY) == 0u) {
      cpu_relax();
      continue;
    }
    const char value = (char)uart[UART_RHR];
    if (value == '\r' || value == '\n') {
      console_write("\n");
      buffer[length] = '\0';
      return length;
    }
    if (value == '\b' || value == 0x7f) {
      if (length != 0u) {
        --length;
        console_write("\b \b");
      }
      continue;
    }
    if (value >= 0x20 && value <= 0x7e && length + 1u < capacity) {
      buffer[length++] = value;
      console_putc(value);
    }
  }
}
