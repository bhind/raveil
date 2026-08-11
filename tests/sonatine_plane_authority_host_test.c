#include <assert.h>
#include <string.h>

#include "plane_authority.h"

void console_write(const char *text) { (void)text; }
void console_write_dec(uint64_t value) { (void)value; }
void console_write_hex(uint64_t value) { (void)value; }

static void identity(uint8_t value[16],uint8_t seed) {
  memset(value,0,16u); value[0]=seed; value[15]=(uint8_t)(seed+1u);
}
static struct raveil_object_manifest_v1 manifest(uint64_t id) {
  struct raveil_object_manifest_v1 value={0};
  value.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;
  value.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
  value.struct_size=sizeof(value);
  value.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  value.object_id=id; value.generation=1u; value.version=1u;
  value.byte_length=8u; value.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
  return value;
}
static struct raveil_job_descriptor_v1 job(
    uint64_t id,const uint8_t program[16],const uint8_t graph[16]) {
  struct raveil_job_descriptor_v1 value={0};
  value.magic=RAVEIL_JOB_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.object_count=1u; value.job_id=id;
  memcpy(value.program_identity,program,16u);
  memcpy(value.graph_variant_identity,graph,16u);
  value.execution_contract_identity[0]=3u; value.target_signature[0]=4u;
  value.resources=(struct raveil_resource_bounds_v1){1u,1u,8u,1u};
  value.objects[0]=(struct raveil_object_ref_v1){1u,1u,1u,0u,8u,
      RAVEIL_OBJECT_WRITE,0u};
  return value;
}
static struct raveil_completion_record_v1 completion(
    const struct sonatine_submission *issued) {
  struct raveil_completion_record_v1 value={0};
  value.magic=RAVEIL_COMPLETION_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.status=RAVEIL_COMPLETION_EXECUTED;
  value.job_id=issued->job.job_id; value.execution_epoch=issued->execution_epoch;
  value.execution_sequence=issued->execution_sequence;
  memcpy(value.completion_cookie,issued->completion_cookie,16u);
  value.output_count=1u;
  value.outputs[0]=(struct raveil_object_version_v1){1u,1u,2u}; return value;
}

