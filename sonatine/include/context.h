#ifndef SONATINE_CONTEXT_H
#define SONATINE_CONTEXT_H
#include <stdbool.h>
#include <stdint.h>
bool context_switch_smoke(uint16_t init_task, uint16_t idle_task);
#endif
