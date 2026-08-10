#include "raveil/job_contract.h"
#include <stddef.h>

static bool zero_bytes(const void *memory,size_t size) {
  const uint8_t *bytes=(const uint8_t *)memory;
  for(size_t i=0;i<size;++i) if(bytes[i]!=0u) return false;
  return true;
}
static bool nonzero_identity(const uint8_t identity[16]) {
  for(size_t i=0;i<16u;++i) if(identity[i]!=0u) return true;
  return false;
}
static bool valid_object(const struct raveil_object_ref_v1 *object) {
  return object->object_id!=0u && object->generation!=0u &&
         object->expected_version!=0u && object->length!=0u &&
         object->offset<=UINT64_MAX-object->length && object->flags==0u &&
         (object->access==RAVEIL_OBJECT_READ ||
          object->access==RAVEIL_OBJECT_WRITE);
}
bool raveil_job_descriptor_validate_v1(const struct raveil_job_descriptor_v1 *job) {
  if(job==NULL || job->magic!=RAVEIL_JOB_MAGIC ||
     job->schema_version!=RAVEIL_JOB_SCHEMA_V1 || job->struct_size!=sizeof(*job) ||
     job->flags!=0u || job->reserved0!=0u || job->reserved1!=0u || job->job_id==0u ||
     job->object_count==0u || job->object_count>RAVEIL_JOB_MAX_OBJECTS ||
     !nonzero_identity(job->program_identity) ||
     !nonzero_identity(job->graph_variant_identity) ||
     !nonzero_identity(job->execution_contract_identity) ||
     !nonzero_identity(job->target_signature) ||
     job->resources.max_runtime_ticks==0u || job->resources.max_input_bytes==0u ||
     job->resources.max_output_bytes==0u || job->resources.max_scratch_bytes==0u) return false;
  uint64_t input_bytes=0u,output_bytes=0u;
  for(uint16_t i=0;i<job->object_count;++i) {
    if(!valid_object(&job->objects[i])) return false;
    if((job->objects[i].access&RAVEIL_OBJECT_READ)!=0u) {
      if(input_bytes>UINT64_MAX-job->objects[i].length) return false;
      input_bytes+=job->objects[i].length;
    }
    if((job->objects[i].access&RAVEIL_OBJECT_WRITE)!=0u) {
      if(output_bytes>UINT64_MAX-job->objects[i].length) return false;
      output_bytes+=job->objects[i].length;
    }
    for(uint16_t j=0;j<i;++j)
      if(job->objects[i].object_id==job->objects[j].object_id &&
         job->objects[i].generation==job->objects[j].generation) return false;
  }
  if(input_bytes>job->resources.max_input_bytes ||
     output_bytes>job->resources.max_output_bytes) return false;
  return zero_bytes(&job->objects[job->object_count],
      (RAVEIL_JOB_MAX_OBJECTS-job->object_count)*sizeof(job->objects[0]));
}
static const struct raveil_object_ref_v1 *write_ref(
    const struct raveil_job_descriptor_v1 *job,uint64_t id,uint64_t generation) {
  for(uint16_t i=0;i<job->object_count;++i)
    if(job->objects[i].object_id==id && job->objects[i].generation==generation &&
       (job->objects[i].access&RAVEIL_OBJECT_WRITE)!=0u) return &job->objects[i];
  return NULL;
}
bool raveil_completion_record_validate_v1(
    const struct raveil_job_descriptor_v1 *job,
    const struct raveil_completion_record_v1 *completion) {
  if(!raveil_job_descriptor_validate_v1(job) || completion==NULL ||
     completion->magic!=RAVEIL_COMPLETION_MAGIC ||
     completion->schema_version!=RAVEIL_JOB_SCHEMA_V1 ||
     completion->struct_size!=sizeof(*completion) || completion->flags!=0u ||
     completion->reserved0!=0u || completion->reserved1!=0u ||
     !zero_bytes(completion->reserved2,sizeof(completion->reserved2)) ||
     completion->job_id!=job->job_id || completion->execution_epoch==0u ||
     completion->execution_sequence==0u ||
     !nonzero_identity(completion->completion_cookie) ||
     completion->status<RAVEIL_COMPLETION_EXECUTED ||
     completion->status>RAVEIL_COMPLETION_FAULT ||
     completion->output_count>RAVEIL_JOB_MAX_OBJECTS) return false;
  if(completion->status!=RAVEIL_COMPLETION_EXECUTED) {
    uint32_t expected_detail=completion->status==RAVEIL_COMPLETION_REJECTED
        ?RAVEIL_DETAIL_INVALID_CONTRACT
        :completion->status==RAVEIL_COMPLETION_CANCELLED
            ?RAVEIL_DETAIL_CANCEL_REQUESTED:RAVEIL_DETAIL_EXECUTION_FAULT;
    return completion->detail==expected_detail && completion->output_count==0u &&
           zero_bytes(completion->outputs,sizeof(completion->outputs));
  }
  if(completion->detail!=0u) return false;
  uint16_t expected_outputs=0u;
  for(uint16_t i=0;i<job->object_count;++i)
    if((job->objects[i].access&RAVEIL_OBJECT_WRITE)!=0u) ++expected_outputs;
  if(completion->output_count!=expected_outputs) return false;
  for(uint16_t i=0;i<completion->output_count;++i) {
    const struct raveil_object_version_v1 *output=&completion->outputs[i];
    const struct raveil_object_ref_v1 *source=write_ref(job,output->object_id,output->generation);
    if(source==NULL || output->version<=source->expected_version) return false;
    for(uint16_t j=0;j<i;++j)
      if(output->object_id==completion->outputs[j].object_id &&
         output->generation==completion->outputs[j].generation) return false;
  }
  return zero_bytes(&completion->outputs[completion->output_count],
      (RAVEIL_JOB_MAX_OBJECTS-completion->output_count)*sizeof(completion->outputs[0]));
}
