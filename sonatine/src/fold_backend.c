#include "fold_backend.h"
#include "fold_bridge.h"
#include "console.h"
#include "job_authority.h"
#include "plane_authority.h"
#include "platform.h"
#include "raveil/affine_fold.h"
#include "raveil/graph_transport.h"

/* Frozen kernel input, not user capability objects. One request per boot. */
static uint8_t envelope[RAVEIL_FOLD_MAX_BYTES];
static struct raveil_fold_request request;
static uint32_t output[256],published[256],expected[256];
static void hex(uint64_t v,unsigned digits) {
  static const char alphabet[]="0123456789abcdef";
  for(int shift=(int)(digits*4u)-4;shift>=0;shift-=4)
    console_putc(alphabet[(v>>(unsigned)shift)&15u]);
}
bool fold_backend_run_if_present(uint16_t task,cap_handle_t program_cap,
                                 cap_handle_t graph_cap,cap_handle_t data_cap,
                                 cap_handle_t experience_cap) {
  const volatile uint32_t *header=(const volatile uint32_t *)RAVEIL_GRAPH_REQUEST_ADDRESS;
  if(header[0]!=RAVEIL_FOLD_MAGIC&&header[0]!=RAVEIL_FOLD_BRIDGE_MAGIC) return false;
  bool bridge=header[0]==RAVEIL_FOLD_BRIDGE_MAGIC;
  uint64_t id=(uint64_t)header[6]|((uint64_t)header[7]<<32);
  uint32_t size=header[2],count=0,chunks=0,status=RAVEIL_COMPLETION_REJECTED;
  bool approved=false,submitted=false,committed=false;
  struct sonatine_job_binding binding;
  struct sonatine_submission issued={0};
  if(size<300u||size>sizeof(envelope)) goto result;
  const volatile uint8_t *source=(const volatile uint8_t *)header;
  for(uint32_t i=0;i<size;++i) envelope[i]=source[i];
  if(!raveil_fold_decode(envelope,size,&request)) goto result;
  id=request.request_id;
  count=request.config[1]*request.config[2];chunks=(count+127u)/128u;
  struct raveil_job_descriptor_v1 job={0};
  job.magic=RAVEIL_JOB_MAGIC;job.schema_version=RAVEIL_JOB_SCHEMA_V1;
  job.struct_size=sizeof(job);job.object_count=chunks;job.job_id=id;
  /* Version identities identify the interpreter, not a program content hash. */
  job.program_identity[0]=0xf1;job.graph_variant_identity[0]=0xf2;
  job.execution_contract_identity[0]=0xf3;job.target_signature[0]=1;
  job.resources=(struct raveil_resource_bounds_v1){1u,1u,count*4u,1u};
  job_authority_init(id);
  if(!plane_program_install(task,program_cap,job.program_identity)||
     !plane_graph_install(task,graph_cap,job.program_identity,job.graph_variant_identity))
    goto result;
  for(uint32_t i=0;i<chunks;++i) {
    uint32_t words=count-i*128u;if(words>128u) words=128u;
    struct raveil_object_manifest_v1 object={0};
    object.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;object.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
    object.struct_size=sizeof(object);object.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
    object.object_id=i+1u;object.generation=1;object.version=1;
    object.byte_length=words*4u;object.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
    if(!plane_data_object_register(task,data_cap,&object)) goto result;
    job.objects[i]=(struct raveil_object_ref_v1){i+1u,1u,1u,0u,words*4u,RAVEIL_OBJECT_WRITE,0u};
  }
  if(!plane_job_submit_bound(task,data_cap,&job,&binding)) goto result;
  submitted=true;
  if(!job_submission_take(&issued)) goto result;
  bool execution_ok=raveil_fold_evaluate(&request,expected);
  if(bridge) {
    if(execution_ok) execution_ok=fold_bridge_exchange(envelope,size,&issued,count,output);
    if(execution_ok) for(uint32_t i=0;i<count;++i)
      if(output[i]!=expected[i])execution_ok=false;
  } else for(uint32_t i=0;i<count;++i)output[i]=expected[i];
  struct raveil_completion_record_v1 completion={0},taken;
  completion.magic=RAVEIL_COMPLETION_MAGIC;completion.schema_version=RAVEIL_JOB_SCHEMA_V1;
  completion.struct_size=sizeof(completion);completion.status=RAVEIL_COMPLETION_EXECUTED;
  completion.job_id=id;completion.execution_epoch=issued.execution_epoch;
  completion.execution_sequence=issued.execution_sequence;completion.output_count=chunks;
  for(unsigned i=0;i<16;++i)completion.completion_cookie[i]=issued.completion_cookie[i];
  if(!execution_ok) {
    completion.status=RAVEIL_COMPLETION_FAULT;
    completion.detail=RAVEIL_DETAIL_EXECUTION_FAULT;completion.output_count=0;
    if(job_completion_post(&completion)&&job_completion_take(&taken))
      (void)plane_experience_record(task,experience_cap,&taken);
    goto result;
  }
  for(uint32_t i=0;i<chunks;++i)
    completion.outputs[i]=(struct raveil_object_version_v1){i+1u,1u,2u};
  if(!job_completion_post(&completion)||!job_completion_take(&taken)||
     !plane_experience_record(task,experience_cap,&taken)) goto result;
  for(uint32_t i=0;i<chunks;++i)
    if(!plane_data_shadow_write(task,data_cap,&binding,i+1u,0u,output+128u*i,
                                (size_t)job.objects[i].length)) goto result;
  /* Approval trusts admitted interpreter execution. The independent SSA
   * oracle checks full committed values on the host, after guest publication. */
  if(!plane_program_approve(task,program_cap,&binding)||
     plane_data_finalize(task,data_cap,&binding,true)!=SONATINE_FINALIZE_COMMITTED) goto result;
  committed=true;
  for(uint32_t i=0;i<chunks;++i)
    if(!job_object_read(i+1u,0u,published+128u*i,(size_t)job.objects[i].length)) goto result;
  for(uint32_t i=0;i<count;++i) if(published[i]!=output[i]) goto result;
  approved=true;status=RAVEIL_COMPLETION_EXECUTED;
result:
  if(!approved&&submitted&&!committed) (void)plane_data_finalize(task,data_cap,&binding,false);
  if(!approved&&submitted) status=RAVEIL_COMPLETION_FAULT;
  if(bridge&&submitted) {
    bool stable=job_inflight_count()==0u&&job_shadow_count()==0u&&job_completion_count()==0u;
    for(uint32_t i=0;i<chunks;++i) {
      struct raveil_object_manifest_v1 observed;
      uint32_t words=count-128u*i;if(words>128u)words=128u;
      if(!job_object_lookup(i+1u,&observed)||observed.version!=(approved?2u:1u)||
         !job_object_read(i+1u,0u,published+128u*i,words*4u)) stable=false;
      else for(uint32_t j=0;j<words;++j)
        if(published[128u*i+j]!=(approved?expected[128u*i+j]:0u))stable=false;
    }
    console_write("RAVEIL-FOLD-BRIDGE-STATE-V1 stable=");console_write_dec(stable?1u:0u);
    console_write(" objects=");console_write_dec(chunks);
    console_write(" version=");console_write_dec(approved?2u:1u);
    console_write(" inflight=");console_write_dec(job_inflight_count());
    console_write(" shadows=");console_write_dec(job_shadow_count());
    console_write(" completions=");console_write_dec(job_completion_count());console_write("\n");
  }
  console_write("RAVEIL-FOLD-RESULT-V1 request=");hex(id,16);
  console_write(" status=");console_write_dec(status);
  console_write(" approved=");console_write_dec(approved?1u:0u);
  console_write(" epoch=");console_write_dec(issued.execution_epoch);
  console_write(" sequence=");console_write_dec(issued.execution_sequence);
  console_write(" cookie=");for(unsigned i=0;i<16;++i)hex(issued.completion_cookie[i],2);
  console_write(" chunks=");console_write_dec(approved?chunks:0u);
  console_write(" version=");console_write_dec(approved?2u:0u);
  console_write(" count=");console_write_dec(approved?count:0u);
  console_write(" output=");
  if(approved) for(uint32_t i=0;i<count;++i)hex(published[i],8);
  else console_putc('-');
  console_write("\n");
  *(volatile uint32_t *)QEMU_TEST_FINISHER=0x5555u;
  for(;;)cpu_wait();
}
