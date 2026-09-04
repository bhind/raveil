#include "raveil_graph_device_dynamic_request.h"
#include "graph_device_axi4lite_transport.h"
#include "graph_device_dag_runtime.h"

#include <array>
#include <cassert>
#include <sstream>

namespace {
class FakeRegisterIo final : public raveil::graph_device::RegisterIo {
public:
    explicit FakeRegisterIo(const std::array<std::uint32_t, 256>& oracle) : oracle_words_(oracle) {}
    raveil::graph_device::DeviceRead read32(std::uint32_t offset) override {
        ++reads;
        if (offset == 0x2014U || offset == 0x3014U) return {true, 2U};
        if (offset == 0x3018U) return {true, program_words};
        if (offset >= 0x3040U && offset < 0x3060U) return {true, program[(offset - 0x3040U) / 4U + 4U]};
        if (offset == 20U) return {true, started ? 18U : 0U};
        if (offset >= 4096U && offset < 5120U) return {true, oracle_words_[(offset - 4096U) / 4U]};
        return {true, 0U};
    }
    bool write32(std::uint32_t offset, std::uint32_t value) override {
        ++writes;
        if (offset >= 0x3400U && offset < 0x3480U) program[(offset - 0x3400U) / 4U] = value, ++program_words;
        if (offset == 16U && value == 1U) started = true;
        return true;
    }
    unsigned reads = 0U, writes = 0U, program_words = 0U;
private:
    std::array<std::uint32_t, 32> program{};
    std::array<std::uint32_t, 256> oracle_words_{};
    bool started = false;
};
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const auto request = raveil::graph_device::read_projected_dynamic_graph_device_request(argv[1]);
    FakeRegisterIo fake(request.oracle);
    raveil::graph_device::Axi4LiteTransport transport(fake, 0U, 0x2000U, 0x3000U);
    std::ostringstream log, errors;
    const int result = raveil::graph_device::run_dynamic_dag(
        transport, transport, transport, request.request.graph_id.c_str(), request.request.affine.c_str(),
        request.request.program, request.request.input, request.oracle, request.request.seed, log, errors);
    assert(result == 0); assert(errors.str().empty()); assert(fake.writes >= 324U + 48U); assert(fake.reads >= 256U);
}
