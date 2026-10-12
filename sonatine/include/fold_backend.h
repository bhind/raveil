#ifndef SONATINE_FOLD_BACKEND_H
#define SONATINE_FOLD_BACKEND_H
#include "graph_backend.h"
bool fold_backend_run_if_present(uint16_t task,cap_handle_t program_cap,
                                 cap_handle_t graph_cap,cap_handle_t data_cap,
                                 cap_handle_t experience_cap);
#endif
