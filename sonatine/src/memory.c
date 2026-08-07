#include "memory.h"

#include "platform.h"

#define MAX_PAGES (QEMU_RAM_SIZE / SONATINE_PAGE_SIZE)
#define BITMAP_BYTES (MAX_PAGES / 8u)

extern char __kernel_end[];

static uint8_t page_bitmap[BITMAP_BYTES];
static size_t free_page_count;
static size_t first_free_index;

static uintptr_t align_up(uintptr_t value, uintptr_t alignment) {
  return (value + alignment - 1u) & ~(alignment - 1u);
}

static bool page_used(size_t index) {
  return (page_bitmap[index / 8u] & (uint8_t)(1u << (index % 8u))) != 0u;
}

static void page_mark(size_t index, bool used) {
  const uint8_t mask = (uint8_t)(1u << (index % 8u));
  if (used) {
    page_bitmap[index / 8u] |= mask;
  } else {
    page_bitmap[index / 8u] &= (uint8_t)~mask;
  }
}

void phys_init(void) {
  for (size_t index = 0; index < BITMAP_BYTES; ++index) {
    page_bitmap[index] = 0xffu;
  }
  const uintptr_t first = align_up((uintptr_t)__kernel_end, SONATINE_PAGE_SIZE);
  first_free_index = (size_t)((first - QEMU_RAM_BASE) / SONATINE_PAGE_SIZE);
  free_page_count = 0u;
  for (size_t index = first_free_index; index < MAX_PAGES; ++index) {
    page_mark(index, false);
    ++free_page_count;
  }
}

void *phys_alloc_page(void) {
  for (size_t index = first_free_index; index < MAX_PAGES; ++index) {
    if (!page_used(index)) {
      page_mark(index, true);
      --free_page_count;
      return (void *)(QEMU_RAM_BASE + index * SONATINE_PAGE_SIZE);
    }
  }
  return NULL;
}

bool phys_free_page(void *page) {
  const uintptr_t address = (uintptr_t)page;
  if ((address % SONATINE_PAGE_SIZE) != 0u || address < QEMU_RAM_BASE ||
      address >= QEMU_RAM_BASE + QEMU_RAM_SIZE) {
    return false;
  }
  const size_t index = (size_t)((address - QEMU_RAM_BASE) / SONATINE_PAGE_SIZE);
  if (index < first_free_index || !page_used(index)) {
    return false;
  }
  page_mark(index, false);
  ++free_page_count;
  return true;
}

size_t phys_free_pages(void) {
  return free_page_count;
}

size_t phys_total_pages(void) {
  return MAX_PAGES;
}

uintptr_t phys_first_free_address(void) {
  return QEMU_RAM_BASE + first_free_index * SONATINE_PAGE_SIZE;
}
