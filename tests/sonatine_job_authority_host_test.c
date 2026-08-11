#include <assert.h>
#include <string.h>
#include "sonatine_job_authority_test_api.h"

void console_write(const char *text) { (void)text; }
void console_write_dec(uint64_t value) { (void)value; }
void console_write_hex(uint64_t value) { (void)value; }

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
static struct sonatine_job_binding binding(const struct sonatine_submission *submission) {
  struct sonatine_job_binding value={0}; value.job_id=submission->job.job_id;
  value.execution_epoch=submission->execution_epoch;
  value.execution_sequence=submission->execution_sequence;
  memcpy(value.completion_cookie,submission->completion_cookie,16u); return value;
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
  struct sonatine_job_binding bound=binding(&issued);
  assert(job_shadow_approve(&bound));
  assert(job_shadow_finalize(&bound,false)==SONATINE_FINALIZE_ROLLED_BACK);
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
  bound=binding(&issued);
  assert(memcmp(&taken,&done,sizeof(done))==0 && job_inflight_count()==0u &&
         job_shadow_count()==1u);
  assert(job_shadow_approve(&bound));
  assert(job_shadow_finalize(&bound,false)==SONATINE_FINALIZE_ROLLED_BACK);
  assert(job_shadow_finalize(&bound,false)==SONATINE_FINALIZE_INVALID);
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
    /* Recover the binding from the completion for explicit rollback. */
    bound=(struct sonatine_job_binding){0}; bound.job_id=taken.job_id;
    bound.execution_epoch=taken.execution_epoch;
    bound.execution_sequence=taken.execution_sequence;
    memcpy(bound.completion_cookie,taken.completion_cookie,16u);
    assert(job_shadow_finalize(&bound,false)==SONATINE_FINALIZE_ROLLED_BACK);
  }
  valid=job(300u); assert(job_submit(&valid)); assert(job_submission_take(&issued));
  assert(issued.execution_sequence==7u);
  done=completion(&issued); assert(job_completion_post(&done));
  assert(job_completion_take(&taken)); bound=binding(&issued);
  assert(job_shadow_finalize(&bound,false)==SONATINE_FINALIZE_ROLLED_BACK);
  assert(job_inflight_count()==0u && job_shadow_count()==0u);

  /* T-0033 explicit approval, publish, conflict, and cancellation. */
  job_authority_init(77u);
  input=manifest(1u,1u,1u,16u,RAVEIL_OBJECT_READ,RAVEIL_OBJECT_BACKING_IMMUTABLE);
  output=manifest(2u,1u,1u,16u,RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE,
                  RAVEIL_OBJECT_BACKING_VOLATILE);
  struct raveil_object_manifest_v1 output_two=manifest(
      3u,1u,1u,16u,RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE,
      RAVEIL_OBJECT_BACKING_VOLATILE);
  assert(job_object_register(&input)); assert(job_object_register(&output));
  assert(job_object_register(&output_two));
  valid=job(400u); valid.objects[0].generation=1u; valid.objects[0].expected_version=1u;
  valid.objects[1].generation=1u; valid.objects[1].expected_version=1u;
  valid.objects[1].offset=0u;
  assert(job_submit_bound(&valid,&bound)); assert(job_submission_take(&issued));
  done=completion(&issued); done.outputs[0].generation=1u; done.outputs[0].version=2u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_object_lookup(2u,&observed) && observed.version==1u);
  assert(job_shadow_finalize(&bound,true)==SONATINE_FINALIZE_ROLLED_BACK);
  assert(job_object_lookup(2u,&observed) && observed.version==1u);

  valid.job_id=401u; assert(job_submit_bound(&valid,&bound));
  assert(job_submission_take(&issued)); done=completion(&issued);
  done.outputs[0].generation=1u; done.outputs[0].version=2u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_shadow_approve(&bound));
  assert(job_shadow_finalize(&bound,true)==SONATINE_FINALIZE_COMMITTED);
  assert(job_object_lookup(2u,&observed) && observed.version==2u);
  assert(job_shadow_finalize(&bound,true)==SONATINE_FINALIZE_INVALID);

  valid.job_id=402u; valid.objects[1].expected_version=2u;
  struct sonatine_job_binding cancelled_binding;
  assert(job_submit_bound(&valid,&cancelled_binding));
  assert(job_cancel(&cancelled_binding));
  assert(job_submission_count()==0u && job_inflight_count()==0u);
  assert(!job_cancel(&cancelled_binding));
  /* A cancelled queued entry cannot dispatch through a reused job ID. */
  assert(job_submit_bound(&valid,&bound));
  assert(job_submission_take(&issued));
  assert(issued.job.job_id==bound.job_id);
  assert(issued.execution_epoch==bound.execution_epoch);
  assert(issued.execution_sequence==bound.execution_sequence);
  assert(memcmp(issued.completion_cookie,bound.completion_cookie,16u)==0);
  assert(!job_cancel(&cancelled_binding));
  done=completion(&issued); done.outputs[0].generation=1u;
  done.outputs[0].version=3u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_shadow_finalize(&cancelled_binding,false)==SONATINE_FINALIZE_INVALID);
  assert(job_shadow_finalize(&bound,false)==SONATINE_FINALIZE_ROLLED_BACK);

  /* Two shadows may race; only the first exact-version commit wins. */
  valid.objects[1].expected_version=2u;
  struct raveil_job_descriptor_v1 contender=valid;
  valid.job_id=403u; contender.job_id=404u;
  struct sonatine_job_binding first_binding,second_binding;
  assert(job_submit_bound(&valid,&first_binding));
  assert(job_submit_bound(&contender,&second_binding));
  assert(job_submission_take(&issued)); done=completion(&issued);
  done.outputs[0].generation=1u; done.outputs[0].version=3u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_shadow_approve(&first_binding));
  assert(job_submission_take(&issued)); done=completion(&issued);
  done.outputs[0].generation=1u; done.outputs[0].version=3u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_shadow_approve(&second_binding));
  assert(job_shadow_finalize(&first_binding,true)==SONATINE_FINALIZE_COMMITTED);
  assert(job_shadow_finalize(&second_binding,true)==SONATINE_FINALIZE_CONFLICT);
  assert(job_object_lookup(2u,&observed) && observed.version==3u);

  /* Structurally valid version jumps and stale bindings fail closed. */
  valid.job_id=408u; valid.objects[1].expected_version=3u;
  assert(job_submit_bound(&valid,&bound)); assert(job_submission_take(&issued));
  done=completion(&issued); done.outputs[0].generation=1u;
  done.outputs[0].version=5u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  struct sonatine_job_binding stale=bound; stale.execution_epoch^=1u;
  assert(!job_shadow_approve(&stale));
  assert(job_shadow_finalize(&stale,true)==SONATINE_FINALIZE_INVALID);
  assert(job_shadow_count()==1u && job_shadow_approve(&bound));
  assert(job_shadow_finalize(&bound,true)==SONATINE_FINALIZE_CONFLICT);
  assert(job_object_lookup(2u,&observed) && observed.version==3u);

  /* A dispatched cancellation wins over a late EXECUTED observation. */
  valid.job_id=405u; valid.objects[1].expected_version=3u;
  assert(job_submit_bound(&valid,&bound)); assert(job_submission_take(&issued));
  assert(job_cancel(&bound)); done=completion(&issued);
  done.outputs[0].generation=1u; done.outputs[0].version=4u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(!job_shadow_approve(&bound));
  assert(job_shadow_finalize(&bound,true)==SONATINE_FINALIZE_ROLLED_BACK);
  assert(job_object_lookup(2u,&observed) && observed.version==3u);

  /* A conflict in the second output publishes neither output. */
  struct raveil_job_descriptor_v1 multi=valid;
  multi.job_id=406u; multi.object_count=3u;
  multi.objects[1].expected_version=3u;
  multi.objects[2]=(struct raveil_object_ref_v1){3u,1u,1u,0u,8u,
                                                 RAVEIL_OBJECT_WRITE,0u};
  multi.resources.max_output_bytes=16u;
  struct raveil_job_descriptor_v1 other=valid;
  other.job_id=407u; other.object_count=1u;
  other.objects[0]=(struct raveil_object_ref_v1){3u,1u,1u,0u,8u,
                                                 RAVEIL_OBJECT_WRITE,0u};
  memset(&other.objects[1],0,3u*sizeof(other.objects[0]));
  struct sonatine_job_binding multi_binding,other_binding;
  assert(job_submit_bound(&multi,&multi_binding));
  assert(job_submit_bound(&other,&other_binding));
  assert(job_submission_take(&issued)); done=completion(&issued);
  done.output_count=2u;
  done.outputs[0]=(struct raveil_object_version_v1){2u,1u,4u};
  done.outputs[1]=(struct raveil_object_version_v1){3u,1u,2u};
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_shadow_approve(&multi_binding));
  assert(job_submission_take(&issued)); done=completion(&issued);
  done.output_count=1u;
  done.outputs[0]=(struct raveil_object_version_v1){3u,1u,2u};
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(job_shadow_approve(&other_binding));
  assert(job_shadow_finalize(&other_binding,true)==SONATINE_FINALIZE_COMMITTED);
  assert(job_shadow_finalize(&multi_binding,true)==SONATINE_FINALIZE_CONFLICT);
  assert(job_object_lookup(2u,&observed) && observed.version==3u);
  assert(job_object_lookup(3u,&observed) && observed.version==2u);
  return 0;
}
