#ifndef SONATINE_TASK_H
#define SONATINE_TASK_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum task_state {
  TASK_UNUSED = 0,
  TASK_READY = 1,
  TASK_RUNNING = 2,
  TASK_BLOCKED = 3,
  TASK_STOPPED = 4
};

enum task_wait_kind {
  TASK_WAIT_NONE = 0,
  TASK_WAIT_IPC_SEND = 1,
  TASK_WAIT_IPC_RECEIVE = 2
};

struct task_view {
  uint16_t id;
  enum task_state state;
  enum task_wait_kind wait_kind;
  uint32_t wait_object;
  const char *name;
};

void task_init(void);
uint16_t task_create(const char *name, enum task_state state);
bool task_set_current(uint16_t task_id);
bool task_block(uint16_t task_id, enum task_wait_kind kind, uint32_t object_id);
bool task_stop(uint16_t task_id);
bool task_wake_one(enum task_wait_kind kind, uint32_t object_id,
                   uint16_t *task_id);
uint16_t task_current(void);
size_t task_count(void);
bool task_get(uint16_t task_id, struct task_view *view);
void task_dump(void);

#endif
