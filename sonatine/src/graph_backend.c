#include "graph_backend.h"

#include <stddef.h>
#include <stdint.h>

#include "console.h"
#include "job_authority.h"
#include "platform.h"
#include "plane_authority.h"
#include "raveil/graph_transport.h"
#include "raveil/job_contract.h"

static void copy16(uint8_t *target,const uint8_t *source) {
  for(size_t index=0;index<16u;++index) target[index]=source[index];
}

static void fixed_hex64(uint64_t value) {
  static const char digits[]="0123456789abcdef";
  for(int shift=60;shift>=0;shift-=4)
    console_putc(digits[(value>>(uint32_t)shift)&0xfu]);
}

static void cookie_hex(const uint8_t *cookie) {
  static const char digits[]="0123456789abcdef";
  for(size_t index=0;index<16u;++index) {
    console_putc(digits[cookie[index]>>4u]);
    console_putc(digits[cookie[index]&0xfu]);
  }
}

static void emit_result(uint64_t request_id,uint32_t status,uint32_t detail,
                        const struct sonatine_submission *issued,
                        uint64_t checksum,uint64_t reference,bool approved) {
  console_write("RAVEIL-GRAPH-RESULT-V1 request="); fixed_hex64(request_id);
  console_write(" status="); console_write_dec(status);
  console_write(" detail="); console_write_dec(detail);
  console_write(" job="); console_write_dec(issued==NULL?0u:issued->job.job_id);
  console_write(" epoch="); console_write_dec(issued==NULL?0u:issued->execution_epoch);
  console_write(" sequence="); console_write_dec(issued==NULL?0u:issued->execution_sequence);
  console_write(" cookie=");
  if(issued==NULL) console_write("00000000000000000000000000000000");
  else cookie_hex(issued->completion_cookie);
  console_write(" checksum="); fixed_hex64(checksum);
  console_write(" reference="); fixed_hex64(reference);
  console_write(" approved="); console_putc(approved?'1':'0'); console_write("\n");
}

static void fill(int32_t *values,size_t count,uint32_t salt) {
  uint32_t state=UINT32_C(0x9e3779b9)^salt;
  for(size_t index=0;index<count;++index) {
    state=state*UINT32_C(1664525)+UINT32_C(1013904223);
    values[index]=(int32_t)((state>>16)%7u)-3;
  }
}

static void gemm(const int32_t *a,const int32_t *b,int64_t *out,
                 uint32_t m,uint32_t n,uint32_t k,uint32_t candidate) {
  for(size_t index=0;index<(size_t)m*n;++index) out[index]=0;
  if(candidate==RAVEIL_GRAPH_CANDIDATE_BASELINE) {
    for(uint32_t i=0;i<m;++i) for(uint32_t j=0;j<n;++j)
      for(uint32_t p=0;p<k;++p)
        out[(size_t)i*n+j]+=(int64_t)a[(size_t)i*k+p]*b[(size_t)p*n+j];
  } else {
    for(uint32_t i=0;i<m;++i) for(uint32_t p=0;p<k;++p)
      for(uint32_t j=0;j<n;++j)
        out[(size_t)i*n+j]+=(int64_t)a[(size_t)i*k+p]*b[(size_t)p*n+j];
  }
}

static uint64_t checksum(const int64_t *values,size_t count) {
  uint64_t hash=UINT64_C(1469598103934665603);
  for(size_t index=0;index<count;++index) {
    const uint64_t word=(uint64_t)values[index];
    for(unsigned shift=0;shift<64u;shift+=8u) {
      hash^=(word>>shift)&UINT64_C(0xff);
      hash*=UINT64_C(1099511628211);
    }
  }
  return hash;
}

