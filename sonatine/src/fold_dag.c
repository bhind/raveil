#include "fold_dag.h"
#include "fold_bridge.h"
#include "console.h"
#include "plane_authority.h"
#include "platform.h"
#include "raveil/affine_fold.h"
#include "raveil/graph_transport.h"

static uint8_t envelope[RAVEIL_FOLD_DAG_MAX_BYTES],materialized[RAVEIL_FOLD_MAX_BYTES];
static struct raveil_fold_dag dag;
static struct raveil_fold_request request;
static uint32_t previous[8][128],published[8][128],expected[256],actual[256];
static uint64_t versions[8],producer_versions[8][2];
static bool producer_ok[8];
static const uint8_t program[16]={0xf1},graph[16]={0xf2};
static void hex(uint64_t value,unsigned digits) {
  static const char alphabet[]="0123456789abcdef";
  for(int shift=(int)(digits*4u)-4;shift>=0;shift-=4)
    console_putc(alphabet[(value>>(unsigned)shift)&15u]);
}
static void version_text(void) {
  for(unsigned i=0;i<8;++i) {if(i)console_putc(',');console_write_dec(versions[i]);}
}
static uint32_t slot_mask(uint32_t index) {
  uint32_t mask=0;for(unsigned j=0;j<dag.chunks[index];++j)mask|=1u<<dag.destinations[index][j];
  return mask;
}
static bool available(uint32_t index) {
  if(!producer_ok[index])return false;
  for(unsigned j=0;j<dag.chunks[index];++j)
    if(versions[dag.destinations[index][j]]!=producer_versions[index][j])return false;
  return true;
}
static bool read_state(void) {
  bool stable=job_submission_count()==0u&&job_inflight_count()==0u&&
    job_completion_count()==0u&&job_shadow_count()==0u;
  for(unsigned i=0;i<8;++i) {
    struct raveil_object_manifest_v1 object;
    if(!job_object_lookup(i+1u,&object)||object.generation!=1u||object.version!=versions[i]||
       object.byte_length!=512u||!job_object_read(i+1u,0u,published[i],512u))stable=false;
    for(unsigned j=0;j<128;++j)if(published[i][j]!=previous[i][j])stable=false;
  }
  return stable;
}
static void stop(void) {
  *(volatile uint32_t *)QEMU_TEST_FINISHER=0x5555u;for(;;)cpu_wait();
}
bool fold_dag_run_if_present(uint16_t task,cap_handle_t program_cap,
                            cap_handle_t graph_cap,cap_handle_t data_cap,
                            cap_handle_t experience_cap) {
  const volatile uint32_t *header=(const volatile uint32_t *)RAVEIL_GRAPH_REQUEST_ADDRESS;
  if(header[0]!=RAVEIL_FOLD_DAG_MAGIC)return false;
  uint32_t size=header[2];if(size<348u||size>sizeof(envelope))goto rejected;
  const volatile uint8_t *source=(const volatile uint8_t *)header;
  for(uint32_t i=0;i<size;++i)envelope[i]=source[i];
  /* Decode, reference-bound admission and all lifetime allocation precede dispatch. */
  if(!raveil_fold_dag_decode(envelope,size,&dag))goto rejected;
  job_authority_init(dag.jobs.epoch);plane_authority_init();
  if(!plane_program_install(task,program_cap,program)||
     !plane_graph_install(task,graph_cap,program,graph))goto rejected;
  for(unsigned i=0;i<8;++i) {
    struct raveil_object_manifest_v1 object={0};
    object.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;object.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
    object.struct_size=sizeof(object);object.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
    object.object_id=i+1u;object.generation=1u;object.version=1u;object.byte_length=512u;
    object.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
    if(!plane_data_object_register(task,data_cap,&object))goto rejected;
    versions[i]=1u;producer_ok[i]=false;
    for(unsigned j=0;j<128;++j)previous[i][j]=0;
  }
  if(!read_state()||plane_experience_count()!=0u)goto rejected;
  uint32_t processed=0,halted=0;
  console_write("RAVEIL-FOLD-DAG-START-V1 epoch=");hex(dag.jobs.epoch,16);
  console_write(" jobs=");console_write_dec(dag.jobs.count);
  console_write(" output=");console_write_dec(dag.output);console_write(" versions=");version_text();console_write("\n");
  for(uint32_t index=0;index<dag.jobs.count;++index) {
    if(!raveil_fold_decode(envelope+dag.jobs.offsets[index],dag.jobs.lengths[index],&request)) {halted=2;break;}
    uint32_t bad=UINT32_MAX,read_mask=0,writes=slot_mask(index),count=request.config[1]*request.config[2];
    for(unsigned b=0;b<2;++b) {
      uint32_t producer=dag.sources[index][b];if(producer==UINT32_MAX)continue;
      if(!available(producer)) {bad=producer;break;}
      uint32_t start=dag.input_offsets[index][b],extent=request.config[5+b];
      for(uint32_t chunk=start/128u;chunk<=(start+extent-1u)/128u;++chunk)
        read_mask|=1u<<dag.destinations[producer][chunk];
    }
    if(bad!=UINT32_MAX) {
      console_write("RAVEIL-FOLD-DAG-BLOCK-V1 index=");console_write_dec(index);
      console_write(" source=");console_write_dec(bad);console_write(" reason=unavailable\n");halted=3;break;
    }
    struct raveil_job_descriptor_v1 job={0};
    job.magic=RAVEIL_JOB_MAGIC;job.schema_version=RAVEIL_JOB_SCHEMA_V1;job.struct_size=sizeof(job);
    job.job_id=request.request_id;job.object_count=0;
    for(unsigned i=0;i<16;++i) {job.program_identity[i]=program[i];job.graph_variant_identity[i]=graph[i];}
    job.execution_contract_identity[0]=0xf5;job.target_signature[0]=1;
    uint32_t read_count=0;
    for(unsigned slot=0;slot<8;++slot)if((read_mask|writes)&(1u<<slot)) {
      bool input=(read_mask&(1u<<slot))!=0;
      if(input)++read_count;
      job.objects[job.object_count++]=(struct raveil_object_ref_v1){slot+1u,1u,versions[slot],
        0u,512u,input?RAVEIL_OBJECT_READ:RAVEIL_OBJECT_WRITE,0u};
    }
    job.resources=(struct raveil_resource_bounds_v1){1u,read_count?512u*read_count:1u,512u*dag.chunks[index],1u};
    struct sonatine_job_binding binding;struct sonatine_submission issued={0};
    if((read_mask&writes)||!plane_job_submit_bound(task,data_cap,&job,&binding)||!job_submission_take(&issued)) {halted=2;break;}
    bool input_ok=true;
    for(unsigned b=0;b<2;++b) {
      uint32_t producer=dag.sources[index][b];if(producer==UINT32_MAX)continue;
      uint32_t start=dag.input_offsets[index][b],extent=request.config[5+b],copied=0;
      while(copied<extent) {
        uint32_t position=start+copied,chunk=position/128u,within=position%128u;
        uint32_t take=128u-within;if(take>extent-copied)take=extent-copied;
        if(!job_submission_read(&issued,dag.destinations[producer][chunk]+1u,4u*within,
                                request.inputs+324u*b+copied,4u*take))input_ok=false;
        copied+=take;
      }
    }
    for(unsigned i=0;i<256;++i)expected[i]=actual[i]=0;
    size_t materialized_size=0;
    input_ok=input_ok&&raveil_fold_evaluate(&request,expected)&&
      raveil_fold_bridge_encode(&request,materialized,sizeof(materialized),&materialized_size);
    bool framed=false,approved=false,committed=false,authority_ok=true;
    bool execution_ok=input_ok&&fold_bridge_exchange_checked(materialized,materialized_size,&issued,count,actual,&framed);
    if(execution_ok)for(uint32_t i=0;i<count;++i)if(actual[i]!=expected[i])execution_ok=false;
    struct raveil_completion_record_v1 completion={0},taken;
    completion.magic=RAVEIL_COMPLETION_MAGIC;completion.schema_version=RAVEIL_JOB_SCHEMA_V1;
    completion.struct_size=sizeof(completion);completion.job_id=job.job_id;
    completion.execution_epoch=issued.execution_epoch;completion.execution_sequence=issued.execution_sequence;
    for(unsigned i=0;i<16;++i)completion.completion_cookie[i]=issued.completion_cookie[i];
    completion.status=execution_ok?RAVEIL_COMPLETION_EXECUTED:RAVEIL_COMPLETION_FAULT;
    completion.detail=execution_ok?RAVEIL_DETAIL_NONE:RAVEIL_DETAIL_EXECUTION_FAULT;
    if(execution_ok) {
      completion.output_count=dag.chunks[index];
      for(unsigned j=0;j<dag.chunks[index];++j) {
        uint32_t slot=dag.destinations[index][j];
        completion.outputs[j]=(struct raveil_object_version_v1){slot+1u,1u,versions[slot]+1u};
      }
    }
    authority_ok=job_completion_post(&completion)&&job_completion_take(&taken)&&plane_experience_record(task,experience_cap,&taken);
    if(authority_ok&&execution_ok) {
      for(unsigned j=0;j<dag.chunks[index];++j)
        if(!plane_data_shadow_write(task,data_cap,&binding,dag.destinations[index][j]+1u,0u,actual+128u*j,512u))authority_ok=false;
      authority_ok=authority_ok&&plane_program_approve(task,program_cap,&binding);
      if(authority_ok) {
        committed=plane_data_finalize(task,data_cap,&binding,true)==SONATINE_FINALIZE_COMMITTED;
        authority_ok=committed;
        if(committed) {
          approved=true;producer_ok[index]=true;
          for(unsigned j=0;j<dag.chunks[index];++j) {
            uint32_t slot=dag.destinations[index][j];producer_versions[index][j]=++versions[slot];
            for(unsigned k=0;k<128;++k)previous[slot][k]=expected[128u*j+k];
          }
        }
      }
    }
    if(!committed&&plane_data_finalize(task,data_cap,&binding,false)!=SONATINE_FINALIZE_ROLLED_BACK)authority_ok=false;
    bool stable=read_state()&&plane_experience_count()==index+1u&&authority_ok;
    ++processed;if(!stable)halted=2;else if(!framed)halted=1;
    console_write("RAVEIL-FOLD-DAG-STATE-V1 index=");console_write_dec(index);
    console_write(" stable=");console_write_dec(stable?1:0);console_write(" framed=");console_write_dec(framed?1:0);
    console_write(" writes=");console_write_dec(writes);console_write(" reads=");console_write_dec(read_mask);
    console_write(" versions=");version_text();console_write(" ledger=");console_write_dec(plane_experience_count());
    console_write(" submissions=");console_write_dec(job_submission_count());console_write(" inflight=");console_write_dec(job_inflight_count());
    console_write(" shadows=");console_write_dec(job_shadow_count());console_write(" completions=");console_write_dec(job_completion_count());
    console_write(" content=");for(unsigned s=0;s<8;++s)for(unsigned j=0;j<128;++j)hex(published[s][j],8);console_write("\n");
    console_write("RAVEIL-FOLD-DAG-RESULT-V1 index=");console_write_dec(index);
    console_write(" request=");hex(request.request_id,16);console_write(" epoch=");hex(issued.execution_epoch,16);
    console_write(" sequence=");console_write_dec(issued.execution_sequence);console_write(" cookie=");
    for(unsigned j=0;j<16;++j)hex(issued.completion_cookie[j],2);
    console_write(" status=");console_write_dec(approved&&stable?1:4);console_write(" approved=");console_write_dec(approved&&stable?1:0);
    console_write(" count=");console_write_dec(approved&&stable?count:0);console_write(" output=");
    if(approved&&stable)for(unsigned j=0;j<count;++j)hex(published[dag.destinations[index][j/128]][j%128],8);
    else console_putc('-');
    console_write("\n");if(halted)break;
  }
  bool final_ok=available(dag.output);uint32_t final_count=0;
  if(final_ok&&raveil_fold_decode(envelope+dag.jobs.offsets[dag.output],dag.jobs.lengths[dag.output],&request))
    final_count=request.config[1]*request.config[2];
  console_write("RAVEIL-FOLD-DAG-OUTPUT-V1 index=");console_write_dec(dag.output);
  console_write(" available=");console_write_dec(final_ok?1:0);console_write(" count=");console_write_dec(final_count);
  console_write(" output=");if(final_ok)for(unsigned j=0;j<final_count;++j)hex(published[dag.destinations[dag.output][j/128]][j%128],8);
  else console_putc('-');
  console_write("\n");
  console_write("RAVEIL-FOLD-DAG-END-V1 epoch=");hex(dag.jobs.epoch,16);console_write(" processed=");console_write_dec(processed);
  console_write(" total=");console_write_dec(dag.jobs.count);console_write(" halted=");console_write_dec(halted);
  console_write(" versions=");version_text();console_write("\n");stop();
rejected:
  console_write("RAVEIL-FOLD-DAG-REJECT-V1 reason=admission-or-initialization\n");stop();return true;
}
