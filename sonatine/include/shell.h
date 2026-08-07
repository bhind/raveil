#ifndef SONATINE_SHELL_H
#define SONATINE_SHELL_H

#include <stdint.h>

#include "capability.h"

void shell_run(uint16_t init_task, cap_handle_t init_endpoint);

#endif
