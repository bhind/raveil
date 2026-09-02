#include "raveil_graph_device_dynamic_request.h"

#include "graph_device_affine_generated.h"

#include <array>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace raveil::graph_device {
namespace {
constexpr std::uint32_t kMagic = 0x52445731U;
constexpr std::uint32_t kVersion = 1U;
constexpr std::uint32_t kHeaderBytes = 64U;
constexpr std::size_t kGraphIdBytes = 32U;
constexpr std::size_t kRequestBytes = 64U + kGraphIdBytes + (32U + 16U + 324U) * 4U;

std::uint32_t word(const unsigned char* p) {
    return static_cast<std::uint32_t>(p[0])
        | (static_cast<std::uint32_t>(p[1]) << 8U)
        | (static_cast<std::uint32_t>(p[2]) << 16U)
        | (static_cast<std::uint32_t>(p[3]) << 24U);
}

std::vector<unsigned char> read_request(const std::filesystem::path& root) {
    const auto status = std::filesystem::symlink_status(root);
    if (std::filesystem::is_symlink(status) || !std::filesystem::is_directory(status))
        throw std::runtime_error("dynamic request root must be a direct directory");
    const auto path = root / "request.bin";
    const auto file_status = std::filesystem::symlink_status(path);
    if (std::filesystem::is_symlink(file_status)
        || !std::filesystem::is_regular_file(file_status)
        || std::filesystem::file_size(path) != kRequestBytes)
        throw std::runtime_error("dynamic request must be an exact regular file");
    std::vector<unsigned char> bytes(kRequestBytes);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!input || input.peek() != EOF) throw std::runtime_error("dynamic request read failed");
    return bytes;
}

std::array<std::uint32_t, 324> read_input_file(const std::filesystem::path& path) {
    const auto status = std::filesystem::symlink_status(path);
    if (std::filesystem::is_symlink(status) || !std::filesystem::is_regular_file(status)
        || std::filesystem::file_size(path) != 324U * 4U)
        throw std::runtime_error("dynamic input is not an exact regular file");
    std::array<unsigned char, 324U * 4U> bytes{};
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!input || input.peek() != EOF) throw std::runtime_error("dynamic input read failed");
    std::array<std::uint32_t, 324> words{};
    for (std::size_t index = 0; index < words.size(); ++index) words[index] = word(bytes.data() + index * 4U);
    return words;
}

void validate_input(const std::array<std::uint32_t, 324>& words, std::uint32_t seed) {
    const std::uint32_t multiplier = seed * 2654435761U;
    for (std::size_t index = 0; index < words.size(); ++index) {
        const auto expected = (static_cast<std::uint32_t>(index + 1U) * multiplier)
            ^ (static_cast<std::uint32_t>(index) << (seed & 7U)) ^ (seed * 17U);
        if (words[index] != expected) throw std::runtime_error("dynamic request input does not match seed");
    }
}

void validate_program(const std::array<std::uint32_t, 32>& payload) {
    if (payload[0] != 0x52504731U || payload[1] != 1U || payload[2] < 2U
        || payload[2] > 16U || payload[3] != 8U)
        throw std::runtime_error("dynamic program header is invalid");
    std::array<bool, 8> defined{};
    unsigned stores = 0;
    for (std::size_t index = 0; index < 16; ++index) {
        const std::uint32_t instruction = payload[12U + index];
        const bool active = index < payload[2];
        const auto opcode = instruction >> 28U;
        const auto destination = (instruction >> 25U) & 7U;
        const auto source_a = (instruction >> 22U) & 7U;
        const auto source_b = (instruction >> 19U) & 7U;
        const auto selector = (instruction >> 22U) & 7U;
        const bool load = opcode == 1U && selector <= 4U && (instruction & 0x003fffffU) == 0U;
        const bool add = opcode == 2U && (instruction & 0x0007ffffU) == 0U
            && defined[source_a] && defined[source_b];
        const bool store = opcode == 3U && (instruction & 0x01ffffffU) == 0U
            && defined[destination] && index == payload[2] - 1U;
        if (active && !(load || add || store)) throw std::runtime_error("dynamic program instruction is invalid");
        if (!active && instruction != 0U) throw std::runtime_error("dynamic program padding is nonzero");
        if (load || add) defined[destination] = true;
        if (store) ++stores;
    }
    for (std::size_t index = 28; index < payload.size(); ++index)
        if (payload[index] != 0U) throw std::runtime_error("dynamic program reserved words are nonzero");
    if (stores != 1U) throw std::runtime_error("dynamic program must have one final store");
}
}  // namespace

