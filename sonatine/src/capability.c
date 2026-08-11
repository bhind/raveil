#include "capability.h"

#include "console.h"

#define CAP_TABLE_SIZE 64u

struct cap_entry {
  bool active;
  bool retired;
  uint16_t generation;
  struct cap_view view;
};

static struct cap_entry cap_table[CAP_TABLE_SIZE];

static cap_handle_t make_handle(size_t slot, uint16_t generation) {
  return ((uint32_t)generation << 16u) | (uint32_t)(slot + 1u);
}

static bool decode_handle(cap_handle_t handle, size_t *slot, uint16_t *generation) {
  const uint32_t encoded_slot = handle & 0xffffu;
  if (encoded_slot == 0u || encoded_slot > CAP_TABLE_SIZE) {
    return false;
  }
  *slot = (size_t)(encoded_slot - 1u);
  *generation = (uint16_t)(handle >> 16u);
  return true;
}

void cap_init(void) {
  for (size_t index = 0; index < CAP_TABLE_SIZE; ++index) {
    cap_table[index].active = false;
    cap_table[index].retired = false;
    cap_table[index].generation = 1u;
  }
}

cap_handle_t cap_create(uint16_t owner_task, uint16_t object_type,
                        uint32_t object_id, uint32_t rights) {
  const uint32_t all_rights = CAP_RIGHT_READ | CAP_RIGHT_WRITE |
                              CAP_RIGHT_SEND | CAP_RIGHT_RECEIVE |
                              CAP_RIGHT_CONTROL;
  if (owner_task == 0u || object_type == CAP_OBJECT_NONE ||
      object_type > CAP_OBJECT_EXPERIENCE_AUTHORITY || object_id == 0u || rights == 0u ||
      (rights & ~all_rights) != 0u) {
    return 0u;
  }
  if (object_type == CAP_OBJECT_FILESYSTEM &&
      (rights & ~(CAP_RIGHT_READ | CAP_RIGHT_WRITE)) != 0u) {
    return 0u;
  }
  if ((object_type == CAP_OBJECT_PROGRAM_AUTHORITY ||
       object_type == CAP_OBJECT_GRAPH_AUTHORITY) &&
      rights != CAP_RIGHT_CONTROL) {
    return 0u;
  }
  if ((object_type == CAP_OBJECT_DATA_AUTHORITY ||
       object_type == CAP_OBJECT_EXPERIENCE_AUTHORITY) &&
      (rights & ~(CAP_RIGHT_WRITE | CAP_RIGHT_CONTROL)) != 0u) {
    return 0u;
  }
  for (size_t index = 0; index < CAP_TABLE_SIZE; ++index) {
    struct cap_entry *entry = &cap_table[index];
    if (!entry->active && !entry->retired) {
      entry->active = true;
      entry->view.owner_task = owner_task;
      entry->view.object_type = object_type;
      entry->view.object_id = object_id;
      entry->view.rights = rights;
      return make_handle(index, entry->generation);
    }
  }
  return 0u;
}

cap_handle_t cap_delegate(uint16_t source_owner, cap_handle_t source,
                          uint16_t target_owner, uint32_t rights) {
  size_t slot;
  uint16_t generation;
  if (target_owner == 0u || rights == 0u ||
      (rights & CAP_RIGHT_CONTROL) != 0u ||
      !decode_handle(source, &slot, &generation)) {
    return 0u;
  }
  const struct cap_entry *entry = &cap_table[slot];
  if (!entry->active || entry->generation != generation ||
      entry->view.owner_task != source_owner ||
      (entry->view.rights & CAP_RIGHT_CONTROL) == 0u ||
      (entry->view.rights & rights) != rights) {
    return 0u;
  }
  return cap_create(target_owner, entry->view.object_type,
                    entry->view.object_id, rights);
}

bool cap_resolve(uint16_t owner_task, cap_handle_t handle,
                 uint16_t required_type, uint32_t required_rights,
                 struct cap_view *view) {
  size_t slot;
  uint16_t generation;
  if (!decode_handle(handle, &slot, &generation)) {
    return false;
  }
  const struct cap_entry *entry = &cap_table[slot];
  if (!entry->active || entry->generation != generation ||
      entry->view.owner_task != owner_task ||
      entry->view.object_type != required_type ||
      (entry->view.rights & required_rights) != required_rights) {
    return false;
  }
  if (view != NULL) {
    *view = entry->view;
  }
  return true;
}

bool cap_revoke(cap_handle_t handle) {
  size_t slot;
  uint16_t generation;
  if (!decode_handle(handle, &slot, &generation)) {
    return false;
  }
  struct cap_entry *entry = &cap_table[slot];
  if (!entry->active || entry->generation != generation) {
    return false;
  }
  entry->active = false;
  if (entry->generation == UINT16_MAX) {
    entry->retired = true;
  } else {
    ++entry->generation;
  }
  return true;
}

size_t cap_active_count(void) {
  size_t count = 0u;
  for (size_t index = 0; index < CAP_TABLE_SIZE; ++index) {
    if (cap_table[index].active) {
      ++count;
    }
  }
  return count;
}

void cap_dump(void) {
  console_write("handle      owner type object rights\n");
  for (size_t index = 0; index < CAP_TABLE_SIZE; ++index) {
    const struct cap_entry *entry = &cap_table[index];
    if (!entry->active) {
      continue;
    }
    console_write_hex(make_handle(index, entry->generation));
    console_write("  ");
    console_write_dec(entry->view.owner_task);
    console_write("     ");
    console_write_dec(entry->view.object_type);
    console_write("    ");
    console_write_dec(entry->view.object_id);
    console_write("      ");
    console_write_hex(entry->view.rights);
    console_write("\n");
  }
}
