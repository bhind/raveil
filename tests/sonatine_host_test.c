#include <assert.h>
#include <stdint.h>

#include "capability.h"
#include "ipc.h"
#include "task.h"

void console_write(const char *text) { (void)text; }
void console_write_dec(uint64_t value) { (void)value; }
void console_write_hex(uint64_t value) { (void)value; }

int main(void) {
  task_init();
  cap_init();
  ipc_init();

  const uint16_t init = task_create("init", TASK_READY);
  assert(init == 1u);
  assert(task_set_current(init));
  assert(task_current() == init);

  const uint32_t endpoint = ipc_endpoint_create(init);
  const cap_handle_t cap = cap_create(
      init, CAP_OBJECT_ENDPOINT, endpoint,
      CAP_RIGHT_SEND | CAP_RIGHT_RECEIVE);
  assert(cap != 0u);

  struct ipc_message sent = {.tag = 7u, .words = {11u, 22u, 33u, 44u}};
  struct ipc_message received;
  assert(ipc_send(init, cap, &sent));
  assert(!ipc_receive((uint16_t)(init + 1u), cap, &received));
  assert(ipc_receive(init, cap, &received));
  assert(received.sender == init);
  assert(received.tag == 7u);
  assert(received.words[3] == 44u);

  assert(cap_revoke(cap));
  assert(!ipc_send(init, cap, &sent));
  return 0;
}
