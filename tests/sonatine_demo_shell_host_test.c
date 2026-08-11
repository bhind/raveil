#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "demo_shell.h"
#include "job_authority.h"
#include "plane_authority.h"
#include "vfs.h"

static char output[4096];
static size_t output_used;
static void append(char value) {
  assert(output_used+1u<sizeof(output)); output[output_used++]=value; output[output_used]='\0';
}
void console_putc(char value) { append(value); }
void console_write(const char *text) { while(*text!='\0') append(*text++); }
void console_write_dec(uint64_t value) {
  char digits[21]; size_t used=0u;
  if(value==0u) { append('0'); return; }
  while(value!=0u) { digits[used++]=(char)('0'+value%10u); value/=10u; }
  while(used!=0u) append(digits[--used]);
}
void console_write_hex(uint64_t value) { (void)value; }
static void clear_output(void) { output_used=0u; output[0]='\0'; }
static void frame(const char *fragment) {
  assert(strstr(output,SONATINE_DEMO_FRAME_PREFIX)!=NULL);
  assert(strstr(output,fragment)!=NULL);
}
static struct raveil_object_manifest_v1 manifest(uint64_t id) {
  struct raveil_object_manifest_v1 value={0};
  value.magic=RAVEIL_OBJECT_MANIFEST_MAGIC; value.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
  value.struct_size=sizeof(value); value.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  value.object_id=id; value.generation=1u; value.version=1u; value.byte_length=8u;
  value.backing=RAVEIL_OBJECT_BACKING_VOLATILE; return value;
}
static struct raveil_job_descriptor_v1 demo_job(uint64_t id,uint64_t version) {
  struct raveil_job_descriptor_v1 value={0};
  value.magic=RAVEIL_JOB_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.object_count=1u; value.job_id=id;
  value.program_identity[0]=0x92u; value.program_identity[1]=1u;
  value.graph_variant_identity[0]=0x92u; value.graph_variant_identity[1]=2u;
  value.execution_contract_identity[0]=0x92u; value.execution_contract_identity[1]=3u;
  value.target_signature[0]=1u;
  value.resources=(struct raveil_resource_bounds_v1){1u,1u,32u,1u};
  value.objects[0]=(struct raveil_object_ref_v1){UINT64_C(0xd092),1u,version,0u,32u,
      RAVEIL_OBJECT_WRITE,0u};
  return value;
}
static struct raveil_completion_record_v1 completion(const struct sonatine_submission *issued) {
  struct raveil_completion_record_v1 value={0};
  value.magic=RAVEIL_COMPLETION_MAGIC; value.schema_version=RAVEIL_JOB_SCHEMA_V1;
  value.struct_size=sizeof(value); value.status=RAVEIL_COMPLETION_EXECUTED;
  value.job_id=issued->job.job_id; value.execution_epoch=issued->execution_epoch;
  value.execution_sequence=issued->execution_sequence;
  memcpy(value.completion_cookie,issued->completion_cookie,sizeof(value.completion_cookie));
  value.output_count=1u;
  value.outputs[0]=(struct raveil_object_version_v1){UINT64_C(0xd092),1u,
      issued->job.objects[0].expected_version+1u};
  return value;
}

