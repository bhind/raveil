#include "capability.h"
#include "console.h"
#include "completion_telemetry.h"
#include "context.h"
#include "ipc.h"
#include "graph_backend.h"
#include "job_authority.h"
#include "memory.h"
#include "platform.h"
#include "plane_authority.h"
#include "shell.h"
#include "task.h"
#include "timer.h"
#include "vm.h"
#include "user.h"
#include "vfs.h"

static void boot_ok(const char *subsystem) {
  console_write("  [ok] ");
  console_write(subsystem);
  console_write("\n");
}

static void boot_fail(const char *subsystem) {
  console_write("  [fail] ");
  console_write(subsystem);
  console_write("\nSonatine halted\n");
  for (;;) {
    cpu_wait();
  }
}

static bool job_contract_smoke(uint16_t task,cap_handle_t program_cap,
                               cap_handle_t graph_cap,cap_handle_t data_cap,
                               cap_handle_t experience_cap) {
  const uint64_t started=*(volatile uint64_t *)QEMU_CLINT_MTIME;
  struct raveil_object_manifest_v1 object={0};
  object.magic=RAVEIL_OBJECT_MANIFEST_MAGIC;
  object.schema_version=RAVEIL_OBJECT_MANIFEST_V1;
  object.struct_size=sizeof(object);
  object.permitted_access=RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE;
  object.object_id=1u; object.generation=1u; object.version=1u;
  object.byte_length=8u; object.backing=RAVEIL_OBJECT_BACKING_VOLATILE;
  struct raveil_job_descriptor_v1 job={0};
  job.magic=RAVEIL_JOB_MAGIC; job.schema_version=RAVEIL_JOB_SCHEMA_V1;
  job.struct_size=sizeof(job); job.object_count=1u; job.job_id=1u;
  job.program_identity[0]=1u; job.graph_variant_identity[0]=1u;
  job.execution_contract_identity[0]=1u; job.target_signature[0]=1u;
  job.resources=(struct raveil_resource_bounds_v1){1u,1u,8u,1u};
  job.objects[0]=(struct raveil_object_ref_v1){1u,1u,1u,0u,8u,RAVEIL_OBJECT_WRITE,0u};
  job_authority_init(1u);
  struct sonatine_job_binding binding;
  if(!plane_program_install(task,program_cap,job.program_identity) ||
     !plane_graph_install(task,graph_cap,job.program_identity,
                          job.graph_variant_identity) ||
     !plane_data_object_register(task,data_cap,&object) ||
     !plane_job_submit_bound(task,data_cap,&job,&binding)) return false;
  struct sonatine_submission issued;
  if(!job_submission_take(&issued)) return false;
  struct raveil_completion_record_v1 completion={0},taken;
  completion.magic=RAVEIL_COMPLETION_MAGIC;
  completion.schema_version=RAVEIL_JOB_SCHEMA_V1;
  completion.struct_size=sizeof(completion); completion.status=RAVEIL_COMPLETION_EXECUTED;
  completion.job_id=job.job_id; completion.execution_epoch=issued.execution_epoch;
  completion.execution_sequence=issued.execution_sequence;
  for(size_t index=0;index<16u;++index)
    completion.completion_cookie[index]=issued.completion_cookie[index];
  completion.output_count=1u;
  completion.outputs[0]=(struct raveil_object_version_v1){1u,1u,2u};
  if(!job_completion_post(&completion) || job_completion_post(&completion) ||
     !job_completion_take(&taken) || job_completion_take(&taken) ||
     job_inflight_count()!=0u) return false;
  const uint64_t finished=*(volatile uint64_t *)QEMU_CLINT_MTIME;
  if(finished<=started) return false;
  if(!plane_experience_record(task,experience_cap,&taken)) return false;
  completion_telemetry_emit(&taken,finished-started);
  struct raveil_object_manifest_v1 observed;
  if(!job_object_lookup(1u,&observed) || observed.version!=1u) return false;
  if(!plane_program_approve(task,program_cap,&binding) ||
     plane_data_finalize(task,data_cap,&binding,true)!=SONATINE_FINALIZE_COMMITTED ||
     plane_data_finalize(task,data_cap,&binding,true)!=SONATINE_FINALIZE_INVALID ||
     !job_object_lookup(1u,&observed) || observed.version!=2u) return false;
  job.objects[0].expected_version=2u;
  job.job_id=2u;
  if(!plane_job_submit_bound(task,data_cap,&job,&binding) || !job_cancel(&binding) ||
     job_submission_take(&issued)) return false;
  job.job_id=3u;
  if(!plane_job_submit_bound(task,data_cap,&job,&binding) ||
     !job_submission_take(&issued)) return false;
  completion.job_id=issued.job.job_id;
  completion.execution_epoch=issued.execution_epoch;
  completion.execution_sequence=issued.execution_sequence;
  for(size_t index=0;index<16u;++index)
    completion.completion_cookie[index]=issued.completion_cookie[index];
  completion.outputs[0].version=3u;
  if(!job_completion_post(&completion) || !job_completion_take(&taken) ||
     plane_data_finalize(task,data_cap,&binding,false)!=SONATINE_FINALIZE_ROLLED_BACK)
    return false;
  return job_inflight_count()==0u && job_shadow_count()==0u;
}

