#include "raveil_graph_device_dynamic_request.h"
#include "graph_device_axi4lite_transport.h"
#include "graph_device_dag_runtime.h"

#include <array>
#include <algorithm>
#include <cassert>
#include <sstream>
#include <vector>

namespace {
class FakeRegisterIo final : public raveil::graph_device::RegisterIo {
public:
    FakeRegisterIo(const std::array<std::uint32_t, 256>& oracle, bool corrupt) : oracle_words_(oracle), corrupt_(corrupt) {}
    raveil::graph_device::DeviceRead read32(std::uint32_t offset) override {
        ++reads; events.push_back(offset | 0x80000000U);
        if (offset == 0x2014U || offset == 0x3014U) return {true, 2U};
        if (offset == 0x3018U) return {true, program_words};
        if (offset >= 0x3040U && offset < 0x3060U) return {true, program[(offset - 0x3040U) / 4U + 4U]};
        if (offset == 20U) return {true, started ? 18U : 0U};
        if (offset >= 4096U && offset < 5120U) return {true, oracle_words_[(offset - 4096U) / 4U] ^ (corrupt_ && offset == 4096U ? 1U : 0U)};
        return {true, 0U};
    }
    bool write32(std::uint32_t offset, std::uint32_t value) override {
        ++writes; events.push_back(offset);
        if (offset >= 0x3400U && offset < 0x3480U) program[(offset - 0x3400U) / 4U] = value, ++program_words;
        if (offset == 16U && value == 1U) started = true;
        return true;
    }
    unsigned reads = 0U, writes = 0U, program_words = 0U;
    std::vector<std::uint32_t> events;
private:
    std::array<std::uint32_t, 32> program{};
    std::array<std::uint32_t, 256> oracle_words_{};
    bool started = false;
    bool corrupt_ = false;
};
}

int main(int argc, char** argv) {
    if (argc != 2 && argc != 3) return 2;
    const auto request = raveil::graph_device::read_projected_dynamic_graph_device_request(argv[1]);
    FakeRegisterIo fake(request.oracle, argc == 3);
    std::ostringstream log, errors;
    const int result = raveil::graph_device::run_projected_dynamic_graph_host_adapter(
        fake, argv[1], log, errors);
    if (argc == 3) { assert(result != 0); assert(errors.str().find("differs from oracle") != std::string::npos); return 0; }
    assert(result == 0); assert(errors.str().empty()); assert(fake.writes >= 324U + 48U); assert(fake.reads >= 256U);
    const auto first_program = std::find(fake.events.begin(), fake.events.end(), 0x3400U);
    const auto first_input = std::find(fake.events.begin(), fake.events.end(), 0x400U);
    const auto start = std::find(first_input, fake.events.end(), 16U);
    const auto output = std::find(fake.events.begin(), fake.events.end(), 0x80001000U);
    assert(first_program != fake.events.end() && first_input != fake.events.end() && start != fake.events.end());
    assert(first_program < first_input && first_input < start && start < output);
}
