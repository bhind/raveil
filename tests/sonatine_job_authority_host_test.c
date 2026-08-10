#include <assert.h>
#include <string.h>
#include "job_authority.h"

static struct raveil_object_manifest_v1 manifest(
    uint64_t id,uint64_t generation,uint64_t version,uint64_t length,
    uint32_t access,uint32_t backing) {
  struct raveil_object_manifest_v1 value={0};
  value.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;
  value.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
  value.struct_size=sizeof(value); value.permitted_access=access;
  value.object_id=id; value.generation=generation; value.version=version;
  value.byte_length=length; value.backing=backing; return value;
}
static struct raveil_job_descriptor_v1 job(uint64_t id) {
  struct raveil_job_descriptor_v1 value={0};
  value.magic=RAVEIL_JOB_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.object_count=2u; value.job_id=id;
  value.program_identity[0]=1u; value.graph_variant_identity[0]=2u;
  value.execution_contract_identity[0]=3u; value.target_signature[0]=4u;
  value.resources=(struct raveil_resource_bounds_v1){100u,16u,8u,32u};
  value.objects[0]=(struct raveil_object_ref_v1){1u,2u,3u,0u,16u,RAVEIL_OBJECT_READ,0u};
  value.objects[1]=(struct raveil_object_ref_v1){2u,4u,5u,8u,8u,RAVEIL_OBJECT_WRITE,0u};
  return value;
}
static struct raveil_completion_record_v1 completion(
    const struct sonatine_submission *submission) {
  struct raveil_completion_record_v1 value={0};
  value.magic=RAVEIL_COMPLETION_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.status=RAVEIL_COMPLETION_EXECUTED;
  value.job_id=submission->job.job_id; value.execution_epoch=submission->execution_epoch;
  value.execution_sequence=submission->execution_sequence;
  memcpy(value.completion_cookie,submission->completion_cookie,16u);
  value.output_count=1u;
  value.outputs[0]=(struct raveil_object_version_v1){2u,4u,6u}; return value;
}
static void predictable_cookie(uint8_t cookie[16],uint64_t epoch,
                               uint64_t job_id,uint64_t sequence) {
  uint64_t first=job_id^epoch^UINT64_C(0x72617665696c6a31);
  uint64_t second=sequence^UINT64_C(0x736f6e6174696e65);
  for(size_t index=0;index<8u;++index) {
    cookie[index]=(uint8_t)(first>>(index*8u));
    cookie[index+8u]=(uint8_t)(second>>(index*8u));
  }
}
int main(void) {
  struct raveil_object_manifest_v1 input=manifest(
      1u,2u,3u,16u,RAVEIL_OBJECT_READ,RAVEIL_OBJECT_BACKING_IMMUTABLE);
  struct raveil_object_manifest_v1 output=manifest(
      2u,4u,5u,16u,RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE,
      RAVEIL_OBJECT_BACKING_VOLATILE),copy,observed;
  assert(raveil_object_manifest_validate_v1(&input));
  assert(raveil_object_manifest_validate_v1(&output));
  assert(!raveil_object_manifest_validate_v1(NULL));
#define BAD_MANIFEST(field,value) do { copy=input; copy.field=(value); \
  assert(!raveil_object_manifest_validate_v1(&copy)); } while(0)
  BAD_MANIFEST(magic,0u); BAD_MANIFEST(schema_version,0u);
  BAD_MANIFEST(struct_size,0u); BAD_MANIFEST(flags,1u);
  BAD_MANIFEST(object_id,0u); BAD_MANIFEST(generation,0u);
  BAD_MANIFEST(version,0u); BAD_MANIFEST(byte_length,0u);
  BAD_MANIFEST(permitted_access,0u); BAD_MANIFEST(permitted_access,4u);
  BAD_MANIFEST(backing,0u); BAD_MANIFEST(backing,99u);
  BAD_MANIFEST(reserved0,1u);
