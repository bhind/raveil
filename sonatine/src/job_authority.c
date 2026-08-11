#include "job_authority.h"
#include "plane_authority.h"

struct object_slot {
  bool active;
  struct raveil_object_manifest_v1 value;
  uint8_t visible[SONATINE_OBJECT_MAX_BYTES];
};
struct inflight_slot {
  bool active;
  bool dispatched;
  bool completion_posted;
  bool cancel_requested;
  struct sonatine_submission submission;
  uint8_t snapshot[RAVEIL_JOB_MAX_OBJECTS][SONATINE_OBJECT_MAX_BYTES];
};
struct shadow_slot {
  bool active;
  bool approved;
  bool cancel_requested;
  struct sonatine_submission submission;
  struct raveil_completion_record_v1 completion;
  uint8_t bytes[RAVEIL_JOB_MAX_OBJECTS][SONATINE_OBJECT_MAX_BYTES];
  uint8_t staged[RAVEIL_JOB_MAX_OBJECTS][SONATINE_OBJECT_MAX_BYTES];
};
static struct object_slot objects[SONATINE_OBJECT_TABLE_SIZE];
static struct sonatine_submission submissions[SONATINE_JOB_RING_DEPTH];
static struct raveil_completion_record_v1 completions[SONATINE_JOB_RING_DEPTH];
static struct inflight_slot inflight[SONATINE_JOB_RING_DEPTH];
static struct shadow_slot shadows[SONATINE_JOB_RING_DEPTH];
static size_t submission_read,submission_write,submission_used;
static size_t completion_read,completion_write,completion_used;
static uint64_t authority_epoch,next_sequence;
static struct object_slot *find_object(uint64_t id);

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
static bool job_object_register_bytes_core(
    const struct raveil_object_manifest_v1 *manifest,
    const void *initial_bytes,size_t length,bool zero_initial) {
  if(!raveil_object_manifest_validate_v1(manifest) ||
     manifest->byte_length>SONATINE_OBJECT_MAX_BYTES ||
     (!zero_initial && (initial_bytes==NULL || length!=manifest->byte_length)))
    return false;
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index)
    if(objects[index].active && objects[index].value.object_id==manifest->object_id)
      return false;
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index) if(!objects[index].active) {
    bytes_zero(&objects[index],sizeof(objects[index]));
    objects[index].active=true; objects[index].value=*manifest;
    if(!zero_initial) {
      const uint8_t *source=(const uint8_t *)initial_bytes;
      for(size_t byte=0;byte<length;++byte) objects[index].visible[byte]=source[byte];
    }
    return true;
  }
  return false;
}
static bool job_object_register_core(const struct raveil_object_manifest_v1 *manifest) {
  return job_object_register_bytes_core(manifest,NULL,0u,true);
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
bool job_object_read(uint64_t object_id,uint64_t offset,
                     void *target,size_t length) {
  struct object_slot *object=find_object(object_id);
  if(object==NULL || target==NULL || offset>object->value.byte_length ||
     length>object->value.byte_length-offset) return false;
  uint8_t *out=(uint8_t *)target;
  for(size_t index=0;index<length;++index) out[index]=object->visible[offset+index];
  return true;
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
static bool job_submit_bound_core(const struct raveil_job_descriptor_v1 *job,
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
  for(uint16_t ref_index=0;ref_index<job->object_count;++ref_index) {
    struct object_slot *object=find_object(job->objects[ref_index].object_id);
    for(size_t byte=0;byte<object->value.byte_length;++byte)
      inflight[slot].snapshot[ref_index][byte]=object->visible[byte];
  }
  binding_from_submission(&value,binding);
  return true;
}
bool job_submission_read(const struct sonatine_submission *submission,
                         uint64_t object_id,uint64_t offset,
                         void *target,size_t length) {
  if(submission==NULL || target==NULL) return false;
  for(size_t slot=0;slot<SONATINE_JOB_RING_DEPTH;++slot) {
    struct inflight_slot *entry=&inflight[slot];
    if(!entry->active || !entry->dispatched || entry->completion_posted ||
       entry->cancel_requested ||
       !submission_matches(&entry->submission,submission)) continue;
    for(uint16_t ref_index=0;ref_index<entry->submission.job.object_count;++ref_index) {
      const struct raveil_object_ref_v1 *ref=&entry->submission.job.objects[ref_index];
      if(ref->access!=RAVEIL_OBJECT_READ || ref->object_id!=object_id ||
         offset<ref->offset ||
         offset>ref->offset+ref->length || length>ref->offset+ref->length-offset)
        continue;
      uint8_t *out=(uint8_t *)target;
      for(size_t byte=0;byte<length;++byte)
        out[byte]=entry->snapshot[ref_index][offset+byte];
      return true;
    }
  }
  return false;
}
#ifdef SONATINE_JOB_AUTHORITY_TESTING
static bool job_submit_core(const struct raveil_job_descriptor_v1 *job) {
  struct sonatine_job_binding ignored;
  return job_submit_bound_core(job,&ignored);
}
#endif
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
static bool completion_move_to_shadow(const struct raveil_completion_record_v1 *completion) {
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(inflight[index].active && inflight[index].completion_posted &&
       completion->job_id==inflight[index].submission.job.job_id &&
       completion->execution_epoch==inflight[index].submission.execution_epoch &&
       completion->execution_sequence==inflight[index].submission.execution_sequence &&
       bytes_equal(completion->completion_cookie,
                   inflight[index].submission.completion_cookie,16u)) {
      bytes_zero(&shadows[index],sizeof(shadows[index]));
      shadows[index].active=true; shadows[index].approved=false;
      shadows[index].cancel_requested=inflight[index].cancel_requested;
      shadows[index].submission=inflight[index].submission;
      shadows[index].completion=*completion;
      bytes_zero(&inflight[index],sizeof(inflight[index])); break;
    }
  return true;
}
static bool completion_take_offset(size_t offset,
                                   struct raveil_completion_record_v1 *completion) {
  if(completion==NULL || offset>=completion_used) return false;
  const size_t position=(completion_read+offset)%SONATINE_JOB_RING_DEPTH;
  *completion=completions[position];
  for(size_t index=offset;index+1u<completion_used;++index) {
    const size_t from=(completion_read+index)%SONATINE_JOB_RING_DEPTH;
    const size_t next=(completion_read+index+1u)%SONATINE_JOB_RING_DEPTH;
    completions[from]=completions[next];
  }
  const size_t last=(completion_read+completion_used-1u)%SONATINE_JOB_RING_DEPTH;
  bytes_zero(&completions[last],sizeof(completions[last]));
  --completion_used;
  completion_write=(completion_read+completion_used)%SONATINE_JOB_RING_DEPTH;
  return completion_move_to_shadow(completion);
}
bool job_completion_take(struct raveil_completion_record_v1 *completion) {
  return completion_take_offset(0u,completion);
}
bool job_completion_pending(const struct sonatine_job_binding *binding) {
  if(binding==NULL) return false;
  for(size_t index=0u;index<completion_used;++index) {
    const struct raveil_completion_record_v1 *completion=
        &completions[(completion_read+index)%SONATINE_JOB_RING_DEPTH];
    if(completion->job_id==binding->job_id &&
       completion->execution_epoch==binding->execution_epoch &&
       completion->execution_sequence==binding->execution_sequence &&
       bytes_equal(completion->completion_cookie,binding->completion_cookie,16u)) return true;
  }
  return false;
}
bool job_completion_take_bound(const struct sonatine_job_binding *binding,
                               struct raveil_completion_record_v1 *completion) {
  if(binding==NULL) return false;
  for(size_t index=0u;index<completion_used;++index) {
    const struct raveil_completion_record_v1 *pending=
        &completions[(completion_read+index)%SONATINE_JOB_RING_DEPTH];
    if(pending->job_id==binding->job_id &&
       pending->execution_epoch==binding->execution_epoch &&
       pending->execution_sequence==binding->execution_sequence &&
       bytes_equal(pending->completion_cookie,binding->completion_cookie,16u))
      return completion_take_offset(index,completion);
  }
  return false;
}
static struct shadow_slot *find_shadow(const struct sonatine_job_binding *binding) {
  for(size_t index=0;index<SONATINE_JOB_RING_DEPTH;++index)
    if(shadows[index].active && binding_matches(binding,&shadows[index].submission))
      return &shadows[index];
  return NULL;
}
static bool job_shadow_approve_core(const struct sonatine_job_binding *binding) {
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL || shadow->cancel_requested ||
     shadow->completion.status!=RAVEIL_COMPLETION_EXECUTED) return false;
  for(uint16_t ref_index=0;ref_index<shadow->submission.job.object_count;++ref_index) {
    const struct raveil_object_ref_v1 *ref=&shadow->submission.job.objects[ref_index];
    if(ref->access!=RAVEIL_OBJECT_WRITE) continue;
    for(uint64_t byte=ref->offset;byte<ref->offset+ref->length;++byte)
      if(shadow->staged[ref_index][byte]==0u) return false;
  }
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
      } else bytes_zero(inflight[index].snapshot,sizeof(inflight[index].snapshot));
      return true;
    }
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL || shadow->cancel_requested) return false;
  shadow->cancel_requested=true; shadow->approved=false;
  bytes_zero(shadow->bytes,sizeof(shadow->bytes));
  bytes_zero(shadow->staged,sizeof(shadow->staged));
  return true;
}
static struct object_slot *find_object(uint64_t id) {
  for(size_t index=0;index<SONATINE_OBJECT_TABLE_SIZE;++index)
    if(objects[index].active && objects[index].value.object_id==id) return &objects[index];
  return NULL;
}
static enum sonatine_finalize_result job_shadow_finalize_core(
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
  for(uint16_t ref_index=0;ref_index<job->object_count;++ref_index) {
    const struct raveil_object_ref_v1 *ref=&job->objects[ref_index];
    if(ref->access!=RAVEIL_OBJECT_WRITE) continue;
    struct object_slot *object=find_object(ref->object_id);
    for(uint64_t byte=ref->offset;byte<ref->offset+ref->length;++byte)
      object->visible[byte]=shadow->bytes[ref_index][byte];
  }
  for(uint16_t index=0;index<shadow->completion.output_count;++index) {
    struct object_slot *object=find_object(shadow->completion.outputs[index].object_id);
    object->value.version=shadow->completion.outputs[index].version;
  }
  bytes_zero(shadow,sizeof(*shadow)); return SONATINE_FINALIZE_COMMITTED;
}