bool graph_backend_run_if_present(uint16_t task,cap_handle_t program_cap,
                                  cap_handle_t graph_cap,cap_handle_t data_cap,
                                  cap_handle_t experience_cap) {
  const struct raveil_graph_request_v1 *request=
      (const struct raveil_graph_request_v1 *)RAVEIL_GRAPH_REQUEST_ADDRESS;
  if(request->magic!=RAVEIL_GRAPH_REQUEST_MAGIC) return false;
  if(!raveil_graph_request_validate_v1(request)) {
    emit_result(request->request_id,RAVEIL_COMPLETION_REJECTED,
                RAVEIL_DETAIL_INVALID_CONTRACT,NULL,0u,0u,false);
    *(volatile uint32_t *)QEMU_TEST_FINISHER=0x5555u;
    for(;;) cpu_wait();
  }

  int32_t a[64],b[64]; int64_t actual_values[64],reference_values[64];
  fill(a,(size_t)request->m*request->k,1u);
  fill(b,(size_t)request->k*request->n,2u);
  gemm(a,b,reference_values,request->m,request->n,request->k,
       RAVEIL_GRAPH_CANDIDATE_BASELINE);
  gemm(a,b,actual_values,request->m,request->n,request->k,request->candidate);
  const uint64_t reference=checksum(reference_values,(size_t)request->m*request->n);
  const uint64_t actual=checksum(actual_values,(size_t)request->m*request->n);

  struct raveil_object_manifest_v1 object={0};
  object.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;
  object.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
  object.struct_size=sizeof(object);
  object.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  object.object_id=1u; object.generation=1u; object.version=1u;
  object.byte_length=(uint64_t)request->m*request->n*8u;
  object.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
  struct raveil_job_descriptor_v1 job={0};
  job.magic=RAVEIL_JOB_MAGIC; job.schema_version=RAVEIL_JOB_SCHEMA_V1;
  job.struct_size=sizeof(job); job.object_count=1u; job.job_id=request->request_id;
  copy16(job.program_identity,request->program_identity);
  copy16(job.graph_variant_identity,request->graph_variant_identity);
  copy16(job.execution_contract_identity,request->execution_contract_identity);
  job.target_signature[0]=1u;
  job.resources=(struct raveil_resource_bounds_v1){1u,1u,object.byte_length,1u};
  job.objects[0]=(struct raveil_object_ref_v1){1u,1u,1u,0u,
      object.byte_length,RAVEIL_OBJECT_WRITE,0u};

  job_authority_init(request->request_id);
  struct sonatine_job_binding binding;
  struct sonatine_submission issued;
  struct raveil_completion_record_v1 completion={0},taken;
  if(!plane_program_install(task,program_cap,job.program_identity) ||
     !plane_graph_install(task,graph_cap,job.program_identity,
                          job.graph_variant_identity) ||
     !plane_data_object_register(task,data_cap,&object) ||
     !plane_job_submit_bound(task,data_cap,&job,&binding) ||
     !job_submission_take(&issued)) {
    emit_result(request->request_id,RAVEIL_COMPLETION_REJECTED,
                RAVEIL_DETAIL_INVALID_CONTRACT,NULL,actual,reference,false);
  } else {
    completion.magic=RAVEIL_COMPLETION_MAGIC;
    completion.schema_version=RAVEIL_JOB_SCHEMA_V1;
    completion.struct_size=sizeof(completion);
    completion.status=RAVEIL_COMPLETION_EXECUTED;
    completion.job_id=job.job_id;
    completion.execution_epoch=issued.execution_epoch;
    completion.execution_sequence=issued.execution_sequence;
    copy16(completion.completion_cookie,issued.completion_cookie);
    completion.output_count=1u;
    completion.outputs[0]=(struct raveil_object_version_v1){1u,1u,2u};
    bool approved=false,committed=false;
    if(job_completion_post(&completion) && job_completion_take(&taken) &&
       plane_experience_record(task,experience_cap,&taken) &&
       plane_data_shadow_write(task,data_cap,&binding,1u,0u,actual_values,
                               (size_t)object.byte_length) &&
       actual==reference && plane_program_approve(task,program_cap,&binding) &&
       plane_data_finalize(task,data_cap,&binding,true)==SONATINE_FINALIZE_COMMITTED) {
      committed=true;
      int64_t published[64];
      if(job_object_read(1u,0u,published,(size_t)object.byte_length) &&
         checksum(published,(size_t)request->m*request->n)==reference)
        approved=true;
      else {
        completion.status=RAVEIL_COMPLETION_FAULT;
        completion.detail=RAVEIL_DETAIL_EXECUTION_FAULT;
        completion.output_count=0u;
        for(size_t index=0;index<RAVEIL_JOB_MAX_OBJECTS;++index)
          completion.outputs[index]=(struct raveil_object_version_v1){0};
      }
    }
    if(!approved && !committed)
      (void)plane_data_finalize(task,data_cap,&binding,false);
    emit_result(request->request_id,completion.status,completion.detail,
                &issued,actual,reference,approved);
  }
  *(volatile uint32_t *)QEMU_TEST_FINISHER=0x5555u;
  for(;;) cpu_wait();
}
