#ifndef RAVEIL_JOB_CONTRACT_H
#define RAVEIL_JOB_CONTRACT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if !defined(__BYTE_ORDER__) || !defined(__ORDER_LITTLE_ENDIAN__)
#error "Raveil job contract v1 requires GCC/Clang byte-order macros"
#elif __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Raveil job contract v1 requires little endian"
#endif

#define RAVEIL_JOB_MAGIC 0x524a4f42u
#define RAVEIL_COMPLETION_MAGIC 0x52434d50u
#define RAVEIL_JOB_SCHEMA_V1 1u
#define RAVEIL_JOB_MAX_OBJECTS 4u

enum raveil_object_access_v1 {
  RAVEIL_OBJECT_READ=1u,
  RAVEIL_OBJECT_WRITE=2u
};
enum raveil_completion_status_v1 {
  RAVEIL_COMPLETION_EXECUTED=1u,
  RAVEIL_COMPLETION_REJECTED=2u,
  RAVEIL_COMPLETION_CANCELLED=3u,
  RAVEIL_COMPLETION_FAULT=4u
};
enum raveil_completion_detail_v1 {
  RAVEIL_DETAIL_NONE=0u,
  RAVEIL_DETAIL_INVALID_CONTRACT=1u,
  RAVEIL_DETAIL_CANCEL_REQUESTED=2u,
  RAVEIL_DETAIL_EXECUTION_FAULT=3u
};
struct raveil_object_ref_v1 {
  uint64_t object_id;
  uint64_t generation;
  uint64_t expected_version;
  uint64_t offset;
  uint64_t length;
  uint32_t access;
  uint32_t flags;
};
struct raveil_resource_bounds_v1 {
  uint64_t max_runtime_ticks;
  uint64_t max_input_bytes;
  uint64_t max_output_bytes;
  uint64_t max_scratch_bytes;
};
struct raveil_job_descriptor_v1 {
  uint32_t magic;
  uint16_t schema_version;
  uint16_t struct_size;
  uint32_t flags;
  uint16_t object_count;
  uint16_t reserved0;
  uint64_t job_id;
  uint8_t program_identity[16];
  uint8_t graph_variant_identity[16];
  uint8_t execution_contract_identity[16];
  uint8_t target_signature[16];
  struct raveil_resource_bounds_v1 resources;
  uint64_t reserved1;
  struct raveil_object_ref_v1 objects[RAVEIL_JOB_MAX_OBJECTS];
};
struct raveil_object_version_v1 {
  uint64_t object_id;
  uint64_t generation;
  uint64_t version;
};
struct raveil_completion_record_v1 {
  uint32_t magic;
  uint16_t schema_version;
  uint16_t struct_size;
  uint32_t flags;
  uint32_t status;
  uint32_t detail;
  uint32_t reserved0;
  uint64_t job_id;
  uint64_t execution_epoch;
  uint64_t execution_sequence;
  uint8_t completion_cookie[16];
  uint16_t output_count;
  uint16_t reserved1;
  uint8_t reserved2[12];
  struct raveil_object_version_v1 outputs[RAVEIL_JOB_MAX_OBJECTS];
};
_Static_assert(sizeof(struct raveil_object_ref_v1)==48u,"object ref ABI");
_Static_assert(sizeof(struct raveil_job_descriptor_v1)==320u,"job ABI");
_Static_assert(sizeof(struct raveil_completion_record_v1)==176u,"completion ABI");
#define RAVEIL_OFFSET(type,field,value) \
  _Static_assert(offsetof(type,field)==(value),"ABI offset " #type "." #field)
RAVEIL_OFFSET(struct raveil_object_ref_v1,object_id,0u);
RAVEIL_OFFSET(struct raveil_object_ref_v1,generation,8u);
RAVEIL_OFFSET(struct raveil_object_ref_v1,expected_version,16u);
RAVEIL_OFFSET(struct raveil_object_ref_v1,offset,24u);
RAVEIL_OFFSET(struct raveil_object_ref_v1,length,32u);
RAVEIL_OFFSET(struct raveil_object_ref_v1,access,40u);
RAVEIL_OFFSET(struct raveil_object_ref_v1,flags,44u);
RAVEIL_OFFSET(struct raveil_resource_bounds_v1,max_runtime_ticks,0u);
RAVEIL_OFFSET(struct raveil_resource_bounds_v1,max_input_bytes,8u);
RAVEIL_OFFSET(struct raveil_resource_bounds_v1,max_output_bytes,16u);
RAVEIL_OFFSET(struct raveil_resource_bounds_v1,max_scratch_bytes,24u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,magic,0u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,schema_version,4u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,struct_size,6u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,flags,8u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,object_count,12u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,reserved0,14u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,job_id,16u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,program_identity,24u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,graph_variant_identity,40u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,execution_contract_identity,56u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,target_signature,72u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,resources,88u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,reserved1,120u);
RAVEIL_OFFSET(struct raveil_job_descriptor_v1,objects,128u);
RAVEIL_OFFSET(struct raveil_object_version_v1,object_id,0u);
RAVEIL_OFFSET(struct raveil_object_version_v1,generation,8u);
RAVEIL_OFFSET(struct raveil_object_version_v1,version,16u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,magic,0u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,schema_version,4u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,struct_size,6u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,flags,8u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,status,12u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,detail,16u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,reserved0,20u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,job_id,24u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,execution_epoch,32u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,execution_sequence,40u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,completion_cookie,48u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,output_count,64u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,reserved1,66u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,reserved2,68u);
RAVEIL_OFFSET(struct raveil_completion_record_v1,outputs,80u);
#undef RAVEIL_OFFSET

bool raveil_job_descriptor_validate_v1(const struct raveil_job_descriptor_v1 *job);
bool raveil_completion_record_validate_v1(
    const struct raveil_job_descriptor_v1 *job,
    const struct raveil_completion_record_v1 *completion);
#endif