int main(void) {
  const uint16_t owner=1u,peer=2u;
  uint8_t program[16],graph[16]; identity(program,1u); identity(graph,2u);
  cap_init();
  cap_handle_t caps[4]={
    cap_create(owner,CAP_OBJECT_PROGRAM_AUTHORITY,1u,CAP_RIGHT_CONTROL),
    cap_create(owner,CAP_OBJECT_GRAPH_AUTHORITY,1u,CAP_RIGHT_CONTROL),
    cap_create(owner,CAP_OBJECT_DATA_AUTHORITY,1u,CAP_RIGHT_WRITE|CAP_RIGHT_CONTROL),
    cap_create(owner,CAP_OBJECT_EXPERIENCE_AUTHORITY,1u,CAP_RIGHT_WRITE|CAP_RIGHT_CONTROL)
  };
  for(size_t index=0;index<4u;++index) assert(caps[index]!=0u);
  assert(cap_create(owner,CAP_OBJECT_PROGRAM_AUTHORITY,1u,CAP_RIGHT_WRITE)==0u);
  assert(cap_create(owner,CAP_OBJECT_DATA_AUTHORITY,1u,CAP_RIGHT_SEND)==0u);

  /* Each operation accepts exactly its own plane capability. */
  for(size_t index=0;index<4u;++index) {
    plane_authority_init();
    assert(plane_program_install(owner,caps[index],program)==(index==0u));
  }
  for(size_t index=0;index<4u;++index) {
    plane_authority_init(); assert(plane_program_install(owner,caps[0],program));
    assert(plane_graph_install(owner,caps[index],program,graph)==(index==1u));
  }
  for(size_t index=0;index<4u;++index) {
    plane_authority_init(); job_authority_init(1u);
    struct raveil_object_manifest_v1 object=manifest(1u);
    assert(plane_data_object_register(owner,caps[index],&object)==(index==2u));
  }
  /* Full identity binding and capability-authorized commit. */
  plane_authority_init(); job_authority_init(9u);
  assert(plane_program_install(owner,caps[0],program));
  assert(!plane_program_install(owner,caps[0],program));
  assert(plane_graph_install(owner,caps[1],program,graph));
  uint8_t unknown[16]; identity(unknown,9u);
  assert(!plane_graph_install(owner,caps[1],unknown,graph));
  struct raveil_object_manifest_v1 object=manifest(1u),visible;
  assert(plane_data_object_register(owner,caps[2],&object));
  struct raveil_job_descriptor_v1 work=job(7u,program,graph);
  struct sonatine_job_binding binding;
  assert(!plane_job_submit_bound(peer,caps[2],&work,&binding));
  work.program_identity[15]^=1u;
  assert(!plane_job_submit_bound(owner,caps[2],&work,&binding));
  work.program_identity[15]^=1u;
  assert(plane_job_submit_bound(owner,caps[2],&work,&binding));
  struct sonatine_submission issued;
  assert(job_submission_take(&issued));
  struct raveil_completion_record_v1 done=completion(&issued),taken;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  struct raveil_completion_record_v1 forged=taken; forged.completion_cookie[0]^=1u;
  assert(!plane_experience_record(owner,caps[0],&taken));
  assert(!plane_experience_record(owner,caps[1],&taken));
  assert(!plane_experience_record(owner,caps[2],&taken));
  assert(!plane_experience_record(owner,caps[3],&forged));
  assert(plane_experience_record(owner,caps[3],&taken));
  assert(!plane_experience_record(owner,caps[3],&taken));
  assert(!plane_program_approve(owner,caps[3],&binding));
  assert(plane_program_approve(owner,caps[0],&binding));
  assert(plane_data_finalize(owner,caps[3],&binding,true)==SONATINE_FINALIZE_INVALID);
  assert(job_object_lookup(1u,&visible) && visible.version==1u);
  assert(plane_data_finalize(owner,caps[2],&binding,true)==SONATINE_FINALIZE_COMMITTED);
  assert(job_object_lookup(1u,&visible) && visible.version==2u);
  assert(plane_experience_count()==1u);

  /* The bounded ledger accepts only genuine consumed completions and never
     overwrites an earlier entry when full. */
  for(uint64_t index=0u;index<7u;++index) {
    work=job(20u+index,program,graph);
    work.objects[0].expected_version=2u;
    assert(plane_job_submit_bound(owner,caps[2],&work,&binding));
    assert(job_submission_take(&issued));
    done=completion(&issued); done.outputs[0].version=3u;
    assert(job_completion_post(&done)); assert(job_completion_take(&taken));
    assert(plane_experience_record(owner,caps[3],&taken));
    assert(plane_data_finalize(owner,caps[2],&binding,false)==SONATINE_FINALIZE_ROLLED_BACK);
  }
  assert(plane_experience_count()==SONATINE_EXPERIENCE_LEDGER_SIZE);
  work=job(99u,program,graph); work.objects[0].expected_version=2u;
  assert(plane_job_submit_bound(owner,caps[2],&work,&binding));
  assert(job_submission_take(&issued));
  done=completion(&issued); done.outputs[0].version=3u;
  assert(job_completion_post(&done)); assert(job_completion_take(&taken));
  assert(!plane_experience_record(owner,caps[3],&taken));
  assert(plane_experience_count()==SONATINE_EXPERIENCE_LEDGER_SIZE);
  assert(plane_data_finalize(owner,caps[2],&binding,false)==SONATINE_FINALIZE_ROLLED_BACK);

  /* Attenuated Data/Experience leaves work only for their own plane. */
  cap_handle_t peer_data=cap_delegate(owner,caps[2],peer,CAP_RIGHT_WRITE);
  cap_handle_t peer_experience=cap_delegate(owner,caps[3],peer,CAP_RIGHT_WRITE);
  assert(peer_data!=0u && peer_experience!=0u);
  assert(cap_delegate(peer,peer_data,owner,CAP_RIGHT_WRITE)==0u);
  assert(cap_delegate(owner,caps[0],peer,CAP_RIGHT_CONTROL)==0u);
  job_authority_init(10u); object=manifest(UINT64_C(0x8000000000000001));
  assert(plane_data_object_register(peer,peer_data,&object));
  assert(!plane_data_object_register(peer,peer_experience,&object));
  assert(cap_revoke(peer_data));
  object=manifest(3u); assert(!plane_data_object_register(peer,peer_data,&object));
  return 0;
}
