#include "context.h"
#include <stddef.h>
#include "console.h"
#include "platform.h"
#include "task.h"
#include "trap.h"
#define CONTEXT_STACK_SIZE 4096u
#define CONTEXT_FRAME_WORDS 14u
extern void context_switch(uintptr_t **old_stack, uintptr_t *new_stack);
static unsigned char idle_stack[CONTEXT_STACK_SIZE] __attribute__((aligned(16)));
static uintptr_t *init_sp;
static uintptr_t *idle_sp;
static uint16_t init_id;
static uint16_t idle_id;
static bool observed;
static volatile uint64_t preemption_count;
static unsigned char user_kernel_stack[CONTEXT_STACK_SIZE] __attribute__((aligned(16)));
static unsigned char preempt_idle_stack[CONTEXT_STACK_SIZE] __attribute__((aligned(16)));
static struct trap_frame *user_frame;
static struct trap_frame *preempt_idle_frame;
extern void context_start(struct trap_frame *frame) __attribute__((noreturn));
static void idle_entry(void) {
  if (!task_set_current(idle_id)) for (;;) {}
  console_write("context switch: init -> idle -> init\n");
  observed=true;
  context_switch(&idle_sp,init_sp);
  for (;;) {}
}
bool context_switch_smoke(uint16_t init_task,uint16_t idle_task) {
  init_id=init_task; idle_id=idle_task; observed=false;
  preemption_count=0u;
  uintptr_t top=(uintptr_t)(idle_stack+sizeof(idle_stack));
  top&=~(uintptr_t)0xfu;
  idle_sp=(uintptr_t *)(top-CONTEXT_FRAME_WORDS*sizeof(uintptr_t));
  for(size_t i=0;i<CONTEXT_FRAME_WORDS;++i) idle_sp[i]=0u;
  idle_sp[0]=(uintptr_t)&idle_entry;
  context_switch(&init_sp,idle_sp);
  return observed && task_set_current(init_id);
}
static void preempt_idle_entry(void) { for(;;) cpu_wait(); }
static struct trap_frame *frame_at_top(unsigned char *stack) {
  uintptr_t top=(uintptr_t)(stack+CONTEXT_STACK_SIZE);
  top&=~(uintptr_t)0xfu;
  return (struct trap_frame *)(top-TRAP_FRAME_SIZE);
}
static void clear_frame(struct trap_frame *frame) {
  uint64_t *words=(uint64_t *)frame;
  for(size_t i=0;i<sizeof(*frame)/sizeof(*words);++i) words[i]=0u;
}
bool context_preemption_configure(uint16_t init_task, uint16_t idle_task,
                                  uintptr_t user_entry, uintptr_t user_stack,
                                  cap_handle_t console_cap,
                                  cap_handle_t clock_cap,
                                  cap_handle_t endpoint_cap,
                                  cap_handle_t wrong_owner_cap,
                                  cap_handle_t send_only_cap,
                                  cap_handle_t filesystem_cap,
                                  cap_handle_t filesystem_read_cap,
                                  cap_handle_t demo_broker_cap) {
  init_id=init_task; idle_id=idle_task;
  user_frame=frame_at_top(user_kernel_stack);
  preempt_idle_frame=frame_at_top(preempt_idle_stack);
  clear_frame(user_frame); clear_frame(preempt_idle_frame);
  user_frame->mepc=user_entry;
  user_frame->mstatus=TRAP_MSTATUS_MPIE;
  trap_set_gpr(user_frame,2u,user_stack);
  trap_set_gpr(user_frame,8u,console_cap);
  trap_set_gpr(user_frame,9u,clock_cap);
  trap_set_gpr(user_frame,18u,endpoint_cap);
  trap_set_gpr(user_frame,19u,wrong_owner_cap);
  trap_set_gpr(user_frame,20u,send_only_cap);
  trap_set_gpr(user_frame,21u,filesystem_cap);
  trap_set_gpr(user_frame,22u,filesystem_read_cap);
  trap_set_gpr(user_frame,27u,demo_broker_cap);
  preempt_idle_frame->mepc=(uintptr_t)&preempt_idle_entry;
  preempt_idle_frame->mstatus=TRAP_MSTATUS_MPP_M|TRAP_MSTATUS_MPIE;
  trap_set_gpr(preempt_idle_frame,2u,
               (uintptr_t)(preempt_idle_stack+CONTEXT_STACK_SIZE));
  preemption_count=0u;
  return task_current()==init_id;
}
void context_start_user(void) {
  context_start(user_frame);
}
uint64_t context_preemption_count(void) { return preemption_count; }
uint16_t context_user_task(void) { return init_id; }
uintptr_t context_trap_select(uintptr_t frame,uintptr_t pc,uintptr_t *resume_pc) {
  ++preemption_count;
  if(task_current()==init_id) {
    struct task_view idle;
    if(!task_get(idle_id, &idle) || idle.state != TASK_READY) {
      *resume_pc=pc; return frame;
    }
    user_frame=(struct trap_frame *)frame;
    user_frame->mepc=pc;
    if(!task_set_current(idle_id)) for(;;) {}
    console_write("clint-preempt from=1 to=2\n");
    *resume_pc=pc;
    return (uintptr_t)preempt_idle_frame;
  } else if(task_current()==idle_id) {
    struct task_view init;
    if(!task_get(init_id, &init) || init.state != TASK_READY) {
      *resume_pc=pc; return frame;
    }
    preempt_idle_frame=(struct trap_frame *)frame;
    preempt_idle_frame->mepc=pc;
    if(!task_set_current(init_id)) for(;;) {}
    console_write("clint-preempt from=2 to=1\n");
    *resume_pc=pc;
    return (uintptr_t)user_frame;
  }
  *resume_pc=pc; return frame;
}
