#ifndef RAVEIL_GRAPH_TRANSPORT_H
#define RAVEIL_GRAPH_TRANSPORT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define RAVEIL_GRAPH_REQUEST_MAGIC 0x52475131u
#define RAVEIL_GRAPH_REQUEST_V1 1u
#define RAVEIL_GRAPH_FAMILY_GEMM 1u
#define RAVEIL_GRAPH_CANDIDATE_BASELINE 1u
#define RAVEIL_GRAPH_CANDIDATE_IKJ 2u
#define RAVEIL_GRAPH_CANDIDATE_TILE32 3u
#define RAVEIL_GRAPH_REQUEST_ADDRESS 0x87ff0000UL

struct raveil_graph_request_v1 {
  uint32_t magic;
  uint16_t schema_version;
  uint16_t struct_size;
  uint32_t flags;
  uint32_t family;
  uint32_t m;
  uint32_t n;
  uint32_t k;
  uint32_t candidate;
  uint32_t reserved0;
  uint32_t reserved_align;
  uint64_t request_id;
  uint8_t program_identity[16];
  uint8_t graph_variant_identity[16];
  uint8_t execution_contract_identity[16];
  uint8_t reserved1[32];
};

_Static_assert(sizeof(struct raveil_graph_request_v1)==128u,
               "graph request ABI");
_Static_assert(offsetof(struct raveil_graph_request_v1,request_id)==40u,
               "graph request id offset");
_Static_assert(offsetof(struct raveil_graph_request_v1,program_identity)==48u,
               "graph request identity offset");

bool raveil_graph_request_validate_v1(
    const struct raveil_graph_request_v1 *request);
#endif
