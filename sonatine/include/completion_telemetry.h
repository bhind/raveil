#ifndef SONATINE_COMPLETION_TELEMETRY_H
#define SONATINE_COMPLETION_TELEMETRY_H
#include <stdint.h>
#include "raveil/job_contract.h"

void completion_telemetry_emit(
    const struct raveil_completion_record_v1 *completion,
    uint64_t smoke_path_ticks);
#endif
