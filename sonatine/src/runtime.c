#include <stddef.h>

void *memcpy(void *destination, const void *source, size_t count) {
  unsigned char *dest = (unsigned char *)destination;
  const unsigned char *src = (const unsigned char *)source;

  for (size_t index = 0; index < count; ++index) {
    dest[index] = src[index];
  }

  return destination;
}
