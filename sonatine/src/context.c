#include "context.h"
#include <stddef.h>
#include "console.h"
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
static void idle_entry(void) {
  if (!task_set_current(idle_id)) for (;;) {}
  console_write("context switch: init -> idle -> init\n");
  observed=true;
  context_switch(&idle_sp,init_sp);
  for (;;) {}
}
bool context_switch_smoke(uint16_t init_task,uint16_t idle_task) {
  init_id=init_task; idle_id=idle_task; observed=false;
  uintptr_t top=(uintptr_t)(idle_stack+sizeof(idle_stack));
  top&=~(uintptr_t)0xfu;
  idle_sp=(uintptr_t *)(top-CONTEXT_FRAME_WORDS*sizeof(uintptr_t));
  for(size_t i=0;i<CONTEXT_FRAME_WORDS;++i) idle_sp[i]=0u;
  idle_sp[0]=(uintptr_t)&idle_entry;
  context_switch(&init_sp,idle_sp);
  return observed && task_set_current(init_id);
}
