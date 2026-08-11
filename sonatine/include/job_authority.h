#ifndef SONATINE_JOB_AUTHORITY_H
#define SONATINE_JOB_AUTHORITY_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "raveil/job_contract.h"
#include "raveil/object_manifest.h"

#define SONATINE_OBJECT_TABLE_SIZE 8u
#define SONATINE_JOB_RING_DEPTH 4u
#define SONATINE_OBJECT_MAX_BYTES 512u

struct sonatine_submission {
  struct raveil_job_descriptor_v1 job;
  uint64_t execution_epoch;
  uint64_t execution_sequence;
  uint8_t completion_cookie[16];
};

struct sonatine_job_binding {
  uint64_t job_id;
  uint64_t execution_epoch;
  uint64_t execution_sequence;
  uint8_t completion_cookie[16];
};

enum sonatine_finalize_result {
  SONATINE_FINALIZE_INVALID=0,
  SONATINE_FINALIZE_COMMITTED=1,
  SONATINE_FINALIZE_ROLLED_BACK=2,
  SONATINE_FINALIZE_CONFLICT=3
};

void job_authority_init(uint64_t execution_epoch);
bool job_object_lookup(uint64_t object_id,
                       struct raveil_object_manifest_v1 *manifest);
bool job_object_read(uint64_t object_id,uint64_t offset,
                     void *target,size_t length);
bool job_submission_read(const struct sonatine_submission *submission,
                         uint64_t object_id,uint64_t offset,
                         void *target,size_t length);
bool job_submission_take(struct sonatine_submission *submission);
bool job_completion_post(const struct raveil_completion_record_v1 *completion);
bool job_completion_take(struct raveil_completion_record_v1 *completion);
bool job_completion_pending(const struct sonatine_job_binding *binding);
bool job_completion_take_bound(const struct sonatine_job_binding *binding,
                               struct raveil_completion_record_v1 *completion);
bool job_cancel(const struct sonatine_job_binding *binding);
size_t job_shadow_count(void);
size_t job_submission_count(void);
size_t job_completion_count(void);
size_t job_inflight_count(void);
#endif