int main(void) {
  const uint16_t owner=1u,peer=2u;
  assert(SONATINE_DEMO_FRAME_MAX==171u);
  cap_init(); vfs_init(); job_authority_init(7u); plane_authority_init();
  const cap_handle_t console=cap_create(owner,CAP_OBJECT_CONSOLE,1u,CAP_RIGHT_WRITE);
  const cap_handle_t peer_console=cap_create(peer,CAP_OBJECT_CONSOLE,1u,CAP_RIGHT_WRITE);
  const cap_handle_t filesystem=cap_create(owner,CAP_OBJECT_FILESYSTEM,VFS_ROOT_OBJECT,
                                            CAP_RIGHT_READ|CAP_RIGHT_WRITE);
  const cap_handle_t program=cap_create(owner,CAP_OBJECT_PROGRAM_AUTHORITY,
      SONATINE_PLANE_AUTHORITY_OBJECT,CAP_RIGHT_CONTROL);
  const cap_handle_t graph=cap_create(owner,CAP_OBJECT_GRAPH_AUTHORITY,
      SONATINE_PLANE_AUTHORITY_OBJECT,CAP_RIGHT_CONTROL);
  const cap_handle_t data=cap_create(owner,CAP_OBJECT_DATA_AUTHORITY,
      SONATINE_PLANE_AUTHORITY_OBJECT,CAP_RIGHT_WRITE|CAP_RIGHT_CONTROL);
  const cap_handle_t experience=cap_create(owner,CAP_OBJECT_EXPERIENCE_AUTHORITY,
      SONATINE_PLANE_AUTHORITY_OBJECT,CAP_RIGHT_WRITE|CAP_RIGHT_CONTROL);
  const cap_handle_t broker=cap_create(owner,CAP_OBJECT_DEMO_AUTHORITY,
      SONATINE_DEMO_AUTHORITY_OBJECT,CAP_RIGHT_CONTROL);
  const cap_handle_t wrong_broker=cap_create(owner,CAP_OBJECT_DEMO_AUTHORITY,99u,CAP_RIGHT_CONTROL);
  const cap_handle_t peer_broker=cap_create(peer,CAP_OBJECT_DEMO_AUTHORITY,
      SONATINE_DEMO_AUTHORITY_OBJECT,CAP_RIGHT_CONTROL);
  assert(console!=0u && peer_console!=0u && filesystem!=0u && program!=0u && graph!=0u &&
         data!=0u && experience!=0u && broker!=0u && wrong_broker!=0u && peer_broker!=0u);
  struct raveil_object_manifest_v1 preserved=manifest(UINT64_C(0x44));
  assert(plane_data_object_register(owner,data,&preserved));
  assert(!sonatine_demo_init(owner,wrong_broker,program,graph,data,experience,filesystem));
  assert(sonatine_demo_init(owner,broker,program,graph,data,experience,filesystem));
  assert(job_object_lookup(UINT64_C(0x44),&preserved));

  clear_output(); assert(sonatine_demo_command_run(owner,console,wrong_broker,SONATINE_DEMO_ECHO)==1u);
  frame("command=echo seq=1 status=DENIED job=0 state=EMPTY semantic=0 checksum=0000000000000000");
  clear_output(); assert(sonatine_demo_command_run(peer,peer_console,peer_broker,SONATINE_DEMO_ECHO)==1u);
  frame("seq=2 status=DENIED");
  clear_output(); assert(sonatine_demo_command_run(owner,console,0u,SONATINE_DEMO_LS)==1u); frame("seq=3 status=DENIED");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_JOBS)==0u); frame("command=jobs seq=4 status=EMPTY");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_CAT)==0u);
  assert(strstr(output,"hello from initramfs")!=NULL); frame("command=cat seq=5 status=OK");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_ECHO)==0u);
  assert(strstr(output,"sonatine fixed echo")!=NULL);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_WRITE)==0u);
  size_t size=0u; bool writable=false;
  assert(vfs_stat(VFS_NODE_SCRATCH,&size,&writable)==VFS_OK && size==5u && writable);
  vfs_init();
  for(size_t index=0u;index<61u;++index) assert(vfs_write(VFS_NODE_SCRATCH,index,'x')==VFS_OK);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_WRITE)==1u);
  frame("status=NO_SPACE");
  assert(vfs_stat(VFS_NODE_SCRATCH,&size,&writable)==VFS_OK && size==61u);

  struct sonatine_job_binding other_bindings[3];
  struct sonatine_submission other_issued[3];
  for(size_t index=0u;index<3u;++index) {
    struct raveil_job_descriptor_v1 other=demo_job(UINT64_C(0x9300)+index,1u);
    assert(plane_job_submit_bound(owner,data,&other,&other_bindings[index]));
    assert(job_submission_take(&other_issued[index]));
    struct raveil_completion_record_v1 done=completion(&other_issued[index]);
    assert(job_completion_post(&done));
  }
  assert(job_completion_count()==3u);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RUN)==0u); frame("state=DISPATCHED");
  assert(sonatine_demo_test_stale_completion() && sonatine_demo_test_stale_cancel());
  assert(sonatine_demo_test_post_completion());
  assert(job_completion_count()==SONATINE_JOB_RING_DEPTH && job_inflight_count()==SONATINE_JOB_RING_DEPTH);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==1u);
  frame("status=BUSY");
  assert(strstr(output,"state=DISPATCHED")!=NULL);
  assert(job_completion_count()==SONATINE_JOB_RING_DEPTH && job_inflight_count()==SONATINE_JOB_RING_DEPTH &&
         job_shadow_count()==0u);
  struct raveil_completion_record_v1 taken;
  assert(job_completion_take(&taken));
  assert(plane_data_finalize(owner,data,&other_bindings[0],false)==SONATINE_FINALIZE_ROLLED_BACK);
  assert(job_completion_count()==3u && job_inflight_count()==3u);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RUN)==1u); frame("status=BUSY");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==0u); frame("status=COMPLETED");
  for(size_t index=1u;index<3u;++index) {
    assert(job_completion_take(&taken));
    assert(plane_data_finalize(owner,data,&other_bindings[index],false)==SONATINE_FINALIZE_ROLLED_BACK);
  }
  assert(job_completion_count()==0u && job_inflight_count()==0u && job_shadow_count()==0u);
  struct raveil_object_manifest_v1 observed; int64_t values[4];
  assert(job_object_lookup(UINT64_C(0xd092),&observed) && observed.version==2u);
  assert(job_object_read(UINT64_C(0xd092),0u,values,sizeof(values)) &&
         values[0]==19 && values[1]==22 && values[2]==43 && values[3]==50);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==0u);
  frame("status=COMPLETED");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_CANCEL)==1u); frame("status=TOO_LATE");

  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RUN)==0u);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_CANCEL)==0u); frame("state=CANCEL_REQUESTED");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==0u); frame("status=CANCELLED");
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==0u); frame("status=CANCELLED");
  assert(job_inflight_count()==0u && job_shadow_count()==0u);

  for(size_t index=0u;index<6u;++index) {
    assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RUN)==0u);
    assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==0u);
  }
  assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RUN)==0u);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==1u);
  frame("status=FAULT");
  assert(strstr(output,"state=FAULT semantic=0 checksum=0000000000000000")!=NULL);
  assert(job_inflight_count()==0u && job_shadow_count()==0u);
  clear_output(); assert(sonatine_demo_command_run(owner,console,broker,SONATINE_DEMO_RESULT)==1u);
  frame("status=FAULT");
  assert(strstr(output,"state=FAULT")!=NULL);
  return 0;
}
