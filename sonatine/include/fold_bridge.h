#ifndef SONATINE_FOLD_BRIDGE_H
#define SONATINE_FOLD_BRIDGE_H
#include "job_authority.h"
bool fold_bridge_exchange(const uint8_t *request,size_t size,
                          const struct sonatine_submission *issued,
                          uint32_t count,uint32_t output[256]);
bool fold_bridge_exchange_checked(const uint8_t *request,size_t size,
                          const struct sonatine_submission *issued,
                          uint32_t count,uint32_t output[256],bool *framed);
#endif
