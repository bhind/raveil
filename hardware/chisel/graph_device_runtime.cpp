#include "graph_device_runtime.h"
#include "graph_device_abi_generated.h"

#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

namespace raveil::graph_device {
namespace {

using Input = std::array<std::uint32_t, abi::kInputCount>;
using Output = std::array<std::uint32_t, abi::kOutputCount>;

bool read_exact(std::ifstream& stream, void* data, std::size_t bytes) {
    stream.read(static_cast<char*>(data), static_cast<std::streamsize>(bytes));
    return stream.gcount() == static_cast<std::streamsize>(bytes) && stream.peek() == EOF;
}

std::uint32_t little_u32(const unsigned char* bytes) {
    return static_cast<std::uint32_t>(bytes[0])
        | (static_cast<std::uint32_t>(bytes[1]) << 8U)
        | (static_cast<std::uint32_t>(bytes[2]) << 16U)
        | (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

bool load_input(const std::filesystem::path& path, Input& words) {
    std::array<unsigned char, abi::kInputCount * 4U> bytes{};
    std::ifstream stream(path, std::ios::binary);
    if (!stream || !read_exact(stream, bytes.data(), bytes.size())) {
        return false;
    }
    for (std::size_t index = 0; index < words.size(); ++index) {
        words[index] = little_u32(bytes.data() + index * 4U);
    }
    return true;
}

bool store_output(const std::filesystem::path& path, const Output& words) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) {
        return false;
    }
    for (const std::uint32_t word : words) {
        const std::array<unsigned char, 4> bytes = {
            static_cast<unsigned char>(word),
            static_cast<unsigned char>(word >> 8U),
            static_cast<unsigned char>(word >> 16U),
            static_cast<unsigned char>(word >> 24U),
        };
        stream.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
    }
    return stream.good();
}

bool read_register(DeviceTransport& device, std::uint32_t offset, std::uint32_t& value) {
    const DeviceRead result = device.read_word(offset);
    if (!result.ok) {
        return false;
    }
    value = result.value;
    return true;
}

bool verify_identity(DeviceTransport& device, std::ostream& log, std::ostream& errors) {
    std::uint32_t value = 0;
    if (!read_register(device, abi::kRegIdentity, value) || value != abi::kIdentity
        || !read_register(device, abi::kRegVersion, value) || value != abi::kVersion
        || !read_register(device, abi::kRegInputCount, value) || value != abi::kInputCount
        || !read_register(device, abi::kRegOutputCount, value) || value != abi::kOutputCount) {
        errors << "device scalar identity mismatch\n";
        return false;
    }
    for (std::uint32_t index = 0; index < 8U; ++index) {
        if (!read_register(device, abi::kRegDescriptorBase + index, value)
            || value != abi::kDescriptorWords[index]
            || !read_register(device, abi::kRegConfigBase + index, value)
            || value != abi::kConfigWords[index]
            || !read_register(device, abi::kRegImplementationBase + index, value)
            || value != abi::kImplementationWords[index]) {
            errors << "device digest identity mismatch word=" << index << '\n';
            return false;
        }
    }
    if (!read_register(device, abi::kRegStatus, value)
        || (value & abi::kStatusFault) != 0U) {
        errors << "RTL configuration binding failed\n";
        return false;
    }
    log << "GraphDevice-ABI-V1 status=OK identity=" << std::hex << std::setw(8)
        << std::setfill('0') << abi::kIdentity << std::dec << std::setfill(' ')
        << " descriptor=" << abi::kDescriptorSha256
        << " configuration=" << abi::kConfigurationSha256
        << " implementation=" << abi::kImplementationSha256 << '\n';
    return true;
}

bool stage(DeviceTransport& device, const Input& input, std::ostream& errors) {
    for (std::uint32_t index = 0; index < input.size(); ++index) {
        if (!device.write_word(abi::kInputBase + index, input[index])) {
            errors << "input staging failed word=" << index << '\n';
            return false;
        }
    }
    return true;
}

bool poll_terminal(
    DeviceTransport& device,
    std::uint32_t& status,
    std::uint32_t& polls,
    std::ostream& errors
) {
    for (polls = 1; polls <= abi::kMaxStatusPolls; ++polls) {
        if (!read_register(device, abi::kRegStatus, status)) {
            errors << "status read failed\n";
            return false;
        }
        if ((status & abi::kStatusFault) != 0U) {
            errors << "device reported a sticky fault\n";
            return false;
        }
        if ((status & (abi::kStatusCompleted | abi::kStatusCancelled)) != 0U) {
            return true;
        }
    }
    errors << "finite status timeout exceeded\n";
    return false;
}

bool run_success(
    DeviceTransport& device,
    const std::filesystem::path& root,
    unsigned seed,
    bool restart,
    std::ostream& log,
    std::ostream& errors
) {
    Input input{};
    if (!load_input(root / "inputs" / ("seed-" + std::to_string(seed) + ".bin"), input)) {
        errors << "input file failed seed=" << seed << '\n';
        return false;
    }
    if (!stage(device, input, errors)
        || !device.write_word(abi::kRegControl, abi::kControlStart)) {
        errors << "start failed seed=" << seed << '\n';
        return false;
    }
    std::uint32_t status = 0;
    std::uint32_t polls = 0;
    if (!poll_terminal(device, status, polls, errors)
        || (status & abi::kStatusCompleted) == 0U
        || (status & abi::kStatusCancelled) != 0U
        || (status & abi::kStatusOutputValid) == 0U
        || (status & abi::kStatusBusy) != 0U) {
        errors << "completion state failed seed=" << seed << '\n';
        return false;
    }
    Output output{};
    for (std::uint32_t index = 0; index < output.size(); ++index) {
        if (!read_register(device, abi::kOutputBase + index, output[index])) {
            errors << "private output read failed seed=" << seed
                   << " word=" << index << '\n';
            return false;
        }
    }
    std::uint32_t checksum_low = 0;
    std::uint32_t checksum_high = 0;
    if (!read_register(device, abi::kRegChecksumLow, checksum_low)
        || !read_register(device, abi::kRegChecksumHigh, checksum_high)
        || !store_output(root / ("private-output-seed-" + std::to_string(seed) + ".bin"), output)) {
        errors << "checksum or private output storage failed seed=" << seed << '\n';
        return false;
    }
    const std::uint64_t checksum = static_cast<std::uint64_t>(checksum_low)
        | (static_cast<std::uint64_t>(checksum_high) << 32U);
    log << "GraphDevice-RUN-" << seed << "-V1 status=COMPLETED staged_words=324"
        << " polls=" << polls << " output_valid=1 output_words=256 checksum="
        << std::hex << std::setw(16) << std::setfill('0') << checksum
        << std::dec << std::setfill(' ') << '\n';
    if (restart) {
        log << "GraphDevice-RESET-RESTART-V1 status=OK seed=" << seed << '\n';
    }
    return true;
}

bool run_cancel(
    DeviceTransport& device,
    const std::filesystem::path& root,
    std::ostream& log,
    std::ostream& errors
) {
    Input input{};
    if (!load_input(root / "inputs" / "seed-3.bin", input)
        || !stage(device, input, errors)
        || !device.write_word(abi::kRegControl, abi::kControlStart)) {
        errors << "cancel scenario setup failed\n";
        return false;
    }
    std::uint32_t status = 0;
    for (unsigned index = 0; index < 17U; ++index) {
        if (!read_register(device, abi::kRegStatus, status)
            || (status & abi::kStatusFault) != 0U
            || (status & abi::kStatusCompleted) != 0U) {
            errors << "cancel precondition failed\n";
            return false;
        }
    }
    if (!device.write_word(abi::kRegControl, abi::kControlCancel)) {
        errors << "cancel command failed\n";
        return false;
    }
    std::uint32_t polls = 0;
    if (!poll_terminal(device, status, polls, errors)
        || (status & abi::kStatusCancelled) == 0U
        || (status & (abi::kStatusCompleted | abi::kStatusOutputValid | abi::kStatusBusy)) != 0U) {
        errors << "cancel terminal state failed\n";
        return false;
    }
    if (device.read_word(abi::kOutputBase).ok) {
        errors << "cancelled private output was readable\n";
        return false;
    }
    log << "GraphDevice-CANCEL-V1 seed=3 status=CANCELLED output_valid=0"
        << " output_words=0 blocked_read=1 published=0\n";
    return true;
}

}  // namespace

int run_mvp(
    DeviceTransport& device,
    const std::filesystem::path& evidence_root,
    std::ostream& log,
    std::ostream& errors
) {
    if (!device.write_word(abi::kRegControl, abi::kControlReset)
        || !verify_identity(device, log, errors)
        || !run_success(device, evidence_root, 1U, false, log, errors)
        || !run_cancel(device, evidence_root, log, errors)
        || !device.write_word(abi::kRegControl, abi::kControlReset)
        || !run_success(device, evidence_root, 2U, true, log, errors)) {
        return 1;
    }
    log << "GraphDevice-DEVICE-RUNTIME-V1 status=OK completed=2 cancelled=1 resets=2"
        << " evidence=rtl-simulation-functional performance=not-measured\n";
    return 0;
}

}  // namespace raveil::graph_device
