#include "fold_session.h"
#include "fold_bridge.h"
#include "console.h"
#include "plane_authority.h"
#include "platform.h"
#include "raveil/affine_fold.h"
#include "raveil/graph_transport.h"

/* A bounded boot session owns this state. Authority is initialized exactly once,
 * after bootstrap diagnostics, and is never reset to recover a failed job. */
static uint8_t envelope[RAVEIL_FOLD_SESSION_MAX_BYTES];
static struct raveil_fold_session session;
static struct raveil_fold_request request;
static uint32_t previous[256],expected[256],actual[256],published[256];
static const uint8_t program[16]={0xf1},graph[16]={0xf2};
static void hex(uint64_t value,unsigned digits) {
  static const char alphabet[]="0123456789abcdef";
  for(int shift=(int)(digits*4u)-4;shift>=0;shift-=4)
    console_putc(alphabet[(value>>(unsigned)shift)&15u]);
}
static void stop(void) {
  *(volatile uint32_t *)QEMU_TEST_FINISHER=0x5555u;
  for(;;)cpu_wait();
}
static bool empty(void) {
  return job_submission_count()==0u&&job_inflight_count()==0u&&
         job_completion_count()==0u&&job_shadow_count()==0u;
}
static bool read_state(uint64_t version,const uint32_t values[256]) {
  bool stable=empty();
  for(unsigned i=0;i<2;++i) {
    struct raveil_object_manifest_v1 object;
    if(!job_object_lookup(i+1u,&object)||object.generation!=1u||
       object.version!=version||object.byte_length!=512u||
       !job_object_read(i+1u,0u,published+128u*i,512u))stable=false;
  }
  for(unsigned i=0;i<256;++i)if(published[i]!=values[i])stable=false;
  return stable;
}
bool fold_session_run_if_present(uint16_t task,cap_handle_t program_cap,
                                 cap_handle_t graph_cap,cap_handle_t data_cap,
                                 cap_handle_t experience_cap) {
  const volatile uint32_t *header=(const volatile uint32_t *)RAVEIL_GRAPH_REQUEST_ADDRESS;
  if(header[0]!=RAVEIL_FOLD_SESSION_MAGIC)return false;
  uint32_t size=header[2];
  if(size<332u||size>sizeof(envelope))goto rejected;
  const volatile uint8_t *source=(const volatile uint8_t *)header;
  for(uint32_t i=0;i<size;++i)envelope[i]=source[i];
  if(!raveil_fold_session_decode(envelope,size,&session))goto rejected;
  /* Bootstrap smoke has its own registry/ledger. Begin the admitted session
   * once with fresh authority; capabilities and the boot log are unchanged. */
  job_authority_init(session.epoch);plane_authority_init();
  if(!plane_program_install(task,program_cap,program)||
     !plane_graph_install(task,graph_cap,program,graph))goto rejected;
  for(unsigned i=0;i<2;++i) {
    struct raveil_object_manifest_v1 object={0};
    object.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;object.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
    object.struct_size=sizeof(object);object.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
    object.object_id=i+1u;object.generation=1u;object.version=1u;
    object.byte_length=512u;object.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
    if(!plane_data_object_register(task,data_cap,&object))goto rejected;
  }
  for(unsigned i=0;i<256;++i)previous[i]=0;
  uint64_t version=1u;uint32_t processed=0,halted=0;
  if(!read_state(version,previous)||plane_experience_count()!=0u)goto rejected;
  console_write("RAVEIL-FOLD-SESSION-START-V1 epoch=");hex(session.epoch,16);
  console_write(" jobs=");console_write_dec(session.count);console_write(" version=1\n");
  for(uint32_t index=0;index<session.count;++index) {
    if(!raveil_fold_decode(envelope+session.offsets[index],session.lengths[index],&request)) {
      halted=2u;break;
    }
    uint32_t count=request.config[1]*request.config[2];
    for(unsigned i=0;i<256;++i)expected[i]=actual[i]=0;
    if(!raveil_fold_evaluate(&request,expected)) {halted=2u;break;}
    struct raveil_job_descriptor_v1 job={0};
    job.magic=RAVEIL_JOB_MAGIC;job.schema_version=RAVEIL_JOB_SCHEMA_V1;
    job.struct_size=sizeof(job);job.object_count=2u;job.job_id=request.request_id;
    for(unsigned i=0;i<16;++i) {job.program_identity[i]=program[i];job.graph_variant_identity[i]=graph[i];}
    job.execution_contract_identity[0]=0xf4;job.target_signature[0]=1u;
    job.resources=(struct raveil_resource_bounds_v1){1u,1u,1024u,1u};
    for(unsigned i=0;i<2;++i)
      job.objects[i]=(struct raveil_object_ref_v1){i+1u,1u,version,0u,512u,RAVEIL_OBJECT_WRITE,0u};
    struct sonatine_job_binding binding;
    struct sonatine_submission issued={0};
    if(!plane_job_submit_bound(task,data_cap,&job,&binding)||!job_submission_take(&issued)) {
      halted=2u;break;
    }
    bool framed=false,approved=false,committed=false,authority_ok=true;
    bool execution_ok=fold_bridge_exchange_checked(envelope+session.offsets[index],
      session.lengths[index],&issued,count,actual,&framed);
    if(execution_ok)for(uint32_t i=0;i<count;++i)
      if(actual[i]!=expected[i])execution_ok=false;
    struct raveil_completion_record_v1 completion={0},taken;
    completion.magic=RAVEIL_COMPLETION_MAGIC;completion.schema_version=RAVEIL_JOB_SCHEMA_V1;
    completion.struct_size=sizeof(completion);completion.job_id=job.job_id;
    completion.execution_epoch=issued.execution_epoch;completion.execution_sequence=issued.execution_sequence;
    for(unsigned i=0;i<16;++i)completion.completion_cookie[i]=issued.completion_cookie[i];
    completion.status=execution_ok?RAVEIL_COMPLETION_EXECUTED:RAVEIL_COMPLETION_FAULT;
    completion.detail=execution_ok?RAVEIL_DETAIL_NONE:RAVEIL_DETAIL_EXECUTION_FAULT;
    if(execution_ok) {
      completion.output_count=2u;
      for(unsigned i=0;i<2;++i)
        completion.outputs[i]=(struct raveil_object_version_v1){i+1u,1u,version+1u};
    }
    authority_ok=job_completion_post(&completion)&&job_completion_take(&taken)&&
      plane_experience_record(task,experience_cap,&taken);
    if(authority_ok&&execution_ok) {
      authority_ok=plane_data_shadow_write(task,data_cap,&binding,1u,0u,actual,512u)&&
        plane_data_shadow_write(task,data_cap,&binding,2u,0u,actual+128,512u)&&
        plane_program_approve(task,program_cap,&binding);
      if(authority_ok) {
        committed=plane_data_finalize(task,data_cap,&binding,true)==SONATINE_FINALIZE_COMMITTED;
        authority_ok=committed;
        if(committed) {++version;approved=true;}
      }
    }
    if(!committed&&plane_data_finalize(task,data_cap,&binding,false)!=SONATINE_FINALIZE_ROLLED_BACK)
      authority_ok=false;
    bool stable=read_state(version,approved?expected:previous)&&
      plane_experience_count()==index+1u&&authority_ok;
    if(approved&&stable)for(unsigned i=0;i<256;++i)previous[i]=published[i];
    ++processed;
    if(!stable)halted=2u;
    else if(!framed)halted=1u;
    console_write("RAVEIL-FOLD-SESSION-STATE-V1 index=");console_write_dec(index);
    console_write(" stable=");console_write_dec(stable?1u:0u);
    console_write(" framed=");console_write_dec(framed?1u:0u);
    console_write(" version=");console_write_dec(version);
    console_write(" ledger=");console_write_dec(plane_experience_count());
    console_write(" submissions=");console_write_dec(job_submission_count());
    console_write(" inflight=");console_write_dec(job_inflight_count());
    console_write(" shadows=");console_write_dec(job_shadow_count());
    console_write(" completions=");console_write_dec(job_completion_count());
    console_write(" content=");for(unsigned i=0;i<256;++i)hex(published[i],8);console_write("\n");
    console_write("RAVEIL-FOLD-SESSION-RESULT-V1 index=");console_write_dec(index);
    console_write(" request=");hex(request.request_id,16);
    console_write(" epoch=");hex(issued.execution_epoch,16);
    console_write(" sequence=");console_write_dec(issued.execution_sequence);
    console_write(" cookie=");for(unsigned i=0;i<16;++i)hex(issued.completion_cookie[i],2);
    console_write(" status=");console_write_dec(approved&&stable?1u:4u);
    console_write(" approved=");console_write_dec(approved&&stable?1u:0u);
    console_write(" version=");console_write_dec(version);
    console_write(" count=");console_write_dec(approved&&stable?count:0u);
    console_write(" output=");
    if(approved&&stable)for(uint32_t i=0;i<count;++i)hex(published[i],8);
    else console_putc('-');
    console_write("\n");
    if(halted)break;
  }
  console_write("RAVEIL-FOLD-SESSION-END-V1 epoch=");hex(session.epoch,16);
  console_write(" processed=");console_write_dec(processed);
  console_write(" total=");console_write_dec(session.count);
  console_write(" halted=");console_write_dec(halted);
  console_write(" version=");console_write_dec(version);console_write("\n");
  stop();
rejected:
  console_write("RAVEIL-FOLD-SESSION-REJECT-V1 reason=admission-or-initialization\n");
  stop();
  return true;
}