#undef BAD_MANIFEST
  copy=input; copy.reserved1[7]=1u; assert(!raveil_object_manifest_validate_v1(&copy));
  copy=input; copy.permitted_access=RAVEIL_OBJECT_WRITE;
  assert(!raveil_object_manifest_validate_v1(&copy));
  copy=input; copy.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
  copy.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  assert(raveil_object_manifest_validate_v1(&copy));
  job_authority_init(42u);
  assert(job_object_register(&input)); assert(job_object_register(&output));
  assert(!job_object_register(&output));
  assert(job_object_lookup(2u,&observed) && observed.version==5u);
  struct raveil_object_manifest_v1 high=manifest(
      UINT64_C(0x8000000000000001),1u,1u,8u,RAVEIL_OBJECT_READ,
      RAVEIL_OBJECT_BACKING_IMMUTABLE);
  assert(job_object_register(&high));
  assert(job_object_lookup(high.object_id,&observed) && observed.object_id==high.object_id);
  struct raveil_job_descriptor_v1 high_job=job(99u);
  high_job.object_count=1u; high_job.objects[0].object_id=high.object_id;
  high_job.objects[0].generation=1u; high_job.objects[0].expected_version=1u;
  high_job.objects[0].length=8u; memset(&high_job.objects[1],0,sizeof(high_job.objects[1]));
  assert(job_submit(&high_job));
  struct sonatine_submission issued;
  assert(job_submission_take(&issued));
  struct raveil_completion_record_v1 done=completion(&issued),wrong,taken;
  done.output_count=0u; memset(done.outputs,0,sizeof(done.outputs));
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  for(uint64_t id=3u;id<=7u;++id) {
    copy=manifest(id,1u,1u,1u,RAVEIL_OBJECT_READ,RAVEIL_OBJECT_BACKING_IMMUTABLE);
    assert(job_object_register(&copy));
  }
  copy=manifest(8u,1u,1u,1u,RAVEIL_OBJECT_READ,RAVEIL_OBJECT_BACKING_IMMUTABLE);
  assert(!job_object_register(&copy));
  struct raveil_job_descriptor_v1 valid=job(100u),bad;
  bad=valid; bad.objects[0].generation=99u; assert(!job_submit(&bad));
  bad=valid; bad.objects[1].expected_version=4u; assert(!job_submit(&bad));
  bad=valid; bad.objects[1].offset=16u; assert(!job_submit(&bad));
  bad=valid; bad.objects[0].access=RAVEIL_OBJECT_WRITE; assert(!job_submit(&bad));
  assert(job_submission_count()==0u && job_inflight_count()==0u);
  assert(job_submit(&valid)); assert(!job_submit(&valid));
  wrong=(struct raveil_completion_record_v1){0};
  wrong.magic=RAVEIL_COMPLETION_MAGIC; wrong.schema_version=RAVEIL_JOB_SCHEMA_V1;
  wrong.struct_size=sizeof(wrong); wrong.status=RAVEIL_COMPLETION_EXECUTED;
  wrong.job_id=valid.job_id; wrong.execution_epoch=42u; wrong.execution_sequence=2u;
  predictable_cookie(wrong.completion_cookie,42u,valid.job_id,2u);
  wrong.output_count=1u;
  wrong.outputs[0]=(struct raveil_object_version_v1){2u,4u,6u};
  assert(!job_completion_post(&wrong));
  assert(job_submission_count()==1u && job_inflight_count()==1u);
  assert(job_submission_take(&issued)); assert(!job_submission_take(&issued));
  assert(issued.execution_epoch==42u && issued.execution_sequence==2u);
  uint8_t zero[16]={0}; assert(memcmp(issued.completion_cookie,zero,16u)!=0);
  done=completion(&issued);
  wrong=done; wrong.job_id=101u; assert(!job_completion_post(&wrong));
  wrong=done; wrong.execution_epoch=41u; assert(!job_completion_post(&wrong));
  wrong=done; wrong.execution_sequence=3u; assert(!job_completion_post(&wrong));
  wrong=done; wrong.completion_cookie[0]^=1u; assert(!job_completion_post(&wrong));
  assert(job_completion_count()==0u && job_inflight_count()==1u);
  assert(job_completion_post(&done)); assert(!job_completion_post(&done));
  assert(job_completion_take(&taken)); assert(!job_completion_take(&taken));
  assert(memcmp(&taken,&done,sizeof(done))==0 && job_inflight_count()==0u);
  assert(!job_completion_post(&done));
  assert(job_object_lookup(2u,&observed) && observed.version==5u);
  /* FIFO, bounded backpressure, and wrap/reuse. */
  for(uint64_t id=200u;id<204u;++id) { valid=job(id); assert(job_submit(&valid)); }
  valid=job(204u); assert(!job_submit(&valid));
  assert(job_submission_count()==4u && job_inflight_count()==4u);
  uint64_t expected_sequence=3u; uint8_t previous_cookie[16]={0};
  for(uint64_t id=200u;id<204u;++id) {
    assert(job_submission_take(&issued)); assert(issued.job.job_id==id);
    assert(issued.execution_sequence==expected_sequence++);
    assert(memcmp(previous_cookie,issued.completion_cookie,16u)!=0);
    memcpy(previous_cookie,issued.completion_cookie,16u);
    done=completion(&issued); assert(job_completion_post(&done));
  }
  assert(job_completion_count()==4u); assert(!job_completion_post(&done));
  for(uint64_t id=200u;id<204u;++id) {
    assert(job_completion_take(&taken)); assert(taken.job_id==id);
  }
  valid=job(300u); assert(job_submit(&valid)); assert(job_submission_take(&issued));
  assert(issued.execution_sequence==7u);
  done=completion(&issued); assert(job_completion_post(&done));
  assert(job_completion_take(&taken)); assert(job_inflight_count()==0u);
  return 0;
}
