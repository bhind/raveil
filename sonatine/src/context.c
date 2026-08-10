#include "context.h"
#include <stddef.h>
#include "console.h"
#include "platform.h"
#include "task.h"
#define CONTEXT_STACK_SIZE 4096u
#define CONTEXT_FRAME_WORDS 14u
extern void context_switch(uintptr_t **old_stack, uintptr_t *new_stack);
static unsigned char idle_stack[CONTEXT_STACK_SIZE] __attribute__((aligned(16)));
static uintptr_t *init_sp;
static uintptr_t *idle_sp;
static uint16_t init_id;
static uint16_t idle_id;
static bool observed;
static bool preemption_enabled;
static volatile uint64_t preemption_count;
static unsigned char preempt_idle_stack[CONTEXT_STACK_SIZE] __attribute__((aligned(16)));
static uintptr_t preempt_init_frame;
static uintptr_t preempt_idle_frame;
static uintptr_t preempt_init_pc;
static uintptr_t preempt_idle_pc;
static void idle_entry(void) {
  if (!task_set_current(idle_id)) for (;;) {}
  console_write("context switch: init -> idle -> init\n");
  observed=true;
  context_switch(&idle_sp,init_sp);
  for (;;) {}
}
bool context_switch_smoke(uint16_t init_task,uint16_t idle_task) {
  init_id=init_task; idle_id=idle_task; observed=false; preemption_enabled=false;
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
void context_preemption_enable(void) {
  uintptr_t top=(uintptr_t)(preempt_idle_stack+sizeof(preempt_idle_stack));
  top&=~(uintptr_t)0xfu;
  preempt_idle_frame=top-256u;
  uintptr_t *words=(uintptr_t *)preempt_idle_frame;
  for(size_t i=0;i<32u;++i) words[i]=0u;
  preempt_idle_pc=(uintptr_t)&preempt_idle_entry;
  preempt_init_frame=0u; preempt_init_pc=0u;
  preemption_count=0u; preemption_enabled=true;
}
uint64_t context_preemption_count(void) { return preemption_count; }
uintptr_t context_trap_select(uintptr_t frame,uintptr_t pc,uintptr_t *resume_pc) {
  if(!preemption_enabled) { *resume_pc=pc; return frame; }
  ++preemption_count;
  if(task_current()==init_id) {
    preempt_init_frame=frame; preempt_init_pc=pc;
    if(!task_set_current(idle_id)) for(;;) {}
    *resume_pc=preempt_idle_pc; return preempt_idle_frame;
  } else if(task_current()==idle_id) {
    preempt_idle_frame=frame; preempt_idle_pc=pc;
    if(!task_set_current(init_id)) for(;;) {}
    *resume_pc=preempt_init_pc; return preempt_init_frame;
  }
  *resume_pc=pc; return frame;
}
