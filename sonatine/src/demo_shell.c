#include "demo_shell.h"

#include <stddef.h>

#include "console.h"
#include "job_authority.h"
#include "plane_authority.h"
#include "vfs.h"

#define DEMO_OBJECT_ID UINT64_C(0xd092)

enum demo_state { DEMO_EMPTY=0, DEMO_DISPATCHED, DEMO_CANCEL_REQUESTED,
                  DEMO_COMPLETED, DEMO_CANCELLED, DEMO_FAULT };

struct demo_context {
  bool initialized;
  uint16_t owner;
  cap_handle_t program_cap,data_cap,experience_cap,filesystem_cap;
  enum demo_state state;
  uint64_t next_job_id,frame_sequence,checksum;
  bool semantic,stale_completion_rejected;
  struct sonatine_job_binding binding;
  struct sonatine_submission issued;
};
static struct demo_context demo;

static void copy16(uint8_t target[16],const uint8_t source[16]) {
  for(size_t index=0u;index<16u;++index) target[index]=source[index];
}
static void fixed_hex64(uint64_t value) {
  static const char digits[]="0123456789abcdef";
  for(int shift=60;shift>=0;shift-=4) console_putc(digits[(value>>(uint32_t)shift)&0xfu]);
}
static uint64_t values_checksum(const int64_t values[4]) {
  uint64_t hash=UINT64_C(1469598103934665603);
  for(size_t index=0u;index<4u;++index) for(unsigned shift=0u;shift<64u;shift+=8u) {
    hash^=((uint64_t)values[index]>>shift)&UINT64_C(0xff);
    hash*=UINT64_C(1099511628211);
  }
  return hash;
}
static const char *state_name(enum demo_state state) {
  switch(state) {
    case DEMO_EMPTY: return "EMPTY";
    case DEMO_DISPATCHED: return "DISPATCHED";
    case DEMO_CANCEL_REQUESTED: return "CANCEL_REQUESTED";
    case DEMO_COMPLETED: return "COMPLETED";
    case DEMO_CANCELLED: return "CANCELLED";
    case DEMO_FAULT: return "FAULT";
  }
  return "FAULT";
}
static const char *command_name(enum sonatine_demo_command command) {
  switch(command) {
    case SONATINE_DEMO_LS: return "ls";
    case SONATINE_DEMO_CAT: return "cat";
    case SONATINE_DEMO_ECHO: return "echo";
    case SONATINE_DEMO_WRITE: return "write";
    case SONATINE_DEMO_STAT: return "stat";
    case SONATINE_DEMO_JOBS: return "jobs";
    case SONATINE_DEMO_RUN: return "run";
    case SONATINE_DEMO_CANCEL: return "cancel";
    case SONATINE_DEMO_RESULT: return "result";
  }
  return "invalid";
}
static const char *terminal_status(void) {
  return demo.state==DEMO_COMPLETED?"COMPLETED":
      demo.state==DEMO_CANCELLED?"CANCELLED":"FAULT";
}
static void emit_frame(enum sonatine_demo_command command,const char *status) {
  const uint64_t sequence=demo.frame_sequence;
  if(demo.frame_sequence!=UINT64_MAX) ++demo.frame_sequence;
  console_write(SONATINE_DEMO_FRAME_PREFIX "command="); console_write(command_name(command));
  console_write(" seq="); console_write_dec(sequence);
  console_write(" status="); console_write(status);
  console_write(" job="); console_write_dec(demo.state==DEMO_EMPTY?0u:demo.issued.job.job_id);
  console_write(" state="); console_write(state_name(demo.state));
  console_write(" semantic="); console_putc(demo.semantic?'1':'0');
  console_write(" checksum="); fixed_hex64(demo.checksum); console_write("\n");
}
static bool broker_authorized(uint16_t task,cap_handle_t broker_cap) {
  struct cap_view view;
  return demo.initialized && task==demo.owner &&
      cap_resolve(task,broker_cap,CAP_OBJECT_DEMO_AUTHORITY,CAP_RIGHT_CONTROL,&view) &&
      view.object_id==SONATINE_DEMO_AUTHORITY_OBJECT;
}
static bool filesystem_allowed(uint16_t task,uint32_t right) {
  struct cap_view view;
  return cap_resolve(task,demo.filesystem_cap,CAP_OBJECT_FILESYSTEM,right,&view) &&
      view.object_id==VFS_ROOT_OBJECT;
}
static void print_node(uint32_t node) {
  size_t size=0u; bool writable=false;
  if(vfs_stat(node,&size,&writable)!=VFS_OK) return;
  console_write(vfs_path(node)); console_write(" size="); console_write_dec(size);
  console_write(" writable="); console_putc(writable?'1':'0'); console_write("\n");
}
static bool print_hello(void) {
  size_t size=0u; bool writable=false;
  if(vfs_stat(VFS_NODE_HELLO,&size,&writable)!=VFS_OK || writable) return false;
  for(size_t offset=0u;offset<size;++offset) {
    uint8_t value=0u;
    if(vfs_read(VFS_NODE_HELLO,offset,&value)!=VFS_OK) return false;
    console_putc((char)value);
  }
  return true;
}
static enum vfs_result append_demo_value(void) {
  static const uint8_t value[]={'d','e','m','o','\n'};
  size_t size=0u; bool writable=false;
  if(vfs_stat(VFS_NODE_SCRATCH,&size,&writable)!=VFS_OK || !writable) return VFS_DENIED;
  if(size>VFS_FILE_CAPACITY-sizeof(value)) return VFS_NO_SPACE;
  for(size_t index=0u;index<sizeof(value);++index)
    if(vfs_write(VFS_NODE_SCRATCH,size+index,value[index])!=VFS_OK) return VFS_INVALID;
  return VFS_OK;
}
static void compute_demo_gemm(int64_t output[4]) {
  static const int32_t left[4]={1,2,3,4},right[4]={5,6,7,8};
  for(size_t index=0u;index<4u;++index) output[index]=0;
  for(uint32_t row=0u;row<2u;++row) for(uint32_t column=0u;column<2u;++column)
    for(uint32_t inner=0u;inner<2u;++inner)
      output[(size_t)row*2u+column]+=(int64_t)left[(size_t)row*2u+inner]*right[(size_t)inner*2u+column];
}
static void expected_demo_gemm(int64_t expected[4]) {
  expected[0]=(int64_t)1*5+(int64_t)2*7;
  expected[1]=(int64_t)1*6+(int64_t)2*8;
  expected[2]=(int64_t)3*5+(int64_t)4*7;
  expected[3]=(int64_t)3*6+(int64_t)4*8;
}
static bool values_equal(const int64_t left[4],const int64_t right[4]) {
  for(size_t index=0u;index<4u;++index) if(left[index]!=right[index]) return false;
  return true;
}
static bool submit_demo(uint16_t task) {
  static const uint8_t program[16]={0x92u,1u};
  static const uint8_t graph[16]={0x92u,2u};
  static const uint8_t contract[16]={0x92u,3u};
  struct raveil_object_manifest_v1 object;
  if(!job_object_lookup(DEMO_OBJECT_ID,&object)) return false;
  struct raveil_job_descriptor_v1 job={0};
  job.magic=RAVEIL_JOB_MAGIC; job.schema_version=RAVEIL_JOB_SCHEMA_V1;
  job.struct_size=sizeof(job); job.object_count=1u; job.job_id=demo.next_job_id++;
  copy16(job.program_identity,program); copy16(job.graph_variant_identity,graph);
  copy16(job.execution_contract_identity,contract); job.target_signature[0]=1u;
  job.resources=(struct raveil_resource_bounds_v1){1u,1u,32u,1u};
  job.objects[0]=(struct raveil_object_ref_v1){DEMO_OBJECT_ID,object.generation,
      object.version,0u,32u,RAVEIL_OBJECT_WRITE,0u};
  return plane_job_submit_bound(task,demo.data_cap,&job,&demo.binding) &&
      job_submission_take(&demo.issued);
}
static void fill_completion(struct raveil_completion_record_v1 *completion,uint32_t status) {
  *completion=(struct raveil_completion_record_v1){0};
  completion->magic=RAVEIL_COMPLETION_MAGIC; completion->schema_version=RAVEIL_JOB_SCHEMA_V1;
  completion->struct_size=sizeof(*completion); completion->status=status;
  completion->job_id=demo.issued.job.job_id;
  completion->execution_epoch=demo.issued.execution_epoch;
  completion->execution_sequence=demo.issued.execution_sequence;
  copy16(completion->completion_cookie,demo.issued.completion_cookie);
  if(status==RAVEIL_COMPLETION_EXECUTED) {
    completion->output_count=1u;
    completion->outputs[0]=(struct raveil_object_version_v1){DEMO_OBJECT_ID,1u,
        demo.issued.job.objects[0].expected_version+1u};
  } else completion->detail=RAVEIL_DETAIL_CANCEL_REQUESTED;
}
static bool stale_completion_rejected(void) {
  struct raveil_completion_record_v1 stale;
  fill_completion(&stale,RAVEIL_COMPLETION_EXECUTED);
  stale.execution_sequence^=UINT64_C(1);
  return !job_completion_post(&stale);
}
static bool terminal_fault(uint16_t task) {
  (void)plane_data_finalize(task,demo.data_cap,&demo.binding,false);
  demo.state=DEMO_FAULT; demo.semantic=false; demo.checksum=0u; return false;
}
static bool finish_demo(uint16_t task,bool cancelled) {
  struct raveil_completion_record_v1 completion,taken;
  fill_completion(&completion,cancelled?RAVEIL_COMPLETION_CANCELLED:RAVEIL_COMPLETION_EXECUTED);
  if(!job_completion_pending(&demo.binding) && !job_completion_post(&completion)) {
    (void)job_cancel(&demo.binding);
    fill_completion(&completion,RAVEIL_COMPLETION_CANCELLED);
    if(!job_completion_post(&completion) || !job_completion_take_bound(&demo.binding,&taken)) return terminal_fault(task);
  } else if(!job_completion_take_bound(&demo.binding,&taken)) return terminal_fault(task);
  if(!plane_experience_record(task,demo.experience_cap,&taken)) return terminal_fault(task);
  if(cancelled) {
    if(plane_data_finalize(task,demo.data_cap,&demo.binding,false)!=SONATINE_FINALIZE_ROLLED_BACK)
      return terminal_fault(task);
    demo.state=DEMO_CANCELLED; demo.semantic=false; demo.checksum=0u; return true;
  }
  int64_t actual[4],expected[4];
  compute_demo_gemm(actual); expected_demo_gemm(expected);
  const uint64_t actual_checksum=values_checksum(actual);
  const uint64_t expected_checksum=values_checksum(expected);
  if(!values_equal(actual,expected) || actual_checksum!=expected_checksum ||
     !plane_data_shadow_write(task,demo.data_cap,&demo.binding,DEMO_OBJECT_ID,0u,actual,sizeof(actual)) ||
     !plane_program_approve(task,demo.program_cap,&demo.binding) ||
     plane_data_finalize(task,demo.data_cap,&demo.binding,true)!=SONATINE_FINALIZE_COMMITTED)
    return terminal_fault(task);
  demo.state=DEMO_COMPLETED; demo.checksum=actual_checksum; demo.semantic=true;
  return true;
}
bool sonatine_demo_init(uint16_t task,cap_handle_t broker_cap,cap_handle_t program_cap,
                        cap_handle_t graph_cap,cap_handle_t data_cap,
                        cap_handle_t experience_cap,cap_handle_t filesystem_cap) {
  static const uint8_t program[16]={0x92u,1u};
  static const uint8_t graph[16]={0x92u,2u};
  struct raveil_object_manifest_v1 object={0};
  demo=(struct demo_context){0}; demo.owner=task; demo.program_cap=program_cap;
  demo.data_cap=data_cap; demo.experience_cap=experience_cap; demo.filesystem_cap=filesystem_cap;
  demo.next_job_id=UINT64_C(0x9200); demo.frame_sequence=1u;
  object.magic=RAVEIL_OBJECT_MANIFEST_MAGIC; object.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
  object.struct_size=sizeof(object); object.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  object.object_id=DEMO_OBJECT_ID; object.generation=1u; object.version=1u;
  object.byte_length=32u; object.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
  struct cap_view broker;
  demo.initialized=cap_resolve(task,broker_cap,CAP_OBJECT_DEMO_AUTHORITY,CAP_RIGHT_CONTROL,&broker) &&
      broker.object_id==SONATINE_DEMO_AUTHORITY_OBJECT &&
      plane_program_install(task,program_cap,program) &&
      plane_graph_install(task,graph_cap,program,graph) &&
      plane_data_object_register(task,data_cap,&object);
  return demo.initialized;
}
uint64_t sonatine_demo_command_run(uint16_t task,cap_handle_t console_cap,
                                   cap_handle_t broker_cap,
                                   enum sonatine_demo_command command) {
  if(!broker_authorized(task,broker_cap) ||
     !cap_resolve(task,console_cap,CAP_OBJECT_CONSOLE,CAP_RIGHT_WRITE,NULL)) {
    emit_frame(command,"DENIED"); return 1u;
  }
  if(command==SONATINE_DEMO_LS) {
    if(!filesystem_allowed(task,CAP_RIGHT_READ)) { emit_frame(command,"DENIED"); return 1u; }
    for(uint32_t node=VFS_NODE_HELLO;node<=VFS_NODE_SCRATCH;++node) print_node(node);
    emit_frame(command,"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_CAT) {
    if(!filesystem_allowed(task,CAP_RIGHT_READ) || !print_hello()) { emit_frame(command,"DENIED"); return 1u; }
    emit_frame(command,"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_ECHO) { console_write("sonatine fixed echo\n"); emit_frame(command,"OK"); return 0u; }
  if(command==SONATINE_DEMO_WRITE) {
    if(!filesystem_allowed(task,CAP_RIGHT_WRITE)) { emit_frame(command,"DENIED"); return 1u; }
    const enum vfs_result wrote=append_demo_value();
    if(wrote!=VFS_OK) { emit_frame(command,wrote==VFS_NO_SPACE?"NO_SPACE":"FAULT"); return 1u; }
    emit_frame(command,"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_STAT) {
    if(!filesystem_allowed(task,CAP_RIGHT_READ)) { emit_frame(command,"DENIED"); return 1u; }
    print_node(VFS_NODE_HELLO); print_node(VFS_NODE_SCRATCH); emit_frame(command,"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_JOBS) {
    if(demo.state==DEMO_EMPTY) console_write("jobs EMPTY\n");
    else { console_write("jobs id="); console_write_dec(demo.issued.job.job_id);
      console_write(" state="); console_write(state_name(demo.state)); console_write("\n"); }
    emit_frame(command,demo.state==DEMO_EMPTY?"EMPTY":"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_RUN) {
    if(demo.state==DEMO_DISPATCHED || demo.state==DEMO_CANCEL_REQUESTED) { emit_frame(command,"BUSY"); return 1u; }
    if(demo.state==DEMO_FAULT || !submit_demo(task)) { emit_frame(command,"FAULT"); return 1u; }
    demo.stale_completion_rejected=stale_completion_rejected();
    if(!demo.stale_completion_rejected) {
      (void)terminal_fault(task); emit_frame(command,"FAULT"); return 1u;
    }
    demo.state=DEMO_DISPATCHED; demo.checksum=0u; demo.semantic=false;
    console_write("u-demo stale-completion=DENIED\n"); emit_frame(command,"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_CANCEL) {
    if(demo.state==DEMO_EMPTY) { emit_frame(command,"EMPTY"); return 0u; }
    if(demo.state!=DEMO_DISPATCHED || !job_cancel(&demo.binding)) { emit_frame(command,"TOO_LATE"); return 1u; }
    demo.state=DEMO_CANCEL_REQUESTED; emit_frame(command,"OK"); return 0u;
  }
  if(command==SONATINE_DEMO_RESULT) {
    if(demo.state==DEMO_EMPTY) { emit_frame(command,"EMPTY"); return 0u; }
    if((demo.state==DEMO_DISPATCHED || demo.state==DEMO_CANCEL_REQUESTED) &&
       job_completion_count()==SONATINE_JOB_RING_DEPTH) {
      emit_frame(command,"BUSY"); return 1u;
    }
    if(demo.state==DEMO_DISPATCHED) (void)finish_demo(task,false);
    else if(demo.state==DEMO_CANCEL_REQUESTED) (void)finish_demo(task,true);
    if(demo.state==DEMO_COMPLETED || demo.state==DEMO_CANCELLED || demo.state==DEMO_FAULT) {
      emit_frame(command,terminal_status()); return demo.state==DEMO_FAULT?1u:0u;
    }
    emit_frame(command,"FAULT"); return 1u;
  }
  emit_frame(command,"INVALID_ORDER"); return 1u;
}
#ifdef SONATINE_DEMO_SHELL_TESTING
bool sonatine_demo_test_stale_cancel(void) {
  if(demo.state!=DEMO_DISPATCHED) return false;
  struct sonatine_job_binding stale=demo.binding; stale.execution_sequence^=UINT64_C(1);
  return !job_cancel(&stale);
}
bool sonatine_demo_test_stale_completion(void) { return demo.stale_completion_rejected; }
bool sonatine_demo_test_post_completion(void) {
  if(demo.state!=DEMO_DISPATCHED) return false;
  struct raveil_completion_record_v1 completion;
  fill_completion(&completion,RAVEIL_COMPLETION_EXECUTED);
  return job_completion_post(&completion);
}
#endif
