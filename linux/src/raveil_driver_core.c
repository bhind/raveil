#include "raveil_driver_core.h"

static bool valid_request(const struct raveil_driver_request *request) {
  return request != 0 && request->magic == RAVEIL_DRIVER_MAGIC &&
         request->abi_version == RAVEIL_DRIVER_ABI_VERSION &&
         request->struct_size == sizeof(*request) && request->flags == 0u &&
         (request->opcode == RAVEIL_OP_PING || request->opcode == RAVEIL_OP_NOP);
}

void raveil_driver_core_init(struct raveil_driver_core *core) {
  core->completion_ready = false;
}

uint32_t raveil_driver_submit(struct raveil_driver_core *core,
                              const struct raveil_driver_request *request) {
  if (core == 0 || !valid_request(request)) return RAVEIL_STATUS_INVALID;
  if (core->completion_ready) return RAVEIL_STATUS_BUSY;
  core->completion.magic = RAVEIL_DRIVER_MAGIC;
  core->completion.abi_version = RAVEIL_DRIVER_ABI_VERSION;
  core->completion.struct_size = sizeof(core->completion);
  core->completion.status = RAVEIL_STATUS_OK;
  core->completion.detail = 0u;
  core->completion.request_id = request->request_id;
  core->completion.result = request->opcode == RAVEIL_OP_PING
                                ? request->argument
                                : 0u;
  core->completion_ready = true;
  return RAVEIL_STATUS_OK;
}

uint32_t raveil_driver_reap(struct raveil_driver_core *core,
                            struct raveil_driver_completion *completion) {
  if (core == 0 || completion == 0) return RAVEIL_STATUS_INVALID;
  if (!core->completion_ready) return RAVEIL_STATUS_EMPTY;
  *completion = core->completion;
  core->completion_ready = false;
  return RAVEIL_STATUS_OK;
}
