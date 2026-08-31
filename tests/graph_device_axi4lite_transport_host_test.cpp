#include "graph_device_axi4lite_transport.h"

#include <cassert>
#include <cstdint>
#include <vector>

namespace {
class Fake final : public raveil::graph_device::RegisterIo {
 public:
  std::vector<std::uint32_t> calls;
  raveil::graph_device::DeviceRead read32(std::uint32_t offset) override { calls.push_back(offset); return {true, offset}; }
  bool write32(std::uint32_t offset, std::uint32_t) override { calls.push_back(offset); return true; }
};
}

int main() {
  Fake fake;
  raveil::graph_device::Axi4LiteTransport transport(fake, 0, 0x2000, 0x3000);
  assert(transport.write_word(4, 1));
  assert(transport.write_install_word(4, 2));
  assert(transport.write_program_word(4, 3));
  assert((fake.calls == std::vector<std::uint32_t>{0x10, 0x2010, 0x3010}));
  assert(transport.read_word(0x7ffU).ok);
  assert(transport.read_install_word(0x3ffU).ok);
  assert(transport.read_program_word(0x3ffU).ok);
  assert((fake.calls == std::vector<std::uint32_t>{
      0x10, 0x2010, 0x3010, 0x1ffc, 0x2ffc, 0x3ffc}));
  const auto before = fake.calls.size();
  assert(!transport.write_word(0xffffffffU, 4));
  assert(!transport.read_word(0x800U).ok);
  assert(!transport.read_install_word(0x400U).ok);
  assert(!transport.read_program_word(0x400U).ok);
  assert(fake.calls.size() == before);

  raveil::graph_device::Axi4LiteTransport misaligned(fake, 1, 0x2000, 0x3000);
  assert(!misaligned.read_word(0).ok);
  assert(fake.calls.size() == before);
}
