#ifndef RAVEIL_LINUX_DRIVER_CORE_H
#define RAVEIL_LINUX_DRIVER_CORE_H
#include <stdbool.h>
#include "uapi/raveil_driver.h"
struct raveil_driver_core {
  bool completion_ready;
  struct raveil_driver_completion completion;
};
void raveil_driver_core_init(struct raveil_driver_core *core);
uint32_t raveil_driver_submit(struct raveil_driver_core *core,
                              const struct raveil_driver_request *request);
uint32_t raveil_driver_reap(struct raveil_driver_core *core,
                            struct raveil_driver_completion *completion);
#endif
