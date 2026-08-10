#ifndef RAVEIL_LINUX_UAPI_DRIVER_H
#define RAVEIL_LINUX_UAPI_DRIVER_H

#include <stdint.h>

#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Raveil driver ABI v1 requires a little-endian host"
#endif

#define RAVEIL_DRIVER_MAGIC 0x5241564cu
#define RAVEIL_DRIVER_ABI_VERSION 1u

enum raveil_driver_opcode {
  RAVEIL_OP_PING = 1u,
  RAVEIL_OP_NOP = 2u
};

enum raveil_driver_status {
  RAVEIL_STATUS_OK = 0u,
  RAVEIL_STATUS_INVALID = 1u,
  RAVEIL_STATUS_BUSY = 2u,
  RAVEIL_STATUS_EMPTY = 3u
};

struct raveil_driver_request {
  uint32_t magic;
  uint16_t abi_version;
  uint16_t struct_size;
  uint32_t opcode;
  uint32_t flags;
  uint64_t request_id;
  uint64_t argument;
};

struct raveil_driver_completion {
  uint32_t magic;
  uint16_t abi_version;
  uint16_t struct_size;
  uint32_t status;
  uint32_t detail;
  uint64_t request_id;
  uint64_t result;
};

_Static_assert(sizeof(struct raveil_driver_request) == 32u,
               "request ABI size changed");
_Static_assert(sizeof(struct raveil_driver_completion) == 32u,
               "completion ABI size changed");

#endif