struct program_authority_entry { bool active; uint8_t identity[16]; };
struct graph_authority_entry {
  bool active; uint8_t program_identity[16]; uint8_t graph_identity[16];
};
struct experience_authority_entry {
  bool active; struct raveil_completion_record_v1 completion;
};
static struct program_authority_entry plane_programs[SONATINE_PROGRAM_REGISTRY_SIZE];
static struct graph_authority_entry plane_graphs[SONATINE_GRAPH_REGISTRY_SIZE];
static struct experience_authority_entry plane_experience[SONATINE_EXPERIENCE_LEDGER_SIZE];
static size_t plane_experience_used;

static bool identity_nonzero(const uint8_t value[16]) {
  if(value==NULL) return false;
  for(size_t index=0;index<16u;++index) if(value[index]!=0u) return true;
  return false;
}
static void identity_copy(uint8_t target[16],const uint8_t source[16]) {
  for(size_t index=0;index<16u;++index) target[index]=source[index];
}
static bool identity_equal(const uint8_t left[16],const uint8_t right[16]) {
  return bytes_equal(left,right,16u);
}
static bool plane_cap_authorized(uint16_t task,cap_handle_t cap,
                                 uint16_t type,uint32_t right) {
  struct cap_view view;
  return cap_resolve(task,cap,type,right,&view) &&
         view.object_id==SONATINE_PLANE_AUTHORITY_OBJECT;
}

