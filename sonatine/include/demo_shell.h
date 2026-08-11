#ifndef SONATINE_DEMO_SHELL_H
#define SONATINE_DEMO_SHELL_H

#include <stdbool.h>
#include <stdint.h>

#include "capability.h"

#define SONATINE_DEMO_AUTHORITY_OBJECT 2u
#define SONATINE_DEMO_FRAME_PREFIX "RAVEIL-SONATINE-DEMO-V1 "
/* Exact grammar (ASCII, no optional fields; maximum including newline 171):
 * RAVEIL-SONATINE-DEMO-V1 command=<fixed> seq=<u64-dec> status=<fixed>
 * job=<u64-dec> state=<fixed> semantic=<0|1> checksum=<16-lowercase-hex>\n
 * command: ls|cat|echo|write|stat|jobs|run|cancel|result|invalid
 * status: OK|EMPTY|BUSY|TOO_LATE|DENIED|NO_SPACE|INVALID_ORDER|COMPLETED|
 *         CANCELLED|FAULT
 * state: EMPTY|DISPATCHED|CANCEL_REQUESTED|COMPLETED|CANCELLED|FAULT
 * Only trusted kernel code emits this prefix. */
#define SONATINE_DEMO_FRAME_MAX 171u

/* Fixed scalar commands accepted by the U-mode operator demo. */
enum sonatine_demo_command {
  SONATINE_DEMO_LS=1u,
  SONATINE_DEMO_CAT=2u,
  SONATINE_DEMO_ECHO=3u,
  SONATINE_DEMO_WRITE=4u,
  SONATINE_DEMO_STAT=5u,
  SONATINE_DEMO_JOBS=6u,
  SONATINE_DEMO_RUN=7u,
  SONATINE_DEMO_CANCEL=8u,
  SONATINE_DEMO_RESULT=9u
};

bool sonatine_demo_init(uint16_t task,cap_handle_t broker_cap,cap_handle_t program_cap,
                        cap_handle_t graph_cap,cap_handle_t data_cap,
                        cap_handle_t experience_cap,cap_handle_t filesystem_cap);
uint64_t sonatine_demo_command_run(uint16_t task,cap_handle_t console_cap,
                                   cap_handle_t broker_cap,
                                   enum sonatine_demo_command command);

#ifdef SONATINE_DEMO_SHELL_TESTING
bool sonatine_demo_test_stale_cancel(void);
bool sonatine_demo_test_stale_completion(void);
bool sonatine_demo_test_post_completion(void);
#endif

#endif
