#ifndef SONATINE_MEMORY_H
#define SONATINE_MEMORY_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SONATINE_PAGE_SIZE 4096UL

void phys_init(void);
void *phys_alloc_page(void);
bool phys_free_page(void *page);
size_t phys_free_pages(void);
size_t phys_total_pages(void);
uintptr_t phys_first_free_address(void);

#endif
