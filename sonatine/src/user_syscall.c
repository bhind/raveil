#include "user.h"

#include "capability.h"
#include "console.h"
#include "context.h"
#include "demo_shell.h"
#include "ipc.h"
#include "platform.h"
#include "task.h"
#include "timer.h"
#include "vfs.h"

#define SYS_LOG 10u
#define SYS_GETC 11u
#define SYS_CLOCK 12u
#define SYS_IPC_SEND 13u
#define SYS_IPC_RECEIVE 14u
#define SYS_EXIT 15u
#define SYS_CAP_PROBE 16u
#define SYS_FS_READ 17u
#define SYS_FS_WRITE 18u
#define SYS_PUTC 19u
#define SYS_DEMO 20u

#define SYS_OK 0u
#define SYS_DENIED ((uint64_t)-1)
#define SYS_INVALID ((uint64_t)-2)
#define SYS_WOULD_BLOCK ((uint64_t)-3)

static bool user_prose_byte_allowed(uint8_t value) {
  static const char protected_prefix[]=SONATINE_DEMO_FRAME_PREFIX;
  static size_t matched;
  if(value==(uint8_t)protected_prefix[matched]) {
    ++matched;
    if(protected_prefix[matched]=='\0') { matched=0u; return false; }
  } else matched=value==(uint8_t)protected_prefix[0]?1u:0u;
  return true;
}

static bool current_user(uint16_t *task_id) {
  const uint16_t current=task_current();
  struct task_view view;
  if(!task_get(current,&view) || view.state!=TASK_RUNNING) return false;
  *task_id=current; return true;
}

static bool resolve_current(cap_handle_t handle,uint16_t type,uint32_t rights) {
  uint16_t current;
  return current_user(&current) &&
         cap_resolve(current,handle,type,rights,NULL);
}

static void log_event(uint64_t event,uint64_t detail,uint64_t value) {
  switch(event) {
    case 1u: console_write("raveil-u> "); break;
    case 2u: console_write("help info ticks ipc fs ls cat echo write stat jobs run cancel result exit\n"); break;
    case 3u: console_write("u-cmd info=ok\n"); break;
    case 4u: console_write("u-shell resumed task=1\n"); break;
    case 5u: console_write("error: command too long\n"); break;
    case 6u: console_write("error: unknown command\n"); break;
    case 8u: console_write("u-ipc send=OK receive=OK\n"); break;
    case 9u: console_write("u-cmd ticks=ok\n"); break;
    case 10u: console_write("u-context register-frame=ok task=1\n"); break;
    case 11u:
      console_write("u-context mismatch=register-x");
      console_write_dec(detail); console_write(" value=");
      console_write_hex(value); console_write("\n"); break;
    case 12u: console_write("u-context mismatch=argument-register\n"); break;
    case 13u: console_write("u-vfs read=hello write-readback=OK\n"); break;
    default: console_write("u-log invalid\n"); break;
  }
}

