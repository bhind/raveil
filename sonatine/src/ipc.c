#include "ipc.h"

#include <stddef.h>

#define ENDPOINT_TABLE_SIZE 8u
#define ENDPOINT_QUEUE_DEPTH 4u

struct endpoint {
  bool active;
  uint16_t owner_task;
  uint8_t read_index;
  uint8_t write_index;
  uint8_t count;
  struct ipc_message queue[ENDPOINT_QUEUE_DEPTH];
};

static struct endpoint endpoints[ENDPOINT_TABLE_SIZE];

void ipc_init(void) {
  for (size_t index = 0; index < ENDPOINT_TABLE_SIZE; ++index) {
    endpoints[index].active = false;
  }
}

uint32_t ipc_endpoint_create(uint16_t owner_task) {
  for (size_t index = 0; index < ENDPOINT_TABLE_SIZE; ++index) {
    struct endpoint *endpoint = &endpoints[index];
    if (!endpoint->active) {
      endpoint->active = true;
      endpoint->owner_task = owner_task;
      endpoint->read_index = 0u;
      endpoint->write_index = 0u;
      endpoint->count = 0u;
      return (uint32_t)(index + 1u);
    }
  }
  return 0u;
}

static struct endpoint *resolve_endpoint(uint16_t task, cap_handle_t handle,
                                         uint32_t right) {
  struct cap_view view;
  if (!cap_resolve(task, handle, CAP_OBJECT_ENDPOINT, right, &view) ||
      view.object_id == 0u || view.object_id > ENDPOINT_TABLE_SIZE) {
    return NULL;
  }
  struct endpoint *endpoint = &endpoints[view.object_id - 1u];
  return endpoint->active ? endpoint : NULL;
}

bool ipc_send(uint16_t sender_task, cap_handle_t endpoint_cap,
              const struct ipc_message *message) {
  struct endpoint *endpoint = resolve_endpoint(sender_task, endpoint_cap, CAP_RIGHT_SEND);
  if (endpoint == NULL || message == NULL || endpoint->count == ENDPOINT_QUEUE_DEPTH) {
    return false;
  }
  endpoint->queue[endpoint->write_index] = *message;
  endpoint->queue[endpoint->write_index].sender = sender_task;
  endpoint->write_index = (uint8_t)((endpoint->write_index + 1u) % ENDPOINT_QUEUE_DEPTH);
  ++endpoint->count;
  return true;
}

bool ipc_receive(uint16_t receiver_task, cap_handle_t endpoint_cap,
                 struct ipc_message *message) {
  struct endpoint *endpoint = resolve_endpoint(receiver_task, endpoint_cap, CAP_RIGHT_RECEIVE);
  if (endpoint == NULL || message == NULL || endpoint->count == 0u ||
      endpoint->owner_task != receiver_task) {
    return false;
  }
  *message = endpoint->queue[endpoint->read_index];
  endpoint->read_index = (uint8_t)((endpoint->read_index + 1u) % ENDPOINT_QUEUE_DEPTH);
  --endpoint->count;
  return true;
}
