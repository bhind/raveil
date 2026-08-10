#include "ipc.h"

#include <stddef.h>
#include "task.h"

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

static enum ipc_result resolve_endpoint(uint16_t task, cap_handle_t handle,
                                        uint32_t right,
                                        struct endpoint **resolved,
                                        uint32_t *object_id) {
  struct cap_view view;
  if (!cap_resolve(task, handle, CAP_OBJECT_ENDPOINT, right, &view)) {
    return IPC_DENIED;
  }
  if (view.object_id == 0u || view.object_id > ENDPOINT_TABLE_SIZE ||
      !endpoints[view.object_id - 1u].active) {
    return IPC_INVALID;
  }
  *resolved = &endpoints[view.object_id - 1u];
  *object_id = view.object_id;
  return IPC_OK;
}

enum ipc_result ipc_send(uint16_t sender_task, cap_handle_t endpoint_cap,
                         const struct ipc_message *message) {
  struct endpoint *endpoint;
  uint32_t object_id;
  if (message == NULL) {
    return IPC_INVALID;
  }
  const enum ipc_result resolution = resolve_endpoint(
      sender_task, endpoint_cap, CAP_RIGHT_SEND, &endpoint, &object_id);
  if (resolution != IPC_OK) {
    return resolution;
  }
  if (endpoint->count == ENDPOINT_QUEUE_DEPTH) {
    return task_block(sender_task, TASK_WAIT_IPC_SEND, object_id)
               ? IPC_BLOCKED : IPC_INVALID;
  }
  endpoint->queue[endpoint->write_index] = *message;
  endpoint->queue[endpoint->write_index].sender = sender_task;
  endpoint->write_index = (uint8_t)((endpoint->write_index + 1u) % ENDPOINT_QUEUE_DEPTH);
  ++endpoint->count;
  (void)task_wake_one(TASK_WAIT_IPC_RECEIVE, object_id, NULL);
  return IPC_OK;
}

enum ipc_result ipc_receive(uint16_t receiver_task, cap_handle_t endpoint_cap,
                            struct ipc_message *message) {
  struct endpoint *endpoint;
  uint32_t object_id;
  if (message == NULL) {
    return IPC_INVALID;
  }
  const enum ipc_result resolution = resolve_endpoint(
      receiver_task, endpoint_cap, CAP_RIGHT_RECEIVE, &endpoint, &object_id);
  if (resolution != IPC_OK) {
    return resolution;
  }
  if (endpoint->count == 0u) {
    return task_block(receiver_task, TASK_WAIT_IPC_RECEIVE, object_id)
               ? IPC_BLOCKED : IPC_INVALID;
  }
  *message = endpoint->queue[endpoint->read_index];
  endpoint->read_index = (uint8_t)((endpoint->read_index + 1u) % ENDPOINT_QUEUE_DEPTH);
  --endpoint->count;
  (void)task_wake_one(TASK_WAIT_IPC_SEND, object_id, NULL);
  return IPC_OK;
}
