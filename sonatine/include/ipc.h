#ifndef SONATINE_IPC_H
#define SONATINE_IPC_H

#include <stdbool.h>
#include <stdint.h>

#include "capability.h"

#define IPC_MESSAGE_WORDS 4u

struct ipc_message {
  uint16_t sender;
  uint16_t tag;
  uint64_t words[IPC_MESSAGE_WORDS];
};

enum ipc_result {
  IPC_OK = 0,
  IPC_BLOCKED = 1,
  IPC_DENIED = 2,
  IPC_INVALID = 3
};

void ipc_init(void);
uint32_t ipc_endpoint_create(uint16_t owner_task);
enum ipc_result ipc_send(uint16_t sender_task, cap_handle_t endpoint_cap,
                         const struct ipc_message *message);
enum ipc_result ipc_receive(uint16_t receiver_task, cap_handle_t endpoint_cap,
                            struct ipc_message *message);

#endif