uintptr_t user_syscall_dispatch(struct trap_frame *frame) {
  const uint64_t number=trap_get_gpr(frame,17u);
  const uint64_t arg0=trap_get_gpr(frame,10u);
  const uint64_t arg1=trap_get_gpr(frame,11u);
  uint16_t current;
  uint64_t result=SYS_INVALID;
  if(!current_user(&current)) return user_fault_dispatch(8u,frame);
  if(number==SYS_LOG) {
    if(resolve_current((cap_handle_t)arg0,CAP_OBJECT_CONSOLE,CAP_RIGHT_WRITE)) {
      log_event(arg1,trap_get_gpr(frame,12u),trap_get_gpr(frame,13u));
      result=SYS_OK;
    } else result=SYS_DENIED;
  } else if(number==SYS_GETC) {
    if(resolve_current((cap_handle_t)arg0,CAP_OBJECT_CONSOLE,CAP_RIGHT_READ)) {
      char value;
      result=console_try_getc(&value)?(uint8_t)value:SYS_WOULD_BLOCK;
    } else result=SYS_DENIED;
  } else if(number==SYS_PUTC) {
    if(resolve_current((cap_handle_t)arg0,CAP_OBJECT_CONSOLE,CAP_RIGHT_WRITE) &&
       arg1<=0x7fu && user_prose_byte_allowed((uint8_t)arg1)) {
      console_putc((char)arg1); result=SYS_OK;
    } else result=SYS_DENIED;
  } else if(number==SYS_CLOCK) {
    if(resolve_current((cap_handle_t)arg0,CAP_OBJECT_CLOCK,CAP_RIGHT_READ))
      result=timer_ticks();
    else result=SYS_DENIED;
  } else if(number==SYS_IPC_SEND) {
    struct ipc_message message={.sender=0u,.tag=0x83u,.words={arg1,0u,0u,0u}};
    enum ipc_result sent=ipc_send(current,(cap_handle_t)arg0,&message);
    result=sent==IPC_OK?SYS_OK:SYS_DENIED;
  } else if(number==SYS_IPC_RECEIVE) {
    struct ipc_message message;
    enum ipc_result received=ipc_receive(current,(cap_handle_t)arg0,&message);
    result=received==IPC_OK?message.words[0]:SYS_DENIED;
  } else if(number==SYS_CAP_PROBE) {
    uint32_t rights=arg1==3u?CAP_RIGHT_RECEIVE:CAP_RIGHT_SEND;
    bool denied=!cap_resolve(current,(cap_handle_t)arg0,CAP_OBJECT_ENDPOINT,
                             rights,NULL);
    if(denied && arg1>=1u && arg1<=3u) {
      console_write(arg1==1u?"kernel-cap forged=DENIED\n":
                    arg1==2u?"kernel-cap wrong-owner=DENIED\n":
                             "kernel-cap escalation=DENIED\n");
      result=SYS_OK;
    } else result=SYS_INVALID;
  } else if(number==SYS_FS_READ) {
    struct cap_view root;
    if(!cap_resolve(current,(cap_handle_t)arg0,CAP_OBJECT_FILESYSTEM,
                    CAP_RIGHT_READ,&root) || root.object_id!=VFS_ROOT_OBJECT) {
      result=SYS_DENIED;
    } else {
      uint8_t value;
      enum vfs_result read=vfs_read((uint32_t)(arg1&0xffu),
                                    (size_t)((arg1>>8u)&0xffffu),&value);
      result=read==VFS_OK?value:SYS_INVALID;
    }
  } else if(number==SYS_FS_WRITE) {
    struct cap_view root;
    if(!cap_resolve(current,(cap_handle_t)arg0,CAP_OBJECT_FILESYSTEM,
                    CAP_RIGHT_WRITE,&root) || root.object_id!=VFS_ROOT_OBJECT) {
      console_write("kernel-file rights=DENIED\n"); result=SYS_DENIED;
    } else {
      enum vfs_result wrote=vfs_write((uint32_t)(arg1&0xffu),
          (size_t)((arg1>>8u)&0xffffu),(uint8_t)(arg1>>24u));
      if(wrote==VFS_DENIED) console_write("kernel-file initramfs=DENIED\n");
      result=wrote==VFS_OK?SYS_OK:wrote==VFS_DENIED?SYS_DENIED:SYS_INVALID;
    }
  } else if(number==SYS_DEMO) {
    result=sonatine_demo_command_run(current,(cap_handle_t)arg0,
                                     (cap_handle_t)trap_get_gpr(frame,12u),
                                     (enum sonatine_demo_command)arg1);
  } else if(number==SYS_EXIT && current==context_user_task()) {
    (void)task_stop(current);
    console_write("u-shell exit task=1\n");
    *(volatile uint32_t *)QEMU_TEST_FINISHER=0x5555u;
    for(;;) cpu_wait();
  } else {
    return user_fault_dispatch(8u,frame);
  }
  trap_set_gpr(frame,10u,result);
  frame->mepc+=4u;
  return (uintptr_t)frame;
}

void machine_fault_dispatch(uint64_t cause,const struct trap_frame *frame) {
  console_write("\nFATAL: machine trap cause="); console_write_hex(cause);
  console_write(" mepc="); console_write_hex(frame->mepc);
  console_write("\n");
  *(volatile uint32_t *)QEMU_TEST_FINISHER=0x3333u;
  for(;;) cpu_wait();
}

uintptr_t user_fault_dispatch(uint64_t cause,struct trap_frame *frame) {
  const uint16_t current=task_current();
  (void)task_stop(current);
  console_write("u-fault contained task="); console_write_dec(current);
  console_write(" cause="); console_write_hex(cause);
  console_write(" state=stopped\n");
  *(volatile uint32_t *)QEMU_TEST_FINISHER=0x3333u;
  (void)frame;
  for(;;) cpu_wait();
}
