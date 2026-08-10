#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include "raveil/job_contract.h"

static struct raveil_job_descriptor_v1 job(void) {
  struct raveil_job_descriptor_v1 value={0};
  value.magic=RAVEIL_JOB_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.object_count=2u;
  value.job_id=UINT64_C(0x8000000000000083);
  value.program_identity[0]=1u; value.graph_variant_identity[0]=2u;
  value.execution_contract_identity[0]=3u; value.target_signature[0]=4u;
  value.resources.max_runtime_ticks=100u; value.resources.max_input_bytes=64u;
  value.resources.max_output_bytes=64u; value.resources.max_scratch_bytes=32u;
  value.objects[0]=(struct raveil_object_ref_v1){1u,1u,7u,0u,16u,RAVEIL_OBJECT_READ,0u};
  value.objects[1]=(struct raveil_object_ref_v1){2u,3u,9u,16u,8u,RAVEIL_OBJECT_WRITE,0u};
  return value;
}
static struct raveil_completion_record_v1 completion(void) {
  struct raveil_completion_record_v1 value={0};
  value.magic=RAVEIL_COMPLETION_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.status=RAVEIL_COMPLETION_EXECUTED;
  value.job_id=UINT64_C(0x8000000000000083); value.execution_epoch=5u;
  value.execution_sequence=6u; value.completion_cookie[0]=7u; value.output_count=1u;
  value.outputs[0]=(struct raveil_object_version_v1){2u,3u,10u}; return value;
}
int main(void) {
  _Static_assert(sizeof(struct raveil_job_descriptor_v1)==320u,"job size");
  _Static_assert(sizeof(struct raveil_completion_record_v1)==176u,"completion size");
  _Static_assert(_Alignof(struct raveil_job_descriptor_v1)==8u,"job align");
  _Static_assert(RAVEIL_OBJECT_READ==1u && RAVEIL_OBJECT_WRITE==2u,"access values");
  _Static_assert(RAVEIL_COMPLETION_EXECUTED==1u && RAVEIL_COMPLETION_FAULT==4u,
                 "completion values");
  _Static_assert(offsetof(struct raveil_job_descriptor_v1,objects)==128u,"object offset");
  _Static_assert(offsetof(struct raveil_completion_record_v1,outputs)==80u,"output offset");
  struct raveil_job_descriptor_v1 valid=job(),copy;
  assert(raveil_job_descriptor_validate_v1(&valid));
  memcpy(&copy,&valid,sizeof(copy)); assert(memcmp(&copy,&valid,sizeof(copy))==0);
#define BAD_JOB(field,value) do { copy=valid; copy.field=(value); assert(!raveil_job_descriptor_validate_v1(&copy)); } while(0)
  BAD_JOB(magic,0u); BAD_JOB(schema_version,2u); BAD_JOB(struct_size,319u);
  BAD_JOB(flags,1u); BAD_JOB(reserved0,1u); BAD_JOB(reserved1,1u);
  BAD_JOB(job_id,0u); BAD_JOB(object_count,0u); BAD_JOB(object_count,5u);
  copy=valid; memset(copy.program_identity,0,16u); assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; memset(copy.graph_variant_identity,0,16u); assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; memset(copy.execution_contract_identity,0,16u); assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; memset(copy.target_signature,0,16u); assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.resources.max_runtime_ticks=0u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.resources.max_scratch_bytes=0u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.resources.max_input_bytes=15u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.resources.max_output_bytes=7u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].length=0u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].generation=0u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].expected_version=0u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].flags=1u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].offset=UINT64_MAX; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].access=4u; assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[0].access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[1].object_id=1u; copy.objects[1].generation=1u;
  assert(!raveil_job_descriptor_validate_v1(&copy));
  copy=valid; copy.objects[2].object_id=99u; assert(!raveil_job_descriptor_validate_v1(&copy));
  struct raveil_completion_record_v1 done=completion(),done_copy;
  assert(raveil_completion_record_validate_v1(&valid,&done));
  memcpy(&done_copy,&done,sizeof(done)); assert(memcmp(&done_copy,&done,sizeof(done))==0);
#define BAD_DONE(field,value) do { done_copy=done; done_copy.field=(value); assert(!raveil_completion_record_validate_v1(&valid,&done_copy)); } while(0)
  BAD_DONE(magic,0u); BAD_DONE(schema_version,2u); BAD_DONE(struct_size,175u);
  BAD_DONE(flags,1u); BAD_DONE(status,0u); BAD_DONE(status,5u); BAD_DONE(detail,1u);
  BAD_DONE(job_id,1u); BAD_DONE(execution_epoch,0u); BAD_DONE(execution_sequence,0u);
  BAD_DONE(output_count,5u); BAD_DONE(reserved0,1u); BAD_DONE(reserved1,1u);
  done_copy=done; done_copy.reserved2[0]=1u;
  assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  copy=valid; done_copy=done; done_copy.completion_cookie[0]=0u;
  assert(!raveil_completion_record_validate_v1(&copy,&done_copy));
  done_copy=done; done_copy.outputs[0].version=9u;
  assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy=done; done_copy.outputs[0].object_id=1u;
  assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy=done; done_copy.output_count=0u; memset(done_copy.outputs,0,sizeof(done_copy.outputs));
  assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy=done; done_copy.outputs[1].object_id=2u;
  assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy=done; done_copy.status=RAVEIL_COMPLETION_REJECTED;
  done_copy.detail=1u; done_copy.output_count=0u; memset(done_copy.outputs,0,sizeof(done_copy.outputs));
  assert(raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy.detail=0u; assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy.detail=UINT32_MAX; assert(!raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy=done; done_copy.status=RAVEIL_COMPLETION_CANCELLED;
  done_copy.detail=RAVEIL_DETAIL_CANCEL_REQUESTED; done_copy.output_count=0u;
  memset(done_copy.outputs,0,sizeof(done_copy.outputs));
  assert(raveil_completion_record_validate_v1(&valid,&done_copy));
  done_copy=done; done_copy.status=RAVEIL_COMPLETION_FAULT;
  done_copy.detail=RAVEIL_DETAIL_EXECUTION_FAULT; done_copy.output_count=0u;
  memset(done_copy.outputs,0,sizeof(done_copy.outputs));
  assert(raveil_completion_record_validate_v1(&valid,&done_copy));
  return 0;
}