void kmain(void) {
  console_init();
  console_write("\nRaveil boot v" RAVEIL_VERSION "\n");
  console_write("Sonatine kernel (RV64 QEMU virt)\n");
  console_write("platform contract: " SONATINE_PLATFORM_NAME "\n");
  boot_ok("console / ns16550a polled UART");

  phys_init();
  if (phys_free_pages() == 0u) {
    boot_fail("physical memory");
  }
  boot_ok("physical memory / 4 KiB bitmap allocator");

  void *user_code = phys_alloc_page();
  void *user_stack = phys_alloc_page();
  if (user_code == NULL || user_stack == NULL ||
      !vm_init((uintptr_t)user_code, (uintptr_t)user_stack) ||
      !user_init_prepare((uintptr_t)user_code)) {
    boot_fail("Sv39 address space");
  }
  vm_activate();
  boot_ok("Sv39 / supervisor kernel map + user window");

  console_write("starting U-mode init: ");
  user_init_enter();
  boot_ok("U-mode init / ecall boundary");
  user_fault_probe_enter();
  boot_ok("U-mode fault / contained return to kernel");

  cap_init();
  boot_ok("capability / generation-checked fixed table");

  task_init();
  const uint16_t init_task = task_create("init", TASK_READY);
  const uint16_t idle_task = task_create("idle", TASK_READY);
  if (init_task == 0u || idle_task == 0u || !task_set_current(init_task)) {
    boot_fail("task");
  }
  boot_ok("task / init + idle kernel tasks");
  if (!context_switch_smoke(init_task, idle_task)) {
    boot_fail("context switch");
  }
  boot_ok("context switch / independent idle stack");

  ipc_init();
  vfs_init();
  const uint32_t endpoint = ipc_endpoint_create(init_task);
  const cap_handle_t endpoint_cap = cap_create(
      init_task, CAP_OBJECT_ENDPOINT, endpoint,
      CAP_RIGHT_SEND | CAP_RIGHT_RECEIVE | CAP_RIGHT_CONTROL);
  const cap_handle_t task_cap = cap_create(
      init_task, CAP_OBJECT_TASK, init_task, CAP_RIGHT_READ | CAP_RIGHT_CONTROL);
  const cap_handle_t console_cap = cap_create(
      init_task, CAP_OBJECT_CONSOLE, 1u, CAP_RIGHT_READ | CAP_RIGHT_WRITE);
  const cap_handle_t clock_cap = cap_create(
      init_task, CAP_OBJECT_CLOCK, 1u, CAP_RIGHT_READ);
  const cap_handle_t wrong_owner_cap = cap_create(
      idle_task, CAP_OBJECT_ENDPOINT, endpoint, CAP_RIGHT_SEND);
  const cap_handle_t send_only_cap = cap_create(
      init_task, CAP_OBJECT_ENDPOINT, endpoint, CAP_RIGHT_SEND);
  const cap_handle_t filesystem_cap = cap_create(
      init_task, CAP_OBJECT_FILESYSTEM, VFS_ROOT_OBJECT,
      CAP_RIGHT_READ | CAP_RIGHT_WRITE);
  const cap_handle_t filesystem_read_cap = cap_create(
      init_task, CAP_OBJECT_FILESYSTEM, VFS_ROOT_OBJECT, CAP_RIGHT_READ);
  const cap_handle_t program_authority_cap = cap_create(
      init_task,CAP_OBJECT_PROGRAM_AUTHORITY,SONATINE_PLANE_AUTHORITY_OBJECT,
      CAP_RIGHT_CONTROL);
  const cap_handle_t graph_authority_cap = cap_create(
      init_task,CAP_OBJECT_GRAPH_AUTHORITY,SONATINE_PLANE_AUTHORITY_OBJECT,
      CAP_RIGHT_CONTROL);
  const cap_handle_t data_authority_cap = cap_create(
      init_task,CAP_OBJECT_DATA_AUTHORITY,SONATINE_PLANE_AUTHORITY_OBJECT,
      CAP_RIGHT_WRITE|CAP_RIGHT_CONTROL);
  const cap_handle_t experience_authority_cap = cap_create(
      init_task,CAP_OBJECT_EXPERIENCE_AUTHORITY,SONATINE_PLANE_AUTHORITY_OBJECT,
      CAP_RIGHT_WRITE|CAP_RIGHT_CONTROL);
  if (endpoint == 0u || endpoint_cap == 0u || task_cap == 0u ||
      console_cap == 0u || clock_cap == 0u || wrong_owner_cap == 0u ||
      send_only_cap == 0u || filesystem_cap == 0u ||
      filesystem_read_cap == 0u || program_authority_cap == 0u ||
      graph_authority_cap == 0u || data_authority_cap == 0u ||
      experience_authority_cap == 0u) {
    boot_fail("IPC");
  }
  boot_ok("IPC / bounded mailbox protected by capabilities");
  boot_ok("VFS / immutable initramfs + bounded RamFS");
  plane_authority_init();
  if(!job_contract_smoke(init_task,program_authority_cap,graph_authority_cap,
                         data_authority_cap,experience_authority_cap))
    boot_fail("Daphnis contract");
  boot_ok("Daphnis contract / object table + bounded rings + replay guard");
  boot_ok("Daphnis metadata shadow / injected approval + commit + cancel + rollback");
  boot_ok("four-plane authority / registry + capability write firewall");

  if(graph_backend_run_if_present(init_task,program_authority_cap,
                                  graph_authority_cap,data_authority_cap,
                                  experience_authority_cap))
    boot_fail("graph backend returned");

  timer_init();
  boot_ok("timer / CLINT machine timer at 100 Hz");
  if (!context_preemption_configure(
          init_task,idle_task,SONATINE_USER_BASE+user_shell_offset(),
          SONATINE_USER_BASE+2u*SONATINE_PAGE_SIZE,console_cap,clock_cap,
          endpoint_cap,wrong_owner_cap,send_only_cap,filesystem_cap,
          filesystem_read_cap)) {
    boot_fail("persistent U-mode context");
  }
  boot_ok("persistent U-mode shell / current-task syscall identity");
  context_start_user();
}
