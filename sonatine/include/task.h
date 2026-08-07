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

struct task_view {
  uint16_t id;
  enum task_state state;
  const char *name;
};

void task_init(void);
uint16_t task_create(const char *name, enum task_state state);
bool task_set_current(uint16_t task_id);
uint16_t task_current(void);
size_t task_count(void);
bool task_get(uint16_t task_id, struct task_view *view);
void task_dump(void);

#endif