DynamicGraphDeviceRequest read_dynamic_graph_device_request(const std::filesystem::path& root) {
    const auto bytes = read_request(root);
    const auto inputs = root / "inputs";
    const auto inputs_status = std::filesystem::symlink_status(inputs);
    if (std::filesystem::is_symlink(inputs_status)
        || !std::filesystem::is_directory(inputs_status))
        throw std::runtime_error("dynamic inputs must be a direct directory");
    if (word(bytes.data()) != kMagic || word(bytes.data() + 4) != kVersion
        || word(bytes.data() + 8) != kHeaderBytes || word(bytes.data() + 20) != 32U
        || word(bytes.data() + 24) != 16U || word(bytes.data() + 28) != 324U)
        throw std::runtime_error("dynamic request header is invalid");
    const std::uint32_t profile = word(bytes.data() + 12);
    if (profile > 1U) throw std::runtime_error("dynamic affine profile is invalid");
    for (std::size_t index = 32; index < 64; ++index)
        if (bytes[index] != 0U) throw std::runtime_error("dynamic request reserved prefix is nonzero");
    DynamicGraphDeviceRequest result;
    result.seed = word(bytes.data() + 16);
    const unsigned char* id = bytes.data() + 64;
    std::size_t length = 0;
    while (length < kGraphIdBytes && id[length] != 0U) {
        const unsigned char value = id[length];
        if (!(value >= 'A' && value <= 'Z') && !(value >= 'a' && value <= 'z')
            && !(value >= '0' && value <= '9') && value != '.' && value != '_' && value != '-')
            throw std::runtime_error("dynamic graph identity is invalid");
        ++length;
    }
    if (length == 0 || length > 31 || id[length] != 0U)
        throw std::runtime_error("dynamic graph identity is invalid");
    for (std::size_t index = length + 1; index < kGraphIdBytes; ++index)
        if (id[index] != 0U) throw std::runtime_error("dynamic graph identity padding is invalid");
    if (!(id[0] >= 'A' && id[0] <= 'Z') && !(id[0] >= 'a' && id[0] <= 'z')
        && !(id[0] >= '0' && id[0] <= '9'))
        throw std::runtime_error("dynamic graph identity must start alphanumeric");
    result.graph_id.assign(reinterpret_cast<const char*>(id), length);
    result.affine = profile == 0U ? "baseline" : "compact";
    std::size_t offset = 96;
    for (auto& value : result.program) { value = word(bytes.data() + offset); offset += 4; }
    for (auto& value : result.configuration) { value = word(bytes.data() + offset); offset += 4; }
    for (auto& value : result.input) { value = word(bytes.data() + offset); offset += 4; }
    const auto& canonical = result.affine == "baseline"
        ? affine_generated::kProfiles[0] : affine_generated::kProfiles[1];
    for (std::size_t index = 0; index < result.configuration.size(); ++index)
        if (result.configuration[index] != canonical.payload[index])
            throw std::runtime_error("dynamic affine payload is not canonical");
    validate_program(result.program);
    validate_input(result.input, result.seed);
    const auto request_input = read_input_file(root / "request-input.bin");
    const auto selected_input = read_input_file(
        root / "inputs" / ("seed-" + std::to_string(result.seed) + ".bin"));
    const auto seed_one_input = read_input_file(root / "inputs" / "seed-1.bin");
    if (request_input != result.input || selected_input != result.input)
        throw std::runtime_error("dynamic input files are not bound to request");
    validate_input(seed_one_input, 1U);
    return result;
}
}  // namespace raveil::graph_device
