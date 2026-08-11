#ifndef SONATINE_PLANE_AUTHORITY_H
#define SONATINE_PLANE_AUTHORITY_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "capability.h"
#include "job_authority.h"

#define SONATINE_PLANE_AUTHORITY_OBJECT 1u
#define SONATINE_PROGRAM_REGISTRY_SIZE 4u
#define SONATINE_GRAPH_REGISTRY_SIZE 4u
#define SONATINE_EXPERIENCE_LEDGER_SIZE 8u

void plane_authority_init(void);
bool plane_program_install(uint16_t task,cap_handle_t cap,
                           const uint8_t identity[16]);
bool plane_graph_install(uint16_t task,cap_handle_t cap,
                         const uint8_t program[16],const uint8_t graph[16]);
bool plane_data_object_register(uint16_t task,cap_handle_t cap,
                                const struct raveil_object_manifest_v1 *manifest);
bool plane_job_submit_bound(uint16_t task,cap_handle_t data_cap,
                            const struct raveil_job_descriptor_v1 *job,
                            struct sonatine_job_binding *binding);
bool plane_program_approve(uint16_t task,cap_handle_t program_cap,
                           const struct sonatine_job_binding *binding);
enum sonatine_finalize_result plane_data_finalize(
    uint16_t task,cap_handle_t data_cap,
    const struct sonatine_job_binding *binding,bool commit);
bool plane_experience_record(uint16_t task,cap_handle_t experience_cap,
                             const struct raveil_completion_record_v1 *completion);
size_t plane_experience_count(void);

#endif
