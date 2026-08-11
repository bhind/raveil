#ifndef SONATINE_JOB_AUTHORITY_TEST_API_H
#define SONATINE_JOB_AUTHORITY_TEST_API_H

#include "job_authority.h"

bool job_object_register_test(const struct raveil_object_manifest_v1 *manifest);
bool job_submit_test(const struct raveil_job_descriptor_v1 *job);
bool job_submit_bound_test(const struct raveil_job_descriptor_v1 *job,
                           struct sonatine_job_binding *binding);
bool job_shadow_approve_test(const struct sonatine_job_binding *binding);
enum sonatine_finalize_result job_shadow_finalize_test(
    const struct sonatine_job_binding *binding,bool commit);

#define job_object_register job_object_register_test
#define job_submit job_submit_test
#define job_submit_bound job_submit_bound_test
#define job_shadow_approve job_shadow_approve_test
#define job_shadow_finalize job_shadow_finalize_test

#endif
