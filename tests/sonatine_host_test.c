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
  const uint16_t peer = task_create("peer", TASK_READY);
  assert(init == 1u);
  assert(peer == 2u);
  assert(task_set_current(init));
  assert(task_current() == init);

  const uint32_t endpoint = ipc_endpoint_create(init);
  const cap_handle_t cap = cap_create(
      init, CAP_OBJECT_ENDPOINT, endpoint,
      CAP_RIGHT_SEND | CAP_RIGHT_RECEIVE);
  assert(cap != 0u);

  struct ipc_message sent = {.tag = 7u, .words = {11u, 22u, 33u, 44u}};
  struct ipc_message received;
  assert(ipc_send(init, cap, &sent) == IPC_OK);
  assert(ipc_receive(peer, cap, &received) == IPC_DENIED);
  assert(ipc_receive(init, cap, &received) == IPC_OK);
  assert(received.sender == init);
  assert(received.tag == 7u);
  assert(received.words[3] == 44u);

  assert(cap_revoke(cap));
  assert(ipc_send(init, cap, &sent) == IPC_DENIED);

  const cap_handle_t control = cap_create(
      init, CAP_OBJECT_ENDPOINT, endpoint,
      CAP_RIGHT_SEND | CAP_RIGHT_RECEIVE | CAP_RIGHT_CONTROL);
  const cap_handle_t peer_send = cap_delegate(init, control, peer, CAP_RIGHT_SEND);
  const cap_handle_t peer_receive = cap_delegate(
      init, control, peer, CAP_RIGHT_RECEIVE);
  assert(peer_send != 0u && peer_receive != 0u);
  assert(cap_delegate(init, control, peer,
                      CAP_RIGHT_SEND | CAP_RIGHT_CONTROL) == 0u);
  assert(cap_delegate(peer, control, peer, CAP_RIGHT_SEND) == 0u);
  assert(ipc_send(peer, peer_send, &sent) == IPC_OK);
  assert(ipc_receive(peer, peer_send, &received) == IPC_DENIED);
  assert(ipc_receive(peer, peer_receive, &received) == IPC_OK);

  assert(task_set_current(peer));
  assert(ipc_receive(peer, peer_receive, &received) == IPC_BLOCKED);
  struct task_view view;
  assert(task_get(peer, &view));
  assert(view.state == TASK_BLOCKED);
  assert(view.wait_kind == TASK_WAIT_IPC_RECEIVE);
  assert(!task_set_current(peer));
  assert(task_set_current(init));
  assert(ipc_send(init, control, &sent) == IPC_OK);
  assert(task_get(peer, &view));
  assert(view.state == TASK_READY);
  assert(ipc_receive(peer, peer_receive, &received) == IPC_OK);

  for (uint16_t tag = 0u; tag < 4u; ++tag) {
    sent.tag = tag;
    assert(ipc_send(init, control, &sent) == IPC_OK);
  }
  assert(ipc_send(init, control, &sent) == IPC_BLOCKED);
  assert(task_get(init, &view));
  assert(view.state == TASK_BLOCKED);
  assert(view.wait_kind == TASK_WAIT_IPC_SEND);
  assert(task_set_current(peer));
  assert(ipc_receive(peer, peer_receive, &received) == IPC_OK);
  assert(received.tag == 0u);
  assert(task_get(init, &view));
  assert(view.state == TASK_READY);
  assert(ipc_send(init, control, &sent) == IPC_OK);

  const cap_handle_t invalid_endpoint = cap_create(
      init, CAP_OBJECT_ENDPOINT, 9u, CAP_RIGHT_SEND);
  assert(ipc_send(init, invalid_endpoint, &sent) == IPC_INVALID);
  assert(task_get(init, &view));
  assert(view.state == TASK_READY);
  assert(cap_revoke(peer_send));
  assert(ipc_send(peer, peer_send, &sent) == IPC_DENIED);
  assert(cap_revoke(control));
  assert(ipc_receive(peer, peer_receive, &received) == IPC_OK);
  return 0;
}
