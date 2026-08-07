#ifndef SONATINE_CONSOLE_H
#define SONATINE_CONSOLE_H

#include <stddef.h>
#include <stdint.h>

void console_init(void);
void console_putc(char value);
void console_write(const char *text);
void console_write_dec(uint64_t value);
void console_write_hex(uint64_t value);
size_t console_readline(char *buffer, size_t capacity);

#endif
