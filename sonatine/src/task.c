#include "task.h"

#include "console.h"
#include "util.h"

#define TASK_TABLE_SIZE 8u
#define TASK_NAME_SIZE 16u

struct task_entry {
  bool active;
  uint16_t id;
  enum task_state state;
  char name[TASK_NAME_SIZE];
};

static struct task_entry task_table[TASK_TABLE_SIZE];
static uint16_t current_task;

void task_init(void) {
  for (size_t index = 0; index < TASK_TABLE_SIZE; ++index) {
    task_table[index].active = false;
  }
  current_task = 0u;
}

uint16_t task_create(const char *name, enum task_state state) {
  for (size_t index = 0; index < TASK_TABLE_SIZE; ++index) {
    struct task_entry *entry = &task_table[index];
    if (!entry->active) {
      entry->active = true;
      entry->id = (uint16_t)(index + 1u);
      entry->state = state;
      rv_strcpy_bounded(entry->name, name, TASK_NAME_SIZE);
      return entry->id;
    }
  }
  return 0u;
}

bool task_set_current(uint16_t task_id) {
  if (task_id == 0u || task_id > TASK_TABLE_SIZE ||
      !task_table[task_id - 1u].active) {
    return false;
  }
  if (current_task != 0u && current_task <= TASK_TABLE_SIZE &&
      task_table[current_task - 1u].state == TASK_RUNNING) {
    task_table[current_task - 1u].state = TASK_READY;
  }
  current_task = task_id;
  task_table[task_id - 1u].state = TASK_RUNNING;
  return true;
}

uint16_t task_current(void) {
  return current_task;
}

size_t task_count(void) {
  size_t count = 0u;
  for (size_t index = 0; index < TASK_TABLE_SIZE; ++index) {
    if (task_table[index].active) {
      ++count;
    }
  }
  return count;
}

bool task_get(uint16_t task_id, struct task_view *view) {
  if (task_id == 0u || task_id > TASK_TABLE_SIZE || view == NULL) {
    return false;
  }
  const struct task_entry *entry = &task_table[task_id - 1u];
  if (!entry->active) {
    return false;
  }
  view->id = entry->id;
  view->state = entry->state;
  view->name = entry->name;
  return true;
}

void task_dump(void) {
  console_write("id  state    name\n");
  for (uint16_t id = 1u; id <= TASK_TABLE_SIZE; ++id) {
    struct task_view view;
    if (!task_get(id, &view)) {
      continue;
    }
    console_write_dec(view.id);
    console_write("   ");
    switch (view.state) {
      case TASK_READY: console_write("ready    "); break;
      case TASK_RUNNING: console_write("running  "); break;
      case TASK_BLOCKED: console_write("blocked  "); break;
      case TASK_STOPPED: console_write("stopped  "); break;
      default: console_write("unused   "); break;
    }
    console_write(view.name);
    console_write("\n");
  }
}
