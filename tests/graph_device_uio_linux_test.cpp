#if defined(__linux__)
#include "raveil_graph_device_uio.h"
#include <cassert>
#include <cstdio>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

int main() {
  void* memory = mmap(nullptr, raveil::graph_device::UioRegisterIo::kBytes, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(memory != MAP_FAILED);
  auto* words = static_cast<volatile unsigned int*>(memory);
  words[0] = 7; assert(words[0] == 7);
  assert(munmap(memory, raveil::graph_device::UioRegisterIo::kBytes) == 0);
  char path[] = "/tmp/raveil-uio-test.XXXXXX";
  const int fd = mkstemp(path); assert(fd >= 0); close(fd);
  bool rejected = false;
  try { (void)raveil::graph_device::UioRegisterIo::open_checked(path); } catch (...) { rejected = true; }
  unlink(path); assert(rejected);
}
#else
int main() { return 0; }
#endif
