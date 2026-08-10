#include "job_authority.h"

struct object_slot { bool active; struct raveil_object_manifest_v1 value; };
struct inflight_slot {
  bool active;
  bool dispatched;
  bool completion_posted;
  bool cancel_requested;
  struct sonatine_submission submission;
};
struct shadow_slot {
  bool active;
  bool approved;
  bool cancel_requested;
  struct sonatine_submission submission;
  struct raveil_completion_record_v1 completion;
};
static struct object_slot objects[SONATINE_OBJECT_TABLE_SIZE];
static struct sonatine_submission submissions[SONATINE_JOB_RING_DEPTH];
static struct raveil_completion_record_v1 completions[SONATINE_JOB_RING_DEPTH];
static struct inflight_slot inflight[SONATINE_JOB_RING_DEPTH];
static struct shadow_slot shadows[SONATINE_JOB_RING_DEPTH];
static size_t submission_read,submission_write,submission_used;
static size_t completion_read,completion_write,completion_used;
static uint64_t authority_epoch,next_sequence;

static void bytes_zero(void *target,size_t size) {
  uint8_t *bytes=(uint8_t *)target;
  for(size_t index=0;index<size;++index) bytes[index]=0u;
}
static bool bytes_equal(const void *left,const void *right,size_t size) {
  const uint8_t *a=(const uint8_t *)left,*b=(const uint8_t *)right;
  for(size_t index=0;index<size;++index) if(a[index]!=b[index]) return false;
  return true;
}
void job_authority_init(uint64_t execution_epoch) {
  bytes_zero(objects,sizeof(objects)); bytes_zero(submissions,sizeof(submissions));
  bytes_zero(completions,sizeof(completions)); bytes_zero(inflight,sizeof(inflight));
  bytes_zero(shadows,sizeof(shadows));
  submission_read=0u; submission_write=0u; submission_used=0u;
  completion_read=0u; completion_write=0u; completion_used=0u;
  authority_epoch=execution_epoch==0u?1u:execution_epoch; next_sequence=1u;
}
bool job_object_register(const struct raveil_object_manifest_v1 *manifest) {
  if(!raveil_object_manifest_validate_v1(manifest)) return false;
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index)
    if(objects[index].active && objects[index].value.object_id==manifest->object_id)
      return false;
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index) if(!objects[index].active) {
    objects[index].active=true; objects[index].value=*manifest; return true;
  }
  return false;
}
bool job_object_lookup(uint64_t object_id,
                       struct raveil_object_manifest_v1 *manifest) {
  if(object_id==0u || manifest==NULL) return false;
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index)
    if(objects[index].active && objects[index].value.object_id==object_id) {
      *manifest=objects[index].value; return true;
    }
  return false;
}
static bool admitted(const struct raveil_job_descriptor_v1 *job) {
  if(!raveil_job_descriptor_validate_v1(job)) return false;
  for(uint16_t ref_index=0;ref_index<job->object_count;++ref_index) {
    const struct raveil_object_ref_v1 *ref=&job->objects[ref_index];
    struct raveil_object_manifest_v1 manifest;
    if(!job_object_lookup(ref->object_id,&manifest) ||
       manifest.generation!=ref->generation || manifest.version!=ref->expected_version ||
       (manifest.permitted_access&ref->access)!=ref->access ||
       ref->offset>manifest.byte_length || ref->length>manifest.byte_length-ref->offset ||
       (ref->access==RAVEIL_OBJECT_WRITE && ref->expected_version==UINT64_MAX))
      return false;
  }
  return true;
}
static void make_cookie(uint8_t cookie[16],uint64_t job_id,uint64_t sequence) {
  uint64_t first=job_id^authority_epoch^UINT64_C(0x72617665696c6a31);
  uint64_t second=sequence^UINT64_C(0x736f6e6174696e65);
  for(size_t index=0;index<8u;++index) {
    cookie[index]=(uint8_t)(first>>(index*8u));
    cookie[index+8u]=(uint8_t)(second>>(index*8u));
  }
}
static void binding_from_submission(const struct sonatine_submission *submission,
                                    struct sonatine_job_binding *binding) {
  binding->job_id=submission->job.job_id;
  binding->execution_epoch=submission->execution_epoch;
  binding->execution_sequence=submission->execution_sequence;
  for(size_t index=0;index<16u;++index)
    binding->completion_cookie[index]=submission->completion_cookie[index];
}
static bool binding_matches(const struct sonatine_job_binding *binding,
                            const struct sonatine_submission *submission) {
  return binding!=NULL && binding->job_id==submission->job.job_id &&
         binding->execution_epoch==submission->execution_epoch &&
         binding->execution_sequence==submission->execution_sequence &&
         bytes_equal(binding->completion_cookie,submission->completion_cookie,16u);
}
static bool submission_matches(const struct sonatine_submission *left,
                               const struct sonatine_submission *right) {
  return left->job.job_id==right->job.job_id &&
         left->execution_epoch==right->execution_epoch &&
         left->execution_sequence==right->execution_sequence &&
         bytes_equal(left->completion_cookie,right->completion_cookie,16u);
}
bool job_submit_bound(const struct raveil_job_descriptor_v1 *job,
                      struct sonatine_job_binding *binding) {
  if(binding==NULL) return false;
  if(!admitted(job) || submission_used==SONATINE_JOB_RING_DEPTH ||
     next_sequence==0u) return false;
  size_t slot=SONATINE_JOB_RING_DEPTH;
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(!inflight[index].active && !shadows[index].active) { slot=index; break; }
  if(slot==SONATINE_JOB_RING_DEPTH) return false;
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(inflight[index].active && inflight[index].submission.job.job_id==job->job_id)
      return false;
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(shadows[index].active && shadows[index].submission.job.job_id==job->job_id)
      return false;
  struct sonatine_submission value;
  bytes_zero(&value,sizeof(value)); value.job=*job;
  value.execution_epoch=authority_epoch; value.execution_sequence=next_sequence++;
  make_cookie(value.completion_cookie,job->job_id,value.execution_sequence);
  submissions[submission_write]=value;
  submission_write=(submission_write+1u)%SONATINE_JOB_RING_DEPTH; ++submission_used;
  inflight[slot].active=true; inflight[slot].dispatched=false;
  inflight[slot].completion_posted=false;
  inflight[slot].cancel_requested=false;
  inflight[slot].submission=value;
  binding_from_submission(&value,binding);
  return true;
}
bool job_submit(const struct raveil_job_descriptor_v1 *job) {
  struct sonatine_job_binding ignored;
  return job_submit_bound(job,&ignored);
}
bool job_submission_take(struct sonatine_submission *submission) {
  if(submission==NULL || submission_used==0u) return false;
  while(submission_used!=0u) {
    *submission=submissions[submission_read];
    bytes_zero(&submissions[submission_read],sizeof(submissions[submission_read]));
    submission_read=(submission_read+1u)%SONATINE_JOB_RING_DEPTH; --submission_used;
    for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
      if(inflight[index].active && !inflight[index].dispatched &&
         submission_matches(&inflight[index].submission,submission)) {
        inflight[index].dispatched=true; return true;
      }
    bytes_zero(submission,sizeof(*submission));
    if(submission_used==0u) return false;
    }
  return false;
}
bool job_completion_post(const struct raveil_completion_record_v1 *completion) {
  if(completion==NULL || completion_used==SONATINE_JOB_RING_DEPTH) return false;
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index) {
    struct inflight_slot *entry=&inflight[index];
    if(entry->active && entry->dispatched && !entry->completion_posted &&
       completion->job_id==entry->submission.job.job_id &&
       completion->execution_epoch==entry->submission.execution_epoch &&
       completion->execution_sequence==entry->submission.execution_sequence &&
       bytes_equal(completion->completion_cookie,entry->submission.completion_cookie,16u) &&
       raveil_completion_record_validate_v1(&entry->submission.job,completion)) {
      completions[completion_write]=*completion;
      completion_write=(completion_write+1u)%SONATINE_JOB_RING_DEPTH; ++completion_used;
      entry->completion_posted=true; return true;
    }
  }
  return false;
}
bool job_completion_take(struct raveil_completion_record_v1 *completion) {
  if(completion==NULL || completion_used==0u) return false;
  *completion=completions[completion_read];
  bytes_zero(&completions[completion_read],sizeof(completions[completion_read]));
  completion_read=(completion_read+1u)%SONATINE_JOB_RING_DEPTH; --completion_used;
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(inflight[index].active && inflight[index].completion_posted &&
       completion->job_id==inflight[index].submission.job.job_id &&
       completion->execution_epoch==inflight[index].submission.execution_epoch &&
       completion->execution_sequence==inflight[index].submission.execution_sequence &&
       bytes_equal(completion->completion_cookie,
                   inflight[index].submission.completion_cookie,16u)) {
      shadows[index].active=true; shadows[index].approved=false;
      shadows[index].cancel_requested=inflight[index].cancel_requested;
      shadows[index].submission=inflight[index].submission;
      shadows[index].completion=*completion;
      bytes_zero(&inflight[index],sizeof(inflight[index])); break;
    }
  return true;
}
static struct shadow_slot *find_shadow(const struct sonatine_job_binding *binding) {
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(shadows[index].active && binding_matches(binding,&shadows[index].submission))
      return &shadows[index];
  return NULL;
}
bool job_shadow_approve(const struct sonatine_job_binding *binding) {
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL || shadow->cancel_requested ||
     shadow->completion.status!=RAVEIL_COMPLETION_EXECUTED) return false;
  shadow->approved=true; return true;
}
bool job_cancel(const struct sonatine_job_binding *binding) {
  if(binding==NULL) return false;
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(inflight[index].active && binding_matches(binding,&inflight[index].submission)) {
      if(inflight[index].cancel_requested) return false;
      inflight[index].cancel_requested=true;
      if(!inflight[index].dispatched) {
        struct sonatine_submission kept[SONATINE_JOB_RING_DEPTH];
        size_t count=0u;
        while(submission_used!=0u) {
          struct sonatine_submission value=submissions[submission_read];
          bytes_zero(&submissions[submission_read],sizeof(submissions[submission_read]));
          submission_read=(submission_read+1u)%SONATINE_JOB_RING_DEPTH; --submission_used;
          if(!binding_matches(binding,&value)) kept[count++]=value;
        }
        submission_read=0u; submission_write=count%SONATINE_JOB_RING_DEPTH;
        for(size_t kept_index=0;kept_index<count;++kept_index)
          submissions[kept_index]=kept[kept_index];
        submission_used=count;
        bytes_zero(&inflight[index],sizeof(inflight[index]));
      }
      return true;
    }
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL || shadow->cancel_requested) return false;
  shadow->cancel_requested=true; shadow->approved=false; return true;
}
static struct object_slot *find_object(uint64_t id) {
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index)
    if(objects[index].active && objects[index].value.object_id==id) return &objects[index];
  return NULL;
}
enum sonatine_finalize_result job_shadow_finalize(
    const struct sonatine_job_binding *binding,bool commit) {
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL) return SONATINE_FINALIZE_INVALID;
  if(!commit || shadow->cancel_requested || !shadow->approved) {
    bytes_zero(shadow,sizeof(*shadow));
    return SONATINE_FINALIZE_ROLLED_BACK;
  }
  const struct raveil_job_descriptor_v1 *job=&shadow->submission.job;
  for(uint16_t index=0;index<job->object_count;++index) {
    const struct raveil_object_ref_v1 *ref=&job->objects[index];
    struct object_slot *object=find_object(ref->object_id);
    if(object==NULL || object->value.generation!=ref->generation ||
       object->value.version!=ref->expected_version ||
       object->value.byte_length<ref->offset ||
       object->value.byte_length-ref->offset<ref->length) {
      bytes_zero(shadow,sizeof(*shadow)); return SONATINE_FINALIZE_CONFLICT;
    }
  }
  for(uint16_t index=0;index<shadow->completion.output_count;++index) {
    const struct raveil_object_version_v1 *output=&shadow->completion.outputs[index];
    struct object_slot *object=find_object(output->object_id);
    if(object==NULL || object->value.generation!=output->generation ||
       object->value.version==UINT64_MAX || output->version!=object->value.version+1u) {
      bytes_zero(shadow,sizeof(*shadow)); return SONATINE_FINALIZE_CONFLICT;
    }
  }
  for(uint16_t index=0;index<shadow->completion.output_count;++index) {
    struct object_slot *object=find_object(shadow->completion.outputs[index].object_id);
    object->value.version=shadow->completion.outputs[index].version;
  }
  bytes_zero(shadow,sizeof(*shadow)); return SONATINE_FINALIZE_COMMITTED;
}
size_t job_submission_count(void) { return submission_used; }
size_t job_completion_count(void) { return completion_used; }
size_t job_inflight_count(void) {
  size_t count=0u; for(size_t i=0;i<SONATINE_JOB_RING_DEPTH;++i) if(inflight[i].active) ++count;
  return count;
}
size_t job_shadow_count(void) {
  size_t count=0u; for(size_t i=0;i<SONATINE_JOB_RING_DEPTH;++i) if(shadows[i].active) ++count;
  return count;
}
