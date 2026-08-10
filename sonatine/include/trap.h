#ifndef SONATINE_TRAP_H
#define SONATINE_TRAP_H

#include <stddef.h>
#include <stdint.h>

#define TRAP_FRAME_SIZE 272u
#define TRAP_MSTATUS_MPIE (1UL << 7u)
#define TRAP_MSTATUS_MPP_M (3UL << 11u)
#define TRAP_MSTATUS_MPP_MASK (3UL << 11u)

struct trap_frame {
  uint64_t gpr[31];
  uint64_t mepc;
  uint64_t mstatus;
  uint64_t padding;
};

_Static_assert(sizeof(struct trap_frame) == TRAP_FRAME_SIZE,
               "trap frame size must match trap.S");
_Static_assert(offsetof(struct trap_frame, mepc) == 248u,
               "trap mepc offset must match trap.S");
_Static_assert(offsetof(struct trap_frame, mstatus) == 256u,
               "trap mstatus offset must match trap.S");

static inline uint64_t trap_get_gpr(const struct trap_frame *frame,
                                    unsigned register_number) {
  return frame->gpr[register_number - 1u];
}

static inline void trap_set_gpr(struct trap_frame *frame,
                                unsigned register_number, uint64_t value) {
  frame->gpr[register_number - 1u] = value;
}

#endif
