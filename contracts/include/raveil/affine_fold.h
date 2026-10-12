#ifndef RAVEIL_AFFINE_FOLD_H
#define RAVEIL_AFFINE_FOLD_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define RAVEIL_FOLD_MAGIC UINT32_C(0x51464631)
#define RAVEIL_FOLD_BRIDGE_MAGIC UINT32_C(0x51464632)
#define RAVEIL_FOLD_END UINT32_C(0x46454e44)
#define RAVEIL_FOLD_MAX_BYTES 2892u
#define RAVEIL_FOLD_SESSION_MAGIC UINT32_C(0x51534631)
#define RAVEIL_FOLD_SESSION_END UINT32_C(0x53454e44)
#define RAVEIL_FOLD_SESSION_MAX_JOBS 8u
#define RAVEIL_FOLD_SESSION_MAX_BYTES (32u+8u*RAVEIL_FOLD_MAX_BYTES)
struct raveil_fold_session {
  uint64_t epoch;
  uint32_t count;
  uint32_t offsets[8],lengths[8];
};
struct raveil_fold_request {
  uint64_t request_id;
  uint32_t config[65];
  uint32_t inputs[648];
};
bool raveil_fold_validate(const uint32_t config[65]);
bool raveil_fold_decode(const uint8_t *bytes,size_t size,
                       struct raveil_fold_request *request);
bool raveil_fold_evaluate(const struct raveil_fold_request *request,
                         uint32_t output[256]);
bool raveil_fold_response_decode(const uint8_t *bytes,size_t size,
  uint64_t request_id,uint64_t epoch,uint64_t sequence,const uint8_t cookie[16],
  uint32_t count,uint32_t output[256]);
bool raveil_fold_session_decode(const uint8_t *bytes,size_t size,
                                struct raveil_fold_session *session);
#define RAVEIL_FOLD_CHAIN_MAGIC UINT32_C(0x51434631)
#define RAVEIL_FOLD_CHAIN_END UINT32_C(0x43454e44)
#define RAVEIL_FOLD_CHAIN_MAX_BYTES (32u+8u*(8u+RAVEIL_FOLD_MAX_BYTES))
struct raveil_fold_chain {
  struct raveil_fold_session jobs;
  uint32_t sources[8],masks[8];
};
bool raveil_fold_chain_decode(const uint8_t *bytes,size_t size,
                              struct raveil_fold_chain *chain);
bool raveil_fold_bridge_encode(const struct raveil_fold_request *request,
                               uint8_t *bytes,size_t capacity,size_t *size);
#define RAVEIL_FOLD_DAG_MAGIC UINT32_C(0x51444631)
#define RAVEIL_FOLD_DAG_END UINT32_C(0x44454e44)
#define RAVEIL_FOLD_DAG_MAX_BYTES (40u+8u*(24u+RAVEIL_FOLD_MAX_BYTES))
struct raveil_fold_dag {
  struct raveil_fold_session jobs;
  uint32_t sources[8][2],destinations[8][2],chunks[8],last_use[8],output;
  uint32_t input_offsets[8][2];
};
bool raveil_fold_dag_decode(const uint8_t *bytes,size_t size,
                            struct raveil_fold_dag *dag);
#endif
