#ifndef SONATINE_FOLD_SESSION_H
#define SONATINE_FOLD_SESSION_H
#include "graph_backend.h"
bool fold_session_run_if_present(uint16_t task,cap_handle_t program_cap,
                                 cap_handle_t graph_cap,cap_handle_t data_cap,
                                 cap_handle_t experience_cap);
#endif
