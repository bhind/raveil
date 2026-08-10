#ifndef SONATINE_CAPABILITY_H
#define SONATINE_CAPABILITY_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef uint32_t cap_handle_t;

enum cap_object_type {
  CAP_OBJECT_NONE = 0,
  CAP_OBJECT_TASK = 1,
  CAP_OBJECT_ENDPOINT = 2,
  CAP_OBJECT_FRAME = 3,
  CAP_OBJECT_CONSOLE = 4,
  CAP_OBJECT_CLOCK = 5,
  CAP_OBJECT_FILESYSTEM = 6
};

enum cap_rights {
  CAP_RIGHT_READ = 1u << 0u,
  CAP_RIGHT_WRITE = 1u << 1u,
  CAP_RIGHT_SEND = 1u << 2u,
  CAP_RIGHT_RECEIVE = 1u << 3u,
  CAP_RIGHT_CONTROL = 1u << 4u
};

struct cap_view {
  uint16_t owner_task;
  uint16_t object_type;
  uint32_t object_id;
  uint32_t rights;
};

void cap_init(void);
cap_handle_t cap_create(uint16_t owner_task, uint16_t object_type,
                        uint32_t object_id, uint32_t rights);
cap_handle_t cap_delegate(uint16_t source_owner, cap_handle_t source,
                          uint16_t target_owner, uint32_t rights);
bool cap_resolve(uint16_t owner_task, cap_handle_t handle,
                 uint16_t required_type, uint32_t required_rights,
                 struct cap_view *view);
bool cap_revoke(cap_handle_t handle);
size_t cap_active_count(void);
void cap_dump(void);

#endif
