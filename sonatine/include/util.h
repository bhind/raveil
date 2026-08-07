#ifndef SONATINE_UTIL_H
#define SONATINE_UTIL_H

#include <stddef.h>

size_t rv_strlen(const char *text);
int rv_strcmp(const char *left, const char *right);
int rv_strncmp(const char *left, const char *right, size_t count);
void rv_strcpy_bounded(char *destination, const char *source, size_t capacity);
void *rv_memset(void *destination, int value, size_t count);

#endif