void plane_authority_init(void) {
  bytes_zero(plane_programs,sizeof(plane_programs));
  bytes_zero(plane_graphs,sizeof(plane_graphs));
  bytes_zero(plane_experience,sizeof(plane_experience));
  plane_experience_used=0u;
}

bool plane_program_install(uint16_t task,cap_handle_t cap,
                           const uint8_t identity[16]) {
  if(!plane_cap_authorized(task,cap,CAP_OBJECT_PROGRAM_AUTHORITY,CAP_RIGHT_CONTROL) ||
     !identity_nonzero(identity)) return false;
  for(size_t index=0;index<SONATINE_PROGRAM_REGISTRY_SIZE;++index)
    if(plane_programs[index].active &&
       identity_equal(plane_programs[index].identity,identity)) return false;
  for(size_t index=0;index<SONATINE_PROGRAM_REGISTRY_SIZE;++index)
    if(!plane_programs[index].active) {
      plane_programs[index].active=true;
      identity_copy(plane_programs[index].identity,identity); return true;
    }
  return false;
}

bool plane_graph_install(uint16_t task,cap_handle_t cap,
                         const uint8_t program[16],const uint8_t graph[16]) {
  if(!plane_cap_authorized(task,cap,CAP_OBJECT_GRAPH_AUTHORITY,CAP_RIGHT_CONTROL) ||
     !identity_nonzero(program) || !identity_nonzero(graph)) return false;
  bool program_known=false;
  for(size_t index=0;index<SONATINE_PROGRAM_REGISTRY_SIZE;++index)
    if(plane_programs[index].active &&
       identity_equal(plane_programs[index].identity,program)) program_known=true;
  if(!program_known) return false;
  for(size_t index=0;index<SONATINE_GRAPH_REGISTRY_SIZE;++index)
    if(plane_graphs[index].active &&
       identity_equal(plane_graphs[index].graph_identity,graph)) return false;
  for(size_t index=0;index<SONATINE_GRAPH_REGISTRY_SIZE;++index)
    if(!plane_graphs[index].active) {
      plane_graphs[index].active=true;
      identity_copy(plane_graphs[index].program_identity,program);
      identity_copy(plane_graphs[index].graph_identity,graph); return true;
    }
  return false;
}

