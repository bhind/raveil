#include <assert.h>
#include <string.h>
#include "raveil_driver_core.h"

static struct raveil_driver_request request(uint32_t opcode,uint64_t id,uint64_t argument) {
  struct raveil_driver_request value={0};
  value.magic=RAVEIL_DRIVER_MAGIC; value.abi_version=RAVEIL_DRIVER_ABI_VERSION;
  value.struct_size=sizeof(value); value.opcode=opcode; value.request_id=id;
  value.argument=argument; return value;
}
int main(void) {
  struct raveil_driver_core core; struct raveil_driver_completion done;
  struct raveil_driver_request ping=request(RAVEIL_OP_PING,7u,0x83u);
  raveil_driver_core_init(&core);
  assert(raveil_driver_reap(&core,&done)==RAVEIL_STATUS_EMPTY);
  assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_OK);
  assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_BUSY);
  assert(raveil_driver_reap(&core,&done)==RAVEIL_STATUS_OK);
  assert(done.request_id==7u && done.result==0x83u && done.status==RAVEIL_STATUS_OK);
  assert(done.magic==RAVEIL_DRIVER_MAGIC &&
         done.abi_version==RAVEIL_DRIVER_ABI_VERSION &&
         done.struct_size==sizeof(done) && done.detail==0u);
  assert(raveil_driver_reap(&core,&done)==RAVEIL_STATUS_EMPTY);
  ping.magic=0u; assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_INVALID);
  ping=request(RAVEIL_OP_NOP,8u,9u); ping.abi_version++;
  assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_INVALID);
  ping=request(RAVEIL_OP_NOP,8u,9u); ping.struct_size--;
  assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_INVALID);
  ping=request(RAVEIL_OP_NOP,8u,9u); ping.flags=1u;
  assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_INVALID);
  ping=request(99u,8u,9u);
  assert(raveil_driver_submit(&core,&ping)==RAVEIL_STATUS_INVALID);
  raveil_driver_core_init(&core);
  assert(raveil_driver_reap(&core,&done)==RAVEIL_STATUS_EMPTY);
  return 0;
}
