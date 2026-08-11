#include "raveil/graph_transport.h"

static bool nonzero(const uint8_t *value,size_t length) {
  uint8_t combined=0u;
  for(size_t index=0;index<length;++index) combined|=value[index];
  return combined!=0u;
}

bool raveil_graph_request_validate_v1(
    const struct raveil_graph_request_v1 *request) {
  if(request==NULL || request->magic!=RAVEIL_GRAPH_REQUEST_MAGIC ||
     request->schema_version!=RAVEIL_GRAPH_REQUEST_V1 ||
     request->struct_size!=sizeof(*request) || request->flags!=0u ||
     request->family!=RAVEIL_GRAPH_FAMILY_GEMM || request->m==0u ||
     request->n==0u || request->k==0u || request->m>8u || request->n>8u ||
     request->k>8u || request->candidate<RAVEIL_GRAPH_CANDIDATE_BASELINE ||
     request->candidate>RAVEIL_GRAPH_CANDIDATE_TILE32 ||
     request->reserved0!=0u || request->reserved_align!=0u ||
     request->request_id==0u ||
     !nonzero(request->program_identity,16u) ||
     !nonzero(request->graph_variant_identity,16u) ||
     !nonzero(request->execution_contract_identity,16u)) return false;
  for(size_t index=0;index<sizeof(request->reserved1);++index)
    if(request->reserved1[index]!=0u) return false;
  return true;
}