static bool plane_job_pair_installed(const struct raveil_job_descriptor_v1 *job) {
  if(job==NULL) return false;
  for(size_t index=0;index<SONATINE_GRAPH_REGISTRY_SIZE;++index)
    if(plane_graphs[index].active &&
       identity_equal(plane_graphs[index].program_identity,job->program_identity) &&
       identity_equal(plane_graphs[index].graph_identity,job->graph_variant_identity))
      return true;
  return false;
}

bool plane_data_object_register(uint16_t task,cap_handle_t cap,
                                const struct raveil_object_manifest_v1 *manifest) {
  return plane_cap_authorized(task,cap,CAP_OBJECT_DATA_AUTHORITY,CAP_RIGHT_WRITE) &&
         job_object_register_core(manifest);
}
bool plane_data_object_register_bytes(
    uint16_t task,cap_handle_t cap,
    const struct raveil_object_manifest_v1 *manifest,
    const void *initial_bytes,size_t length) {
  return plane_cap_authorized(task,cap,CAP_OBJECT_DATA_AUTHORITY,CAP_RIGHT_WRITE) &&
         job_object_register_bytes_core(manifest,initial_bytes,length,false);
}

bool plane_job_submit_bound(uint16_t task,cap_handle_t data_cap,
                            const struct raveil_job_descriptor_v1 *job,
                            struct sonatine_job_binding *binding) {
  return plane_cap_authorized(task,data_cap,CAP_OBJECT_DATA_AUTHORITY,CAP_RIGHT_WRITE) &&
         plane_job_pair_installed(job) && job_submit_bound_core(job,binding);
}

bool plane_program_approve(uint16_t task,cap_handle_t program_cap,
                           const struct sonatine_job_binding *binding) {
  return plane_cap_authorized(task,program_cap,CAP_OBJECT_PROGRAM_AUTHORITY,
                              CAP_RIGHT_CONTROL) &&
         job_shadow_approve_core(binding);
}
static bool job_shadow_write_core(const struct sonatine_job_binding *binding,
                                  uint64_t object_id,uint64_t offset,
                                  const void *source,size_t length) {
  if(binding==NULL || source==NULL || length==0u) return false;
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL || shadow->approved || shadow->cancel_requested ||
     shadow->completion.status!=RAVEIL_COMPLETION_EXECUTED) return false;
  for(uint16_t ref_index=0;ref_index<shadow->submission.job.object_count;++ref_index) {
    const struct raveil_object_ref_v1 *ref=&shadow->submission.job.objects[ref_index];
    if(ref->object_id!=object_id || ref->access!=RAVEIL_OBJECT_WRITE ||
       offset<ref->offset || offset>ref->offset+ref->length ||
       length>ref->offset+ref->length-offset) continue;
    for(size_t byte=0;byte<length;++byte)
      if(shadow->staged[ref_index][offset+byte]!=0u) return false;
    const uint8_t *input=(const uint8_t *)source;
    for(size_t byte=0;byte<length;++byte) {
      shadow->bytes[ref_index][offset+byte]=input[byte];
      shadow->staged[ref_index][offset+byte]=1u;
    }
    return true;
  }
  return false;
}
bool plane_data_shadow_write(uint16_t task,cap_handle_t data_cap,
                             const struct sonatine_job_binding *binding,
                             uint64_t object_id,uint64_t offset,
                             const void *source,size_t length) {
  return plane_cap_authorized(task,data_cap,CAP_OBJECT_DATA_AUTHORITY,
                              CAP_RIGHT_WRITE) &&
         job_shadow_write_core(binding,object_id,offset,source,length);
}

