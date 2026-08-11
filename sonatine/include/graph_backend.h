#ifndef SONATINE_GRAPH_BACKEND_H
#define SONATINE_GRAPH_BACKEND_H
#include <stdbool.h>
#include <stdint.h>
#include "capability.h"
bool graph_backend_run_if_present(uint16_t task,cap_handle_t program_cap,
                                  cap_handle_t graph_cap,cap_handle_t data_cap,
                                  cap_handle_t experience_cap);
#endif
