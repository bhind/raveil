#include "util.h"

size_t rv_strlen(const char *text) {
  size_t length = 0;
  while (text[length] != '\0') {
    ++length;
  }
  return length;
}

int rv_strcmp(const char *left, const char *right) {
  while (*left != '\0' && *left == *right) {
    ++left;
    ++right;
  }
  return (unsigned char)*left - (unsigned char)*right;
}

int rv_strncmp(const char *left, const char *right, size_t count) {
  for (size_t index = 0; index < count; ++index) {
    const unsigned char l = (unsigned char)left[index];
    const unsigned char r = (unsigned char)right[index];
    if (l != r || l == 0u) {
      return (int)l - (int)r;
    }
  }
  return 0;
}

void rv_strcpy_bounded(char *destination, const char *source, size_t capacity) {
  if (capacity == 0u) {
    return;
  }
  size_t index = 0;
  while (index + 1u < capacity && source[index] != '\0') {
    destination[index] = source[index];
    ++index;
  }
  destination[index] = '\0';
}

void *rv_memset(void *destination, int value, size_t count) {
  unsigned char *bytes = (unsigned char *)destination;
  for (size_t index = 0; index < count; ++index) {
    bytes[index] = (unsigned char)value;
  }
  return destination;
}
