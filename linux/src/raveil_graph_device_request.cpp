#include "raveil_graph_device_request.h"

#include "graph_device_dag_generated.h"

#include <array>
#include <fstream>
#include <stdexcept>
#include <string>

namespace raveil::graph_device {
namespace {
constexpr std::size_t kInputWords = 324U;
constexpr std::size_t kRequestBytes = 20U;

std::uint32_t word(const unsigned char* p) {
    return static_cast<std::uint32_t>(p[0])
        | (static_cast<std::uint32_t>(p[1]) << 8U)
        | (static_cast<std::uint32_t>(p[2]) << 16U)
        | (static_cast<std::uint32_t>(p[3]) << 24U);
}

template <std::size_t N>
std::array<unsigned char, N> read_exact(const std::filesystem::path& path) {
    const auto status = std::filesystem::symlink_status(path);
    if (std::filesystem::is_symlink(status)
        || !std::filesystem::is_regular_file(status)
        || std::filesystem::file_size(path) != N) {
        throw std::runtime_error("request file is not an exact regular file");
    }
    std::array<unsigned char, N> bytes{};
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(N));
    if (!input || input.peek() != EOF) throw std::runtime_error("request file read failed");
    return bytes;
}

std::array<std::uint32_t, kInputWords> expected_input(std::uint32_t seed) {
    std::array<std::uint32_t, kInputWords> result{};
    const std::uint32_t multiplier = seed * 2654435761U;
    for (std::size_t i = 0; i < result.size(); ++i) {
        result[i] = (static_cast<std::uint32_t>(i + 1U) * multiplier)
            ^ (static_cast<std::uint32_t>(i) << (seed & 7U)) ^ (seed * 17U);
    }
    return result;
}

void compare_input(const std::filesystem::path& path, std::uint32_t seed) {
    const auto bytes = read_exact<kInputWords * 4U>(path);
    const auto expected = expected_input(seed);
    for (std::size_t i = 0; i < expected.size(); ++i) {
        if (word(bytes.data() + i * 4U) != expected[i])
            throw std::runtime_error("request input does not match seed");
    }
}
}  // namespace

AdmittedGraphDeviceRequest admit_graph_device_request(const std::filesystem::path& root) {
    const auto root_status = std::filesystem::symlink_status(root);
    if (std::filesystem::is_symlink(root_status)
        || !std::filesystem::is_directory(root_status))
        throw std::runtime_error("request root must be a direct directory");
    const auto binding = read_exact<kRequestBytes>(root / "uio-request.bin");
    if (word(binding.data()) != 0x52555131U || word(binding.data() + 4) != 1U
        || word(binding.data() + 8) != kRequestBytes)
        throw std::runtime_error("UIO request header is invalid");
    const std::uint32_t index = word(binding.data() + 12);
    if (index >= dag_generated::kGraphs.size()) throw std::runtime_error("graph index is invalid");
    const std::uint32_t seed = word(binding.data() + 16);
    const auto inputs = root / "inputs";
    const auto inputs_status = std::filesystem::symlink_status(inputs);
    if (std::filesystem::is_symlink(inputs_status)
        || !std::filesystem::is_directory(inputs_status))
        throw std::runtime_error("inputs must be a direct directory");
    compare_input(root / "request-input.bin", seed);
    compare_input(inputs / ("seed-" + std::to_string(seed) + ".bin"), seed);
    // run_selected_dag() first exercises its fixed malformed-program matrix;
    // that path consumes seed-1 input before the selected invocation.
    compare_input(inputs / "seed-1.bin", 1U);
    return {dag_generated::kGraphs[index].id, seed};
}
}  // namespace raveil::graph_device