enum sonatine_finalize_result plane_data_finalize(
    uint16_t task,cap_handle_t data_cap,
    const struct sonatine_job_binding *binding,bool commit) {
  if(!plane_cap_authorized(task,data_cap,CAP_OBJECT_DATA_AUTHORITY,CAP_RIGHT_WRITE))
    return SONATINE_FINALIZE_INVALID;
  return job_shadow_finalize_core(binding,commit);
}

bool plane_experience_record(uint16_t task,cap_handle_t experience_cap,
                             const struct raveil_completion_record_v1 *completion) {
  if(!plane_cap_authorized(task,experience_cap,CAP_OBJECT_EXPERIENCE_AUTHORITY,
                           CAP_RIGHT_WRITE) || completion==NULL ||
     plane_experience_used==SONATINE_EXPERIENCE_LEDGER_SIZE) return false;
  struct sonatine_job_binding binding={0};
  binding.job_id=completion->job_id;
  binding.execution_epoch=completion->execution_epoch;
  binding.execution_sequence=completion->execution_sequence;
  for(size_t index=0;index<16u;++index)
    binding.completion_cookie[index]=completion->completion_cookie[index];
  struct shadow_slot *shadow=find_shadow(&binding);
  if(shadow==NULL ||
     !bytes_equal(&shadow->completion,completion,sizeof(*completion))) return false;
  for(size_t index=0;index<plane_experience_used;++index)
    if(bytes_equal(&plane_experience[index].completion,completion,sizeof(*completion)))
      return false;
  plane_experience[plane_experience_used].active=true;
  plane_experience[plane_experience_used].completion=*completion;
  ++plane_experience_used; return true;
}

size_t plane_experience_count(void) { return plane_experience_used; }

#ifdef SONATINE_JOB_AUTHORITY_TESTING
bool job_object_register_test(const struct raveil_object_manifest_v1 *manifest) {
  return job_object_register_core(manifest);
}
bool job_submit_test(const struct raveil_job_descriptor_v1 *job) {
  return job_submit_core(job);
}
bool job_submit_bound_test(const struct raveil_job_descriptor_v1 *job,
                           struct sonatine_job_binding *binding) {
  return job_submit_bound_core(job,binding);
}
bool job_shadow_approve_test(const struct sonatine_job_binding *binding) {
  return job_shadow_approve_core(binding);
}
bool job_shadow_stage_zero_test(const struct sonatine_job_binding *binding) {
  struct shadow_slot *shadow=find_shadow(binding);
  if(shadow==NULL || shadow->approved) return false;
  for(uint16_t ref_index=0;ref_index<shadow->submission.job.object_count;++ref_index) {
    const struct raveil_object_ref_v1 *ref=&shadow->submission.job.objects[ref_index];
    if(ref->access!=RAVEIL_OBJECT_WRITE) continue;
    for(uint64_t byte=ref->offset;byte<ref->offset+ref->length;++byte) {
      shadow->bytes[ref_index][byte]=0u;
      shadow->staged[ref_index][byte]=1u;
    }
  }
  return true;
}
bool job_shadow_write_test(const struct sonatine_job_binding *binding,
                           uint64_t object_id,uint64_t offset,
                           const void *source,size_t length) {
  return job_shadow_write_core(binding,object_id,offset,source,length);
}
enum sonatine_finalize_result job_shadow_finalize_test(
    const struct sonatine_job_binding *binding,bool commit) {
  return job_shadow_finalize_core(binding,commit);
}
#endif

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
