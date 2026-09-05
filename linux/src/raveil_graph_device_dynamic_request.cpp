#include "raveil_graph_device_dynamic_request.h"

#include "graph_device_affine_generated.h"

#include <array>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <regex>
#include <string>
#include <vector>

namespace raveil::graph_device {
namespace {
constexpr std::uint32_t kMagic = 0x52445731U;
constexpr std::uint32_t kVersionV1 = 1U;
constexpr std::uint32_t kVersionV2 = 2U;
constexpr std::uint32_t kVersionV3 = 3U;
constexpr std::uint32_t kHeaderBytes = 64U;
constexpr std::size_t kGraphIdBytes = 32U;
constexpr std::size_t kRequestBytes = 64U + kGraphIdBytes + (32U + 16U + 324U) * 4U;

std::uint32_t word(const unsigned char* p) {
    return static_cast<std::uint32_t>(p[0])
        | (static_cast<std::uint32_t>(p[1]) << 8U)
        | (static_cast<std::uint32_t>(p[2]) << 16U)
        | (static_cast<std::uint32_t>(p[3]) << 24U);
}

std::uint32_t rotr(std::uint32_t value, unsigned shift) {
    return (value >> shift) | (value << (32U - shift));
}

std::array<unsigned char, 32> sha256(const std::vector<unsigned char>& input) {
    static constexpr std::array<std::uint32_t, 64> k = {
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};
    std::vector<unsigned char> bytes(input);
    const std::uint64_t bits = static_cast<std::uint64_t>(bytes.size()) * 8U;
    bytes.push_back(0x80U);
    while ((bytes.size() % 64U) != 56U) bytes.push_back(0U);
    for (int shift = 56; shift >= 0; shift -= 8) bytes.push_back(static_cast<unsigned char>(bits >> shift));
    std::array<std::uint32_t, 8> state = {0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U};
    for (std::size_t base = 0; base < bytes.size(); base += 64U) {
        std::array<std::uint32_t, 64> schedule{};
        for (unsigned i = 0; i < 16U; ++i) schedule[i] = (static_cast<std::uint32_t>(bytes[base + 4U*i]) << 24U) | (static_cast<std::uint32_t>(bytes[base + 4U*i + 1U]) << 16U) | (static_cast<std::uint32_t>(bytes[base + 4U*i + 2U]) << 8U) | bytes[base + 4U*i + 3U];
        for (unsigned i = 16; i < 64U; ++i) { const auto s0 = rotr(schedule[i-15U], 7U) ^ rotr(schedule[i-15U], 18U) ^ (schedule[i-15U] >> 3U); const auto s1 = rotr(schedule[i-2U], 17U) ^ rotr(schedule[i-2U], 19U) ^ (schedule[i-2U] >> 10U); schedule[i] = schedule[i-16U] + s0 + schedule[i-7U] + s1; }
        auto a=state[0], b=state[1], c=state[2], d=state[3], e=state[4], f=state[5], g=state[6], h=state[7];
        for (unsigned i = 0; i < 64U; ++i) { const auto s1=rotr(e,6U)^rotr(e,11U)^rotr(e,25U); const auto choice=(e&f)^((~e)&g); const auto t1=h+s1+choice+k[i]+schedule[i]; const auto s0=rotr(a,2U)^rotr(a,13U)^rotr(a,22U); const auto majority=(a&b)^(a&c)^(b&c); h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+s0+majority; }
        state[0]+=a; state[1]+=b; state[2]+=c; state[3]+=d; state[4]+=e; state[5]+=f; state[6]+=g; state[7]+=h;
    }
    std::array<unsigned char, 32> output{};
    for (unsigned i = 0; i < 8U; ++i) for (unsigned j = 0; j < 4U; ++j) output[4U*i+j] = static_cast<unsigned char>(state[i] >> (24U - 8U*j));
    return output;
}

std::string sha256_hex(const std::vector<unsigned char>& input) {
    static constexpr char digits[] = "0123456789abcdef";
    const auto digest = sha256(input);
    std::string result;
    result.reserve(64U);
    for (const auto byte : digest) { result.push_back(digits[byte >> 4U]); result.push_back(digits[byte & 15U]); }
    return result;
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

std::array<std::uint32_t, 256> read_output_file(const std::filesystem::path& path) {
    const auto status = std::filesystem::symlink_status(path);
    if (std::filesystem::is_symlink(status) || !std::filesystem::is_regular_file(status)
        || std::filesystem::file_size(path) != 256U * 4U)
        throw std::runtime_error("dynamic oracle is not an exact regular file");
    std::array<unsigned char, 256U * 4U> bytes{};
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!input || input.peek() != EOF) throw std::runtime_error("dynamic oracle read failed");
    std::array<std::uint32_t, 256> words{};
    for (std::size_t index = 0; index < words.size(); ++index) words[index] = word(bytes.data() + index * 4U);
    return words;
}

std::vector<unsigned char> exact_file(const std::filesystem::path& path, std::size_t bytes) {
    const auto status = std::filesystem::symlink_status(path);
    if (std::filesystem::is_symlink(status) || !std::filesystem::is_regular_file(status)
        || std::filesystem::file_size(path) != bytes)
        throw std::runtime_error("sealed dynamic payload is not an exact regular file");
    std::vector<unsigned char> result(bytes);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char*>(result.data()), static_cast<std::streamsize>(result.size()));
    if (!input || input.peek() != EOF) throw std::runtime_error("sealed dynamic payload read failed");
    return result;
}

template <std::size_t Count>
std::vector<unsigned char> words_bytes(const std::array<std::uint32_t, Count>& words) {
    std::vector<unsigned char> result;
    result.reserve(Count * 4U);
    for (const auto value : words)
        for (unsigned shift = 0; shift < 32U; shift += 8U)
            result.push_back(static_cast<unsigned char>(value >> shift));
    return result;
}

void validate_input(const std::array<std::uint32_t, 324>& words, std::uint32_t seed) {
    const std::uint32_t multiplier = seed * 2654435761U;
    for (std::size_t index = 0; index < words.size(); ++index) {
        const auto expected = (static_cast<std::uint32_t>(index + 1U) * multiplier)
            ^ (static_cast<std::uint32_t>(index) << (seed & 7U)) ^ (seed * 17U);
        if (words[index] != expected) throw std::runtime_error("dynamic request input does not match seed");
    }
}

void validate_program(const std::array<std::uint32_t, 32>& payload, std::uint32_t request_version) {
    if (payload[0] != 0x52504731U || payload[1] != request_version ||
        (request_version != kVersionV1 && request_version != kVersionV2
            && request_version != kVersionV3) || payload[2] < 2U
        || payload[2] > 16U || payload[3] != 8U)
        throw std::runtime_error("dynamic program header is invalid");
    std::vector<unsigned char> digest_input;
    for (std::size_t index = 0; index <= payload[2]; ++index) {
        const std::uint32_t value = index == 0U ? payload[2] : payload[11U + index];
        for (unsigned shift = 0; shift < 32U; shift += 8U)
            digest_input.push_back(static_cast<unsigned char>(value >> shift));
    }
    const auto digest = sha256(digest_input);
    for (unsigned index = 0; index < 8U; ++index)
        if (payload[4U + index] != word(digest.data() + index * 4U))
            throw std::runtime_error("dynamic program digest is invalid");
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
        const auto row_bits = (instruction >> 20U) & 31U;
        const auto column_bits = (instruction >> 15U) & 31U;
        const bool signed_unit_row = row_bits == 0U || row_bits == 1U || row_bits == 31U;
        const bool signed_unit_column = column_bits == 0U || column_bits == 1U
            || column_bits == 31U;
        const bool legacy_load = request_version != kVersionV3 && selector <= 4U
            && (instruction & 0x003fffffU) == 0U;
        const bool relative_load = request_version == kVersionV3
            && signed_unit_row && signed_unit_column
            && (instruction & 0x00007fffU) == 0U;
        const bool load = opcode == 1U && (legacy_load || relative_load);
        const bool add = opcode == 2U && (instruction & 0x0007ffffU) == 0U
            && defined[source_a] && defined[source_b];
        const bool max_u32 = opcode == 4U
            && (request_version == kVersionV2 || request_version == kVersionV3)
            && (instruction & 0x0007ffffU) == 0U && defined[source_a] && defined[source_b];
        const bool store = opcode == 3U && (instruction & 0x01ffffffU) == 0U
            && defined[destination] && index == payload[2] - 1U;
        if (active && !(load || add || max_u32 || store)) throw std::runtime_error("dynamic program instruction is invalid");
        if (!active && instruction != 0U) throw std::runtime_error("dynamic program padding is nonzero");
        if (load || add || max_u32) defined[destination] = true;
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
    const std::uint32_t request_version = word(bytes.data() + 4);
    if (word(bytes.data()) != kMagic || (request_version != kVersionV1
        && request_version != kVersionV2 && request_version != kVersionV3)
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
    validate_program(result.program, request_version);
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

ProjectedDynamicGraphDeviceRequest read_projected_dynamic_graph_device_request(
    const std::filesystem::path& root
) {
    const auto status = std::filesystem::symlink_status(root);
    if (std::filesystem::is_symlink(status) || !std::filesystem::is_directory(status))
        throw std::runtime_error("projected dynamic root must be a direct directory");
    const auto request_bytes = exact_file(root / "request.bin", kRequestBytes);
    const auto request = read_dynamic_graph_device_request(root);
    if (request.program[1] != kVersionV2)
        throw std::runtime_error("projected dynamic request must be v2");
    const auto oracle = read_output_file(root / "request-oracle.bin");
    const auto binding_status = std::filesystem::symlink_status(root / "seal-binding.json");
    if (std::filesystem::is_symlink(binding_status) || !std::filesystem::is_regular_file(binding_status)
        || std::filesystem::file_size(root / "seal-binding.json") == 0U
        || std::filesystem::file_size(root / "seal-binding.json") > 4096U)
        throw std::runtime_error("projected dynamic seal binding is invalid");
    const auto binding = exact_file(root / "seal-binding.json", std::filesystem::file_size(root / "seal-binding.json"));
    const std::string binding_text(binding.begin(), binding.end());
    const std::string request_sha = sha256_hex(request_bytes);
    static const std::regex binding_pattern(
        R"bind(^\{"manifest_sha256":"([0-9a-f]{64})","request_sha256":"([0-9a-f]{64})","schema":"raveil\.graph-device-dynamic-sealed-replay/v1","seal_sha256":"([0-9a-f]{64})"\}\n$)bind");
    std::smatch match;
    if (!std::regex_match(binding_text, match, binding_pattern)
        || match[1].str() != match[3].str() || match[2].str() != request_sha)
        throw std::runtime_error("projected dynamic seal binding does not bind request identity");
    return {request, kVersionV2, oracle};
}
}  // namespace raveil::graph_device
