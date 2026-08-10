#ifndef RAVEIL_OBJECT_MANIFEST_H
#define RAVEIL_OBJECT_MANIFEST_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if !defined(__BYTE_ORDER__) || !defined(__ORDER_LITTLE_ENDIAN__)
#error "Raveil object manifest v1 requires GCC/Clang byte-order macros"
#elif __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Raveil object manifest v1 requires little endian"
#endif

#define RAVEIL_OBJECT_MANIFEST_MAGIC 0x524f424au
#define RAVEIL_OBJECT_MANIFEST_V1 1u

enum raveil_object_backing_v1 {
  RAVEIL_OBJECT_BACKING_VOLATILE = 1u,
  RAVEIL_OBJECT_BACKING_IMMUTABLE = 2u
};

struct raveil_object_manifest_v1 {
  uint32_t magic;
  uint16_t schema_version;
  uint16_t struct_size;
  uint32_t flags;
  uint32_t permitted_access;
  uint64_t object_id;
  uint64_t generation;
  uint64_t version;
  uint64_t byte_length;
  uint32_t backing;
  uint32_t reserved0;
  uint8_t reserved1[8];
};

_Static_assert(sizeof(struct raveil_object_manifest_v1)==64u,"manifest ABI");
#define RAVEIL_MANIFEST_OFFSET(field,value) \
  _Static_assert(offsetof(struct raveil_object_manifest_v1,field)==(value), \
                 "manifest ABI offset " #field)
RAVEIL_MANIFEST_OFFSET(magic,0u);
RAVEIL_MANIFEST_OFFSET(schema_version,4u);
RAVEIL_MANIFEST_OFFSET(struct_size,6u);
RAVEIL_MANIFEST_OFFSET(flags,8u);
RAVEIL_MANIFEST_OFFSET(permitted_access,12u);
RAVEIL_MANIFEST_OFFSET(object_id,16u);
RAVEIL_MANIFEST_OFFSET(generation,24u);
RAVEIL_MANIFEST_OFFSET(version,32u);
RAVEIL_MANIFEST_OFFSET(byte_length,40u);
RAVEIL_MANIFEST_OFFSET(backing,48u);
RAVEIL_MANIFEST_OFFSET(reserved0,52u);
RAVEIL_MANIFEST_OFFSET(reserved1,56u);
#undef RAVEIL_MANIFEST_OFFSET

bool raveil_object_manifest_validate_v1(
    const struct raveil_object_manifest_v1 *manifest);
#endif
