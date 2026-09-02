#include "raveil_graph_device_uio.h"
#include "graph_device_dag_runtime.h"
#include "graph_device_dag_generated.h"
#include "graph_device_uio_request_generated.h"

#include <array>
#include <cerrno>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>

namespace {
namespace request = raveil::graph_device::uio_request_generated;

std::uint32_t little_u32(const unsigned char* bytes) {
    return static_cast<std::uint32_t>(bytes[0])
        | (static_cast<std::uint32_t>(bytes[1]) << 8U)
        | (static_cast<std::uint32_t>(bytes[2]) << 16U)
        | (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

template <std::size_t Size>
bool exact_file(
    const std::filesystem::path& path,
    const std::array<unsigned char, Size>& expected
) {
    const auto state = std::filesystem::symlink_status(path);
    if (!std::filesystem::is_regular_file(state)
        || std::filesystem::is_symlink(state)
        || std::filesystem::file_size(path) != Size) return false;
    std::array<unsigned char, Size> actual{};
    std::ifstream stream(path, std::ios::binary);
    stream.read(reinterpret_cast<char*>(actual.data()), actual.size());
    return stream.gcount() == static_cast<std::streamsize>(actual.size())
        && stream.peek() == EOF && actual == expected;
}

std::pair<const char*, std::uint32_t> admitted_request(
    const std::filesystem::path& root
) {
    const auto state = std::filesystem::symlink_status(root);
    if (!std::filesystem::is_directory(state)
        || std::filesystem::is_symlink(state)) {
        throw std::runtime_error("request root must be a direct directory");
    }
    if (!exact_file(root / "uio-request.bin", request::kBinding)
        || !exact_file(root / "request.json", request::kRequestJson)
        || !exact_file(root / "request-input.bin", request::kInput)
        || little_u32(request::kBinding.data()) != 0x52555131U
        || little_u32(request::kBinding.data() + 4) != 1U
        || little_u32(request::kBinding.data() + 8) != request::kBinding.size()) {
        throw std::runtime_error("UIO request binding is invalid");
    }
    const std::uint32_t graph = little_u32(request::kBinding.data() + 12);
    if (graph >= raveil::graph_device::dag_generated::kGraphs.size()) {
        throw std::runtime_error("UIO request graph is invalid");
    }
    const std::uint32_t seed = little_u32(request::kBinding.data() + 16);
    if (seed != request::kSeed
        || std::string(raveil::graph_device::dag_generated::kGraphs[graph].id)
            != request::kGraphId) {
        throw std::runtime_error("UIO compiled request identity differs");
    }
    const auto input = root / "inputs" / ("seed-" + std::to_string(seed) + ".bin");
    if (!exact_file(input, request::kInput)) {
        throw std::runtime_error("UIO request input is invalid");
    }
    return {raveil::graph_device::dag_generated::kGraphs[graph].id, seed};
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 3) { std::cerr << "usage: raveil-graph-device-uio-run /dev/uioN REQUEST_ROOT\n"; return 2; }
    try {
        const std::filesystem::path root(argv[2]);
        const auto [graph_id, seed] = admitted_request(root);
        auto io = raveil::graph_device::UioRegisterIo::open_checked(argv[1]);
        // These are relative words in the contract's fixed 16 KiB aperture;
        // this runner intentionally has no physical-address input.
        raveil::graph_device::Axi4LiteTransport transport(io, 0x0000U, 0x2000U, 0x3000U);
        std::ostringstream runtime_log;
        std::ostringstream runtime_errors;
        const int result = raveil::graph_device::run_selected_dag(
            transport, transport, transport, root, graph_id, seed,
            runtime_log, runtime_errors
        );
        if (result != 0) {
            std::cerr << runtime_errors.str();
            return result;
        }
        std::cout << "GraphDevice-UIO-TRANSPORT-V1 runtime_return=0"
            << " graph_output=unpromoted evidence=linux-uio-transport-unverified"
            << " same_rtl=not-verified hardware=not-verified\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "UIO Graph-device runner: " << error.what() << '\n';
        return 1;
    }
}
