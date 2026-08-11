#include <assert.h>
#include <string.h>
#include "raveil/graph_transport.h"

static struct raveil_graph_request_v1 valid_request(void) {
  struct raveil_graph_request_v1 value={0};
  value.magic=RAVEIL_GRAPH_REQUEST_MAGIC;
  value.schema_version=RAVEIL_GRAPH_REQUEST_V1;
  value.struct_size=sizeof(value); value.family=RAVEIL_GRAPH_FAMILY_GEMM;
  value.m=8u; value.n=8u; value.k=8u;
  value.candidate=RAVEIL_GRAPH_CANDIDATE_BASELINE; value.request_id=1u;
  value.program_identity[0]=1u; value.graph_variant_identity[0]=1u;
  value.execution_contract_identity[0]=1u;
  return value;
}

int main(void) {
  struct raveil_graph_request_v1 value=valid_request();
  assert(raveil_graph_request_validate_v1(&value));
  struct raveil_graph_request_v1 broken=value;
  broken.schema_version=2u; assert(!raveil_graph_request_validate_v1(&broken));
  broken=value; broken.struct_size=127u;
  assert(!raveil_graph_request_validate_v1(&broken));
  broken=value; broken.m=9u; assert(!raveil_graph_request_validate_v1(&broken));
  broken=value; broken.candidate=99u;
  assert(!raveil_graph_request_validate_v1(&broken));
  broken=value; memset(broken.program_identity,0,16u);
  assert(!raveil_graph_request_validate_v1(&broken));
  broken=value; broken.reserved1[31]=1u;
  assert(!raveil_graph_request_validate_v1(&broken));
  assert(!raveil_graph_request_validate_v1(NULL));
  return 0;
}
